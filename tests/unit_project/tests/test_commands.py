from djangosanetesting import UnitTestCase, DatabaseTestCase

from cthulhubot.commands import get_available_commands, get_command, get_undiscovered_commands
from cthulhubot.models import Command
from cthulhubot.err import UnconfiguredCommandError
from cthulhubot.forms import get_command_params_from_form_data

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

    def test_sleep_discovered(self):
        assert get_command('cthulhubot-sleep') is not None


    def test_discovery_of_unconfigured_packages_misses_configured_ones(self):
        cmd = get_command('cthulhubot-debian-build-debian-package')()
        Command.objects.create(slug=cmd.identifier)

        commands = get_undiscovered_commands()
        assert cmd.identifier not in commands

    def test_discovery_of_unconfigured_packages_matches_unconfigured(self):
        slug = 'cthulhubot-debian-build-debian-package'
        commands = get_undiscovered_commands()
        self.assert_equals(slug, commands.get(slug).identifier)

    def test_discovery_of_unconfigured_packages_finding_configured_and_unconfigured(self):
        slug = 'cthulhubot-debian-build-debian-package'
        cmd = get_command(slug)()
        Command.objects.create(slug=cmd.identifier)

        unconfigured_slug = 'cthulhubot-django-unit-test-config'

        commands = get_undiscovered_commands()

        self.assert_equals(None, commands.get(cmd.identifier))
        self.assert_equals(unconfigured_slug, commands.get(unconfigured_slug).identifier)

    def test_unconfigured_parameters_found(self):
        cmd = get_command('cthulhubot-debian-package-ftp-upload')()

        self.assert_equals(4, len(cmd.get_unconfigured_parameters()))


    def test_form_back_translation(self):
        form_data = {'Cthulhubot-debian-package-ftp-upload: ftp_host' : u'host' , 'Cthulhubot-debian-package-ftp-upload: ftp_password' : u'password'}
        params = get_command_params_from_form_data(form_data)
        expected_params = {
            'cthulhubot-debian-package-ftp-upload' : {
                'ftp_host' : u'host',
                'ftp_password' : u'password',
            }
        }

        self.assert_equals(expected_params, params)

class TestDatabaseStore(DatabaseTestCase):
    def test_database_association(self):
        cmd = get_command('cthulhubot-debian-build-debian-package')()
        command = Command.objects.create(slug=cmd.identifier)

        self.assert_equals(command.get_command(), cmd.get_command())


class TestGit(DatabaseTestCase):
    def test_git_repository_uri_propagation(self):
        cmd = get_command('cthulhubot-git')()
        cmd.update_config(config={'repository' : '/tmp/repo'})

        self.assert_equals('/tmp/repo', cmd.get_buildbot_command().args['repourl'])
