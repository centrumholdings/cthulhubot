from djangosanetesting import DatabaseTestCase

from cthulhubot.models import Buildmaster, Project

class TestBuildmaster(DatabaseTestCase):

    def setUp(self):
        super(TestBuildmaster, self).setUp()

        self.project = Project.objects.create(name='test', slug='test', tracker_uri='http://example.com', repository_uri='/dev/null')
        self.project_second = Project.objects.create(name='test2', slug='test2', tracker_uri='http://example.com', repository_uri='/dev/null')

    def test_api_port_generated_on_save(self):
        master = Buildmaster.objects.create(project=self.project, directory='/dev/null', password='shabang')
        assert master.api_port is not None

    def test_save_supported_mutiple_times(self):
        master = Buildmaster.objects.create(project=self.project, directory='/dev/null', password='shabang')
        api_port =  master.api_port
        master.directory = '/dev/nullable'
        master.save()
        master.directory = '/dev/null'
        master.save()

        self.assert_equals(api_port, master.api_port)

    def test_nonconflicting_generation(self):
        master_first = Buildmaster.objects.create(project=self.project, directory='/dev/null', password='shabang')
        master_second = Buildmaster.objects.create(project=self.project_second, directory='/dev/zero', password='shabang')

        self.assert_not_equals(master_first.api_port, master_second.api_port)
