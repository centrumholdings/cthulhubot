from django.http import HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.generic.simple import direct_to_template

from pymongo.objectid import ObjectId
from pymongo import DESCENDING

from pickle import dumps as pickle_dumps

from djangohttpdigest.decorators import protect_digest_model

from cthulhubot.bbot import create_master
from cthulhubot.commands import get_undiscovered_commands
from cthulhubot.forms import CreateProjectForm, ComputerForm, get_build_computer_selection_form, get_job_configuration_form, get_command_params_from_form_data, get_scheduler_form
from cthulhubot.jobs import get_undiscovered_jobs
from cthulhubot.models import BuildComputer, Project, Job, Command, JobAssignment, ProjectClient, Buildmaster
from cthulhubot.mongo import get_database_connection
from cthulhubot.project import create_project
from cthulhubot.utils import dispatch_post

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
    client = ProjectClient.objects.get(pk=int(post.get('client_id')))
    client.start()
    return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
        "project" : project.slug,
    }))

def create_slave_dir(post, project, **kwargs):
    client = ProjectClient.objects.get(pk=int(post.get('client_id')))
    client.create_build_directory()
    return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
        "project" : project.slug,
    }))

def create_job_assignment(job, computer, project, params=None):

    assignment = JobAssignment(
        job = job.model,
        project = project,
        computer = computer,
    ).get_domain_object()
    assignment.create_config(params)
    assignment.model.save()

    if len(ProjectClient.objects.filter(project=project, computer=computer)) == 0:
        client = ProjectClient(project=project, computer=computer)
        client.generate_password()
        client.save()

    return assignment

def force_build(post, project, user, **kwargs):
    assignment = JobAssignment.objects.get(pk=int(post.get('assignment_id'))).get_domain_object()
    assignment.force_build()

    user.message_set.create(message="Build forced")

    return HttpResponseRedirect(reverse("cthulhubot-project-detail", kwargs={
        "project" : project.slug,
    }))


########### VIEWS
@login_required
@transaction.commit_on_success
def dashboard(request):
    return direct_to_template(request, 'cthulhubot/dashboard.html')

@login_required
def projects(request):
    projects = Project.objects.all().order_by('name')
#    for project in projects:
#        project.get_absolute_url()
    return direct_to_template(request, 'cthulhubot/projects.html', {
        'projects' : projects,
    })

@login_required
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

@login_required
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

    clients = list(set([assignment.get_client() for assignment in assignments]))

    return direct_to_template(request, 'cthulhubot/project_detail.html', {
        'project' : project,
        'job_assignments' : assignments,
        'clients' : clients,
    })


@login_required
def project_changeset_view(request, project):
    project = get_object_or_404(Project, slug=project)

    db = get_database_connection()

    info = db.repository.find().sort([("commiter_date", DESCENDING),])

    changesets = []

    for changeset in info:
        changeset['results'] = [build['result'] for build in db.builds.find({"changeset" : changeset['hash']})]
        changesets.append(changeset)

    return direct_to_template(request, 'cthulhubot/project_changeset_view.html', {
        'project' : project,
        'changesets' : changesets,
    })

@login_required
@transaction.commit_on_success
def computers(request):
    computers = BuildComputer.objects.all().order_by('name')
    return direct_to_template(request, 'cthulhubot/computers.html', {
        'computers' : computers,
    })

@login_required
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

@login_required
@transaction.commit_on_success
def computer_detail(request, computer):
    computer = get_object_or_404(BuildComputer, slug=computer)

    return direct_to_template(request, 'cthulhubot/computer_detail.html', {
        'computer' : computer,
    })

@login_required
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

@login_required
@transaction.commit_on_success
def commands(request):
    commands = Command.objects.all().order_by('slug')
    return direct_to_template(request, 'cthulhubot/commands.html', {
        'commands' : commands,
    })

@login_required
@transaction.commit_on_success
def commands_discover(request):
    if request.method == "POST":
        if len(request.POST.keys()) == 1:
            command_slug = request.POST.keys()[0]
            command = get_undiscovered_commands().get(command_slug)
            if command:
                Command.objects.get_or_create(slug=command.identifier)
            return HttpResponseRedirect(reverse('cthulhubot-commands-discover'))


    return direct_to_template(request, 'cthulhubot/commands_discover.html', {
        'commands' : get_undiscovered_commands(),
    })

@login_required
@transaction.commit_on_success
def jobs(request):
    jobs = Job.objects.all().order_by('slug')
    return direct_to_template(request, 'cthulhubot/jobs.html', {
        'jobs' : jobs,
    })

@login_required
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

@login_required
@transaction.commit_on_success
def job_add(request, job):
    job_class = get_undiscovered_jobs().get(job)
    if not job_class:
        raise Http404()

    job = job_class()

    form = get_job_configuration_form(job)

    return direct_to_template(request, 'cthulhubot/job_add.html', {
        'job' : job,
        'form' : form,
    })


@login_required
@transaction.commit_on_success
def job_assigment(request, project):
    project = get_object_or_404(Project, slug=project)
    jobs = Job.objects.all().order_by('slug')

    return direct_to_template(request, 'cthulhubot/job_assigment.html', {
        'project' : project,
        'jobs' : jobs,
    })


@login_required
@transaction.commit_on_success
def job_assigment_config(request, project, job):
    project = get_object_or_404(Project, slug=project)
    job = get_object_or_404(Job, slug=job)
    job = job.get_domain_object()
    computers = BuildComputer.objects.all().order_by('name')

    computer_form = get_build_computer_selection_form(computers)()
    job_form = get_job_configuration_form(job)
    scheduler_form = get_scheduler_form()

    if request.method == "POST":
        computer_form = get_build_computer_selection_form(computers)(request.POST)
        job_form = get_job_configuration_form(job, post=request.POST)
        scheduler_form = get_scheduler_form(post=request.POST)

        if computer_form.is_valid() and job_form.is_valid() and scheduler_form.is_valid():
            computer = get_object_or_404(BuildComputer, pk=computer_form.cleaned_data['computer'])
            params = get_command_params_from_form_data(job, job_form.cleaned_data)
            params.update(scheduler_form.get_configuration_dict())
            create_job_assignment(computer=computer, job=job, project=project, params=params)
            return HttpResponseRedirect(reverse('cthulhubot-project-detail', kwargs={'project' : project.slug}))


    return direct_to_template(request, 'cthulhubot/job_assigment_config.html', {
        'project' : project,
        'job' : job,
        'job_form' : job_form,
        'computers' : computers,
        'computer_form' : computer_form,
        'scheduler_form' : scheduler_form,
    })

@login_required
@transaction.commit_on_success
def job_assigment_detail(request, assignment_id):
    assignment = get_object_or_404(JobAssignment, pk=assignment_id).get_domain_object()

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
        'builds' : assignment.builds,
    })


@protect_digest_model(realm=Buildmaster.REALM,
      model=Buildmaster,
      realm_field = None,
      username_field='buildmaster_port',
      password_field='password'
)
def api_buildmaster_config(request, identifier):
    master = get_object_or_404(Buildmaster, pk=identifier)
    return HttpResponse(pickle_dumps(master.get_config()))

@login_required
def step_part_detail(request, step, detail_name):
    db = get_database_connection()
    step = db.steps.find_one({"_id" : ObjectId(str(step))})
    if not step or detail_name not in step:
        return HttpResponseNotFound()
    
    return HttpResponse(step[detail_name])
