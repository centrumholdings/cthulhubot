from django.core.management import call_command
from djangosanetesting import DatabaseTestCase, UnitTestCase

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

class TestJob(UnitTestCase):
    def setUp(self):
        super(TestJob, self).setUp()
        self.job = Job(slug='cthulhubot-sleep').get_domain_object()
        self.echo_job = Job(slug='cthulhubot-test-helper-echo-job').get_domain_object()

    def test_unicode_on_job_returns_proper_text(self):
        self.assert_equals(u"Sleep for a sec", unicode(self.job))

    def test_unicode_on_model_returns_slug(self):
        self.assert_equals(u"cthulhubot-sleep", unicode(self.job.model))

    def test_dict_bad_slug_raises_error(self):
        self.assert_raises(ValueError, self.job.get_parameter_dict, 0, 'zoidberg')

    def test_dict_contains_proper_help_text(self):
        self.assert_equals(SleepCommand.parameters['time']['help'], self.job.get_parameter_description_dict(0, 'time')['help'])

    def test_dict_contains_job_value_if_it_overwrites_command(self):
        self.assert_equals(0.02, self.job.get_parameter_dict(0, 'time'))

    def test_empty_form_provided_for_command_one_returned(self):
        self.assert_equals({'commands' : [{'command': 'cthulhubot-sleep', 'parameters': {}}]}, get_command_params_from_form_data(self.job, {}))

    def test_form_created_with_proper_number_of_fields(self):
        self.assert_equals(1, len(get_job_configuration_form(self.job).fields))

    def test_form_default_values_propagated_to_initials(self):
        self.assert_equals(0.02, get_job_configuration_form(self.job).initial.get('job_configuration_0'))

    def test_parameters_from_command_propagated_to_form_even_if_not_specified_there(self):
        self.assert_equals(1, len(get_job_configuration_form(self.echo_job).fields))


class TestJobSubclassing(UnitTestCase):

    def test_directly_overwritten_dict_contains_subclassed_job_value(self):
        job = Job(slug='cthulhubot-test-helper-echo-name-job').get_domain_object()
        self.assert_equals('name', job.get_parameter_dict(0, 'what'))

    def test_global_overwriting_works_on_first_match(self):
        job = Job(slug='cthulhubot-test-helper-multiple-echo-all-defined-job').get_domain_object()
        self.assert_equals('overwritten by job', job.get_parameter_dict(0, 'what'))

    def test_global_overwriting_works_on_all_matches(self):
        job = Job(slug='cthulhubot-test-helper-multiple-echo-all-defined-job').get_domain_object()
        for i in xrange(0, 3):
            self.assert_equals('overwritten by job', job.get_parameter_dict(i, 'what'))

    def test_overwriting_with_callback_works_for_proper_match(self):
        job = Job(slug='cthulhubot-test-helper-multiple-echo-2-defined-job').get_domain_object()
        self.assert_equals('overwritten by job callback', job.get_parameter_dict(1, 'what'))

    def test_overwriting_with_callback_works_do_not_overwrite_unrelated_matches(self):
        job = Job(slug='cthulhubot-test-helper-multiple-echo-2-defined-job').get_domain_object()
        self.assert_equals('first', job.get_parameter_dict(0, 'what'))

class TestCommandConfigUpdate(UnitTestCase):
    def setUp(self):
        super(TestCommandConfigUpdate, self).setUp()
        self.job = Job(slug='cthulhubot-sleep').get_domain_object()

    def test_bad_command_raises_error(self):
        self.assert_raises(ValueError, self.job.update_command_config, 5, {})

    def test_mismatched_command_name(self):
        self.assert_raises(ValueError, self.job.update_command_config, 0, {'command' : 'blahblahblah', 'parameters' : {'time' : 5}})

    def test_config_updated(self):
        self.job.update_command_config(0, {'command' : 'cthulhubot-sleep', 'parameters' : {'time' : 5}})
        self.assert_equals(5, self.job.get_parameter_dict(0, 'time'))

class TestSlotReplacement(UnitTestCase):

    def setUp(self):
        super(TestSlotReplacement, self).setUp()
        self.job = Job(slug='cthulhubot-test-output-job').get_domain_object()

    def test_slot_command_propagated_according_to_config(self):
        config = {
            'command' : 'cthulhubot-test-helper-echo',
            'parameters' : {}
        }
        self.job.update_command_config(0, config)

        self.assert_equals(config['command'], self.job.get_configuration_parameters()[0]['command'])

    def test_update_with_command_from_other_slot_prohibited(self):
        self.assert_raises(ValueError, self.job.update_command_config, 0, {'command' : 'cthulhubot-sleep', 'parameters' : {}})

    def test_attempt_to_work_with_unconfigured_slot_raises_error(self):
        self.assert_raises(UnconfiguredCommandError, self.job.get_commands)


