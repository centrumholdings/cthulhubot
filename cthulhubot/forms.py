from django.utils.html import conditional_escape
from django.forms.widgets import RadioInput
from django.forms.widgets import RadioFieldRenderer
from django.utils.datastructures import SortedDict
from django.forms import (
    Form, ModelForm, BaseForm,
    Field,
    CharField, URLField, ChoiceField, Textarea,
    IntegerField, RadioSelect, BooleanField,
    ValidationError
)

from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from cthulhubot.models import BuildComputer

class CreateProjectForm(Form):
    name = CharField(max_length=50)
    issue_tracker = URLField()
    repository = CharField(widget=Textarea())

class ComputerForm(ModelForm):
    class Meta:
        model = BuildComputer

class BranchField(CharField):
    """
    Field for repository branch: empty string should be included
    in cleaned_data and should normalize to None
    """

    def clean(self, *args, **kwargs):
        value = super(BranchField, self).clean(*args, **kwargs)
        if not value:
            value = None
        return value

class IntegerOrStarField(CharField):
    """
    Field for nighly scheduler: empty string or '*' normalizes to '*' string,
    otherwise normalizes to integer or raises validation error. 
    """

    def clean(self, *args, **kwargs):
        value = super(IntegerOrStarField, self).clean(*args, **kwargs)
        if not value or value == '*':
            return '*'

        try:
            return int(str(value))
        except (ValueError, TypeError):
            raise ValidationError("Value must be integer or star (*)")


#TODO: Do metaprogramming for the field name prefixes. Find a way to chain after DeclarativeFieldsMetaclass. See #

# To create new Scheduler form, do form as following ones, add to SCHEDULER_SUBFORMS
# and SchedulerForm attributes. Also don't foget to add it to assignment.SCHEDULER_CLASS_MAP

class SchedulerSubForm(Form):
    scheduler = "after_push"
    after_push_branch = BranchField(label="branch", required=False)
    after_push_treeStableTimer = IntegerField(label="Tree stable timer (in seconds)", initial=1)

class PeriodicSubForm(Form):
    scheduler = "periodic"
    periodic_branch = BranchField(label="branch", required=False)
    periodic_periodicBuildTimer = IntegerField(label="Interval (in seconds)", initial=1)

class NightlySubForm(Form):
    scheduler = "nightly"
    nightly_branch = BranchField(label="branch", required=False)
    nightly_minute = IntegerOrStarField(label="When to run (minute)", initial=0)
    nightly_hour = IntegerOrStarField(label="When to run (hour)", initial='*')
    nightly_dayOfMonth = IntegerOrStarField(label="When to run (day of month)", initial='*')
    nightly_month = IntegerOrStarField(label="When to run (month)", initial='*')
    nightly_dayOfWeek = IntegerOrStarField(label="When to run (day of month)", initial='*')

SCHEDULER_SUBFORMS = [SchedulerSubForm, PeriodicSubForm, NightlySubForm]

class SchedulerForm(Form):
    periodic = BooleanField(required=False)
    nightly = BooleanField(required=False)
    after_push = BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.subforms = kwargs.pop('subforms')
        self.subforms_dict = dict([(form.scheduler, form) for form in self.subforms])

        super(SchedulerForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            if field in self.subforms_dict:
                self.fields[field].subform = self.subforms_dict[field]
                #self.fields[field].subform = self.subforms_dict[field]

    def clean(self):
        schedulers_enabled = [scheduler for scheduler in self.cleaned_data if self.cleaned_data[scheduler]]

        for scheduler in schedulers_enabled:
            if not self.fields[scheduler].subform.is_valid():
                raise ValidationError("Settings for scheduler are not valid")

        return self.cleaned_data


    def get_configuration_dict(self):
        """
        Return dictionary to be used for job assignment configuration
        """
        if not self.is_valid():
            raise ValidationError("Cannot return configuration if I'm invalid")

        enabled_schedulers = [scheduler for scheduler in self.cleaned_data if self.cleaned_data[scheduler]]
        return {
            'schedule' : [
                {
                    'identifier' : self.fields[scheduler].subform.scheduler,
                    'parameters' : dict([
                        # param : value, where param must be trimmed for subform name prefix and trailing _
                        (param[len(self.fields[scheduler].subform.scheduler)+1:], self.fields[scheduler].subform.cleaned_data[param])
                        for param in self.fields[scheduler].subform.cleaned_data
                    ])
                }
                for scheduler in enabled_schedulers
            ]
        }

def get_scheduler_form(post=None):
    subforms = [form(post) for form in SCHEDULER_SUBFORMS]
    return SchedulerForm(post, subforms=subforms)

def get_job_configuration_form(job, post=None):
    params = job.get_configuration_parameters()
    fields = SortedDict()
    initial_data = {}
    i = 0
    for command in params:
        for param in command['parameters']:
            id = 'job_configuration_%s' % i
            if 'required' in command['parameters']:
                required = command['parameters']['required']
            else:
                required = False
            fields[id] = CharField(label=u"%s for command %s: " % (
                param, command['command']
            ), required=required)
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
    params = {'commands' : []}
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
        params['commands'].append(command_params)

    return params

