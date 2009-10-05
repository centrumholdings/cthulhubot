from djangosanetesting.cases import DestructiveDatabaseTestCase
from example_project.tests.helpers import MockJob, MockBuildmaster
from mock import Mock

import os, os.path
from shutil import rmtree
from tempfile import mkdtemp

from django.conf import settings

from cthulhubot.assignment import Assignment
from cthulhubot.computer import Computer


class TestBuildDirectory(DestructiveDatabaseTestCase):
    def setUp(self):
        super(TestBuildDirectory, self).setUp()


        self.base_directory = mkdtemp()
        self.computer = Computer(key=None, host="localhost", user=None)
        self.computer._basedir = self.base_directory

        mocked_assignment = Mock()
        mocked_assignment.pk = 1

        self.assignment = Assignment(
            computer=self.computer,
            job = MockJob(),
            model = mocked_assignment
        )

        self.build_directory = os.path.join(self.base_directory, str(mocked_assignment.pk))

        default_buildmaster_port = 9000

        self.assignment.job.buildmaster = MockBuildmaster()
        self.assignment.job.buildmaster.buildmaster_port = default_buildmaster_port

    def test_dir_not_exists_by_default(self):
        self.assert_equals(0, len(os.listdir(self.base_directory)))
        self.assert_false(self.assignment.build_directory_exists(self.build_directory))

    def test_creating_creates_dir(self):
        self.assert_equals(0, len(os.listdir(self.base_directory)))

        self.assignment.create_build_directory()
        self.assert_equals(1, len(os.listdir(self.base_directory)))

    def test_exists_check_recognizes_created_dir(self):
        self.assert_equals(0, len(os.listdir(self.base_directory)))

        self.assignment.create_build_directory()

        self.assert_true(self.assignment.build_directory_exists(self.build_directory))

    def test_master_string_creation(self):
        master = settings.BUILDMASTER_NETWORK_NAME
        port = 9000
        
        self.assignment.job.buildmaster.buildmaster_port = port

        self.assert_equals("%s:%s" % (master, port), self.assignment.get_master_connection_string())

#    def test_exists_check(self):
#        self.computer.connect()
#        self.computer.create_build_directory(
#            directory=self.build_directory,
#            master = "localhost:99999",
#            username = "notworking",
#            password = "badpassword"
#        )
#        self.assert_true(self.computer.build_directory_exists(self.build_directory))

    def tearDown(self):
        rmtree(self.base_directory)

        super(TestBuildDirectory, self).tearDown()

