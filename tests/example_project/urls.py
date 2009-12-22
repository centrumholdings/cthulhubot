from django.conf.urls.defaults import patterns, url, include
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.MEDIA_ROOT, 'show_indexes': True }),
    url(r'^admin/(.*)', admin.site.root),
    url(r'^', include('cthulhubot.urls')),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name="login"),

)

