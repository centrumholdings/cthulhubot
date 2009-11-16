from djangosanetesting import HttpTestCase
from pickle import loads
import urllib2
import logging

from django.conf import settings
from django.core.urlresolvers import reverse

from cthulhubot.models import BuildComputer, Job
from cthulhubot.views import create_project, create_job_assignment

"""
Tests for API that Cthylla uses. Be careful with regressions, changing behaivor
here is extremely troublesome for apps that are already in the wild!
"""

class TestConfigurationRetrieval(HttpTestCase):

    def setUp(self):
        super(TestConfigurationRetrieval, self).setUp()

        #FIXME: DST should have helper function for this
        from djangosanetesting.noseplugins import DEFAULT_URL_ROOT_SERVER_ADDRESS, DEFAULT_LIVE_SERVER_PORT

        self.url_root = "http://%s:%s" % (
            getattr(settings, "URL_ROOT_SERVER_ADDRESS", DEFAULT_URL_ROOT_SERVER_ADDRESS),
            getattr(settings, "LIVE_SERVER_PORT", DEFAULT_LIVE_SERVER_PORT)
        )

        self.network_root = settings.NETWORK_ROOT
        settings.NETWORK_ROOT = self.url_root

        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com", repository_uri="/tmp/test")
        self.buildmaster = self.project.buildmaster_set.all()[0]
        self.computer_model = self.computer = BuildComputer.objects.create(name="localhost", hostname="localhost")
        self.job = Job.objects.create(slug='cthulhubot-sleep').get_domain_object()
        self.job.auto_discovery()
        self.assignment = create_job_assignment(
            computer = self.computer_model,
            job = self.job,
            project = self.project,
        )
        self.config = self.buildmaster.get_config()

        self.realm = 'buildmaster'
        self.username = self.buildmaster.buildmaster_port
        self.password = self.buildmaster.password

        self.transaction.commit()

    def retrieve(self, path):
        auth_handler = urllib2.HTTPDigestAuthHandler()
        auth_handler.add_password(self.realm, self.url_root, self.username, self.password)
        opener = urllib2.build_opener(auth_handler)

        request = urllib2.Request(self.url_root+path)
        try:
            response = opener.open(request)
        except urllib2.HTTPError, err:
            if err.fp:
                error = ": %s" % err.fp.read()
            else:
                error = ''
            logging.error("Error occured while opening HTTP %s" % error)
            raise
        res = response.read()
        response.close()
        
        return res

    def test_result_unpicklable_without_error(self):
        data = self.retrieve(reverse("cthulhubot-api-project-master-configuration", kwargs={"identifier" : self.buildmaster.pk}))
        loads(data)


    def tearDown(self):
        settings.NETWORK_ROOT = self.network_root
        super(TestConfigurationRetrieval, self).tearDown()