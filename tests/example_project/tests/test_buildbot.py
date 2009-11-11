import os

from django.conf import settings
from djangosanetesting import HttpTestCase

from cthulhubot.models import Project, Buildmaster

from tests.helpers import create_project

# test is spawning child that will not share transaction - test must be destructive
class TestBuildmaster(HttpTestCase):

    def setUp(self):
        super(TestBuildmaster, self).setUp()
        #FIXME: DST should have helper function for this
        from djangosanetesting.noseplugins import DEFAULT_URL_ROOT_SERVER_ADDRESS, DEFAULT_LIVE_SERVER_PORT

        self.url_root = "http://%s:%s" % (
            getattr(settings, "URL_ROOT_SERVER_ADDRESS", DEFAULT_URL_ROOT_SERVER_ADDRESS),
            getattr(settings, "LIVE_SERVER_PORT", DEFAULT_LIVE_SERVER_PORT)
        )

        self.network_root = settings.NETWORK_ROOT
        settings.NETWORK_ROOT = self.url_root

        self.project_name = u"project"
        self.project = create_project(self)
        self.buildmaster = self.project.buildmaster_set.all()[0]
        self.transaction.commit()

    def assert_running(self):
        self.assert_true(self.buildmaster.is_running())

    def start_master(self):
        import cthulhubot
        import example_project
        self.buildmaster.start(env={
            "PYTHONPATH" : ':'.join([
                os.path.abspath(os.path.join(os.path.dirname(cthulhubot.__file__), os.pardir)),
                os.path.abspath(os.path.join(os.path.dirname(example_project.__file__), os.pardir))
            ]),
            "DJANGO_SETTINGS_MODULE" : "example_project.buildbot_settings",
        })

    def stop_master(self):
        import cthulhubot
        import example_project
        self.buildmaster.stop(env={
            "PYTHONPATH" : ':'.join([
                os.path.abspath(os.path.join(os.path.dirname(cthulhubot.__file__), os.pardir)),
                os.path.abspath(os.path.join(os.path.dirname(example_project.__file__), os.pardir))
            ]),
            "DJANGO_SETTINGS_MODULE" : "example_project.buildbot_settings",
        })

    def test_master_start(self):
        self.start_master()
        self.assert_running()

    def test_master_stop(self):
        self.start_master()
        self.stop_master()
        self.assert_false(self.buildmaster.is_running())

    def test_master_not_started_after_creation(self):
        self.assert_false(self.buildmaster.is_running())

    def tearDown(self):
        settings.NETWORK_ROOT = self.network_root
        self.project.delete()
        self.transaction.commit()
        super(TestBuildmaster, self).tearDown()
