from __future__ import absolute_import

from copy import copy
import logging
import os
from platform import node
from shutil import rmtree
from subprocess import PIPE, CalledProcessError, Popen
import sys
from tempfile import gettempdir
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.generic import GenericForeignKey, GenericRelation

from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils import simplejson
from django.db import models

from cthulhubot.utils import check_call
from cthulhubot.commands import get_command
from cthulhubot.err import UndiscoveredCommandError, CommunicationError, RemoteCommandError
from cthulhubot.jobs import get_job
from cthulhubot.mongo import get_database_connection, get_database_name, get_database_info
from cthulhubot.computer import LocalComputerAdapter, RemoteComputerAdapter

from buildbot.changes.pb import PBChangeSource
from buildbot.buildslave import BuildSlave
from buildbot.scheduler import Scheduler

from bbmongostatus.status import MongoDb

from django.conf import settings

DEFAULT_BUILDMASTER_BASEDIR = gettempdir()
log = logging.getLogger("cthulhubot.models")


class BuildComputer(models.Model):
    """
    Computer with installed operating system we own
    """
    name = models.CharField(max_length=40, unique=True)
    slug = models.CharField(max_length=40, unique=True)
    description = models.TextField()
    hostname = models.CharField(max_length=255, unique=True)

    username = models.CharField(max_length=40)
    ssh_key = models.TextField(blank=True)
    basedir = models.CharField(max_length=255, default="/var/buildslaves")

    def __init__(self, *args, **kwargs):
        super(BuildComputer, self).__init__(*args, **kwargs)
        self._domain_object = None

        port = 22

        if self.hostname in ("localhost", "127.0.0.1", "::1"):
            self.adapter = LocalComputerAdapter()
        else:
            self.adapter = RemoteComputerAdapter(hostname=self.hostname, username=self.username, ssh_key=self.ssh_key, port=port)

    def get_absolute_url(self):
        return reverse("cthulhubot-computer-detail", kwargs={
                "computer" : self.slug,
            })

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError, e:
            if hasattr(self.adapter, name):
                return getattr(self.adapter, name)
            raise

    def __unicode__(self):
        return self.name

    def build_directory_exists(self, directory):
        return self.get_command_return_status(["test", "-d", directory]) == 0

    def get_base_build_directory(self):
        return self.basedir


    def create_build_directory(self, *args, **kwargs):
        self.assignment.create_build_directory(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(BuildComputer, self).save(*args, **kwargs)



class Command(models.Model):
    slug = models.CharField(max_length=255, unique=True)

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        self._command = None

    def get_command(self, config=None):
        if config:
            self.command.update_config(config)
        return self.command.get_command()

    def get_command_config(self):
        return None
#        try:
#            config = CommandConfiguration.objects.get()

    def get_command_class(self):
        if not self._command:
            self._command = get_command(slug=self.slug)()
            if not self._command:
                raise ValueError(u"Command %s cannot be resolved" % self.slug)

        return self._command

    command = property(fget=get_command_class)

    def save_configuration(self, job, config_options):
        command_config = {}
        for config in config_options:
            if config in self.command.parameters:
                command_config[config] = config_options[config]

        CommandConfiguration.objects.create(
            job = job,
            command = self,
            config = simplejson.dumps(command_config)
        )

    def __unicode__(self):
        return self.slug


class Job(models.Model):
    slug = models.CharField(max_length=255, unique=True)

    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)

        self._job = None

    def get_domain_object(self):
        if not self._job:
            self._job = get_job(slug=self.slug)(model=self)
            if not self._job:
                raise ValueError(u"Job %s cannot be resolved" % self.slug)

        return self._job
    
    # backward compatibility
    get_job_class = get_domain_object

    def get_commands(self):
        return self.get_domain_object().get_commands()

    def auto_discovery(self):
        job = get_job(self.slug)()
        for command in job.get_commands():
            Command.objects.get_or_create(slug=command.identifier)

    def __unicode__(self):
        return self.slug

