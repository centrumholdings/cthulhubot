from django.core.management import call_command
from djangosanetesting import DatabaseTestCase

from django.utils.simplejson import dumps

from cthulhubot.jobs import get_job, get_undiscovered_jobs
from cthulhubot.commands import get_command
from cthulhubot.models import Command, Job, JobAssignment
from cthulhubot.err import ConfigurationError, UndiscoveredCommandError, UnconfiguredCommandError

from unit_project.tests.helpers import (
    MockJob, MockBuildComputer, MockProject,
    EchoJob
)


class TestDiscoverCommand(DatabaseTestCase):
    def test_no_command_available_without_discovery(self):
        self.assert_equals(0, Job.objects.count())

    def test_sleep_discovered(self):
        call_command("discover", commit=0)

        slug = 'cthulhubot-sleep'
        try:
            Job.objects.get(slug=slug)
        except Job.DoesNotExist:
            assert False, "Job not discovered!"

class TestJobsDiscovery(DatabaseTestCase):

    def test_debian_package_creator_discovered(self):
        # aka basic discovering
        job = get_job('cthulhubot-debian-package-creation')
        self.assert_true(job is not None)

    def test_auto_discovery(self):
        self.assert_equals(0, len(Command.objects.all()))
        job = Job.objects.create(slug='cthulhubot-debian-package-creation')
        job.auto_discovery()

        self.assert_equals(4, len(Command.objects.all()))


    def test_command_retrieval(self):
        job = Job.objects.create(slug='cthulhubot-debian-package-creation')
        job.auto_discovery()
        
        commands = job.get_commands()
        self.assert_equals(4, len(commands))

    def test_undiscovered_jobs_retrieval(self):
        assert 'cthulhubot-debian-package-creation' in get_undiscovered_jobs()

    def test_command_not_discovered_as_job(self):
        assert 'cthulhubot-debian-build-debian-package' not in get_undiscovered_jobs()

    def test_get_command_for_configuration(self):
        job = get_undiscovered_jobs().get('cthulhubot-debian-package-creation')()
        params = job.get_configuration_parameters()

        # we're expecting configuration parameters for git & upload only
        self.assert_equals(2, len(params))

        # and 4 unconfigured commands in ftp
        self.assert_equals(4, len(params[1]['parameters']))

class TestHelperJobCreation(DatabaseTestCase):
    def setUp(self):
        super(TestHelperJobCreation, self).setUp()
        self.job = EchoJob()

    def test_commands_retrieved(self):
        self.assert_equals(1, len(self.job.get_commands()))

class TestJob(DatabaseTestCase):
    def setUp(self):
        super(TestJob, self).setUp()

        self.job_model = Job.objects.create(slug='cthulhubot-sleep')
        self.job_model.auto_discovery()

        self.job = self.job_model.get_domain_object()

    def test_unicode_on_job_returns_proper_text(self):
        self.assert_equals(u"Sleep for a sec", unicode(self.job))

    def test_unicode_on_model_returns_slug(self):
        self.assert_equals(u"cthulhubot-sleep", unicode(self.job_model))
