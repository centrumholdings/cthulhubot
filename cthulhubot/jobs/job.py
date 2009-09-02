from copy import copy

class Job(object):

    # must be globally unique. Prefix with you own project.
    slug = 'cthulhubot-unique-identifier'
    name = u"I'm a job - a predefined set of commands"
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


    def get_commands(self):
        commands = []
        for config in self.commands:
            cmd = config['command']()
            if config.has_key('parameters'):
                cmd.update_config(config['parameters'])
            commands.append(cmd)

        return commands
