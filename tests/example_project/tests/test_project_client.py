from djangosanetesting.cases import HttpTestCase
from example_project.tests.helpers import MockJob, MockBuildmaster
from mock import Mock

import os, os.path
from shutil import rmtree
from tempfile import mkdtemp

from django.conf import settings
from django.utils.simplejson import dumps, loads

from cthulhubot.assignment import Assignment
from cthulhubot.err import RemoteCommandError, UnconfiguredCommandError
from cthulhubot.models import Job, JobAssignment, BuildComputer, Command, ProjectClient, DirectoryNotCreated, ClientOffline, ClientReady
from cthulhubot.views import create_job_assignment

from tests.helpers import create_project

class TestProjectClient(HttpTestCase):
    def setUp(self):
        super(TestProjectClient, self).setUp()

        #FIXME: DST should have helper function for this
        from djangosanetesting.noseplugins import DEFAULT_URL_ROOT_SERVER_ADDRESS, DEFAULT_LIVE_SERVER_PORT

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
            params = [
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
            ]
        )

        self.project_client = ProjectClient.objects.all()[0]
        assert self.project_client.project == self.project

        self.build_directory = os.path.join(self.base_directory, self.project_client.get_identifier())

        self.transaction.commit()

    def test_dir_not_exists_by_default(self):
        self.assert_equals(0, len(os.listdir(self.base_directory)))
        self.assert_false(self.project_client.build_directory_exists())

    def test_creating_creates_dir(self):
        self.assert_equals(0, len(os.listdir(self.base_directory)))

        self.project_client.create_build_directory()
        self.assert_equals(1, len(os.listdir(self.base_directory)))

    def test_exists_check_recognizes_created_dir(self):
        self.assert_equals(0, len(os.listdir(self.base_directory)))

        self.project_client.create_build_directory()

        self.assert_true(self.project_client.build_directory_exists())

    def test_remote_error_on_bad_directory_nesting(self):
        self.project_client.computer.basedir = "/badly/nested/nonexistent/basedir"
        self.assert_raises(RemoteCommandError, self.project_client.create_build_directory)

    def test_directory_not_created_by_default(self):
        self.assert_equals(DirectoryNotCreated.ID, self.project_client.get_status().ID)

    def test_directory_not_created_by_default_in_text(self):
        assert len(unicode(DirectoryNotCreated)) > 0
        self.assert_equals(DirectoryNotCreated.DEFAULT_STATUS, self.project_client.get_text_status())

    def test_bare_offline_after_directory_created(self):
        self.project_client.create_build_directory()
        self.assert_equals(ClientOffline.ID, self.project_client.get_status().ID)

    def test_offline_after_master_started_without_slave(self):
        self.project_client.create_build_directory()
        self.buildmaster.start()
        self.assert_equals(ClientOffline.ID, self.project_client.get_status().ID)

    def test_ready_after_starting_up(self):
        self.project_client.create_build_directory()
        self.buildmaster.start()
        self.project_client.start()
        try:
            self.assert_equals(ClientReady.ID, self.project_client.get_status().ID)
        finally:
            self.project_client.stop()

    def test_deleting_client_stops_slave(self):
        self.project_client.create_build_directory()
        self.buildmaster.start()
        self.project_client.start()
        try:
            self.assert_true(self.project_client.builder_running())
        finally:
            self.project_client.stop()

        self.project_client.delete()
        self.assert_false(self.project_client.builder_running())

    def tearDown(self):
        settings.NETWORK_ROOT = self.network_root

        self.buildmaster.stop(ignore_not_running=True)
        self.buildmaster.delete()
        rmtree(self.base_directory)

        super(TestProjectClient, self).tearDown()

