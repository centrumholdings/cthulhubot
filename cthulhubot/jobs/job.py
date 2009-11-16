from copy import deepcopy

from cthulhubot.commands import get_command

class Job(object):

    # must be globally unique. Prefix with you own project.
    identifier = 'cthulhubot-unique-identifier'
    name = u"I'm a job - a predefined set of commands"
    register_as_job = True

#    commands = [
#        {
#            'command' : ComputeGitVersion,
#        },
#        {
#            'command' : BuildDebianPackage,
#        },
#        {
#            'command' : DebianPackageFtpUpload,
#            'parameters' : {
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
    def __unicode__(self):
        return self.name

    def get_commands(self):
        commands = []
        for config in self.commands:
            cmd = get_command(config['command'])()
            if config.has_key('parameters'):
                cmd.update_config(config['parameters'])
            commands.append(cmd)

        return commands

    def update_command_config(self, command_slug, config):
        for conf in self.commands:
            if conf['command'] == command_slug:
                conf['parameters'].update(config)

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

    def get_parameter_dict(self, command_index, parameter):
        identifier = self.commands[command_index]['command']
        command = get_command(identifier)

        if parameter not in command.parameters:
            raise ValueError("Requested nonexisting parameter %s for command %s" % (parameter, identifier))
        
        config = deepcopy(command.parameters[parameter])
        if self.commands[command_index].get('parameters', None) and self.commands[command_index]['parameters'].has_key(parameter):
            config.update({'value' : self.commands[command_index]['parameters'][parameter]})

        return config

    def get_configuration_parameters(self):
        """
        Return unconfigured parameters to be used for configuration.
        One dict is returned per every command in job, even if it should be an empty dict

        format:

        [{
            'identifier' : 'command-identifier',
             'parameters' : {
                 'name' : <command-dictionary>,
             }
           }
        }]
        <command-dicitonary> = {
            'help' : u'string',
            'value' : u'current-value',
            'required' : bool
        }
        """
        params_list = []
        i = 0
        for command in self.get_commands():
            command_params = deepcopy(command.parameters)
            if command_params:
                parameters = dict([(param, self.get_parameter_dict(i, param)) for param in command_params])
            else:
                parameters = {}

            command_dict = {
                    'identifier' : command.identifier,
                    'parameters' : parameters,
            }
            params_list.append(command_dict)
            i += 1

        return params_list


    def auto_discovery(self, *args, **kwargs):
        return self.model.auto_discovery(*args, **kwargs)