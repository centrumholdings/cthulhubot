from django.db import models

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
    tracker_uri = models.URLField(max_length=255, verify_exists=False)

class Buildmaster(models.Model):
    webstatus_port = models.PositiveIntegerField(unique=True)
    buildmaster_port = models.PositiveIntegerField(unique=True)
    project = models.ForeignKey(Project)

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
