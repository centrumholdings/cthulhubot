from django.db import models
from django.utils.translation import ugettext_lazy as _

class BuildComputer(models.Model):
    """
    Computer with installed operating system we own
    """
    name = models.CharField(max_length=40, unique=True)
    description = models.TextField()
    hostname = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.name

