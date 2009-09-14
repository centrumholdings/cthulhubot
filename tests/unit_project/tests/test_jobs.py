from djangosanetesting import DatabaseTestCase

from cthulhubot.jobs import get_job, get_undiscovered_jobs
from cthulhubot.commands import get_command
from cthulhubot.models import Command, Job
from cthulhubot.err import ConfigurationError, UndiscoveredCommandError, UnconfiguredCommandError


class TestJobsDiscovery(DatabaseTestCase):

    def test_debian_package_creator_discovered(self):
        # aka basic discovering
        job = get_job('cthulhubot-debian-package-creation')
        self.assert_true(job is not None)

#TODO: This is test for configure-job-on-discovery user story, this is actually not implemented yet
#    def test_configuration_storing_for_jobs(self):
#        # prepare jobs & commands
#        config_options = {
#            "database_config_file" : "fajl.py",
#            "django_settings_directory" : "dir"
#        }
#
#        job = Job.objects.create(slug='enterprise-unit-test-system')
#
#        unit_test = Command.objects.create(slug=get_command('cthulhubot-django-unit-test-config').slug)
#        unit_test.save_configuration(job=job, config_options=config_options)
#
#        # now check that job is aware of configuration
#        # and that configuration took only that config options it's interested in
#
#        self.assert_equals(["python", "setup.py", "configtest", "-f",
#                "--database-config-file=fajl.py", "--django-settings-directory=dir",
#            ],
#
#            job.get_configured_command(unit_test)
#        )

#    def test_usage_of_undiscovered_commands(self):
#        # let's take DebianPackageFtpUpload, configure host and let every
#        # project configure user & pass
#        job = Job.objects.create(slug='cthulhubot-debian-package-creation')
#
#        self.assert_raises(UndiscoveredCommandError,
#            job.get_configured_commands
#        )
#
#    def test_configuration_propagation_unconfigured_raises_error(self):
#        # let's take DebianPackageFtpUpload, configure host and let every
#        # project configure user & pass
#        job = Job.objects.create(slug='cthulhubot-debian-package-creation')
#        job.auto_discovery()
#
#        self.assert_raises(UnconfiguredCommandError,
#            job.get_configured_commands
#        )


    def test_auto_discovery(self):
        self.assert_equals(0, len(Command.objects.all()))
        job = Job.objects.create(slug='cthulhubot-debian-package-creation')
        job.auto_discovery()

        self.assert_equals(3, len(Command.objects.all()))


    def test_command_retrieval(self):
        job = Job.objects.create(slug='cthulhubot-debian-package-creation')
        job.auto_discovery()
        
        commands = job.get_commands()
        self.assert_equals(3, len(commands))

    def test_undiscovered_jobs_retrieval(self):
        assert 'cthulhubot-debian-package-creation' in get_undiscovered_jobs()

    def test_command_not_discovered_as_job(self):
        assert 'cthulhubot-debian-build-debian-package' not in get_undiscovered_jobs()

    def test_get_command_for_configuration(self):
        job = get_undiscovered_jobs().get('cthulhubot-debian-package-creation')()
        params = job.get_configuration_parameters()

        # we're expecting configuration parameters for upload only
        self.assert_equals(1, len(params))

        # and 4 unconfigured commands in it
        self.assert_equals(4, len(params[0]['parameters']))

