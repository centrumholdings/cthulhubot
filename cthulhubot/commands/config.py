from cthulhubot.commands.interface import Command

class DjangoUnitTestConfiguration(Command):
    slug = 'cthulhubot-django-unit-test-config'
    name = {
        'basic' : u"update from repository",
        'running' : u'updating repository',
        'succeeded' : u'repository updated',
        'failed' : u'failed to update from repository',
    }

    parameters = {
        'database_config_file' : {
            'help' : u'Path to configuration file (on given slave), where DATABASE_* settings are specified',
            'value' : None,
            'required' : True,
        },
        'django_settings_directory' : {
            "help" : u"Directory (relative to repository root), where gathered configuration should be written (as local.py). Default to tests/unit_project/settings",
            'value' : 'tests/unit_project/settings',
            'required' : False,
        },
    }

    command = ["python", "setup.py", "configtest", "-f",
        "--database-config-file=%(database_config_file)s", "--django-settings-directory=%(django_settings_directory)s",
    ]



