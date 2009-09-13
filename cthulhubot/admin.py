from django.contrib import admin
from cthulhubot.models import BuildComputer, Command, Project, Job

admin.site.register([BuildComputer, Command, Project, Job])

