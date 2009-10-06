import logging
import os
from platform import node

from django.conf import settings
from django.core.urlresolvers import reverse

from cthulhubot.err import RemoteCommandError

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

    def builder_running(self, directory):
        pid_file = os.path.join(directory, 'twistd.pid')
        cmd = ["test", "-f", "\"%(pid)s\"", "&&", "test", "-d", "/proc/`cat \"%(pid)s\"`"  % {'pid  ' : pid_file},]
        return self.computer.get_command_return_status(cmd) == 0


    def get_identifier(self):
        id = self.model.pk
        if not id:
            raise ValueError("I need identifier for directory creation! (JobAssignment model has no ID. Not saved yet?)")
        return str(id)

    def create_build_directory(self):

        username = 'job@host'
        password = 'xxx'

        cmd = ["buildbot", "create-slave", self.build_directory, self.get_master_connection_string(), username, password]
        status = self.computer.get_command_return_status(cmd)

        if status != 0:
            raise RemoteCommandError("Command '%s' exited with status %s" % (str(cmd), status))

    def get_absolute_url(self):
        return reverse("cthulhubot-job-assignment-detail", kwargs={
                "assignment_id" : self.get_identifier(),
            })

    def get_status(self):
        # first ask buidmaster for OK status
        master = self.project.buildmaster

        if not master.is_running():
            return BuildmasterOffline()
        


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

class BuildmasterOffline(AssignmentStatus):
    ID = 5
