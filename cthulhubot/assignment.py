from __future__ import absolute_import

import logging
from uuid import uuid4
from copy import deepcopy

from buildbot.process.factory import BuildFactory
from buildbot.scheduler import AnyBranchScheduler, Scheduler
from buildbot.status.builder import SUCCESS, WARNINGS, FAILURE, SKIPPED, EXCEPTION

from django.core.urlresolvers import reverse
from django.utils.simplejson import loads, dumps
from django.utils.safestring import mark_safe

from cthulhubot.err import RemoteCommandError
from cthulhubot.mongo import get_database_connection
from cthulhubot.buildbot import BuildForcer
from cthulhubot.models import ProjectClient
from cthulhubot.builds import Build, BUILD_RESULTS_DICT


log = logging.getLogger("cthulhubot.assignment")

from buildbot.scheduler import Periodic

SCHEDULER_CLASS_MAP = {
    "after_push" : Scheduler,
    "periodic" : Periodic,
}


class Assignment(object):
    """
    Domain object for job assignment, i.e. configured job to be performed on a given computer
    """

    def __init__(self, model):
        super(Assignment, self).__init__()

        self.model = model
        self.computer = model.computer
        self.job = model.job.get_domain_object()
        self.project = model.project

    def create_config(self, configuration):
        if configuration:
            whole_config = deepcopy(configuration)
        else:
            whole_config = {'commands' : []}

        if 'commands' not in whole_config:
            raise ValueError("When creating configuration, I expect 'command' configuration to be present")


        # for command, we want to do special 'assign by validation'

        command_configuration = whole_config['commands']
        whole_config['commands'] = []
        
        for command_no in xrange(0, len(self.job.get_commands())):
            if command_configuration and len(command_configuration) >= command_no+1:
                whole_config['commands'].append(command_configuration[command_no])
            else:
                whole_config['commands'].append({})
        self.model.config = dumps(whole_config)

    def get_master_connection_string(self):
        return self.project.buildmaster.get_master_connection_string()

    def get_absolute_url(self):
        return reverse("cthulhubot-job-assignment-detail", kwargs={
                "assignment_id" : self.get_identifier(),
            })

    def get_factory(self):
        commands = self.job.get_commands()

        factory = BuildFactory()

        if self.model.config:
            config = loads(self.model.config)
            # we're interested only in commands here
            config = config['commands']
        else:
            config = None
        i = 0

        for command in commands:
            conf = None
            if config and config.has_key('commands') and len(config['commands']) >= i+1:
                # empty dict assumed as don't care; otherwise command must be given for integrity

                if not config['commands'][i].has_key('command'):
                    if config['commands'][i].has_key('parameters'):
                        raise ValueError("Parameters present, but command identifier not given: corrupted database?")
                    else:
                        conf = {}
                else:
                    if config['commands'][i]['command'] != command.identifier:
                        raise ValueError("Configuration saved for command %s, but %s is in it's place: config not upgraded?" % (
                            config['commands'][i]['command'], command.identifier
                        ))

                    # no 'parameters' means "don't care"
                    if config['commands'][i].has_key('parameters'):
                        conf = config['commands'][i]['parameters']
                    else:
                        conf = {}

            if conf is None:
                conf = {}
            factory.addStep(command.get_buildbot_command(config=conf, project=self.project, computer=self.computer, job=self.job))
            i += 1
        return factory

    def get_shell_commands(self):
        config = loads(self.model.config)
        if config.has_key('commands'):
            config = config['commands']
        else:
            config = None
        return self.job.get_configured_shell_commands(config=config)

    def force_build(self):
        forcer = BuildForcer(master_string=self.get_master_connection_string())
        forcer.run()
        return forcer

    def get_last_build_status(self):
        db = get_database_connection()
        try:
            build = Build(db.builds.find({'builder' : self.get_identifier(), 'time_end' : {'$ne' : None}}).sort([("time_end", -1)]).limit(1).next())
        except StopIteration:
            return BUILD_RESULTS_DICT[None]

        return build.get_text_result()

    def get_builds(self):
        db = get_database_connection()
        return [build for build in db.builds.find({"builder" : self.get_identifier()}).sort([("number", -1)])]

    builds = property(fget=get_builds)

    def get_identifier(self):
        return str(self.model.pk)

    def get_client(self):
        return ProjectClient.objects.get(project=self.project, computer=self.computer)

    def get_status(self):
        db = get_database_connection()
        builder = db.builders.find_one({'name' : self.get_identifier(), 'master_id' : self.project.get_buildmaster().pk})
        if not builder or 'status' not in builder:
            return 'no builder / no result yet'
        else:
            return builder['status']

    def get_text_status(self):
        return unicode(self.get_status())

    #TODO: Move HTML away
    def get_status_action(self):
        return mark_safe('<input type="submit" name="force_build" value="Force build">')

    def get_schedulers(self):
        config = loads(self.model.config)
        if not 'schedule' in config:
            return [
                    AnyBranchScheduler(name="%s-scheduler" % self.get_identifier(), branches=None, treeStableTimer=1, builderNames=[self.get_identifier()])
            ]

        else:
            schedulers = []
            for scheduler in config['schedule']:
                # monkeypatch: assume that off-branch scheduler is in fact anybranch scheduler
                # this is for backward compatibility
                if scheduler['identifier'] == 'after_push' and (
                    'branch' not in scheduler['parameters'] or not scheduler['parameters']['branch']
                ):
                    klass = AnyBranchScheduler
                    del scheduler['parameters']['branch']
                    scheduler['parameters']['branches'] = None
                else:
                    klass = SCHEDULER_CLASS_MAP[scheduler['identifier']]


                schedulers.append(klass(
                    name="%s-%s" % (self.get_identifier(), str(uuid4())),
                    builderNames=[self.get_identifier()],
                    **dict([(str(key), scheduler['parameters'][key]) for key in scheduler['parameters']])
                ))
            return schedulers