class Project(models.Model):
    name = models.CharField(max_length=40)
    slug = models.CharField(max_length=40, unique=True)
    tracker_uri = models.URLField(max_length=255, verify_exists=False)
    repository_uri = models.TextField()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(Project, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("cthulhubot-project-detail", kwargs={
                "project" : self.slug,
            })

    def get_buildmaster(self):
        masters = self.buildmaster_set.all()
        assert len(masters) == 1
        return masters[0]

    buildmaster = property(fget=get_buildmaster)

    def delete(self, *args, **kwargs):
        for master in self.buildmaster_set.all():
            master.delete()
        
        super(Project, self).delete(*args, **kwargs)

class JobAssignment(models.Model):
    job = models.ForeignKey(Job)
    computer = models.ForeignKey(BuildComputer)
    project = models.ForeignKey(Project)
    config = models.TextField()

    # config structure:
#    config = {
#        'slots' : {
#            '$slot' : '$command-slug'
#        },
#        'commands' : [
#            {
#                'identifier' : '$command-slugname',
#                'parameters' : {
#                   '$param' : '$value'
#                }
#            }
#        ]
#    }


    unique_together = (("job", "project", "computer"),)

    def get_identifier(self):
        if not self.pk:
            raise ValueError("Cannot identify myself yet!")
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("cthulhubot-job-assignment-detail", kwargs={
                "assignment_id" : self.get_identifier(),
            })

    def get_domain_object(self):
        from cthulhubot.assignment import Assignment
        return Assignment(model = self)

class ClientStatus(object):
    ID = None

    def __init__(self, status=None):
        super(ClientStatus, self).__init__()
        self.status = status

    def __unicode__(self):
        return self.status or self.DEFAULT_STATUS


class DirectoryNotCreated(ClientStatus):
    ID = 1
    DEFAULT_STATUS = u"Buildslave directory not created yet"

class ClientOffline(ClientStatus):
    ID = 2
    DEFAULT_STATUS = u"Offline, not connected to buildmaster"

class ClientRunning(ClientStatus):
    ID = 3
    DEFAULT_STATUS = u"Running"

class ClientReady(ClientStatus):
    ID = 4
    DEFAULT_STATUS = u"Connected and ready"

class StatusError(ClientStatus):
    ID = 4
    DEFAULT_STATUS = u"Problem with Client status"

class ProjectClient(models.Model):
    project = models.ForeignKey(Project)
    computer = models.ForeignKey(BuildComputer)
    password = models.CharField(max_length=36)

    unique_together = (("project", "computer"),)


    def generate_password(self):
        if not self.password:
            self.password = str(uuid4())

    def get_name(self):
        return '%s-at-%s' % (self.project.slug, self.computer.slug)

    def start(self):
        self.execute_remote_command_for_success(["buildbot", "start", self.build_directory])

    def stop(self):
        self.execute_remote_command_for_success(["buildbot", "stop", self.build_directory])

    def execute_remote_command_for_success(self, cmd):
        status = self.computer.get_command_return_status(cmd)

        if status != 0:
            raise RemoteCommandError("Command '%s' exited with status %s." % (str(cmd), status))

    def get_identifier(self):
        return str(self.pk)

    def get_build_directory(self):
        return os.path.join(self.computer.get_base_build_directory(), self.get_identifier())

    build_directory = property(fget=get_build_directory)

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

    def create_build_directory(self, username=None, password=None):
        username = username or self.get_name()
        password = password or self.password

        self.execute_remote_command_for_success(["buildbot", "create-slave", self.build_directory, self.get_master_connection_string(), username, password])
        self.execute_remote_command_for_success(["touch", os.path.join(self.build_directory, 'twistd.log')])

    def get_master_connection_string(self):
        return self.project.buildmaster.get_master_connection_string()

    def get_status_from_database(self):
        db = get_database_connection()
        builder = db.builders.find_one({'name' : self.get_identifier(), 'master_id' : self.project.get_buildmaster().pk})
        if not builder:
            return ClientOffline()
        else:
            BUILDBOT_CLIENT_STATUS_MAP = {
                'offline' : ClientOffline,
                'building' : ClientRunning,
                'idle' : ClientReady
            }

            if builder['status'] not in BUILDBOT_CLIENT_STATUS_MAP:
                raise ValueError("Received unexpected BuildBot status %s" % builder['status'])

            return BUILDBOT_CLIENT_STATUS_MAP[builder['status']]()

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
        from django.utils.safestring import mark_safe

        INPUT_HTML_DICT = {
            ClientOffline.ID : mark_safe('<input type="submit" name="start_slave" value="Start"> (but check buildmaster status)'),
            DirectoryNotCreated.ID : mark_safe('<input type="submit" name="create_slave_dir" value="Create directory">'),
        }

        if status.ID in INPUT_HTML_DICT:
            return INPUT_HTML_DICT[status.ID]
        else:
            return u''


class Buildmaster(models.Model):
    webstatus_port = models.PositiveIntegerField(unique=True)
    buildmaster_port = models.PositiveIntegerField(unique=True)
    project = models.ForeignKey(Project, unique=True)
    directory = models.CharField(unique=True, max_length=255)
    password = models.CharField(max_length=40)

    port_attributes = ("webstatus_port", "buildmaster_port")

    REALM = "buildmaster"

    def get_master_connection_string(self):
        host = getattr(settings, "BUILDMASTER_NETWORK_NAME", None)
        if not host:
            host = node() or "127.0.0.1"
            log.warn("BUILDMASTER_NETWORK_NAME not given, assuming %s" % host)
        return "%s:%s" % (host, self.buildmaster_port)



    def generate_new_port(self, attr, settings_attr, settings_default):
        try:
            obj = self.__class__.objects.all().order_by('-%s' % attr)[0]
            return getattr(obj, attr)+1
        except IndexError:
            return getattr(settings, settings_attr, settings_default)

    def generate_buildmaster_directory(self):
        base_dir = getattr(settings, "CTHULHUBOT_BUILDMASTER_BASEDIR", DEFAULT_BUILDMASTER_BASEDIR)
        return os.path.join(base_dir, self.project.slug)

    def check_port_uniqueness(self):
        # from database administrators POV, this is ugly & awful, but given
        # the expected number of buildmasters & frequency of creation, it should
        # be OK. Patches welcomed.
        new_ports = [getattr(self, attr) for attr in self.port_attributes]
        if len(set(new_ports)) != len(new_ports):
            for i in new_ports:
                if new_ports.count(i) > 1:
                    port = i

            raise ValidationError("Port number %s attempted to be used for multiple services" % port)

        for port in new_ports:
            candidates = [
                len(self.__class__.objects.filter(**{
                    "%s__exact" % attr : port
                }))
                for attr in self.port_attributes
            ]

            if sum(candidates) > 0:
                raise ValidationError("Port %s already in use" % port)

    def generate_webstatus_port(self):
        return self.generate_new_port("webstatus_port", "GENERATED_WEBSTATUS_PORT_START", 8020)

    def generate_buildmaster_port(self):
        return self.generate_new_port("buildmaster_port", "GENERATED_BUILDMASTER_PORT_START", 12000)

    def generate_password(self):
        return str(uuid4())

    def get_webstatus_uri(self):
        host = getattr(settings, "BUILDMASTER_NETWORK_NAME", None)
        if not host:
            host = node() or "127.0.0.1"
            log.warn("BUILDMASTER_NETWORK_NAME not given, assuming %s" % host)
        return 'http://%s:%s/' % (host, self.webstatus_port)

    webstatus_uri = property(fget=get_webstatus_uri)

    def get_waterfall_uri(self):
        return self.get_webstatus_uri() + "waterfall"

    def save(self, *args, **kwargs):
        if not self.webstatus_port:
            self.webstatus_port = self.generate_webstatus_port()

        if not self.buildmaster_port:
            self.buildmaster_port = self.generate_buildmaster_port()

        if not self.directory:
            self.directory = self.generate_buildmaster_directory()

        if not self.password:
            self.password = self.generate_password()

        self.check_port_uniqueness()

        super(Buildmaster, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(Buildmaster, self).delete(*args, **kwargs)

        if self.is_running():
            self.stop()

        if os.path.exists(self.directory):
            rmtree(self.directory)

    def get_buildbot_environment(self, env):
        e = copy(os.environ)
        env = env or {}
        e.update(env)

        import cthulhubot
        # PYTHONPATH and DJANGO_SETTINGS_MODULE must be present for child process
        if not e.has_key('PYTHONPATH'):
            e.update({
                "PYTHONPATH" : ":".join(sys.path)
            })

        if not e.has_key('DJANGO_SETTINGS_MODULE'):
            e.update({
                "DJANGO_SETTINGS_MODULE" : "settings"
            })

        return e

    def start(self, env=None):
        e = self.get_buildbot_environment(env)

        check_call(["buildbot", "start", self.directory], env=e, cwd=self.directory,
            stdout=PIPE, stderr=PIPE)

    def stop(self, env=None, ignore_not_running=False):
        e = self.get_buildbot_environment(env)
        cmd = ["buildbot", "stop", self.directory]
        popen = Popen(cmd, env=e, cwd=self.directory,
            stdout=PIPE, stderr=PIPE)
        stdout, stderr = popen.communicate()
        retcode = popen.returncode
        if retcode:
            log.error("Calling process failed. STDOUT: %s STDERR: %s" % (stdout, stderr))
            if "BuildbotNotRunningError" not in stderr and not ignore_not_running:
                raise CalledProcessError(retcode, cmd)

    def is_running(self):
        """ Is buildmaster process running? Return True if process found, False otherwise.

        #TODO: This will now work only for linux, which is my target platform.
        It could probably be modified for BSD with os.kill(pid, 0), anyone to test it?
        Also, any windows guru for a win way?
        """
        # This will work only on linux, which is my target platform

        pid_file = os.path.join(self.directory, 'twistd.pid')
        if not os.path.exists(pid_file):
            return False

        f = open(pid_file)
        pid = f.read()
        f.close()

        try:
            pid = int(pid)
        except ValueError:
            return False

        return os.path.exists("/proc/%s" % pid)


    def get_text_status(self):
        if self.is_running():
            return "Running"
        else:
            return "Not running"

    def get_config(self):

        #computers = project.job_set.buildcomputer_set.all()
        assignments = self.project.jobassignment_set.all()
#        computers = assignments.computers_set.all()

        db_info = get_database_info()

        config = {
            'slavePortnum' : int(self.buildmaster_port),
            'slaves' : [BuildSlave(client.get_name(), client.password) for client in ProjectClient.objects.filter(project=self.project)],
            'change_source' : PBChangeSource(),
            'schedulers' : [
                Scheduler(name="scheduler", branch="master", treeStableTimer=1, builderNames=[
                    assignment.get_domain_object().get_identifier() for assignment in assignments
                ])
            ],
            'builders' : [
                {
                      'name': assignment.get_domain_object().get_identifier(),
                      'slavename': ProjectClient.objects.get(project=self.project, computer=assignment.computer).get_name(),
                      'builddir': assignment.get_domain_object().get_identifier(),
                      'factory': assignment.get_domain_object().get_factory()
                }
                for assignment in assignments
            ],
            'status' : [
                MongoDb(database = get_database_name(),
                        master_id = self.pk,
                        host = db_info['host'],
                        port = db_info['port'],
                        username = db_info['username'],
                        password = db_info['password'],
                ),
            ],
            'projectName' : self.project.name,
            'projectURL' : self.project.tracker_uri,
            'buildbotURL' : self.get_webstatus_uri()
        }
        return config


