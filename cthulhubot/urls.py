from django.conf.urls.defaults import patterns, url

from cthulhubot.views import (
    dashboard,
    projects, projects_create, project_detail,
    computers, computers_create, computer_detail,
    commands, commands_discover,
    jobs, jobs_configure, job_add, job_assigment, job_assigment_config,
)

urlpatterns = patterns('',
    url(r'^$', dashboard, name='cthulhubot-dashboard'),
    url(r'^projects/$', projects, name='cthulhubot-projects'),
    url(r'^projects/create/$', projects_create, name='cthulhubot-create-project'),
    url(r'^project/(?P<project>[\w\-]+)/$', project_detail, name='cthulhubot-project-detail'),
    
    url(r'^job-assigment/(?P<project>[\w\-]+)/(?P<job>[\w\-]+)/$', job_assigment_config, name='cthulhubot-job-assigment-add'),
    url(r'^job-assigment/(?P<project>[\w\-]+)/$', job_assigment, name='cthulhubot-job-assigment'),

    url(r'^computers/$', computers, name='cthulhubot-computers'),
    url(r'^computers/create/$', computers_create, name='cthulhubot-add-computer'),
    url(r'^computers/(?P<computer>[\w\-]+)/$', computer_detail, name='cthulhubot-computer-detail'),

    url(r'^commands/$', commands, name='cthulhubot-commands'),
    url(r'^commands/discover/$', commands_discover, name='cthulhubot-commands-discover'),

    url(r'^job/(?P<job>[\w\-]+)/add/$', job_add, name='cthulhubot-job-add'),

    url(r'^jobs/$', jobs, name='cthulhubot-jobs'),
    url(r'^jobs/configure/$', jobs_configure, name='cthulhubot-jobs-configure'),

    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name="login"),
)

