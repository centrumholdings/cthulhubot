from urllib2 import urlopen
import os

from cthulhubot.views import create_job_assignment
from django.conf import settings
from cthulhubot.models import Job, BuildComputer, ProjectClient
from django.utils.simplejson import dumps
from tests.helpers import BuildmasterTestCase


class TestMasterApi(BuildmasterTestCase):
    """
    Test our buildmaster scheduler plugin
    """

    def setUp(self):
        super(TestMasterApi, self).setUp()

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
        s = 'http://%s:%s/force_build' % (settings.BUILDMASTER_NETWORK_NAME, port)

        data = {
            'changeset' : 'FETCH_HEAD',
            'builder' : ProjectClient.objects.all()[0].get_identifier()
        }
        
        f = urlopen(s, dumps(data))
        self.assert_equals('OK', f.read())

    def tearDown(self):
        self.project_client.stop()
        self.assignment.delete()

        super(TestMasterApi, self).tearDown()
