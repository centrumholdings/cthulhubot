from cthulhubot.commands.interface import Command

class ComputeGitVersion(Command):
    slug = 'cthulhubot-version-compute-git'
    name = {
        'basic' : u"Compute version from git",
        'running' : u'Computing version from git',
        'succeeded' : u'Version computed',
        'failed' : u'Failed to compute version',
    }

    parameters = {}

    command = ["python", "setup.py", "compute_version_git"]

