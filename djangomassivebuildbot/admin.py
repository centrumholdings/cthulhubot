from django.contrib import admin
from djangomassivebuildbot.models import BuildComputer, Command

admin.site.register([BuildComputer, Command, Project])

