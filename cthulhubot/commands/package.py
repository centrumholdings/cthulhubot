from cthulhubot.commands.interface import Command

from buildbot.steps.shell import ShellCommand

class CreateStepWithBuildNumber(ShellCommand):
    command = ["python", "setup.py", "create_debian_package"]

    def start(self, *args, **kwargs):
#        if getattr(self, 'builder', None):
#            build_number = self.builder.getProperty("number")
#            self.setCommand(["python", "setup.py", "create_debian_package", "--build-number=%s" % build_number])
#

        ShellCommand.start(self, *args, **kwargs)

class BuildDebianPackage(Command):
    identifier = 'cthulhubot-debian-build-debian-package'
    name = {
        'basic' : u"Build Debian Package",
        'running' : u'building debian package',
        'succeeded' : u'Debian package build',
        'failed' : u'Failed to build debian package',
    }

    parameters = {}

    def get_buildbot_command(self, config=None, **kwargs):
        return CreateStepWithBuildNumber(**self.get_buildbot_kwargs())

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


