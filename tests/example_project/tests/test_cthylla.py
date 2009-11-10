from djangosanetesting import DestructiveDatabaseTestCase
import urllib2
import logging

"""
Tests for API that Cthylla uses. Be careful with regressions, changing behaivor
here is extremely troublesome for apps that are already in the wild!
"""

class TestConfigurationRetrieval(DestructiveDatabaseTestCase):

    def setUp(self):
        super(TestBuildmaster, self).setUp()

        self.realm = 'buildmaster'
        self.username = 'xxx'
        self.password = 'xxx'

        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com", repository_uri="/tmp/test")
        self.buildmaster = self.project.buildmaster_set.all()[0]
        self.computer_model = self.computer = BuildComputer.objects.create(name="localhost", hostname="localhost")
        self.job = job = Job.objects.create(slug='cthulhubot-sleep')
        self.job.auto_discovery()
        self.assignment_model = create_job_assignment(
            computer = self.computer_model,
            job = self.job,
            project = self.project,
        )
        self.config = self.buildmaster.get_config()

        self.transaction.commit()

    def retrieve(self, path):
        auth_handler = urllib2.HTTPDigestAuthHandler()
        auth_handler.add_password(self.realm, self.url, self.username, self.password)
        opener = urllib2.build_opener(auth_handler)

        request = urllib2.Request(self.url+path)
        try:
            response = opener.open(request)
        except urllib2.HTTPError, err:
            if err.fp:
                error = ": %s" % err.fp.read()
            else:
                error = ''
            logging.error("Error occured while opening HTTP %s" % error)
            raise
        self.assertEquals(200, response.code)
        response.close()


    def test_result_unpicklable_without_error(self):
        raise NotImplementedError
