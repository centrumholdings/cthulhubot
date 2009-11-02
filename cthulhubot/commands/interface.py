from copy import copy

from cthulhubot.err import UnconfiguredCommandError

from buildbot.steps.shell import ShellCommand

class Command(object):
    """
    Those classes should be implemented on top of buildbot's steps
    """

    # must be globally unique. Prefix with you own project.
    identifier = 'cthulhubot-unique-identifier'
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

        self.config = copy(config) or {}
        self.fill_default_values()
        if config:
            self.update_config(config)

    def fill_default_values(self):
        for cmd in self.parameters:
            if self.parameters[cmd].get('value') is not None:
                self.config[cmd] = self.parameters[cmd]['value']

    def update_config(self, config):
        for command in config:
            if command in self.parameters.keys() and config[command] is not None:
                self.config[command] = config[command]

    def get_unconfigured_parameters(self):
        params = []
        for command in self.parameters:
            if command not in self.config.keys():
                if self.parameters[command]['required'] is True:
                    params.append(command)
        return params

    def check_config(self):
        params = self.get_unconfigured_parameters()
        if len(params) > 0:
            raise UnconfiguredCommandError("Parameters %s required to be present in config" % (','.join(params),))

    def get_command(self):
        command = []

        self.check_config()

        for arg in self.command:
            try:
                command.append(arg % self.config)
            except KeyError:
                command.append(arg)
                
        return command
    
    def get_buildbot_command(self):
        return ShellCommand(command=self.get_command())