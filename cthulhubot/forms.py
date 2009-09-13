from django.forms import (
    Form, ModelForm, BaseForm,
    CharField, URLField, ChoiceField,
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

def get_build_computer_selection_form(computers):
    fields = {
        'computer' : ChoiceField(choices=tuple([(computer.pk, computer.name) for computer in computers]))
    }
    return type('BuildComputerSelectionForm', (BaseForm,), {'base_fields': fields })
