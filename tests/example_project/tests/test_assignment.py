from djangosanetesting.cases import DestructiveDatabaseTestCase
from example_project.tests.helpers import MockJob, MockBuildmaster
from mock import Mock

import os, os.path
from shutil import rmtree
from tempfile import mkdtemp

from django.conf import settings

from cthulhubot.assignment import Assignment, DirectoryNotCreated, AssignmentOffline, AssignmentReady
from cthulhubot.computer import Computer
from cthulhubot.err import RemoteCommandError
from cthulhubot.project import create_project

class TestBuildDirectory(DestructiveDatabaseTestCase):
    def setUp(self):
        super(TestBuildDirectory, self).setUp()


        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com")
        self.buildmaster = self.project.buildmaster_set.all()[0]

        self.base_directory = mkdtemp()
        self.computer = Computer(key=None, host="localhost", user=None)
        self.computer._basedir = self.base_directory

        mocked_assignment = Mock()
        mocked_assignment.pk = 1

        self.assignment = Assignment(
            computer=self.computer,
            job = MockJob(),
            project=self.project,
            model = mocked_assignment
        )

        self.build_directory = os.path.join(self.base_directory, str(mocked_assignment.pk))

        self.assignment.job.buildmaster = self.buildmaster

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

    def test_master_string_creation(self):
        master = settings.BUILDMASTER_NETWORK_NAME
        self.assert_equals("%s:%s" % (master, self.buildmaster.buildmaster_port), self.assignment.get_master_connection_string())

    def test_uri_constructed(self):
        self.assert_true(self.assignment.get_absolute_url() is not None)

    def test_remote_error_on_bad_directory_nesting(self):
        self.computer._basedir = "/badly/nested/nonexistent/basedir"
        self.assert_raises(RemoteCommandError, self.assignment.create_build_directory)

    def test_directory_not_created_by_default(self):
        self.assert_equals(DirectoryNotCreated.ID, self.assignment.get_status().ID)

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

    def tearDown(self):
        self.buildmaster.stop(ignore_not_running=True)
        #self.buildmaster.delete()
        rmtree(self.base_directory)

        super(TestBuildDirectory, self).tearDown()

