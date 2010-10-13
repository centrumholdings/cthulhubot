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
from cthulhubot.bbot import BuildForcer
from cthulhubot.models import ProjectClient
from cthulhubot.builds import Build, BUILD_RESULTS_DICT


log = logging.getLogger("cthulhubot.assignment")

from buildbot.scheduler import Periodic, Nightly

SCHEDULER_CLASS_MAP = {
    "after_push" : Scheduler,
    "periodic" : Periodic,
    "nightly" : Nightly,
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

    def upgrade_config(self, config):
        """
        Iterate through rest of upgrades. No version means 0, = all of 'em.
        Version is assigned as the lenght of the upgrades list. Thus,

        **********************************************************************
        *** NEVER REMOVE UPGRADE FUNCTIONS FROM UPGRADE LIST AFTER DEPLOYMENT
        **********************************************************************

        If You'll do so, upgrades may be reapplied, 500's may be rised and kittens
        could be eaten.

        It's up to individual upgrades to decide whether they would like to upgrade
        themselves or not. They must not set layout.changed flag, as version upgrade
        must be recorded anyway.

        Upgrades MUST return new configuration dictionary, please do not do thing mutably.

        Each job assignment is upgraded separately; it's up to job to decide what
        to do with it's command minions. When not given, empty upgrades list is assumed.
        """
        job_upgrades = getattr(self.job, 'upgrades', [])

        if self.model.version < len(job_upgrades):
            for upgrade in job_upgrades[self.configuration_version:]:
                config = upgrade(config)

        self.model.version = len(job_upgrades)
        self.model.save()

        return config



    def get_factory(self):
        commands = self.job.get_commands()

        factory = BuildFactory()

        config = None
        if self.model.config:
            config = loads(self.model.config)
            if self.configuration_version < self.job_version:
                config = self.upgrade_config(config)


            # we're interested only in commands here
            if config.has_key('commands'):
                config = config['commands']
        i = 0

        for command in commands:
            conf = None
            if config and len(config) >= i+1:
                # empty dict assumed as don't care; otherwise command must be given for integrity

                if not config[i].has_key('command'):
                    if config[i].has_key('parameters'):
                        raise ValueError("Parameters present, but command identifier not given: corrupted database?")
                    else:
                        conf = {}
                else:
                    if config[i]['command'] != command.identifier:
                        raise ValueError("Configuration saved for command %s, but %s is in it's place: config not upgraded?" % (
                            config[i]['command'], command.identifier
                        ))

                    # no 'parameters' means "don't care"
                    if config[i].has_key('parameters'):
                        conf = config[i]['parameters']
                    else:
                        conf = {}

            if conf is None:
                conf = {}
            factory.addStep(command.get_buildbot_command(config=conf, project=self.project, computer=self.computer, job=self.job))
            i += 1
        return factory

    def get_shell_commands(self):
        return self.job.get_configured_shell_commands(loads(self.model.config))

    def force_build(self):
        forcer = BuildForcer(master=self.model.project.buildmaster, assignment=self)
        forcer.run()
        return forcer

    def get_last_build_status(self):
        db = get_database_connection()
        try:
            build = Build(db.builds.find({'builder' : self.get_identifier(), 'time_end' : {'$ne' : None}}).sort([("time_end", -1)]).limit(1).next())
        except StopIteration:
            return BUILD_RESULTS_DICT["no-result"]

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
                AnyBranchScheduler(name="%s-scheduler" % self.get_identifier(), treeStableTimer=1, builderNames=[self.get_identifier()])
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
                else:
                    klass = SCHEDULER_CLASS_MAP[scheduler['identifier']]


                schedulers.append(klass(
                    name="%s-%s" % (self.get_identifier(), str(uuid4())),
                    builderNames=[self.get_identifier()],
                    **dict([(str(key), scheduler['parameters'][key]) for key in scheduler['parameters']])
                ))
            return schedulers

    def delete(self, *args, **kwargs):
        return self.model.delete(*args, **kwargs)

    def get_configuration_version(self):
        return self.model.version

    def get_job_version(self):
        return len(getattr(self.job, 'upgrades', []))

    configuration_version = property(fget=get_configuration_version)
    job_version = property(fget=get_job_version)