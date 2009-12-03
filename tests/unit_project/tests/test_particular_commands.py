from djangosanetesting import UnitTestCase, DatabaseTestCase

from django.conf import settings

from cthulhubot.commands import get_available_commands, get_command, get_undiscovered_commands
from cthulhubot.mongo import get_database_name

from cthulhubot.commands import Git, ADDITIONAL_COMMANDS

class TestingGitWithDefaultParameters(Git):
    identifier = 'cthulhubot-test-git-defaulted'
    parameters = {
        'repository' : {
            'help' : u'Out git',
            'value' : 'ssh://our.server.tld/GIT/$name',
        },
        'branch' : {
            'help' : u'Branch to export',
            'value' : 'automation',
        }
    }

class TestGit(UnitTestCase):

    def setUp(self):
        if TestingGitWithDefaultParameters.identifier not in ADDITIONAL_COMMANDS:
            ADDITIONAL_COMMANDS[TestingGitWithDefaultParameters.identifier] = TestingGitWithDefaultParameters

        self.command = get_command('cthulhubot-git')()
        self.sub_command = get_command('cthulhubot-test-git-defaulted')()


    def test_discovered(self):
        assert self.command is not None

    def test_helper_command_discovered(self):
        assert self.sub_command is not None

    def test_parent_argument_taken_by_default(self):
        self.assert_equals('export', self.sub_command.get_buildbot_command().args['mode'])

    def test_overwritten_arg_taken_over_default(self):
        self.assert_equals('ssh://our.server.tld/GIT/$name', self.sub_command.get_buildbot_command().args['repourl'])

    def test_overwritten_arg_taken_over_default_when_parent_has_none(self):
        self.assert_equals('automation', self.sub_command.get_buildbot_command().args['branch'])

    def test_given_args_takes_precedence_over_class_defaults(self):
        repo = 'ssh://our.server.tld/GIT/myrepo.git'
        self.assert_equals(repo, self.sub_command.get_buildbot_command(config={'repository' : repo}).args['repourl'])

class TestUpdateRepositoryInformation(UnitTestCase):

    def setUp(self):
        super(TestUpdateRepositoryInformation, self).setUp()
        self.command = get_command('cthulhubot-update-repository-info')()

    def test_command_configured(self):
        self.assert_equals([
                "python", "setup.py", "save_repository_information_git",
                "--mongodb-host=%s" % getattr(settings, "MONGODB_HOST", "localhost"),
                "--mongodb-port=%s" % getattr(settings, "MONGODB_PORT", 27017),
                "--mongodb-username=%s" % getattr(settings, "MONGODB_USERNAME", None),
                "--mongodb-password=%s" % getattr(settings, "MONGODB_PASSWORD", None),
                "--mongodb-database=%s" % get_database_name(),
                "--mongodb-collection=repository",
            ],
            self.command.get_shell_command()
        )

