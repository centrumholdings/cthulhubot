from cthulhubot.models import JobAssignment
from django.http import Http404
from django.http import HttpResponseNotFound
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template
from django.utils.simplejson import dumps

from cthulhubot.forms import CreateProjectForm, ComputerForm, get_build_computer_selection_form, get_job_configuration_form, get_command_params_from_form_data
from cthulhubot.models import BuildComputer, Project, Job, Command, JobAssignment, ProjectClient
from cthulhubot.project import create_project
from cthulhubot.utils import dispatch_post
from cthulhubot.buildbot import create_master
from cthulhubot.commands import get_undiscovered_commands
from cthulhubot.jobs import get_undiscovered_jobs


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

def check_builder(post, user, assignment, **kwargs):
#    user.message_set.create(message="Your playlist was added successfully.")

    return HttpResponseRedirect(reverse("cthulhubot-job-assignment-detail", kwargs={"assignment_id" : assignment.pk}))

def start_slave(post, project, **kwargs):
    assignment = JobAssignment.objects.get(pk=int(post.get('assignment_id'))).get_domain_object()
    assignment.start()
    return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
        "project" : project.slug,
    }))

def create_slave_dir(post, project, **kwargs):
    assignment = JobAssignment.objects.get(pk=int(post.get('assignment_id'))).get_domain_object()
    assignment.create_build_directory()
    return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
        "project" : project.slug,
    }))

def create_job_assignment(job, computer, project, params=None):
    assigmnent = JobAssignment.objects.create(
        job = job,
        project = project,
        computer = computer
    )

    if params:
        for command in params:
            assigmnent.config.create(
                command = Command.objects.get(slug=command),
                config = dumps(params[command])
            )

    if len(ProjectClient.objects.filter(project=project, computer=computer)) == 0:
        client = ProjectClient(project=project, computer=computer)
        client.generate_password()
        client.save()

    return assigmnent

