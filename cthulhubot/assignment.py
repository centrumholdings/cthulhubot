from __future__ import absolute_import

import logging
from django.utils.safestring import mark_safe
import os
from platform import node

from buildbot.process.factory import BuildFactory

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.simplejson import loads

from cthulhubot.err import RemoteCommandError
from cthulhubot.mongo import get_database_connection
from cthulhubot.buildbot import BuildForcer
from cthulhubot.models import ProjectClient

log = logging.getLogger("cthulhubot.assignment")

from buildbot.status.builder import SUCCESS, WARNINGS, FAILURE, SKIPPED, EXCEPTION

BUILD_RESULTS_DICT = {
    SUCCESS : "Success",
    WARNINGS : "Warning",
    FAILURE : "Failure",
    SKIPPED : "Skipped",
    EXCEPTION : "Exception",
    None : "No result yet",
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

    def get_build_directory(self):
        return os.path.join(self.computer.get_base_build_directory(), self.get_identifier())

    build_directory = property(fget=get_build_directory)

    def get_master_connection_string(self):
        host = getattr(settings, "BUILDMASTER_NETWORK_NAME", None)
        if not host:
            host = node() or "127.0.0.1"
            log.warn("BUILDMASTER_NETWORK_NAME not given, assuming %s" % host)
        return "%s:%s" % (host, self.project.buildmaster.buildmaster_port)


    def build_directory_exists(self):
        return self.computer.build_directory_exists(self.build_directory)

    def builder_running(self, directory=None):
        directory = directory or self.build_directory
        pid_file = os.path.join(directory, 'twistd.pid')
        cmd = ["test", "-f", pid_file]
        if self.computer.get_command_return_status(cmd) != 0:
            return False
        cmd = ["test", "-d", "/proc/`cat \"%(pid)s\"`"  % {'pid' : pid_file}]
        return self.computer.get_command_return_status(cmd) == 0

    def get_identifier(self):
        return self.model.get_identifier()

    def get_client(self):
        return ProjectClient.objects.get(project=self.model.project, computer=self.model.computer)

    def create_build_directory(self, username=None, password=None):
        username = username or self.get_client().get_name()
        password = password or self.get_client().password

        self.execute_remote_command_for_success(["buildbot", "create-slave", self.build_directory, self.get_master_connection_string(), username, password])
        self.execute_remote_command_for_success(["touch", os.path.join(self.build_directory, 'twistd.log')])

    def get_absolute_url(self):
        return reverse("cthulhubot-job-assignment-detail", kwargs={
                "assignment_id" : self.get_identifier(),
            })

    def get_status_from_database(self):
        db = get_database_connection()
        builder = db.builders.find_one({'name' : self.get_identifier(), 'master_id' : self.model.project.get_buildmaster().pk})
        if not builder:
            return AssignmentOffline()
        else:

            BUILDBOT_ASSIGNMENT_STATUS_MAP = {
                'offline' : AssignmentOffline,
                'building' : AssignmentRunning,
                'idle' : AssignmentReady
            }

            if builder['status'] not in BUILDBOT_ASSIGNMENT_STATUS_MAP:
                raise ValueError("Received unexpected BuildBot status %s" % builder['status'])

            return BUILDBOT_ASSIGNMENT_STATUS_MAP[builder['status']]()
            

    def get_status(self):
        if not self.builder_running() and not self.build_directory_exists():
            status = DirectoryNotCreated()
        else:
            status = self.get_status_from_database()

        return status

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


    def get_factory(self):
        commands = self.job.get_commands()

        factory = BuildFactory()

        if self.model.config:
            config = loads(self.model.config)
        else:
            config = {}
        i = 0
        for command in commands:
            try:
                conf = config['commands'][i]['parameters']
            except KeyError:
                conf = {}
            factory.addStep(command.get_buildbot_command(config=conf))
            i += 1
        return factory

    def execute_remote_command_for_success(self, cmd):
        status = self.computer.get_command_return_status(cmd)

        if status != 0:
            raise RemoteCommandError("Command '%s' exited with status %s." % (str(cmd), status))

    def start(self):
        self.execute_remote_command_for_success(["buildbot", "start", self.build_directory])

    def stop(self):
        self.execute_remote_command_for_success(["buildbot", "stop", self.build_directory])

    def get_shell_commands(self):
        return self.job.get_configured_shell_commands(config=loads(self.model.config))

    def force_build(self):
        forcer = BuildForcer(master_string=self.get_master_connection_string())
        forcer.run()
        return forcer

    def get_last_build_status(self):
        db = get_database_connection()
        try:
            build = db.builds.find({'builder' : self.get_identifier(), 'time_end' : {'$ne' : None}}).sort([("time_end", -1)]).limit(1).next()
        except StopIteration:
            return BUILD_RESULTS_DICT[None]

        result = None
        priorities = [SKIPPED, SUCCESS, WARNINGS, FAILURE, EXCEPTION]

        for step in build['steps']:
            if step.get('time_end', None):
                if not result:
                    result = step['result']
                else:
                    if priorities.index(step['result']) > priorities.index(result):
                        result = step['result']
            else:
                log.debug("Step %s without time_end, not considering" % str(step))

        return BUILD_RESULTS_DICT[result]


    def get_build_directory(self):
        return os.path.join(self.computer.get_base_build_directory(), self.get_identifier())

    build_directory = property(fget=get_build_directory)

    def get_master_connection_string(self):
        host = getattr(settings, "BUILDMASTER_NETWORK_NAME", None)
        if not host:
            host = node() or "127.0.0.1"
            log.warn("BUILDMASTER_NETWORK_NAME not given, assuming %s" % host)
        return "%s:%s" % (host, self.project.buildmaster.buildmaster_port)


    def build_directory_exists(self):
        return self.computer.build_directory_exists(self.build_directory)

    def builder_running(self, directory=None):
        directory = directory or self.build_directory
        pid_file = os.path.join(directory, 'twistd.pid')
        cmd = ["test", "-f", pid_file]
        if self.computer.get_command_return_status(cmd) != 0:
            return False
        cmd = ["test", "-d", "/proc/`cat \"%(pid)s\"`"  % {'pid' : pid_file}]
        return self.computer.get_command_return_status(cmd) == 0


    def get_identifier(self):
        return str(self.model.pk)

    def get_client(self):
        return ProjectClient.objects.get(project=self.project, computer=self.computer)

    def create_build_directory(self, username=None, password=None):
        username = username or self.get_client().get_name()
        password = password or self.get_client().password

        self.execute_remote_command_for_success(["buildbot", "create-slave", self.build_directory, self.get_master_connection_string(), username, password])
        self.execute_remote_command_for_success(["touch", os.path.join(self.build_directory, 'twistd.log')])

    def get_status_from_database(self):
        db = get_database_connection()
        builder = db.builders.find_one({'name' : self.get_identifier(), 'master_id' : self.project.get_buildmaster().pk})
        if not builder:
            return AssignmentOffline()
        else:

            BUILDBOT_ASSIGNMENT_STATUS_MAP = {
                'offline' : AssignmentOffline,
                'building' : AssignmentRunning,
                'idle' : AssignmentReady
            }

            if builder['status'] not in BUILDBOT_ASSIGNMENT_STATUS_MAP:
                raise ValueError("Received unexpected BuildBot status %s" % builder['status'])

            return BUILDBOT_ASSIGNMENT_STATUS_MAP[builder['status']]()


    def get_status(self):
        if not self.builder_running() and not self.build_directory_exists():
            status = DirectoryNotCreated()
        else:
            status = self.get_status_from_database()
        return status

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


class AssignmentStatus(object):
    ID = None

    def __init__(self, status=None):
        super(AssignmentStatus, self).__init__()
        self.status = status

    def __unicode__(self):
        return self.status or self.DEFAULT_STATUS


class DirectoryNotCreated(AssignmentStatus):
    ID = 1
    DEFAULT_STATUS = u"Buildslave directory not created yet"

class AssignmentOffline(AssignmentStatus):
    ID = 2
    DEFAULT_STATUS = u"Offline, not connected to buildmaster"

class AssignmentRunning(AssignmentStatus):
    ID = 3
    DEFAULT_STATUS = u"Running"

class AssignmentReady(AssignmentStatus):
    ID = 4
    DEFAULT_STATUS = u"Connected and ready"

class AssignmentStatusError(AssignmentStatus):
    ID = 4
    DEFAULT_STATUS = u"Problem with assignment status"
