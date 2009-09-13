from django.forms import (
    Form, ModelForm, BaseForm,
    CharField, URLField, ChoiceField,
)

from django.template.defaultfilters import slugify
from cthulhubot.models import BuildComputer

JOB_CONFIGURATION_FIELD_SEPARATOR = ': '

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
            fields['%s%s%s' % (command['slug'], JOB_CONFIGURATION_FIELD_SEPARATOR, param)] = CharField()
    return type('JobConfigurationForm', (BaseForm,), {'base_fields': fields })

def get_build_computer_selection_form(computers):
    fields = {
        'computer' : ChoiceField(choices=tuple([(computer.pk, computer.name) for computer in computers]))
    }
    return type('BuildComputerSelectionForm', (BaseForm,), {'base_fields': fields })

def get_command_params_from_form_data(data):
    params = {}

    for key in data:
        command = slugify(key.split(JOB_CONFIGURATION_FIELD_SEPARATOR)[0])
        param = key[len(command)+len(JOB_CONFIGURATION_FIELD_SEPARATOR):]
        if not params.has_key(command):
            params[command] = {}
        params[command][param] = data[key]

    return params

