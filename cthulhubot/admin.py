from django.contrib import admin
from cthulhubot.models import BuildComputer, Command

admin.site.register([BuildComputer, Command, Project])

