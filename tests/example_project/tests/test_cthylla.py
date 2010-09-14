from pickle import loads
import urllib2
import logging

from django.conf import settings
from django.core.urlresolvers import reverse

from cthulhubot.models import BuildComputer, Job
from cthulhubot.views import create_job_assignment

from tests.helpers import BuildmasterTestCase

"""
Tests for API that Cthylla uses. Be careful with regressions, changing behaivor
here is extremely troublesome for apps that are already in the wild!
"""

class TestConfigurationRetrieval(BuildmasterTestCase):

    def setUp(self):
        super(TestConfigurationRetrieval, self).setUp()

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

        request = urllib2.Request(self.url_root.rstrip("/")+"/"+path.lstrip("/"))
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