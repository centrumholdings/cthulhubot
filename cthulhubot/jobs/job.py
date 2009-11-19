from copy import deepcopy

from cthulhubot.commands import get_command
from cthulhubot.err import UnconfiguredCommandError

class Job(object):

    # must be globally unique. Prefix with you own project.
    identifier = 'cthulhubot-unique-identifier'
    name = u"I'm a job - a predefined set of commands"
    register_as_job = True

    global_command_parameters = {}
#    commands = [
#        {
#            'command' : 'ComputeGitVersion-slug',
#        },
#        {
#            'command' : 'BuildDebianPackage-slug',
#        },
#        {
#            'command' : 'DebianPackageFtpUpload-slug',
#            'command' : {
#                'ftp_host' : None,
#                'ftp_user' : None,
#                'ftp_password' : None,
#                'ftp_directory' : None,
#            },
#        },
#    ]

    def __init__(self, model=None):
        super(Job, self).__init__()

        self.model = model

        self.commands = deepcopy(self.__class__.commands)

        self.commands_retrieval_chain = [self.insert_commands_in_slots, self.apply_global_command_parameters, self.filter_commands]
        self.command_validators = [self.check_command_present]
        
    def __unicode__(self):
        return self.name

    def apply_job_defaults(self, commands):
        i = 0
        for command in commands:
            if self.commands[i].has_key('parameters'):
                command.update_config(self.commands[i]['parameters'])
        return commands

    def apply_global_command_parameters(self, commands):
        for command_ident in self.global_command_parameters:
            for command in commands:
                if command['command'] == command_ident:
                    if not command.has_key('parameters'):
                        command['parameters'] = {}
                    command['parameters'].update(self.global_command_parameters[command_ident])
        return commands

    def insert_commands_in_slots(self, commands):
        return commands

    def filter_commands(self, commands):
        # this can be used by any subclass to modify my commands or their parameters
        return commands

    def get_commands_dictionary(self):
        # return copy of self.commands dictionary and fill it
        # with ['parameters'] if they don't exists
        commands_dictionary = deepcopy(self.commands)
        for dict in commands_dictionary:
            if not dict.has_key('parameters'):
                dict['parameters'] = {}
        return commands_dictionary

    def check_command_present(self, commands):
        for command_dict in commands:
            if not command_dict.has_key('command'):
                raise UnconfiguredCommandError("Dictionary %s does not contain command" % str(command_dict))

    def check_command_configuration(self, commands):
        for validator in self.command_validators:
            validator(commands)

    def get_configured_command_list(self):
        commands = self.get_commands_dictionary()
        # pass through chain
        for filter in self.commands_retrieval_chain:
            commands = filter(commands)

        # check before retrieving
        self.check_command_configuration(commands)

        return commands

    def get_commands(self):
        return [
            get_command(command_dict['command'])(config=command_dict['parameters'])
            for command_dict in self.get_configured_command_list()
        ]

    def update_command_config(self, command_index, config):
        if len(self.commands) < command_index:
            raise ValueError("Requested update for command on index %s, but I have only %s commands" % (command_index, len(self.commands)))
        if not self.commands[command_index].has_key('command'):
            command = get_command(config['command'])
            if self.commands[command_index].has_key('slot') and self.commands[command_index]['slot'] in getattr(command, "slots", []):
                self.commands[command_index]['command'] = config['command']
            else:
                raise ValueError("Command at index %s (dict: %s) has no command and no command for matching slot provided." % (command_index, str(self.commands[command_index])))

        elif config['command'] != self.commands[command_index]['command']:
            raise ValueError("Trying to update config for command %s, but %s found" % (config['command'], self.commands[command_index]['command']))

        if not self.commands[command_index].has_key('parameters'):
            self.commands[command_index]['parameters'] = {}

        self.commands[command_index]['parameters'].update(config['parameters'])

    def get_configured_shell_commands(self, config):
        #FIXME: we should use config directly, not introducing state
        commands = []

        i = 0
        for command_dict in self.commands:
            command = get_command(command_dict['command'])()
            command_config = {}
            if command_dict.has_key('parameters'):
                command_config.update(command_dict['parameters'])

            if config and len(config) >= i+1 and config[i].has_key('parameters'):
                command_config.update(config[i]['parameters'])

            shell_command = command.get_shell_command(config=command_config)

            commands.append(shell_command)
            i += 1
        return commands

    def get_configuration_parameters(self):
        """
        Return unconfigured parameters to be used for configuration.
        One dict is returned per every command in job, even if it should be an empty dict.
        This is basically self.get_configured_command_list, flavoured with parameters_description.

        format:

        [{
            'command' : 'command-identifier',
             'parameters' : {
                 <name> : <current-value>,
             },
             'parameters_description' : {
                 <name> : <parameter-dictionary>
             }
           }
        }]
        <parameter-dictionary> = cthulhubot.commands.interface.Command.parameters[<name>], i.e.
            {
                'name' : {name-dict}
                'required' : <bool>,
                'help' : u'help text',
            }
        """
        command_list = self.get_configured_command_list()
        for command_dict in command_list:
            if not command_dict.has_key('parameters_description'):
                command_dict['parameters_description'] = {}
            for parameter in command_dict['parameters']:
                command_dict['parameters_description'][parameter] = get_command(command_dict['command']).parameters[parameter]
            

        return command_list

    def get_command_dictionary(self, command_index):
        commands = self.get_configuration_parameters()

        if len(commands) <= command_index:
            raise ValueError("Requested command on index %s, but I have only %s commands" % (command_index, len(commands)))

        return commands[command_index]


    def get_parameter_dict(self, command_index, parameter):
        command_dict = self.get_command_dictionary(command_index)
        if parameter not in command_dict['parameters']:
            raise ValueError("Requested nonexisting parameter %s for command %s" % (parameter, command_dict['command']))

        return command_dict['parameters'][parameter]

    def get_parameter_description_dict(self, command_index, parameter):
        command_dict = self.get_command_dictionary(command_index)

        if parameter not in command_dict['parameters_description']:
            raise ValueError("Requested description nonexisting parameter %s for command %s" % (parameter, command_dict['command']))

        return command_dict['parameters_description'][parameter]


    def auto_discovery(self, *args, **kwargs):
        return self.model.auto_discovery(*args, **kwargs)
