from django.contrib import admin
from cthulhubot.models import BuildComputer, Command, Project, Job, JobAssignment

admin.site.register([BuildComputer, Command, Project, Job, JobAssignment])

