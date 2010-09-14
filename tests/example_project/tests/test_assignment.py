from djangosanetesting.cases import HttpTestCase
from djangosanetesting.utils import get_live_server_path
from tests.helpers import BuildmasterTestCase
from example_project.tests.helpers import MockJob, MockBuildmaster
from mock import Mock

import os, os.path
from shutil import rmtree
from tempfile import mkdtemp

from django.conf import settings
from django.utils.simplejson import dumps, loads

from cthulhubot.assignment import Assignment
from cthulhubot.err import RemoteCommandError, UnconfiguredCommandError
from cthulhubot.models import Job, JobAssignment, BuildComputer, Command, ProjectClient
from cthulhubot.views import create_job_assignment

from tests.helpers import create_project

class TestBuildDirectory(BuildmasterTestCase):
    def setUp(self):
        super(TestBuildDirectory, self).setUp()

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

    def test_loading_assignment_config_works(self):
        self.assert_equals(4, len(self.assignment.get_shell_commands()))

    def test_master_string_creation(self):
        master = settings.BUILDMASTER_NETWORK_NAME
        self.assert_equals("%s:%s" % (master, self.buildmaster.buildmaster_port), self.assignment.get_master_connection_string())

    def test_uri_constructed(self):
        self.assert_true(self.assignment.get_absolute_url() is not None)

class TestAssignmentHandling(BuildmasterTestCase):
    def setUp(self):
        super(TestAssignmentHandling, self).setUp()

        self.base_directory = mkdtemp()
        self.computer_model = self.computer = BuildComputer.objects.create(hostname = "localhost", basedir=self.base_directory)

        self.job = job = Job.objects.create(slug='cthulhubot-sleep').get_domain_object()
        self.job.auto_discovery()

        self.assignment = create_job_assignment(
            computer = self.computer_model,
            job = job,
            project = self.project,
        )

        self.assignment_second = create_job_assignment(
            computer = self.computer_model,
            job = job,
            project = self.project,
        )

        self.project_client = ProjectClient.objects.all()[0]

        self.build_directory = os.path.join(self.base_directory, self.assignment.get_identifier())

        self.transaction.commit()


    def test_assignment_deletes_itself(self):
        self.assignment_second.model.delete()
        self.assert_equals(1, JobAssignment.objects.all().count())

    def test_deleting_single_assignment_leaves_client_alone(self):
        self.assignment_second.model.delete()
        self.assert_equals(1, ProjectClient.objects.all().count())

    def test_deleting_last_assignment_on_computer_deletes_client(self):
        self.assignment_second.model.delete()
        self.assignment.model.delete()
        self.assert_equals(0, ProjectClient.objects.all().count())
