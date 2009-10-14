from cthulhubot.commands.interface import Command

class Sleep(Command):
    slug = 'cthulhubot-sleep'
    name = {
        'basic' : u"Sleep",
        'running' : u'Sleeping',
        'succeeded' : u'Got a sleep',
        'failed' : u'Failed to sleep',
    }

    parameters = {
        'time' : {
            'help' : u'How long to sleep (in seconds)',
            'value' : 1,
            'required' : True,
        },
    }


    def get_command(self):
        return ["sleep", self.parameters['time']['value']]

    command = property(get_command)


