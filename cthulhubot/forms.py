from django.utils.datastructures import SortedDict
from django.forms import (
    Form, ModelForm, BaseForm,
    CharField, URLField, ChoiceField,
)

from cthulhubot.models import BuildComputer

class CreateProjectForm(Form):
    name = CharField(max_length=50)
    issue_tracker = URLField()
    repository = CharField(max_length=50)

class ComputerForm(ModelForm):
    class Meta:
        model = BuildComputer

def get_job_configuration_form(job, post=None):
    params = job.get_configuration_parameters()
    fields = SortedDict()
    initial_data = {}
    i = 0
    for command in params:
        for param in command['parameters']:
            id = 'job_configuration_%s' % i
            fields[id] = CharField(label=u"%s for command %s: " % (
                param, command['command']
            ))
            if command['parameters'][param]:
                initial_data[id] = command['parameters'][param]
            i += 1
    form_klass = type('JobConfigurationForm', (BaseForm,), {'base_fields': fields })
    return form_klass(post, initial=initial_data)

def get_build_computer_selection_form(computers):
    fields = {
        'computer' : ChoiceField(choices=tuple([(computer.pk, computer.name) for computer in computers]))
    }
    return type('BuildComputerSelectionForm', (BaseForm,), {'base_fields': fields })

def get_command_params_from_form_data(job, data):
    params = []
    job_params = job.get_configuration_parameters()

    i = 0
    for command in job_params:
        command_params = {
            'command' : command['command'],
            'parameters' : {}
        }
        for param in command['parameters']:
            id = 'job_configuration_%s' % i
            if data.has_key(id):
                command_params['parameters'][param] = data[id]
            i += 1
        params.append(command_params)

    return params

