from djangosanetesting import DatabaseTestCase

from djangomassivebuildbot.models import Project, Buildmaster
from djangomassivebuildbot.project import create_project

class TestProjectCreation(DatabaseTestCase):

    def setUp(self):
        super(TestProjectCreation, self).setUp()
        self.project_name = u"project"

    def test_project_created(self):
        create_project(name=self.project_name, tracker_uri="http://example.com")
        self.assert_equals(self.project_name, Project.objects.all()[0].name)

#    def test_buildmaster_createdwith_autodetected_values(self):
#        project = create_project(name=self.project_name, tracker_uri="http://example.com")
#        self.assert_equals(project, Buildmaster.objects.all()[0].project)
