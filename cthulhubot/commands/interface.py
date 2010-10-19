from copy import copy, deepcopy

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
#        # 'parname' will be send as kwarg
#        'parname' : {
#            'help' : u'This help will be shown to user in some way. You should document what is command doing',
#            'required' : <bool>,
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
    buildbot_commands_kwargs = {}

    def __init__(self, config=None, job=None, **kwargs):
        super(Command, self).__init__()

        self.config = copy(config) or {}
        self.job = job
        self.get_initial_parameters()

        self.fill_default_values()

        if config:
            self.update_config(config)

    def get_initial_parameters(self):
        # traverse through hierarchy until I have .parameters
        # then, update from top to bottom, with param_config being most preferred
        self.parameters = {}
        classes = list(self.__class__.__mro__)
        classes.reverse()
        for cls in classes:
            self.parameters.update(getattr(cls, "parameters", {}))

    def fill_default_values(self):
        for cmd in self.parameters:
            if self.parameters[cmd].get('value') is not None:
                self.config[cmd] = self.parameters[cmd]['value']

    def update_config(self, config):
        for command in config:
            if command in self.parameters.keys() and config[command] is not None:
                self.config[command] = config[command]

    def get_unconfigured_parameters(self, config=None):
        params = []
        config = config or {}
        for command in self.parameters:
            if command not in self.config.keys()+config.keys():
                if self.parameters[command]['required'] is True:
                    params.append(command)
        return params

    def check_config(self, config=None):
        params = self.get_unconfigured_parameters(config=config)
        if len(params) > 0:
            raise UnconfiguredCommandError("Parameters %s required to be present in config" % (','.join(params),))


    def get_config_for_shell_command(self, config):
        self.check_config(config=config)
        if config:
            orig_config = copy(self.config)
            orig_config.update(config)
            config = orig_config
        else:
            config = self.config

        return config

    def substitute_command(self, command, config):
        substitued_command = []
        for arg in command:
            try:
                cmd = str(arg) % config
                substitued_command.append(cmd)
            except KeyError:
                substitued_command.append(arg)
        return substitued_command


    def get_buildbot_kwargs(self):
        kwargs = deepcopy(self.buildbot_commands_kwargs)
        if self.job:
            kwargs.update(deepcopy(getattr(self.job, "buildbot_commands_kwargs", {})))

        return kwargs


    def get_command(self):
        return self.get_shell_command()

    def get_shell_command(self, config=None, **kwargs):
        config = self.get_config_for_shell_command(config)
        return self.substitute_command(self.command, config)
    
    def get_buildbot_command(self, config=None, **kwargs):
        return ShellCommand(command=self.get_shell_command(config=config, **kwargs), **self.get_buildbot_kwargs())