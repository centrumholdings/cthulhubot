from cthulhubot.jobs.job import Job

class BareNoseTests(Job):
    identifier = 'cthulhubot-bare-nose-tests'
    name = u'Run nosetests over a project'

    commands = [
        {
            'command' : 'cthulhubot-git',
        },
        {
            'command' : 'cthulhubot-git-associate',
        },
        {
            'command' : 'cthulhubot-tests-nose',
        }
    ]

class PaverVirtualTests(Job):
    identifier = 'cthulhubot-paver-virtual-tests'
    name = u'Run tests inside virtualenv using paver'

    buildbot_commands_kwargs = {
        'env' : {
            'PATH': "bin:${PATH}"
        }
    }

    commands = [
        {
            'command' : 'cthulhubot-git',
        },
        {
            'command' : 'cthulhubot-git-associate',
        },
        {
            'command' : 'cthulhubot-paver-bootstrap',
        },
        {
            'command' : 'cthulhubot-paver-prepare',
        },
        {
            'command' : 'cthulhubot-paver-test',
        }
    ]

class PaverVirtualUnitTests(Job):
    identifier = 'cthulhubot-paver-virtual-unit-tests'
    name = u'Run unittests tests inside virtualenv using paver'

    buildbot_commands_kwargs = {
        'env' : {
            'PATH': "bin:${PATH}"
        }
    }

    commands = [
        {
            'command' : 'cthulhubot-git',
        },
        {
            'command' : 'cthulhubot-git-associate',
        },
        {
            'command' : 'cthulhubot-paver-bootstrap',
        },
        {
            'command' : 'cthulhubot-paver-prepare',
        },
        {
            'command' : 'cthulhubot-paver-unit',
        }
    ]

class PaverVirtualIntegrationTests(Job):
    identifier = 'cthulhubot-paver-virtual-integration-tests'
    name = u'Run integration tests inside virtualenv using paver'

    buildbot_commands_kwargs = {
        'env' : {
            'PATH': "bin:${PATH}"
        }
    }

    commands = [
        {
            'command' : 'cthulhubot-git',
        },
        {
            'command' : 'cthulhubot-git-associate',
        },
        {
            'command' : 'cthulhubot-paver-bootstrap',
        },
        {
            'command' : 'cthulhubot-paver-prepare',
        },
        {
            'command' : 'cthulhubot-paver-integrate',
        }
    ]

