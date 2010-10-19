from cthulhubot.commands.interface import Command

class Sleep(Command):
    identifier = 'cthulhubot-sleep'
    name = {
        'basic' : u"Sleep",
        'running' : u'Sleeping',
        'succeeded' : u'Got a sleep',
        'failed' : u'Failed to sleep',
    }

    parameters = {
        'time' : {
            'help' : u'How long to sleep (in seconds)',
            'value' : 0.01,
            'required' : True,
        },
    }

    command = ["sleep", "%(time)s"]