def force_build(post, project, user, **kwargs):
    assignment = JobAssignment.objects.get(pk=int(post.get('assignment_id'))).get_domain_object()
    assignment.force_build()

    user.message_set.create(message="Build forced")

    return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
        "project" : project.slug,
    }))


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
                tracker_uri = form.cleaned_data['issue_tracker'],
                repository_uri = form.cleaned_data['repository']
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
            "start_master" : start_master,
            "stop_master" : stop_master,
            "stop_master" : stop_master,
            "start_slave" : start_slave,
            "create_slave_dir" : create_slave_dir,
            "force_build" : force_build,
        },
        kwargs = {
            "project" : project,
            "user" : request.user,
        }
    )
    if redirect:
        return redirect

    assignments = [assignment.get_domain_object() for assignment in JobAssignment.objects.filter(project=project)]

    return direct_to_template(request, 'cthulhubot/project_detail.html', {
        'project' : project,
        'job_assignments' : assignments,
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
        form = ComputerForm(request.POST)
        if form.is_valid():
            computer = form.save()
            return HttpResponseRedirect(reverse("cthulhubot-computer-detail", kwargs={
                "computer" : computer.slug,
            }))
    else:
        form = ComputerForm()
        
    return direct_to_template(request, 'cthulhubot/computers_create.html', {
        'form' : form
    })

@transaction.commit_on_success
def computer_detail(request, computer):
    computer = get_object_or_404(BuildComputer, slug=computer)

    return direct_to_template(request, 'cthulhubot/computer_detail.html', {
        'computer' : computer,
    })

@transaction.commit_on_success
def computer_edit(request, computer):
    computer = get_object_or_404(BuildComputer, slug=computer)
    if request.method == "POST":
        form = ComputerForm(request.POST, instance=computer)
        if form.is_valid():
            computer = form.save()
            return HttpResponseRedirect(reverse("cthulhubot-computer-detail", kwargs={
                "computer" : computer.slug,
            }))
    else:
        form = ComputerForm(instance=computer)

    return direct_to_template(request, 'cthulhubot/computers_edit.html', {
        'form' : form
    })

@transaction.commit_on_success
def commands(request):
    commands = Command.objects.all().order_by('slug')
    return direct_to_template(request, 'cthulhubot/commands.html', {
        'commands' : commands,
    })

@transaction.commit_on_success
def commands_discover(request):
    if request.method == "POST":
        if len(request.POST.keys()) == 1:
            command_slug = request.POST.keys()[0]
            command = get_undiscovered_commands().get(command_slug)
            if command:
                Command.objects.get_or_create(slug=command.slug)
            return HttpResponseRedirect(reverse('cthulhubot-commands-discover'))


    return direct_to_template(request, 'cthulhubot/commands_discover.html', {
        'commands' : get_undiscovered_commands(),
    })

@transaction.commit_on_success
def jobs(request):
    jobs = Job.objects.all().order_by('slug')
    return direct_to_template(request, 'cthulhubot/jobs.html', {
        'jobs' : jobs,
    })

@transaction.commit_on_success
def jobs_configure(request):
    discovered = get_undiscovered_jobs()
    available_commands = []

    if request.method == "POST" and u'auto-discovery' in request.POST:
        for job in get_undiscovered_jobs():
            Job.objects.get_or_create(slug=job)
        return HttpResponseRedirect(reverse('cthulhubot-jobs'))

    return direct_to_template(request, 'cthulhubot/jobs_configure.html', {
        'discovered_jobs' : discovered,
        'available_commands' : available_commands,
    })

@transaction.commit_on_success
def job_add(request, job):
    job_class = get_undiscovered_jobs().get(job)
    if not job_class:
        raise Http404()

    job = job_class()

    form = get_job_configuration_form(job)()

    return direct_to_template(request, 'cthulhubot/job_add.html', {
        'job' : job,
        'form' : form,
    })


@transaction.commit_on_success
def job_assigment(request, project):
    project = get_object_or_404(Project, slug=project)
    jobs = Job.objects.all().order_by('slug')

    return direct_to_template(request, 'cthulhubot/job_assigment.html', {
        'project' : project,
        'jobs' : jobs,
    })


@transaction.commit_on_success
def job_assigment_config(request, project, job):
    project = get_object_or_404(Project, slug=project)
    job = get_object_or_404(Job, slug=job)
    job = job.get_domain_object()
    computers = BuildComputer.objects.all().order_by('name')

    computer_form = get_build_computer_selection_form(computers)()
    job_form = get_job_configuration_form(job)()

    if request.method == "POST":
        computer_form = get_build_computer_selection_form(computers)(request.POST)
        job_form = get_job_configuration_form(job)(request.POST)

        if computer_form.is_valid() and job_form.is_valid():
            computer = get_object_or_404(BuildComputer, pk=computer_form.cleaned_data['computer'])
            params = get_command_params_from_form_data(job_form.cleaned_data)

            assignment = create_job_assignment(computer=computer, job=job.model, project=project, params=params)

            return HttpResponseRedirect(reverse('cthulhubot-project-detail', kwargs={'project' : project.slug}))


    return direct_to_template(request, 'cthulhubot/job_assigment_config.html', {
        'project' : project,
        'job' : job,
        'job_form' : job_form,
        'computers' : computers,
        'computer_form' : computer_form,
    })

@transaction.commit_on_success
def job_assigment_detail(request, assignment_id):
    assignment = get_object_or_404(JobAssignment, pk=assignment_id)

    redirect = dispatch_post(request, {
            "builder-check" : check_builder,
        },
        kwargs = {
            "user" : request.user,
            "assignment" : assignment,
        }
    )
    if redirect:
        return redirect

    return direct_to_template(request, 'cthulhubot/job_assignment_detail.html', {
        'assignment' : assignment,
        'project' : assignment.project,
        'computer' : assignment.computer,
        'job' : assignment.job,
    })
