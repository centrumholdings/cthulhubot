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

