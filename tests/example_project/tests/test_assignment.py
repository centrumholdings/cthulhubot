from djangosanetesting.cases import DestructiveDatabaseTestCase
from example_project.tests.helpers import MockJob, MockBuildmaster
from mock import Mock

import os, os.path
from shutil import rmtree
from tempfile import mkdtemp

from django.conf import settings
from django.utils.simplejson import dumps, loads

from cthulhubot.assignment import Assignment, DirectoryNotCreated, AssignmentOffline, AssignmentReady
from cthulhubot.err import RemoteCommandError, UnconfiguredCommandError
from cthulhubot.models import Job, JobAssignment, BuildComputer, Command
from cthulhubot.views import create_job_assignment

from tests.helpers import create_project

class TestBuildDirectory(DestructiveDatabaseTestCase):
    def setUp(self):
        super(TestBuildDirectory, self).setUp()


        self.project_name = u"project"
        self.project = create_project(self)
        self.buildmaster = self.project.buildmaster_set.all()[0]

        self.base_directory = mkdtemp()
        self.computer_model = self.computer = BuildComputer.objects.create(hostname = "localhost", basedir=self.base_directory)

        self.job = job = Job.objects.create(slug='cthulhubot-debian-package-creation')
        self.job.auto_discovery()

        self.assignment_model = create_job_assignment(
            computer = self.computer_model,
            job = job,
            project = self.project,
            params = {
                'commands' : [
                    {
                        'identifier' : 'cthulhubot-git',
                        'parameters' : {
                            'repository' : '/tmp/repo.git'
                        }
                    },
                    {},
                    {},
                    {
                        'identifier' : 'cthulhubot-debian-package-ftp-upload',
                        'parameters' : {
                            'ftp_user' : 'xxx',
                            'ftp_password' : 'xxx',
                            'ftp_directory' : '',
                            'ftp_host' : ''
                        }
                    }
                ]
            }
        )
        
        self.assignment = self.assignment_model.get_domain_object()

        self.build_directory = os.path.join(self.base_directory, self.assignment.get_identifier())

        self.transaction.commit()

    def test_dir_not_exists_by_default(self):
        self.assert_equals(0, len(os.listdir(self.base_directory)))
        self.assert_false(self.assignment.build_directory_exists())

    def test_creating_creates_dir(self):
        self.assert_equals(0, len(os.listdir(self.base_directory)))

        self.assignment.create_build_directory()
        self.assert_equals(1, len(os.listdir(self.base_directory)))

    def test_exists_check_recognizes_created_dir(self):
        self.assert_equals(0, len(os.listdir(self.base_directory)))

        self.assignment.create_build_directory()

        self.assert_true(self.assignment.build_directory_exists())

    def test_loading_assignment_config_works(self):
        self.assert_equals(4, len(self.assignment.get_shell_commands()))

    def test_master_string_creation(self):
        master = settings.BUILDMASTER_NETWORK_NAME
        self.assert_equals("%s:%s" % (master, self.buildmaster.buildmaster_port), self.assignment.get_master_connection_string())

    def test_uri_constructed(self):
        self.assert_true(self.assignment.get_absolute_url() is not None)

    def test_remote_error_on_bad_directory_nesting(self):
        self.computer.basedir = "/badly/nested/nonexistent/basedir"
        self.assert_raises(RemoteCommandError, self.assignment.create_build_directory)

    def test_directory_not_created_by_default(self):
        self.assert_equals(DirectoryNotCreated.ID, self.assignment.get_status().ID)

    def test_directory_not_created_by_default_in_text(self):
        assert len(unicode(DirectoryNotCreated)) > 0
        self.assert_equals(DirectoryNotCreated.DEFAULT_STATUS, self.assignment.get_text_status())

    def test_bare_offline_after_directory_created(self):
        self.assignment.create_build_directory()
        self.assert_equals(AssignmentOffline.ID, self.assignment.get_status().ID)

    def test_offline_after_master_started_without_slave(self):
        self.assignment.create_build_directory()
        self.buildmaster.start()
        self.assert_equals(AssignmentOffline.ID, self.assignment.get_status().ID)

    def test_ready_after_starting_up(self):
        self.assignment.create_build_directory()
        self.buildmaster.start()
        self.assignment.start()
        try:
            self.assert_equals(AssignmentReady.ID, self.assignment.get_status().ID)
        finally:
            self.assignment.stop()


    def test_factory_retrieval(self):
        self.assignment.get_factory()

    def tearDown(self):
        self.buildmaster.stop(ignore_not_running=True)
        self.buildmaster.delete()
        rmtree(self.base_directory)

        super(TestBuildDirectory, self).tearDown()

