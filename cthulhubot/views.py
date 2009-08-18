from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template

from cthulhubot.forms import CreateProjectForm, AddProjectForm
from cthulhubot.models import BuildComputer, Project
from cthulhubot.project import create_project
from cthulhubot.utils import dispatch_post
from cthulhubot.buildbot import create_master



########### Helper controller-model dispatchers

def create_master(post, project, **kwargs):
    create_master(project = project)
    return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
        "project" : project.slug,
    }))

def start_master(post, project, **kwargs):
    project.buildmaster.start()
    return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
        "project" : project.slug,
    }))

def stop_master(post, project, **kwargs):
    project.buildmaster.stop()
    return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
        "project" : project.slug,
    }))

def add_computer(post, **kwargs):
    return BuildComputer.objects.add(
        **kwargs
    )


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
    return direct_to_template(request, 'cthulhubot/project_detail.html', {
        'project' : project
    })


@transaction.commit_on_success
def computers(request):
    computers = BuildComputer.objects.all().order_by('name')
    return direct_to_template(request, 'cthulhubot/computers.html', {
        'computers' : computers,
    })

@transaction.commit_on_success
def computers_create(request):
    if request.method == "POST":
        form = AddProjectForm(request.POST)
        if form.is_valid():
            computer = form.save()
            return HttpResponseRedirect(reverse("cthulhubot-computer-detail", kwargs={
                "computer" : computer.slug,
            }))
    else:
        form = AddProjectForm()
        
    return direct_to_template(request, 'cthulhubot/computers_create.html', {
        'form' : form
    })

@transaction.commit_on_success
def computer_detail(request, computer):
    computer = get_object_or_404(BuildComputer, slug=computer)

    return direct_to_template(request, 'cthulhubot/computer_detail.html', {
        'computer' : computer,
    })
