from cthulhubot.jobs.job import Job

class CreateDebianPackage(Job):
    identifier = 'cthulhubot-debian-package-creation'
    name = u'Create Debian package'

    commands = [
        {
            'command' : 'cthulhubot-git',
        },
        {
            'command' : 'cthulhubot-version-compute-git',
        },
        {
            'command' : 'cthulhubot-debian-build-debian-package',
        },
        {
            'command' : 'cthulhubot-debian-package-ftp-upload',
            'parameters' : {
                'ftp_host' : None,
                'ftp_user' : None,
                'ftp_password' : None,
                'ftp_directory' : None,
            },
        },
    ]

