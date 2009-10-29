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
from django.contrib.contenttypes.models import ContentType

from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils import simplejson
from django.db import models

from cthulhubot.utils import check_call
from cthulhubot.commands import get_command
from cthulhubot.computer import Computer
from cthulhubot.err import UndiscoveredCommandError, CommunicationError
from cthulhubot.jobs import get_job
from cthulhubot.mongo import get_database_name

from buildbot.changes.pb import PBChangeSource
from buildbot.buildslave import BuildSlave
from buildbot.scheduler import Scheduler
from buildbot.status import html

from bbmongostatus.status import MongoDb

from django.core.exceptions import ImproperlyConfigured
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

    def get_absolute_url(self):
        return reverse("cthulhubot-computer-detail", kwargs={
                "computer" : self.slug,
            })

    def get_domain_object(self):
        from cthulhubot.computer import Computer
        if not self._domain_object:
            self._domain_object = Computer(
                host=self.hostname,
                user=self.username,
                key=self.ssh_key,
                model=self
            )
        return self._domain_object
    
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

#TODO: This is actually code scetch for configure-job-on-discovery use case,
# not implemented yet
#    def get_configured_command(self, command):
#        try:
#            config = CommandConfiguration.objects.get(
#                job = self,
#                command = command
#            )
#            config = simplejson.loads(config.config)
#        except CommandConfiguration.DoesNotExist:
#            config = {}
#
#        return command.get_command(config=config)
#
#    def get_configured_commands(self):
#        job = get_job(self.slug)()
#        try:
#            return [
#                self.get_configured_command(Command.objects.get(slug=command.slug))
#                for command in job.get_commands()
#            ]
#        except Command.DoesNotExist:
#            raise UndiscoveredCommandError("Command %s not yet configured" % command.slug)



    def get_domain_object(self):
        if not self._job:
            self._job = get_job(slug=self.slug)()
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
            Command.objects.get_or_create(slug=command.slug)

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

class CommandConfiguration(models.Model):
    command = models.ForeignKey(Command)
    # config is dumped json object in form of {'key' : value'} configuration parameters for given command
    config = models.TextField()
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    configuration_for = GenericForeignKey()

    unique_together = (("command", "job"),)


class JobAssignment(models.Model):
    job = models.ForeignKey(Job)
    computer = models.ForeignKey(BuildComputer)
    project = models.ForeignKey(Project)
    config = GenericRelation(CommandConfiguration)

    unique_together = (("job", "project", "computer"),)

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
        return str(self.pk)

    def get_client(self):
        return ProjectClient.objects.get(project=self.project, computer=self.computer)

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
        builder = db.builders.find_one({'name' : self.get_identifier(), 'master_id' : self.project.get_buildmaster().pk})
        from cthulhubot.assignment import *
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

    def get_domain_object(self):
        from cthulhubot.assignment import Assignment
        return Assignment(
            computer = self.computer.get_domain_object(),
            job = self.job.get_domain_object(),
            project = self.project,
            model = self
        )
   
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
        from buildbot.steps.source import Git

        self.load_configuration()
        commands = self.job.get_commands()

        factory = BuildFactory()
#        factory.addStep(Git(self.project.repository_uri, branch="master"))

        for command in commands:
            try:
                config = self.config.get(command=Command(slug=command.slug))
                command.update_config(config)
            except CommandConfiguration.DoesNotExist:
                pass

            factory.addStep(command.get_buildbot_command())
        return factory

    def execute_remote_command_for_success(self, cmd):
        status = self.computer.get_command_return_status(cmd)

        if status != 0:
            raise RemoteCommandError("Command '%s' exited with status %s." % (str(cmd), status))

    def start(self):
        self.execute_remote_command_for_success(["buildbot", "start", self.build_directory])

    def stop(self):
        self.execute_remote_command_for_success(["buildbot", "stop", self.build_directory])

    def load_configuration(self):
        #TODO: apply also other configurations for given job
        for config in self.config.select_related().all():
            self.job.update_command_config(command_slug=config.command.slug, config=loads(config.config))

    def force_build(self):
        from cthulhubot.buildbot import BuildForcer
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

class ProjectClient(models.Model):
    project = models.ForeignKey(Project)
    computer = models.ForeignKey(BuildComputer)
    password = models.CharField(max_length=36)

    def generate_password(self):
        if not self.password:
            self.password = str(uuid4())

    def get_name(self):
        return '%s-at-%s' % (self.project.slug, self.computer.slug)

    unique_together = (("project", "computer"),)



class Buildmaster(models.Model):
    webstatus_port = models.PositiveIntegerField(unique=True)
    buildmaster_port = models.PositiveIntegerField(unique=True)
    project = models.ForeignKey(Project, unique=True)
    directory = models.CharField(unique=True, max_length=255)

    port_attributes = ("webstatus_port", "buildmaster_port")

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

        config = {
            'slavePortnum' : self.buildmaster_port,
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
            'status' : [html.WebStatus(http_port=self.webstatus_port), MongoDb(database=get_database_name(), master_id=self.pk)],
            'projectName' : self.project.name,
            'projectURL' : self.project.tracker_uri,
            'buildbotURL' : self.get_webstatus_uri()
        }
        return config


