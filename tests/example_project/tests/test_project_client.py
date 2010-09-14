import os, os.path
from tempfile import mkdtemp

from cthulhubot.err import RemoteCommandError
from cthulhubot.models import Job, BuildComputer, ProjectClient, DirectoryNotCreated, ClientOffline, ClientReady
from cthulhubot.views import create_job_assignment

from tests.helpers import BuildmasterTestCase

class TestProjectClient(BuildmasterTestCase):
    def setUp(self):
        super(TestProjectClient, self).setUp()

        self.client_directory = mkdtemp(dir=self.base_directory)
        self.computer_model = self.computer = BuildComputer.objects.create(hostname = "localhost", basedir=self.client_directory)

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

        self.project_client = ProjectClient.objects.all()[0]
        assert self.project_client.project == self.project

        self.build_directory = os.path.join(self.client_directory, self.project_client.get_identifier())

        self.transaction.commit()

    def test_dir_not_exists_by_default(self):
        self.assert_equals(0, len(os.listdir(self.client_directory)))
        self.assert_false(self.project_client.build_directory_exists())

    def test_creating_creates_dir(self):
        self.assert_equals(0, len(os.listdir(self.client_directory)))

        self.project_client.create_build_directory()
        self.assert_equals(1, len(os.listdir(self.client_directory)))

    def test_exists_check_recognizes_created_dir(self):
        self.assert_equals(0, len(os.listdir(self.client_directory)))

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

