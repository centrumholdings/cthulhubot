from djangosanetesting import UnitTestCase

from cthulhubot.commands import get_available_commands

class TestCommandsDiscoverable(UnitTestCase):

    def test_debian_package_creator_discovered(self):
        # aka basic discovering
        assert 'cthulhubot-debian-build-debian-package' in get_available_commands()

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
