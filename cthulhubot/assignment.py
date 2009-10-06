import logging
import os
from platform import node

from django.conf import settings
from django.core.urlresolvers import reverse

from cthulhubot.err import RemoteCommandError
from cthulhubot.mongo import get_database_connection

log = logging.getLogger("cthulhubot.assignment")

class Assignment(object):
    """
    Domain object for job assignment, i.e. configured job to be performed on a given computer
    """

    def __init__(self, computer, job, project, model=None):
        super(Assignment, self).__init__()

        self.computer = computer
        self.job = job
        self.project = project
        self.model = model

    def get_build_directory(self):
        return os.path.join(self.computer.get_base_build_directory(), self.get_identifier())

    build_directory = property(fget=get_build_directory)

    def get_master_connection_string(self):
        host = getattr(settings, "BUILDMASTER_NETWORK_NAME", None)
        if not host:
            host = node() or "localhost"
            log.warn("BUILDMASTER_NETWORK_NAME not given, assuming %s" % host)
        return "%s:%s" % (host, self.job.buildmaster.buildmaster_port)


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
        id = self.model.pk
        if not id:
            raise ValueError("I need identifier for directory creation! (JobAssignment model has no ID. Not saved yet?)")
        return str(id)

    def create_build_directory(self):
        username = 'job@host'
        password = 'xxx'

        self.execute_remote_command_for_success(["buildbot", "create-slave", self.build_directory, self.get_master_connection_string(), username, password])
        self.execute_remote_command_for_success(["touch", os.path.join(self.build_directory, 'twistd.log')])

    def get_absolute_url(self):
        return reverse("cthulhubot-job-assignment-detail", kwargs={
                "assignment_id" : self.get_identifier(),
            })

    def get_status_from_database(self):
        db = get_database_connection()
        builder = db.builders.find_one({'name' : self.get_identifier(), 'master_id' : None})
        if not builder:
            return AssignmentOffline()
        else:
            #TODO: map status from buildbot to result object
            raise NotImplementedError()

    def get_status(self):

        if not self.builder_running() and not self.build_directory_exists():
            status = DirectoryNotCreated()
        else:
            status = self.get_status_from_database()

        return status

    def execute_remote_command_for_success(self, cmd):
        status = self.computer.get_command_return_status(cmd)

        if status != 0:
            raise RemoteCommandError("Command '%s' exited with status %s." % (str(cmd), status))

    def start(self):
        self.execute_remote_command_for_success(["buildbot", "start", self.build_directory])

    def stop(self):
        self.execute_remote_command_for_success(["buildbot", "stop", self.build_directory])


class AssignmentStatus(object):
    ID = None

class DirectoryNotCreated(AssignmentStatus):
    ID = 1

class AssignmentOffline(AssignmentStatus):
    ID = 2

class AssignmentRunning(AssignmentStatus):
    ID = 3

class AssignmentReady(AssignmentStatus):
    ID = 4

