from djangosanetesting.cases import DatabaseTestCase

from django.utils.simplejson import dumps
from bbmongostatus.status import MongoDb

from cthulhubot.assignment import Assignment
from cthulhubot.buildbot import get_buildmaster_config
from cthulhubot.models import BuildComputer, JobAssignment, Job, Command
from cthulhubot.views import create_project

from unit_project.tests.helpers import MockJob
from mock import Mock

class TestSchedulers(DatabaseTestCase):
    def setUp(self):
        super(TestSchedulers, self).setUp()
        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com")
        self.buildmaster = self.project.buildmaster_set.all()[0]

        self.computer = BuildComputer.objects.create(hostname="localhost")

        job = Job.objects.create(slug='cthulhubot-debian-package-creation')
        job.auto_discovery()
        self.assignment = JobAssignment.objects.create(
            job = job,
            computer = self.computer,
            project = self.project
        )

        self.assignment.config.create(
            command = Command.objects.get(slug='cthulhubot-debian-package-ftp-upload'),
            config = dumps({
                'ftp_user' : 'xxx',
                'ftp_password' : 'xxx',
                'ftp_directory' : '',
                'ftp_host' : ''
            })
        )


    def test_single_post_hook_by_default(self):
        config = self.buildmaster.get_config()
        self.assert_equals(1, len(config['schedulers']))

    def test_single_post_hook_by_default_contains_all_builders(self):
        config = self.buildmaster.get_config()
        builders = [builder['name'] for builder in config['builders']]

        scheduler_builders = config['schedulers'][0].builderNames

        self.assert_equals(scheduler_builders, builders)

    def test_builders_generated(self):
        config = self.buildmaster.get_config()
        self.assert_equals(1, len(config['builders']))

    def test_status_fed_in_mongo(self):
        config = self.buildmaster.get_config()
        self.assert_true(MongoDb in [i.__class__ for i in config['status']])

    def test_(self):
        config = self.buildmaster.get_config()
        self.assert_true(MongoDb in [i.__class__ for i in config['status']])

    def tearDown(self):
        self.buildmaster.delete()
        super(TestSchedulers, self).tearDown()

class TestBuildmasterFrontend(DatabaseTestCase):
    def setUp(self):
        super(TestBuildmasterFrontend, self).setUp()
        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com")
        self.buildmaster = self.project.buildmaster_set.all()[0]

    def test_frontend_is_not_screwing_up(self):
        model_config = self.buildmaster.get_config()
        master_config = get_buildmaster_config(self.project_name)

        for attr in ['projectURL', 'buildbotURL', 'slavePortnum', 'projectName']:
            self.assert_equals(model_config[attr], master_config[attr])

    def tearDown(self):
        self.buildmaster.delete()
        super(TestBuildmasterFrontend, self).tearDown()

