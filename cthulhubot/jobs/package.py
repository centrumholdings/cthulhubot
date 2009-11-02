from cthulhubot.commands import BuildDebianPackage, ComputeGitVersion, DebianPackageFtpUpload

from cthulhubot.jobs.job import Job

class CreateDebianPackage(Job):
    identifier = 'cthulhubot-debian-package-creation'
    name = u'Create Debian package'

    commands = [
        {
            'command' : ComputeGitVersion,
        },
        {
            'command' : BuildDebianPackage,
        },
        {
            'command' : DebianPackageFtpUpload,
            'parameters' : {
                'ftp_host' : None,
                'ftp_user' : None,
                'ftp_password' : None,
                'ftp_directory' : None,
            },
        },
    ]

