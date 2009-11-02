from cthulhubot.commands.interface import Command

from buildbot.steps.source import Git as BuildbotGit

class ComputeGitVersion(Command):
    identifier = 'cthulhubot-compute-git'
    name = {
        'basic' : u"Compute version from git",
        'running' : u'Computing version from git',
        'succeeded' : u'Version computed',
        'failed' : u'Failed to compute version',
    }

    parameters = {}

    command = ["python", "setup.py", "compute_version_git"]

class Git(Command):
    identifier = 'cthulhubot-git'
    name = {
        'basic' : u"Compute version from git",
        'running' : u'Computing version from git',
        'succeeded' : u'Version computed',
        'failed' : u'Failed to compute version',
    }

    parameters = {
        'repository' : {
            'help' : u'Path to git repository',
            'value' : None,
            'required' : True,
        },
        'mode' : {
            'help' : u'Git checkout mode. Default to "export"',
            'value' : "export",
            'required' : True,
        },
        'branch' : {
            'help' : u'Which branch should I check out? Default to master.',
            'value' : "master",
            'required' : True,
        },
    }

    def get_buildbot_command(self):
        repourl = self.config['repository']
        mode = self.config['mode']
        branch = self.config['branch']
        return BuildbotGit(repourl=repourl, mode=mode, branch=branch)

