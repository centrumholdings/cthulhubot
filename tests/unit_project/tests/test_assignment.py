from djangosanetesting.cases import UnitTestCase
from djangosanetesting.cases import DatabaseTestCase
from mock import Mock
from unit_project.tests.helpers import (
    MockJob, MockBuildComputer, MockProject,
    EchoJob,
    register_mock_jobs_and_commands,
)

import os, os.path
from shutil import rmtree
from tempfile import mkdtemp
from datetime import datetime

from django.conf import settings
from django.utils.simplejson import dumps, loads
from django.core import urlresolvers
from django.core.urlresolvers import get_script_prefix

from buildbot.status.builder import SUCCESS, WARNINGS, FAILURE, SKIPPED, EXCEPTION

from cthulhubot.assignment import Assignment, DirectoryNotCreated, AssignmentOffline, AssignmentReady
from cthulhubot.err import RemoteCommandError, UnconfiguredCommandError
from cthulhubot.project import create_project
from cthulhubot.models import Job, JobAssignment, BuildComputer, Command, ProjectClient
from cthulhubot.views import create_job_assignment
from cthulhubot.mongo import get_database_connection

class TestJobsConfiguration(DatabaseTestCase):
    def setUp(self):
        super(TestJobsConfiguration, self).setUp()

        register_mock_jobs_and_commands()

        job_model = Mock()
        self.job = EchoJob(model=job_model)

        job_model.get_domain_object.return_value = self.job

        computer = MockBuildComputer()
        computer.id = 1

        project = MockProject()
        project.id = 1

        assignment_model = Mock()
        assignment_model.computer = computer
        assignment_model.job = self.job.model
        assignment_model.project = project,
        assignment_model.config = dumps({})
        self.assignment = Assignment(model=assignment_model)

    def test_unconfigured_job_retrieval(self):
        self.assert_raises(UnconfiguredCommandError, self.assignment.get_shell_commands)

    def test_loading_empty_configuration_still_raises_error(self):
        self.assert_raises(UnconfiguredCommandError, self.assignment.get_shell_commands)

    def test_configuration_propageted_to_command(self):
        text = 'bazaah!'
        self.assignment.model.config = dumps({
            'commands' : [
                {
                    'identifier' : 'cthulhubot-test-helper-echo',
                    'parameters' : {
                        'what' : text
                    }
                }
            ]
        })
        self.assert_equals([['echo', text]], self.assignment.get_shell_commands())

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

    def test_identification_generated_from_pk(self):
        self.create_assignment()
        self.assert_equals(str(self.assignment_model.pk), self.assignment_model.get_identifier())

    def test_identification_raises_value_error_when_not_available(self):
        assignment = JobAssignment(project=self.project, computer=self.computer_model, job=self.job)
        self.assert_raises(ValueError, assignment.get_identifier)

    def test_client_password_generated(self):
        self.create_assignment()
        assert len(ProjectClient.objects.all()[0].password) > 0

    def test_client_password_not_update_for_multiple_assignments(self):
        self.create_assignment()
        password = ProjectClient.objects.all()[0].password
        self.create_assignment()
        self.assert_equals(password, ProjectClient.objects.all()[0].password)

class TestAssignment(DatabaseTestCase):
    def setUp(self):
        super(TestAssignment, self).setUp()

        self.computer = MockBuildComputer()
        self.computer.adapter = Mock()
        self.job = MockJob()
        self.project = MockProject()

        self.assignment = JobAssignment(pk=1, project=self.project, computer=self.computer, job=self.job)

        self._mock_resolver()

    def _mock_resolver(self):
        self._original_resolver = urlresolvers.get_resolver

        resolver = Mock()
        self.prefix = get_script_prefix()
        self.mocked_uri = resolver.reverse.return_value="heureka"

        urlresolvers.get_resolver = lambda conf: resolver

    def _unmock_resolver(self):
        urlresolvers.get_resolver = self._original_resolver
        self._original_resolver = None

    def test_url_retrieving(self):
        self.assert_equals(self.prefix+self.mocked_uri, self.assignment.get_absolute_url())

    def tearDown(self):
        super(TestAssignment, self).tearDown()

        self._unmock_resolver()

class TestResults(DatabaseTestCase):
    def setUp(self):
        super(TestResults, self).setUp()
        self.db = get_database_connection()

        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com", repository_uri="/tmp/project")
        self.buildmaster = self.project.buildmaster_set.all()[0]

        self.computer_model = self.computer = BuildComputer.objects.create(hostname = "localhost")

        self.job = job = Job.objects.create(slug='cthulhubot-sleep')
        self.job.auto_discovery()

        self.assignment_model = create_job_assignment(
            computer = self.computer_model,
            job = job,
            project = self.project
        )

        self.assignment = self.assignment_model.get_domain_object()

    def insert_build(self, time_end=False, time_start=False):
        if not time_start:
            time_start = datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00)

        if time_end is False:
            time_start = datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01)

        build = {
            'builder' : str(self.assignment.get_identifier()),
            'slaves' : [ProjectClient.objects.all()[0].get_name()],
            'number' : 1,
            'time_start' : time_start,
            'time_end' : time_end,
            'steps' : [],
        }
        self.db.builds.insert(build)

        return build

    def insert_step(self, build, result=False, successful=False, time_end=False, time_start=False):
        if result is False:
            result = FAILURE

        if time_end is False:
            time_end = datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01)

        if time_start is False:
            time_start = datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00)

        step = {
            'time_start' : time_start,
            'time_end' : time_end,
            'stdout' : '',
            'stderr' : '',
            'headers' : '',
            'successful' : successful,
            'result' : result,
        }
        self.db.steps.insert(step)
        build['steps'].append(step)
        self.db.builds.save(build)
        return step

    def test_build_results_before_first_run(self):
        self.assert_equals(u"No result yet", self.assignment.get_last_build_status())

    def test_build_results_before_first_run_ended(self):
        self.insert_build()
        self.assert_equals(u"No result yet", self.assignment.get_last_build_status())

    def test_failed_result(self):
        build = self.insert_build(time_end=datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01))
        self.insert_step(build)

        self.assert_equals(u"Failure", self.assignment.get_last_build_status())

    def test_failure_before_success_is_still_fails(self):
        build = self.insert_build()
        self.insert_step(build)
        self.insert_step(build, result=SUCCESS)
        self.assert_equals(u"Failure", self.assignment.get_last_build_status())

    def test_simple_success(self):
        build = self.insert_build(time_end=datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01))
        self.insert_step(build, result=SUCCESS)
        self.assert_equals(u"Success", self.assignment.get_last_build_status())

    def test_last_finished_build_used_when_last_is_not_finished_yet(self):
        build = self.insert_build(time_end=datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01))
        self.insert_step(build, result=SUCCESS)

        build = self.insert_build(time_start=datetime(year=2009, month=01, day=01, hour=13, minute=00, second=00), time_end=None)
        self.insert_step(build, result=FAILURE, time_start = datetime(year=2009, month=01, day=01, hour=13, minute=00, second=00), time_end=datetime(year=2009, month=01, day=01, hour=13, minute=00, second=01))
        self.insert_step(build, result=None, time_end=None, time_start=datetime(year=2009, month=01, day=01, hour=13, minute=00, second=01))
        self.assert_equals(u"Success", self.assignment.get_last_build_status())

    def tearDown(self):
        self.buildmaster.stop(ignore_not_running=True)
        self.buildmaster.delete()

        super(TestResults, self).tearDown()


class TestJobConfigurationForm(UnitTestCase):
    def test_form_generated(self):
        raise self.SkipTest()