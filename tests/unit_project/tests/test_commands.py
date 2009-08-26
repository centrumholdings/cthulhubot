from djangosanetesting import UnitTestCase, DatabaseTestCase

from cthulhubot.commands import get_available_commands, get_command
from cthulhubot.models import Command, Job

class TestCommandsDiscoverable(UnitTestCase):

    def test_debian_package_creator_discovered(self):
        # aka basic discovering
        command = get_command('cthulhubot-debian-build-debian-package')
        self.assert_true(command is not None)

    def test_substitution_default(self):
        django_test = get_available_commands().get('cthulhubot-django-unit-test-config')

        self.assert_equals(["python", "setup.py", "configtest", "-f",
            "--database-config-file=fajl.py", "--django-settings-directory=tests/unit_project/settings",
        ], django_test(config={
            "database_config_file" : "fajl.py"
        }).get_command())

    def test_substitution_default_overwritten(self):
        django_test = get_available_commands().get('cthulhubot-django-unit-test-config')

        self.assert_equals(["python", "setup.py", "configtest", "-f",
            "--database-config-file=fajl.py", "--django-settings-directory=dir",
        ], django_test(config={
            "database_config_file" : "fajl.py",
            "django_settings_directory" : "dir"
        }).get_command())

    def test_substitution_required_not_provided(self):
        klass = get_available_commands().get('cthulhubot-django-unit-test-config')
        cmd = klass(config={})

        self.assert_raises(ValueError, cmd.get_command)

class TestCommandConfigurableFromDatabase(DatabaseTestCase):
    def test_database_association(self):
        cmd = get_command('cthulhubot-debian-build-debian-package')()
        command = Command.objects.create(slug=cmd.slug)

        self.assert_equals(command.get_command(), cmd.get_command())

    def test_saving_configuration(self):
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



        



        