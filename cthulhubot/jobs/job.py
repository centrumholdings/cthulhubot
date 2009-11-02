from copy import deepcopy

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
        for command in self.commands:
            command['command'] = command['command']()

    def __unicode__(self):
        return self.name

    def get_commands(self):
        commands = []
        for config in self.commands:
            cmd = config['command']
            if config.has_key('parameters'):
                cmd.update_config(config['parameters'])
            commands.append(cmd)

        return commands

    def update_command_config(self, command_slug, config):
        for conf in self.commands:
            if conf['command'].identifier == command_slug:
                conf['parameters'].update(config)


    def get_configuration_parameters(self):
        """
        Return unconfigured parameters to be used for configuration

        format:

        [{
            'slug' : 'command-slug',
#           'command-name' : cmdname' : ,
#            'help' : u'This help will be shown to user in some way. You should document what is command doing',
#            # command name as shown on page
#            'name' : {
#                # 'basic' will be used for usual description and when command is to be run in future
#                'basic' : u'run command',
#                'running' : u'command is running, hide!',
#                'succeeded' : u'World dominated successfully',
#                'failed' : u'Developer suck and commited broken software',
#            }
#          }
#       }]
        """
        params_list = []
        for command in self.get_commands():
            params = command.get_unconfigured_parameters()
            if params:
                params_list.append({
                    'slug' : command.identifier,
                    'parameters' : dict([(param, command.parameters[param]) for param in params])
                })

        return params_list
        
