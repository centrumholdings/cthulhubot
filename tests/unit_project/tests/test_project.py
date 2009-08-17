import os

from django.core.exceptions import ValidationError
from djangosanetesting import DatabaseTestCase

from cthulhubot.models import Project, Buildmaster
from cthulhubot.project import create_project

class TestProjectCreation(DatabaseTestCase):

    def setUp(self):
        super(TestProjectCreation, self).setUp()
        self.project_name = u"project"
        self.project_slug = self.project_name

    def test_project_created(self):
        create_project(name=self.project_name, tracker_uri="http://example.com")
        self.assert_equals(self.project_name, Project.objects.all()[0].name)

    def test_project_created_and_retrievable_by_slug(self):
        create_project(name=self.project_name, tracker_uri="http://example.com")
        self.assert_equals(self.project_name, Project.objects.get(slug=self.project_slug).name)

    def test_buildmaster_created_with_autodetected_values(self):
        project = create_project(name=self.project_name, tracker_uri="http://example.com")
        self.assert_equals(project, Buildmaster.objects.all()[0].project)

    def test_buildmaster_cannot_be_created_with_conflicting_ports(self):
        self.assert_raises(ValidationError, create_project, name=self.project_name,
            tracker_uri="http://example.com",
            webstatus_port=50, buildmaster_port=50
        )

    def test_buildmaster_cannot_be_created_with_whenever_ports_are_conflicting(self):
        create_project(name=self.project_name,
            tracker_uri="http://example.com",
            webstatus_port=50, buildmaster_port=51
        )

        self.assert_raises(ValidationError, create_project, name=self.project_name+"2",
            tracker_uri="http://example.com",
            webstatus_port=51, buildmaster_port=52
        )

    def test_buildmaster_directory_generated(self):
        project = create_project(name=self.project_name, tracker_uri="http://example.com")
        self.assert_true(os.path.exists(project.buildmaster_set.all()[0].directory))
        self.assert_true(os.path.exists(os.path.join(project.buildmaster_set.all()[0].directory, "master.cfg")))

    def test_buildmaster_available_as_property(self):
        project = create_project(name=self.project_name, tracker_uri="http://example.com")
        self.assert_equals(project, project.buildmaster.project)

    def tearDown(self):
        for master in Buildmaster.objects.all():
            master.delete()

        super(TestProjectCreation, self).tearDown()