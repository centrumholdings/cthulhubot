from django.conf.urls.defaults import patterns, url

from cthulhubot.views import (
    dashboard,
    projects, projects_create, project_detail, project_changeset_view,
    computers, computers_create, computer_detail, computer_edit,
    commands, commands_discover,
    jobs, jobs_configure, job_add, job_assigment, job_assigment_config, job_assigment_detail, step_part_detail,
    api_buildmaster_config
)

urlpatterns = patterns('',
    url(r'^$', dashboard, name='cthulhubot-dashboard'),

    url(r'^api/project/(?P<identifier>.+)/master/configuration/$', api_buildmaster_config, name='cthulhubot-api-project-master-configuration'),

    url(r'^projects/$', projects, name='cthulhubot-projects'),
    url(r'^projects/create/$', projects_create, name='cthulhubot-create-project'),
    url(r'^project/(?P<project>[\w\-]+)/$', project_detail, name='cthulhubot-project-detail'),
    url(r'^project/(?P<project>[\w\-]+)/changesets/$', project_changeset_view, name='cthulhubot-project-changeset-view'),
    
    url(r'^assigment/(?P<assignment_id>[\d]+)/$', job_assigment_detail, name='cthulhubot-job-assignment-detail'),
    url(r'^job-assigment/(?P<project>[\w\-]+)/(?P<job>[\w\-]+)/$', job_assigment_config, name='cthulhubot-job-assigment-add'),
    url(r'^job-assigment/(?P<project>[\w\-]+)/$', job_assigment, name='cthulhubot-job-assigment'),

    url(r'^step/(?P<step>[\d\w\-]+)/(?P<detail_name>[\w\-]+)$', step_part_detail, name='cthulhubot-step-part-detail'),

    url(r'^computers/$', computers, name='cthulhubot-computers'),
    url(r'^computers/create/$', computers_create, name='cthulhubot-add-computer'),
    url(r'^computers/(?P<computer>[\w\-]+)/$', computer_detail, name='cthulhubot-computer-detail'),
    url(r'^computers/(?P<computer>[\w\-]+)/edit/$', computer_edit, name='cthulhubot-computer-edit'),

    url(r'^commands/$', commands, name='cthulhubot-commands'),
    url(r'^commands/discover/$', commands_discover, name='cthulhubot-commands-discover'),

    url(r'^job/(?P<job>[\w\-]+)/add/$', job_add, name='cthulhubot-job-add'),

    url(r'^jobs/$', jobs, name='cthulhubot-jobs'),
    url(r'^jobs/configure/$', jobs_configure, name='cthulhubot-jobs-configure'),
)

