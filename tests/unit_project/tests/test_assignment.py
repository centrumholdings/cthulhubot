from djangosanetesting.cases import DatabaseTestCase
from example_project.tests.helpers import MockJob, MockBuildmaster
from mock import Mock

import os, os.path
from shutil import rmtree
from tempfile import mkdtemp
from datetime import datetime

from django.conf import settings
from django.utils.simplejson import dumps

from buildbot.status.builder import SUCCESS, WARNINGS, FAILURE, SKIPPED, EXCEPTION

from cthulhubot.assignment import Assignment, DirectoryNotCreated, AssignmentOffline, AssignmentReady
from cthulhubot.err import RemoteCommandError, UnconfiguredCommandError
from cthulhubot.project import create_project
from cthulhubot.models import Job, JobAssignment, BuildComputer, Command, CommandConfiguration, ProjectClient
from cthulhubot.views import create_job_assignment
from cthulhubot.mongo import get_database_connection


class TestCreation(DatabaseTestCase):
    def setUp(self):
        super(TestCreation, self).setUp()
        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com", repository_uri="/tmp/project")
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

    def test_one_client_per_assigned_computer(self):
        self.create_assignment()
        new_computer = BuildComputer.objects.create(name="blah", hostname="blah")
        create_job_assignment(computer = new_computer, job = self.job, project = self.project)

        self.assertEquals(2, len(ProjectClient.objects.all()))


    def test_client_password_generated(self):
        self.create_assignment()
        assert len(ProjectClient.objects.all()[0].password) > 0

    def test_client_password_not_update_for_multiple_assignments(self):
        self.create_assignment()
        password = ProjectClient.objects.all()[0].password
        self.create_assignment()
        self.assert_equals(password, ProjectClient.objects.all()[0].password)


class TestResults(DatabaseTestCase):
    def setUp(self):
        super(TestResults, self).setUp()
        self.db = get_database_connection()

        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com", repository_uri="/tmp/project")
        self.buildmaster = self.project.buildmaster_set.all()[0]

        self.computer_model = BuildComputer.objects.create(hostname = "localhost")
        self.computer = self.computer_model.get_domain_object()

        self.job = job = Job.objects.create(slug='cthulhubot-sleep')
        self.job.auto_discovery()

        self.assignment_model = create_job_assignment(
            computer = self.computer_model,
            job = job,
            project = self.project
        )

        self.assignment = self.assignment_model.get_domain_object()

    def test_build_results_before_first_run(self):
        self.db.builds.insert({
            'builder' : str(self.assignment.get_identifier()),
            'slaves' : [ProjectClient.objects.all()[0].get_name()],
            'number' : 1,
            'time_start' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00),
            'time_stop' : None,
            'steps' : [],
        })

        self.assert_equals(u"No result yet", self.assignment.get_last_build_status())

    def test_failed_result(self):
        build = {
            'builder' : str(self.assignment.get_identifier()),
            'slaves' : [ProjectClient.objects.all()[0].get_name()],
            'number' : 1,
            'time_start' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00),
            'time_stop' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01),
            'steps' : [],
        }

        self.db.builds.insert(build)
        step = {
            'time_start' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00),
            'time_stop' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01),
            'stdout' : '',
            'stderr' : '',
            'headers' : '',
            'successful' : False,
            'result' : FAILURE,
        }

        self.db.steps.insert(step)
        build['steps'].append(step)
        self.db.builds.save(build)
        self.assert_equals(u"Failure", self.assignment.get_last_build_status())

    def test_failure_before_success_is_still_fails(self):
        build = {
            'builder' : str(self.assignment.get_identifier()),
            'slaves' : [ProjectClient.objects.all()[0].get_name()],
            'number' : 1,
            'time_start' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00),
            'time_stop' : None,
            'steps' : [],
        }

        self.db.builds.insert(build)

        step = {
            'time_start' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00),
            'time_stop' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01),
            'stdout' : '',
            'stderr' : '',
            'headers' : '',
            'successful' : False,
            'result' : FAILURE,
        }

        self.db.steps.insert(step)
        build['steps'].append(step)
        step = {
            'time_start' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01),
            'time_stop' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01),
            'stdout' : '',
            'stderr' : '',
            'headers' : '',
            'successful' : False,
            'result' : SUCCESS,
        }
        self.db.steps.insert(step)
        build['steps'].append(step)


        self.db.builds.save(build)
        self.assert_equals(u"Failure", self.assignment.get_last_build_status())

    def test_simple_success(self):
        build = {
            'builder' : str(self.assignment.get_identifier()),
            'slaves' : [ProjectClient.objects.all()[0].get_name()],
            'number' : 1,
            'time_start' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00),
            'time_stop' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01),
            'steps' : [],
        }

        self.db.builds.insert(build)

        step = {
            'time_start' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00),
            'time_stop' : datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01),
            'stdout' : '',
            'stderr' : '',
            'headers' : '',
            'successful' : True,
            'result' : SUCCESS,
        }

        self.db.steps.insert(step)
        build['steps'].append(step)
        self.db.builds.save(build)
        self.assert_equals(u"Success", self.assignment.get_last_build_status())



    def tearDown(self):
        self.buildmaster.stop(ignore_not_running=True)
        self.buildmaster.delete()

        super(TestResults, self).tearDown()

