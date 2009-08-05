from django.conf.urls.defaults import patterns, url

from djangomassivebuildbot.views import (
    dashboard,
    projects, projects_create, project_detail,
)

urlpatterns = patterns('',
    url(r'^$', dashboard, name='djangomassivebuildbot-dashboard'),
    url(r'^projects/$', projects, name='djangomassivebuildbot-projects'),
    url(r'^projects/create/$', projects_create, name='djangomassivebuildbot-create-project'),
    url(r'^project/(?P<project>[\w]+)/$', project_detail, name='djangomassivebuildbot-project-detail'),

    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name="login"),
)

