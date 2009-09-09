from djangosanetesting import UnitTestCase, DatabaseTestCase

from cthulhubot.commands import get_available_commands, get_command, get_undiscovered_commands
from cthulhubot.models import Command, Job
from cthulhubot.err import UnconfiguredCommandError

class TestCommandsDiscovery(UnitTestCase):

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

        self.assert_raises(UnconfiguredCommandError, cmd.get_command)

class TestCommandsConfigurationAndDiscovery(DatabaseTestCase):

    def test_build_and_unit_discovered(self):
        assert get_command('cthulhubot-debian-build-debian-package') is not None
        assert get_command('cthulhubot-django-unit-test-config') is not None

    def test_discovery_of_unconfigured_packages_misses_configured_ones(self):
        cmd = get_command('cthulhubot-debian-build-debian-package')()
        Command.objects.create(slug=cmd.slug)

        commands = get_undiscovered_commands()
        assert cmd.slug not in commands

    def test_discovery_of_unconfigured_packages_matches_unconfigured(self):
        slug = 'cthulhubot-debian-build-debian-package'
        commands = get_undiscovered_commands()
        self.assert_equals(slug, commands.get(slug).slug)

    def test_discovery_of_unconfigured_packages_finding_configured_and_unconfigured(self):
        slug = 'cthulhubot-debian-build-debian-package'
        cmd = get_command(slug)()
        Command.objects.create(slug=cmd.slug)

        unconfigured_slug = 'cthulhubot-django-unit-test-config'

        commands = get_undiscovered_commands()

        self.assert_equals(None, commands.get(cmd.slug))
        self.assert_equals(unconfigured_slug, commands.get(unconfigured_slug).slug)

class TestDatabaseStore(DatabaseTestCase):
    def test_database_association(self):
        cmd = get_command('cthulhubot-debian-build-debian-package')()
        command = Command.objects.create(slug=cmd.slug)

        self.assert_equals(command.get_command(), cmd.get_command())

        