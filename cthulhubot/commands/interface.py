class Command(object):
    """
    Those classes should be implemented on top of buildbot's steps
    """

    # must be globally unique. Prefix with you own project.
    slug = 'cthulhubot-unique-identifier'
    name = u"I'm a command to use for jobs "

    # parameters should be in form:
#    parameters = {
#        # 'cmdname' will be send as kwarg
#        'cmdname' : {
#            'help' : u'This help will be shown to user in some way. You should document what is command doing',
#            # command name as shown on page
#            'name' : {
#                # 'basic' will be used for usual description and when command is to be run in future
#                'basic' : u'run command',
#                'running' : u'command is running, hide!',
#                'succeeded' : u'World dominated successfully',
#                'failed' : u'Developer suck and commited broken software',
#            }
#        }
#    }


    parameters = {}
    command = []

    def __init__(self, config=None, **kwargs):
        super(Command, self).__init__()

        self.config = config or {}

        for command in self.parameters:
            if command not in self.config.keys():
                if self.parameters[command]['required'] is True:
                    raise ValueError("Paramater %s required to be present in config" % command)
                elif self.parameters[command]['value'] is not None:
                    self.config[command] = self.parameters[command]['value']

    def get_command(self):
        command = []

        for arg in self.command:
            try:
                command.append(arg % self.config)
            except KeyError:
                command.append(arg)
                
        return command


