from cthulhubot.commands.interface import Command

class PaverBootstrap(Command):
    identifier = 'cthulhubot-paver-bootstrap'
    name = {
        'basic' : u"Bootstrap",
        'running' : u'Bootstrapping',
        'succeeded' : u'Bootstrapped',
        'failed' : u'Bootstrap failed',
    }

    parameters = {}

    command = ["paver", "bootstrap"]

class PaverPrepare(Command):
    identifier = 'cthulhubot-paver-prepare'
    name = {
        'basic' : u"Prepare",
        'running' : u'Preparing',
        'succeeded' : u'Prepared',
        'failed' : u'Preparation failed',
    }

    parameters = {}

    command = ["paver", "prepare"]

