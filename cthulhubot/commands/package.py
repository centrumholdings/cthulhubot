from cthulhubot.commands.interface import Command

class BuildDebianPackage(Command):
    slug = 'cthulhubot-debian-build-debian-package'
    name = {
        'basic' : u"Build Debian Package",
        'running' : u'building debian package',
        'succeeded' : u'Debian package build',
        'failed' : u'Failed to build debian package',
    }

    parameters = {}

    command = ["python", "setup.py", "create_debian_package"]

class DebianPackageFtpUpload(Command):
    slug = 'cthulhubot-debian-package-ftp-upload'
    name = {
        'basic' : u"Build Debian Package",
        'running' : u'building debian package',
        'succeeded' : u'Debian package build',
        'failed' : u'Failed to build debian package',
    }

    parameters = {}

    command = ["python", "setup.py", "upload_packages"]


