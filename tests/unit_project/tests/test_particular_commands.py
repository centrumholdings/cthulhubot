from djangosanetesting import UnitTestCase, DatabaseTestCase

from cthulhubot.commands import get_available_commands, get_command, get_undiscovered_commands
from cthulhubot.models import Command
from cthulhubot.err import UnconfiguredCommandError

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
