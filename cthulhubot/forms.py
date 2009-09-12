from django.forms import (
    Form, ModelForm, BaseForm,
    CharField, URLField
)

from cthulhubot.models import BuildComputer

class CreateProjectForm(Form):
    name = CharField(max_length=50)
    issue_tracker = URLField()

class AddProjectForm(ModelForm):
    class Meta:
        model = BuildComputer

def get_job_configuration_form(job):
    params = job.get_configuration_parameters()
    fields = {}
    for command in params:
        for param in command['parameters']:
            fields['%s-%s' % (command['slug'], param)] = CharField()
    return type('JobConfigurationForm', (BaseForm,), {'base_fields': fields })

