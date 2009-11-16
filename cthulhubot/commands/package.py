from cthulhubot.commands.interface import Command

class BuildDebianPackage(Command):
    identifier = 'cthulhubot-debian-build-debian-package'
    name = {
        'basic' : u"Build Debian Package",
        'running' : u'building debian package',
        'succeeded' : u'Debian package build',
        'failed' : u'Failed to build debian package',
    }

    parameters = {}

    command = ["python", "setup.py", "create_debian_package"]

class DebianPackageFtpUpload(Command):
    identifier = 'cthulhubot-debian-package-ftp-upload'
    name = {
        'basic' : u"Build Debian Package",
        'running' : u'building debian package',
        'succeeded' : u'Debian package build',
        'failed' : u'Failed to build debian package',
    }

    parameters = {
        'ftp_host' : {
            'help' : u'FTP server hostname',
            'value' : None,
            'required' : True,
        },
        'ftp_user' : {
            'help' : u'User to login with. E-mail for anonymous login',
            'value' : None,
            'required' : True,
        },
        'ftp_password' : {
            'help' : u'Password to use. Empty string for anonymous login',
            'value' : None,
            'required' : True,
        },
        'ftp_directory' : {
            'help' : u'Directory to upload packages to',
            'value' : None,
            'required' : True,
        },
    }

    command = ["python", "setup.py", "upload_deb_devel"]


