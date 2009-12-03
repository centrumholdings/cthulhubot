from __future__ import absolute_import

import logging
from django.utils.safestring import mark_safe
import os

from buildbot.process.factory import BuildFactory

from django.core.urlresolvers import reverse
from django.utils.simplejson import loads, dumps

from cthulhubot.err import RemoteCommandError
from cthulhubot.mongo import get_database_connection
from cthulhubot.buildbot import BuildForcer
from cthulhubot.models import ProjectClient
from cthulhubot.builds import Build, BUILD_RESULTS_DICT

from buildbot.status.builder import SUCCESS, WARNINGS, FAILURE, SKIPPED, EXCEPTION

log = logging.getLogger("cthulhubot.assignment")

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

    def create_config(self, command_configuration):
        config = []
        for command_no in xrange(0, len(self.job.get_commands())):
            if command_configuration and len(command_configuration) >= command_no+1:
                config.append(command_configuration[command_no])
            else:
                config.append({})
        self.model.config = dumps(config)

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
        else:
            config = None
        i = 0
        for command in commands:
            if config and len(config) >= i+1 and config[i].has_key('command'):
                if config[i]['command'] != command.identifier:
                    raise ValueError("Configuration saved for command %s, but %s is in it's place: config not upgraded?" % (
                        config[i]['command'], command.identifier
                    ))
                conf = config[i]['parameters']
            else:
                conf = {}
            factory.addStep(command.get_buildbot_command(config=conf))
            i += 1
        return factory

    def get_shell_commands(self):
        return self.job.get_configured_shell_commands(config=loads(self.model.config))

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
        status = self.get_status()

        INPUT_HTML_DICT = {
            AssignmentOffline.ID : mark_safe('<input type="submit" name="start_slave" value="Start"> (but check buildmaster status)'),
            DirectoryNotCreated.ID : mark_safe('<input type="submit" name="create_slave_dir" value="Create directory">'),
            AssignmentReady.ID : mark_safe('<input type="submit" name="force_build" value="Force build">'),
        }

        if status.ID in INPUT_HTML_DICT:
            return INPUT_HTML_DICT[status.ID]
        else:
            return u''


