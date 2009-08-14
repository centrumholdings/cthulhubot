import os

from django.core.exceptions import ValidationError
from djangosanetesting import DatabaseTestCase

from cthulhubot.models import Project, Buildmaster
from cthulhubot.project import create_project

class TestBuildmaster(DatabaseTestCase):

    def setUp(self):
        super(TestBuildmaster, self).setUp()
        self.project_name = u"project"
        self.project = create_project(name=self.project_name, tracker_uri="http://example.com")
        self.buildmaster = self.project.buildmaster_set.all()[0]

    def test_master_start(self):
        import cthulhubot
        import unit_project
        self.buildmaster.start(env={
            "PYTHONPATH" : ':'.join([
                os.path.abspath(os.path.join(os.path.dirname(cthulhubot.__file__), os.pardir)),
                os.path.abspath(os.path.join(os.path.dirname(unit_project.__file__), os.pardir))
            ])
        })


    def tearDown(self):
        self.project.delete()
        super(TestBuildmaster, self).tearDown()