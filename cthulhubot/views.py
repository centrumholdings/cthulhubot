from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template

from cthulhubot.forms import CreateProjectForm
from cthulhubot.models import Project
from cthulhubot.project import create_project
from cthulhubot.utils import dispatch_post
from cthulhubot.buildbot import create_master



########### Helper controller-model dispatchers

def create_master(post, project, **kwargs):
    create_master(project = project)



########### VIEWS

@transaction.commit_on_success
def dashboard(request):
    return direct_to_template(request, 'cthulhubot/dashboard.html')

def projects(request):
    projects = Project.objects.all().order_by('name')
#    for project in projects:
#        project.get_absolute_url()
    return direct_to_template(request, 'cthulhubot/projects.html', {
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
            return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
                "project" : project.slug,
            }))
    else:
        form = CreateProjectForm()
    return direct_to_template(request, 'cthulhubot/projects_create.html', {
        'form' : form
    })

@transaction.commit_on_success
def project_detail(request, project):
    project = get_object_or_404(Project, slug=project)

    redirect = dispatch_post(request, {
            "create_master" : create_master,
        },
        kwargs = {
            "project" : project,
        }
    )
    if redirect:
        return redirect

    return direct_to_template(request, 'cthulhubot/project_detail.html', {
        'project' : project
    })
