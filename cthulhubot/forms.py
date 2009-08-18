from django.forms import (
    Form, ModelForm,
    CharField, URLField
)

from cthulhubot.models import BuildComputer

class CreateProjectForm(Form):
    name = CharField(max_length=50)
    issue_tracker = URLField()

class AddProjectForm(ModelForm):
    class Meta:
        model = BuildComputer
