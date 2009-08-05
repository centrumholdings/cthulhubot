from django.conf.urls.defaults import patterns, url

from djangomassivebuildbot.views import (
    dashboard,
    masters, masters_create,
)

urlpatterns = patterns('',
    url(r'^$', dashboard, name='djangomassivebuildbot-dashboard'),
    url(r'^masters/$', masters, name='djangomassivebuildbot-masters'),
    url(r'^masters/create/$', masters_create, name='djangomassivebuildbot-create-master'),
)

