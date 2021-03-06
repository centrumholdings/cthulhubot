from buildbot.steps.source import Git as BuildbotGit
from buildbot.steps.shell import ShellCommand
from buildbot.status.builder import STDOUT
from twisted.python import log

from django.conf import settings

from cthulhubot.commands.interface import Command
from cthulhubot.mongo import get_database_name

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


class GitAssociate(ShellCommand):
    command = ["git", "rev-parse", "HEAD"]

    def commandComplete(self, cmd):
        out = ''.join(cmd.logs['stdio'].getChunks([STDOUT], onlyText=True)).strip()
        
        # we expect full 40-length SHA hash
        if len(out) != 40:
            log.msg("Bad revision when associating: %s" % out)
        else:
            self.build.getStatus().changeset = out
            log.msg("changeset %s given to build %s" % (str(out), self.build.getStatus()))

class AssociateWithRevision(Command):
    identifier = 'cthulhubot-git-associate'
    name = {
        'basic' : u"Associate with changeset",
        'running' : u'Associating with changeset',
        'succeeded' : u'Changeset associated',
        'failed' : u'Cannot associate with changeset',
    }

    def get_buildbot_command(self, **kwargs):
        return GitAssociate()

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

    def get_buildbot_command(self, config=None, project=None, **kwargs):
        config = config or {}
        repourl = config.get('repository', None) or self.config.get('repository', None)
        if not repourl:
            if not project:
                raise ValueError("Repository URI must be somehow given")
            repourl = project.repository_uri

        mode = config.get('mode', None) or self.config.get('mode', None)
        branch = config.get('branch', None) or self.config.get('branch', None)
        return BuildbotGit(repourl=repourl, mode=mode, branch=branch)


class UpdateRepositoryInformation(Command):
    identifier = 'cthulhubot-update-repository-info'
    name = {
        'basic' : u"Update repository information",
        'running' : u'Updating repository information',
        'succeeded' : u'Repository information updated',
        'failed' : u'Failed to update repository information',
    }

    parameters = {}

    def _get_command_skeleton(self):
        
        command = [
                "python", "setup.py", "save_repository_information_git",
                "--mongodb-host=%s" % getattr(settings, "MONGODB_HOST", "localhost"),
                "--mongodb-port=%s" % getattr(settings, "MONGODB_PORT", 27017),
                "--mongodb-database=%s" % get_database_name(),
                "--mongodb-collection=repository",
                
        ]
        if getattr(settings, "MONGODB_USERNAME", None):
                command.append("--mongodb-username=%s" % getattr(settings, "MONGODB_USERNAME", None))
        if getattr(settings, "MONGODB_PASSWORD", None):
                command.append("--mongodb-password=%s" % getattr(settings, "MONGODB_PASSWORD", None))
        return command

    command = property(fget=_get_command_skeleton)

    def get_shell_command(self, config=None, project=None, **kwargs):
        command = super(UpdateRepositoryInformation, self).get_shell_command(config=config, project=project, **kwargs)
        repourl = None
        if config:
            repourl = config.get('repository', None)
        if not repourl and not project:
            raise ValueError("Cannot figure repository URL")

        repourl = project.repository_uri

        command.append("--repository-uri=%s" % repourl)
        return command
