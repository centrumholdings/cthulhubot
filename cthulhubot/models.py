from __future__ import absolute_import

from copy import copy
from subprocess import check_call, PIPE
import os
from tempfile import gettempdir

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template.defaultfilters import slugify
from shutil import rmtree
from django.db import models

DEFAULT_BUILDMASTER_BASEDIR = gettempdir()

class BuildComputer(models.Model):
    """
    Computer with installed operating system we own
    """
    name = models.CharField(max_length=40, unique=True)
    description = models.TextField()
    hostname = models.CharField(max_length=255, unique=True)

    username = models.CharField(max_length=40)
    ssh_key = models.TextField()

    def __unicode__(self):
        return self.name

class Command(models.Model):
    name = models.CharField(max_length=40, unique=True)
    command = models.TextField()

class Project(models.Model):
    name = models.CharField(max_length=40)
    slug = models.CharField(max_length=40, unique=True)
    tracker_uri = models.URLField(max_length=255, verify_exists=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        super(Project, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("cthulhubot-project-detail", kwargs={
                "project" : self.slug,
            })

    def delete(self, *args, **kwargs):
        for master in self.buildmaster_set.all():
            master.delete()
        
        super(Project, self).delete(*args, **kwargs)

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

    def start(self, env=None):
        e = copy(os.environ)
        e.update(env)
        check_call(["buildbot", "start", self.directory], env=e, cwd=self.directory,
            stdout=PIPE, stderr=PIPE)

    def stop(self, env=None):
        e = copy(os.environ)
        e.update(env)
        check_call(["buildbot", "stop", self.directory], env=e, cwd=self.directory,
            stdout=PIPE, stderr=PIPE)

    def is_running(self):
        """ Is buildmaster process running? Return True if process found, False otherwise.

        #TODO: This will now work only for linux, which is my target platform.
        It could probably be modified for BSD with os.kill(pid, 0), anyone to test it?
        Also, any windows guru for a win way?
        """
        # This will work only on linux, which is my target platform
        # for BSD,

        pid_file = os.path.join(self.directory, 'twistd.pid')
        if not os.path.exists(pid_file):
            return False

        f = open(pid_file)
        pid = int(f.read())
        f.close()

        try:
            pid = int(pid)
        except ValueError:
            return False

        return os.path.exists("/proc/%s" % pid)



class NamedStep(models.Model):
    name = models.CharField(max_length=255)

class NamedFactory(models.Model):
    name = models.CharField(max_length=40)
    project = models.ForeignKey(Project)
    steps = models.ManyToManyField(NamedStep)

class Repository(models.Model):
    uri = models.URLField(max_length=255, verify_exists=False, unique=True)

class DedicatedVncNumber(models.Model):
    computer = models.ForeignKey(BuildComputer)
    number = models.PositiveIntegerField()

    unique_together = (("computer", "number"),)

class SeleniumProxy(models.Model):
    name = models.CharField(max_length=40)
    port = models.PositiveIntegerField()

class WindowsSeleniumProxy(models.Model):
    pass

class UnixVncSeleniumProxy(SeleniumProxy):
    pass
