from django.views.generic.simple import direct_to_template

from djangomassivebuildbot.forms import CreateProjectForm
from djangomassivebuildbot.project import create_project

def dashboard(request):
    return direct_to_template(request, 'djangomassivebuildbot/dashboard.html')

def projects(request):
    return direct_to_template(request, 'djangomassivebuildbot/masters.html')

def projects_create(request):
    if request.method == "POST":
        form = CreateProjectForm(request.POST)
        if form.is_valid():
            create_project()
    else:
        form = CreateProjectForm()
    return direct_to_template(request, 'djangomassivebuildbot/masters_create.html', {
        'form' : form
    })


