from django.conf.urls.defaults import patterns, url, include

from django.conf import settings

urlpatterns = patterns('',
    # serve static files
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.MEDIA_ROOT, 'show_indexes': True }),
    url(r'^', include('djangomassivebuildbot.urls')),

)

