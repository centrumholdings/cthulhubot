from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template

from djangomassivebuildbot.forms import CreateProjectForm
from djangomassivebuildbot.models import Project
from djangomassivebuildbot.project import create_project

@transaction.commit_on_success
def dashboard(request):
    return direct_to_template(request, 'djangomassivebuildbot/dashboard.html')

def projects(request):
    projects = Project.objects.all().order_by('name')
#    for project in projects:
#        project.get_absolute_url()
    return direct_to_template(request, 'djangomassivebuildbot/projects.html', {
        'projects' : projects,
    })

@transaction.commit_on_success
def projects_create(request):
    if request.method == "POST":
        form = CreateProjectForm(request.POST)
        if form.is_valid():
            project = create_project(
                name = form.cleaned_data['name'],
                tracker_uri = form.cleaned_data['issue_tracker']
            )
            return HttpResponseRedirect(reverse("djangomassivebuildbot-project-detail", kwargs={
                "project" : project.slug,
            }))
    else:
        form = CreateProjectForm()
    return direct_to_template(request, 'djangomassivebuildbot/projects_create.html', {
        'form' : form
    })

@transaction.commit_on_success
def project_detail(request, project):
    project = get_object_or_404(Project, slug=project)
    return direct_to_template(request, 'djangomassivebuildbot/project_detail.html', {
        'project' : project
    })
