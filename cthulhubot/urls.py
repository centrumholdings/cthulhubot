from django.conf.urls.defaults import patterns, url

from cthulhubot.views import (
    dashboard,
    projects, projects_create, project_detail,
)

urlpatterns = patterns('',
    url(r'^$', dashboard, name='cthulhubot-dashboard'),
    url(r'^projects/$', projects, name='cthulhubot-projects'),
    url(r'^projects/create/$', projects_create, name='cthulhubot-create-project'),
    url(r'^project/(?P<project>[\w]+)/$', project_detail, name='cthulhubot-project-detail'),

    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name="login"),
)

