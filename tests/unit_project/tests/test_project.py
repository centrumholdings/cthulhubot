import os

from djangosanetesting import DatabaseTestCase
from mock import Mock

from django.core.exceptions import ValidationError
from django.core import urlresolvers
from django.core.urlresolvers import get_script_prefix

from cthulhubot.models import Project, Buildmaster
from cthulhubot.project import create_project

class TestProjectCreation(DatabaseTestCase):

    def setUp(self):
        super(TestProjectCreation, self).setUp()
        self.project_name = u"project"
        self.project_slug = self.project_name
        self._mock_resolver()

    def _mock_resolver(self):
        self._original_resolver = urlresolvers.get_resolver

        resolver = Mock()
        self.prefix = get_script_prefix()
        self.mocked_uri = resolver.reverse.return_value="heureka"

        urlresolvers.get_resolver = lambda conf: resolver

    def _unmock_resolver(self):
        urlresolvers.get_resolver = self._original_resolver
        self._original_resolver = None

    def create_project(self):
        return create_project(name=self.project_name, tracker_uri="http://example.com", repository_uri = "/tmp/test")

    def test_project_created(self):
        self.create_project()
        self.assert_equals(self.project_name, Project.objects.all()[0].name)

    def test_project_created_and_retrievable_by_slug(self):
        self.create_project()
        self.assert_equals(self.project_name, Project.objects.get(slug=self.project_slug).name)

    def test_buildmaster_created_with_autodetected_values(self):
        project = self.create_project()
        self.assert_equals(project, Buildmaster.objects.all()[0].project)

    def test_buildmaster_cannot_be_created_with_conflicting_ports(self):
        self.assert_raises(ValidationError, create_project, name=self.project_name,
            tracker_uri="http://example.com",
            repository_uri = "/tmp/test",
            webstatus_port=50, buildmaster_port=50
        )

    def test_buildmaster_cannot_be_created_with_whenever_ports_are_conflicting(self):
        create_project(name=self.project_name,
            tracker_uri="http://example.com",
            repository_uri = "/tmp/test",
            webstatus_port=50, buildmaster_port=51
        )

        self.assert_raises(ValidationError, create_project, name=self.project_name+"2",
            tracker_uri="http://example.com",
            repository_uri = "/tmp/test",
            webstatus_port=51, buildmaster_port=52
        )

    def test_buildmaster_directory_generated(self):
        project = self.create_project()
        self.assert_true(os.path.exists(project.buildmaster_set.all()[0].directory))
        self.assert_true(os.path.exists(os.path.join(project.buildmaster_set.all()[0].directory, "master.cfg")))

    def test_buildmaster_available_as_property(self):
        project = self.create_project()
        self.assert_equals(project, project.buildmaster.project)

    def tearDown(self):
        for master in Buildmaster.objects.all():
            master.delete()

        self._unmock_resolver()

        super(TestProjectCreation, self).tearDown()