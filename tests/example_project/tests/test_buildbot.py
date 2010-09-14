import os

from django.conf import settings
from djangosanetesting import HttpTestCase
from djangosanetesting.utils import get_live_server_path

from cthulhubot.models import Project, Buildmaster

from tests.helpers import create_project
from tests.helpers import BuildmasterTestCase

# test is spawning child that will not share transaction - test must be destructive
class TestBuildmaster(BuildmasterTestCase):

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
