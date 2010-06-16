from cthulhubot.commands.interface import Command

class NoseTests(Command):
    identifier = 'cthulhubot-tests-nose'
    name = {
        'basic' : u"Run tests",
        'running' : u'Running tests',
        'succeeded' : u'Tested',
        'failed' : u'Test failed',
    }

    parameters = {}

    command = ["nosetests"]

class PaverTests(Command):
    identifier = 'cthulhubot-paver-test'
    name = {
        'basic' : u"Run tests",
        'running' : u'Running tests',
        'succeeded' : u'Tested',
        'failed' : u'Test failed',
    }

    parameters = {}

    command = ["paver", "test"]

class PaverUnitTests(Command):
    identifier = 'cthulhubot-paver-unit'
    name = {
        'basic' : u"Run unittests",
        'running' : u'Running unittests',
        'succeeded' : u'Tested',
        'failed' : u'Unitests failed',
    }

    parameters = {}

    command = ["paver", "unit"]

class PaverIntegrationTests(Command):
    identifier = 'cthulhubot-paver-integrate'
    name = {
        'basic' : u"Run integration tests",
        'running' : u'Running integration tests',
        'succeeded' : u'Tested',
        'failed' : u'Integration tests failed',
    }

    parameters = {}

    command = ["paver", "integrate"]

