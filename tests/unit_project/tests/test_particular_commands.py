from djangosanetesting import UnitTestCase
from mock import Mock

from django.conf import settings

from cthulhubot.commands import get_available_commands, get_command, get_undiscovered_commands
from cthulhubot.mongo import get_database_name

from cthulhubot.models import Project
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

        self.repository_uri = '/tmp/repo.git'
        self.project = Project(name='test', slug='test', tracker_uri='http://example.com', repository_uri=self.repository_uri)

    def test_discovered(self):
        assert self.command is not None

    def test_helper_command_discovered(self):
        assert self.sub_command is not None

    def test_parent_argument_taken_by_default(self):
        self.assert_equals('export', self.sub_command.get_buildbot_command().args['mode'])

    def test_overwritten_arg_taken_over_default(self):
        self.assert_equals('ssh://our.server.tld/GIT/$name', self.sub_command.get_buildbot_command().repourl)

    def test_overwritten_arg_taken_over_default_when_parent_has_none(self):
        self.assert_equals('automation', self.sub_command.get_buildbot_command().args['branch'])

    def test_given_args_takes_precedence_over_class_defaults(self):
        repo = 'ssh://our.server.tld/GIT/myrepo.git'
        self.assert_equals(repo, self.sub_command.get_buildbot_command(config={'repository' : repo}).repourl)

    def test_git_uri_taken_from_project_by_default(self):
        self.assert_equals(self.repository_uri, self.command.get_buildbot_command(project=self.project).repourl)

    def test_git_uri_hierarchically_parent_first(self):
        self.assert_equals('ssh://our.server.tld/GIT/$name', self.sub_command.get_buildbot_command(project=self.project).repourl)

class TestUpdateRepositoryInformation(UnitTestCase):

    def setUp(self):
        super(TestUpdateRepositoryInformation, self).setUp()
        self.command = get_command('cthulhubot-update-repository-info')()

        self.mongo_config = {
            "host" : "host",
            "port" : 20000,
            "username" : "user",
            "password" : "heslo",
            "database_name" : "db",
        }

        self.project = Mock()
        self.project.repository_uri = '/tmp/repo.git'

        self.original_config = {}

        self._mock_mongo_settings()

    def _mock_mongo_settings(self):
        for key in self.mongo_config:
            setting = "MONGODB_%s" % key.upper()

            # we're test...
            if key == 'database_name':
                setting = "TEST_" + setting

            if hasattr(settings, setting):
                self.original_config[setting] = getattr(settings, setting)
                
            setattr(settings, setting, self.mongo_config[key])

    def _unmock_mongo_settings(self):
        for key in self.mongo_config:
            setting = "MONGODB_%s" % key.upper()

            # we're test...
            if key == 'database_name':
                setting = "TEST_" + setting

            if setting in self.original_config:
                setattr(settings, setting, self.original_config[setting])
            elif hasattr(settings, setting):
                delattr(settings._wrapped, setting)

    def test_command_configured(self):
        self.assert_equals([
                "python", "setup.py", "save_repository_information_git",
                "--mongodb-host=%s" % self.mongo_config['host'],
                "--mongodb-port=%s" % self.mongo_config['port'],
                "--mongodb-database=%s" % self.mongo_config['database_name'],
                "--mongodb-collection=repository",
                "--mongodb-username=%s" % self.mongo_config['username'],
                "--mongodb-password=%s" % self.mongo_config['password'],
                "--repository-uri=%s" % self.project.repository_uri,
            ],
            self.command.get_shell_command(project=self.project)
        )

    def test_empty_params_ommited(self):
        settings.MONGODB_USERNAME = None
        settings.MONGODB_PASSWORD = None

        self.assert_equals([
                "python", "setup.py", "save_repository_information_git",
                "--mongodb-host=%s" % self.mongo_config['host'],
                "--mongodb-port=%s" % self.mongo_config['port'],
                "--mongodb-database=%s" % self.mongo_config['database_name'],
                "--mongodb-collection=repository",
                "--repository-uri=%s" % self.project.repository_uri,
            ],
            self.command.get_shell_command(project=self.project)
        )

    def test_repository_uri_required(self):
        self.assert_raises(ValueError, self.command.get_shell_command)

    def tearDown(self):
        self._unmock_mongo_settings()
        
        super(TestUpdateRepositoryInformation, self).tearDown()
