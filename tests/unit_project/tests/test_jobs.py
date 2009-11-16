from django.core.management import call_command
from djangosanetesting import DatabaseTestCase, UnitTestCase

from django.utils.simplejson import dumps

from cthulhubot.jobs import get_job, get_undiscovered_jobs
from cthulhubot.commands import get_command, Sleep as SleepCommand
from cthulhubot.models import Command, Job, JobAssignment
from cthulhubot.err import ConfigurationError, UndiscoveredCommandError, UnconfiguredCommandError
from cthulhubot.forms import get_command_params_from_form_data, get_job_configuration_form

from unit_project.tests.helpers import (
    MockJob, MockBuildComputer, MockProject,
    EchoJob,
    register_mock_jobs_and_commands
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

        # We shoudl receive one dict per job command
        self.assert_equals(len(job.commands), len(params))

        # and 4 unconfigured commands in ftp
        self.assert_equals(4, len(params[-1:][0]['parameters']))

class TestHelperJobCreation(UnitTestCase):
    def setUp(self):
        super(TestHelperJobCreation, self).setUp()
        self.job = EchoJob()
        register_mock_jobs_and_commands()


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

    def test_dict_bad_slug_raises_error(self):
        self.assert_raises(ValueError, self.job.get_parameter_dict, 0, 'zoidberg')

    def test_dict_contains_proper_help_text(self):
        self.assert_equals(SleepCommand.parameters['time']['help'], self.job.get_parameter_dict(0, 'time')['help'])

    def test_dict_contains_job_value_if_it_overwrites_command(self):
        self.assert_equals(0.02, self.job.get_parameter_dict(0, 'time')['value'])

    def test_empty_form_provided_for_command_one_returned(self):
        self.assert_equals([{'identifier': 'cthulhubot-sleep', 'parameters': {}}], get_command_params_from_form_data(self.job, {}))

    def test_form_created_with_proper_number_of_fields(self):
        self.assert_equals(1, len(get_job_configuration_form(self.job).fields))

#    def test_form_back_translation(self):
#        params = get_command_params_from_form_data(form_data)
#        expected_params = {
#            'cthulhubot-debian-package-ftp-upload' : {
#                'ftp_host' : u'host',
#                'ftp_password' : u'password',
#            }
#        }
#
#        self.assert_equals(expected_params, params)


#    def test_form_generated_in_order_and_proper_empty_dictionaries_returned(self):
#        form_data = {
#            'Cthulhubot-debian-package-ftp-upload: ftp_host' : u'host',
#            'Cthulhubot-debian-package-ftp-upload: ftp_password' : u'password'
#        }
#        params = get_command_params_from_form_data(form_data)
#        expected_params = {
#            'cthulhubot-debian-package-ftp-upload' : {
#                'ftp_host' : u'host',
#                'ftp_password' : u'password',
#            }
#        }
#
#        self.assert_equals(expected_params, params)
#
