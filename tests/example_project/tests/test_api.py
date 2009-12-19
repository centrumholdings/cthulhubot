from djangosanetesting.cases import HttpTestCase
from djangosanetesting.noseplugins import DEFAULT_URL_ROOT_SERVER_ADDRESS, DEFAULT_LIVE_SERVER_PORT

from urllib2 import urlopen
import os

from cthulhubot.views import create_job_assignment
from django.conf import settings
from cthulhubot.models import Job, JobAssignment, BuildComputer, Command, ProjectClient
from tempfile import mkdtemp
from django.utils.simplejson import dumps, loads
from tests.helpers import create_project

from shutil import rmtree

class TestMasterApi(HttpTestCase):
    """
    Test our buildmaster scheduler plugin
    """

    def setUp(self):
        super(TestMasterApi, self).setUp()


        self.url_root = "http://%s:%s" % (
            getattr(settings, "URL_ROOT_SERVER_ADDRESS", DEFAULT_URL_ROOT_SERVER_ADDRESS),
            getattr(settings, "LIVE_SERVER_PORT", DEFAULT_LIVE_SERVER_PORT)
        )

        self.network_root = settings.NETWORK_ROOT
        settings.NETWORK_ROOT = self.url_root


        self.project_name = u"project"
        self.project = create_project(self)
        self.buildmaster = self.project.buildmaster_set.all()[0]

        self.base_directory = mkdtemp()
        self.computer_model = self.computer = BuildComputer.objects.create(hostname = "localhost", basedir=self.base_directory)

        self.job = job = Job.objects.create(slug='cthulhubot-debian-package-creation').get_domain_object()
        self.job.auto_discovery()

        self.assignment = create_job_assignment(
            computer = self.computer_model,
            job = job,
            project = self.project,
            params = {
              'commands' : [
                {
                    'command' : 'cthulhubot-git',
                    'parameters' : {
                        'repository' : '/tmp/repo.git',
                    }
                },
                {},
                {},
                {
                    'command' : 'cthulhubot-debian-package-ftp-upload',
                    'parameters' : {
                        'ftp_user' : 'xxx',
                        'ftp_password' : 'xxx',
                        'ftp_directory' : '',
                        'ftp_host' : ''
                    }
                }
            ]}
        )


        self.project_client = self.assignment.get_client()
        self.build_directory = os.path.join(self.base_directory, self.project_client.get_identifier())

        self.transaction.commit()

        self.buildmaster.start()
        self.project_client.create_build_directory()
        self.project_client.start()

    def test_rewrite_this_test(self):
        port = self.buildmaster.api_port
        s = 'http://%s:%s/force_build' % (getattr(settings, "URL_ROOT_SERVER_ADDRESS", DEFAULT_URL_ROOT_SERVER_ADDRESS), port)

        data = {
            'changeset' : 'FETCH_HEAD',
            'builder' : ProjectClient.objects.all()[0].get_identifier()
        }
        f = urlopen(s, dumps(data))
        self.assert_equals(False, f.read())

    def tearDown(self):
        settings.NETWORK_ROOT = self.network_root

        self.project_client.stop()
        self.assignment.delete()

        self.buildmaster.stop(ignore_not_running=True)
        self.buildmaster.delete()
        rmtree(self.base_directory)

        super(TestMasterApi, self).tearDown()
