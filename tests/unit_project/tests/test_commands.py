from djangosanetesting import UnitTestCase, DatabaseTestCase

from cthulhubot.commands import get_available_commands, get_command
from cthulhubot.models import Command

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
        django_test = get_available_commands().get('cthulhubot-django-unit-test-config')

        self.assert_raises(ValueError, django_test, config={})

class TestCommandConfigurableFromDatabase(DatabaseTestCase):
    def test_database_association(self):
        cmd = get_command('cthulhubot-debian-build-debian-package')()
        command, created = Command.objects.get_or_create(slug=cmd.slug)

        self.assert_equals(command.get_command(), cmd.get_command())

