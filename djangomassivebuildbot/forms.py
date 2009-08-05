from django.forms import (
    Form,
    CharField, URLField
)

class CreateProjectForm(Form):
    name = CharField(max_length=50)
    issue_tracker = URLField()

