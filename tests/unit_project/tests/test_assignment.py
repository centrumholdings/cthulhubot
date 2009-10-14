from djangosanetesting.cases import DatabaseTestCase
from example_project.tests.helpers import MockJob, MockBuildmaster
from mock import Mock

import os, os.path
from shutil import rmtree
from tempfile import mkdtemp

from django.conf import settings
from django.utils.simplejson import dumps

from cthulhubot.assignment import Assignment, DirectoryNotCreated, AssignmentOffline, AssignmentReady
from cthulhubot.err import RemoteCommandError, UnconfiguredCommandError
from cthulhubot.project import create_project
from cthulhubot.models import Job, JobAssignment, BuildComputer, Command, CommandConfiguration, ProjectClient
from cthulhubot.views import create_job_assignment


class TestCreation(DatabaseTestCase):
    def setUp(self):
        super(TestCreation, self).setUp()
        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com")
        self.computer_model = BuildComputer.objects.create(hostname = "localhost")
        self.job = Job.objects.create(slug='cthulhubot-sleep')
        self.job.auto_discovery()

    def create_assignment(self):
        self.assignment_model = create_job_assignment(
            computer = self.computer_model,
            job = self.job,
            project = self.project,
        )

    def test_client_created_when_missing(self):
        self.assertEquals(0, len(ProjectClient.objects.all()))
        self.create_assignment()
        self.assertEquals(1, len(ProjectClient.objects.all()))

    def test_client_password_generated(self):
        self.create_assignment()
        assert len(ProjectClient.objects.all()[0].password) > 0

    def test_client_password_not_update_for_multiple_assignments(self):
        self.create_assignment()
        password = ProjectClient.objects.all()[0].password
        self.create_assignment()
        self.assert_equals(password, ProjectClient.objects.all()[0].password)


class TestProjectAssignment(DatabaseTestCase):
    def setUp(self):
        super(TestProjectAssignment, self).setUp()
        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com")
        self.buildmaster = self.project.buildmaster_set.all()[0]

        self.computer_model = BuildComputer.objects.create(hostname = "localhost")
        self.computer = self.computer_model.get_domain_object()

        self.job = job = Job.objects.create(slug='cthulhubot-sleep')
        self.job.auto_discovery()

        self.assignment_model = JobAssignment.objects.create(
            computer = self.computer_model,
            job = job,
            project = self.project
        )

        self.assignment = self.assignment_model.get_domain_object()

    def tearDown(self):
        self.buildmaster.stop(ignore_not_running=True)
        self.buildmaster.delete()

        super(TestProjectAssignment, self).tearDown()

