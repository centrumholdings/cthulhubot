from djangosanetesting import UnitTestCase, DatabaseTestCase

from cthulhubot.jobs import get_job
from cthulhubot.commands import get_command
from cthulhubot.models import Command, Job

class TestJobsDiscovery(DatabaseTestCase):

    def test_debian_package_creator_discovered(self):
        # aka basic discovering
        job = get_job('cthulhubot-debian-package-creation')
        self.assert_true(job is not None)

    def test_configuration_storing(self):
        # prepare jobs & commands
        config_options = {
            "database_config_file" : "fajl.py",
            "django_settings_directory" : "dir"
        }

        job = Job.objects.create(slug='enterprise-unit-test-system')

        unit_test = Command.objects.create(slug=get_command('cthulhubot-django-unit-test-config').slug)
        unit_test.save_configuration(job=job, config_options=config_options)

        # now check that job is aware of configuration
        # and that configuration took only that config options it's interested in

        self.assert_equals(["python", "setup.py", "configtest", "-f",
                "--database-config-file=fajl.py", "--django-settings-directory=dir",
            ],

            job.get_configured_command(unit_test)
        )


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

    def test_configuration_propagation_unconfigured_raises_configuration_error(self):
        # let's take DebianPackageFtpUpload, configure host and let every
        # project configure user & pass
        pass
