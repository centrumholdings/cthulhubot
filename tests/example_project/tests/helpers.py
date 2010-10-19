from djangosanetesting.cases import HttpTestCase, SeleniumTestCase
from djangosanetesting.utils import get_live_server_path

import os
from mock import Mock
from tempfile import mkdtemp
from shutil import rmtree
from subprocess import Popen, PIPE

from django.contrib.auth.models import User
from django.conf import settings
from django.core.management import call_command

from cthulhubot.models import Project, Job, BuildComputer, Buildmaster
from cthulhubot.project import create_project as cthulhu_create_project
from cthulhubot.views import create_job_assignment

def create_project(case, name=None, tracker_uri=None, repository_uri=None, master_directory=None):
    return cthulhu_create_project(
        name=name or case.project_name,
        tracker_uri=tracker_uri or "http://example.com",
        repository_uri=repository_uri or "/tmp/test",
        master_directory=master_directory
    )

def mock_url_root(case):
    case.url_root = get_live_server_path()

    case.network_root = settings.NETWORK_ROOT
    settings.NETWORK_ROOT = case.url_root

def unmock_url_root(case):
    settings.NETWORK_ROOT = case.network_root

#####
# Helpers for working with git repository
#####

def do_piped_command_for_success(self, command):
    proc = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    self.assertEquals(0, proc.returncode)

    return (stdout, stderr)

def commit(message='dummy'):
    """ Commmit into repository and return commited revision """
    do_piped_command_for_success(['git', 'commit', '-a', '-m', '"%s"' % message])
    stdout = do_piped_command_for_success(['git', 'rev-parse', 'HEAD'])[0]
    return stdout.strip()

def create_git_repository(case, dir=None):
    """
    Create git repository in temporary directory, chdir to it and configure.

    Repository path is stored in case.repo, old working path in case.cwd
    """
    # create temporary directory and initialize git repository there
    case.repo = mkdtemp(prefix='test_git_', dir=dir)
    case.oldcwd = os.getcwd()
    os.chdir(case.repo)
    proc = Popen(['git', 'init'], stdout=PIPE, stdin=PIPE)
    proc.wait()
    case.assertEquals(0, proc.returncode)

    # also setup dummy name / email for this repo for tag purposes
    proc = Popen(['git', 'config', 'user.name', 'dummy-tester'])
    proc.wait()
    case.assertEquals(0, proc.returncode)
    proc = Popen(['git', 'config', 'user.email', 'dummy-tester@example.com'])
    proc.wait()
    case.assertEquals(0, proc.returncode)


def prepare_tagged_repo_with_file(case, tag="0.1", dir=None):
    """
    Create git repository with commited file in it and a tag
    """
    create_git_repository(case, dir=None)
    
    f = open(os.path.join(case.repo, 'test.txt'), 'wb')
    f.write("test")
    f.close()

    proc = Popen(["git", "add", "*"])
    proc.wait()
    case.assertEquals(0, proc.returncode)

    proc = Popen(['git', 'commit', '-m', '"dummy"'], stdout=PIPE, stdin=PIPE)
    proc.wait()
    case.assertEquals(0, proc.returncode)

    proc = Popen(['git', 'tag', '-m', '"tagging"', '-a', tag], stdout=PIPE, stdin=PIPE)
    proc.wait()
    case.assertEquals(0, proc.returncode)

def clean_repository(case):
    """
    Drop created repository and chdir to old path
    """
    rmtree(case.repo)
    os.chdir(case.oldcwd)
    case.oldcwd = None

def create_assignment(case, repository_dir=None):
    case.project_name = u"project"
    case.project = create_project(case, master_directory=case.base_directory, repository_uri=repository_dir)
    case.buildmaster = case.project.buildmaster_set.all()[0]

    case.computer_model = case.computer = BuildComputer.objects.create(hostname = "localhost", basedir=case.base_directory)

    case.job_test = Job.objects.create(slug='cthulhubot-bare-nose-tests').get_domain_object()
    case.job_test.auto_discovery()

    case.job_repository = Job.objects.create(slug='cthulhubot-save-repository-information').get_domain_object()
    case.job_repository.auto_discovery()

    case.assignment_test = create_job_assignment(
        computer = case.computer_model,
        job = case.job_test,
        project = case.project,
        params = {
          'commands' : [{}, {}, {}]
        }
    )
    case.assignment_repository = create_job_assignment(
        computer = case.computer_model,
        job = case.job_repository,
        project = case.project,
        params = {
          'commands' : [{}, {}]
        }
    )


def prepare_working_assignment(case):
    """
    Prepare working Job assignment: create repository, and friends and assign basic simple projects
    """
    case.base_directory = mkdtemp()

    prepare_tagged_repo_with_file(case, dir=case.base_directory)
    create_assignment(case, repository_dir=case.repo)


    case.project_client = case.assignment_test.get_client()
    case.build_directory = os.path.join(case.base_directory, case.project_client.get_identifier())

    case.transaction.commit()

    case.buildmaster.start()
    case.project_client.create_build_directory()
    case.project_client.start()


def clean_assignment(case):
    """
    Clean created assignments, repositories and friends
    """
    case.buildmaster.stop(ignore_not_running=True)
    case.project_client.stop()
    rmtree(case.base_directory)
    case.buildmaster.delete()
    case.computer.delete()


#####
# End of git helpers
#####

class BuildmasterTestCase(HttpTestCase):
    def setUp(self):
        super(BuildmasterTestCase, self).setUp()

        self._old_builddir = getattr(settings, "CTHULHUBOT_BUILDMASTER_BASEDIR", None)

        self.base_directory = mkdtemp()

        settings.CTHULHUBOT_BUILDMASTER_BASEDIR = self.base_directory

        self.url_root = get_live_server_path()

        self.network_root = settings.NETWORK_ROOT
        settings.NETWORK_ROOT = self.url_root


        self.project_name = u"project"
        self.project = create_project(self)
        self.buildmaster = self.project.buildmaster_set.all()[0]

        self.transaction.commit()

    def tearDown(self):
        self.buildmaster.stop(ignore_not_running=True)
        self.buildmaster.delete()
        self.project.delete()
        rmtree(self.base_directory)

        settings.NETWORK_ROOT = self.network_root
        settings.CTHULHUBOT_BUILDMASTER_BASEDIR = self._old_builddir


class WebTestCase(SeleniumTestCase):
    elements = {
        'menu' : {
            'login' : "menu-link-login",
            'projects' : "menu-link-projects",
            'computers' : "menu-link-computers",
            'commands' : "menu-link-commands",
            'jobs' : "menu-link-jobs",
        },
        'login' : {
            'username' : "id_username",
            'password' : "id_password",
            'submit_form' : "//input[@type='submit']",
        },
        'projects' : {
            "create" : "link-create-project",
            "list" : "id('projects-list')/li",
            "project_link" : "id('projects-list')/li[%(position)s]/a",
            "project_link_single" : "//ul[@class='projects-list']/li/a",
        },
        'projects_create' : {
            'submit_form' : "//input[@type='submit']",
        },
        'project_detail' : {
            'name' : "project-name",
            'buildmaster_status' : "buildmaster-status",
            'start_buildmaster' : 'submit-start-master',
            'stop_buildmaster' : 'submit-stop-master',
            'buildmaster_status' : 'buildmaster-status',
            'computer_status' : "//ul[@class='computers-list']/li[%(position)s]//span[@class='computer-status']",
            'single_computer_status' : "//ul[@class='computers-list']/li//span[@class='computer-status']",
        },
        'computers' : {
            "create" : "link-add-computer",
            "list" : "id('computers-list')/li",
            "computer_link" : "id('computers-list')/li[%(position)s]/a",
            "computer_link_single" : "//ul[@class='computers-list']/li/a",
        },
        'computers_create' : {
            'submit_form' : "//input[@type='submit']",
        },
        'computer_detail' : {
            'name' : "computer-name",
        },
        'commands' : {
            'link-discovery' : 'link-discovery',
            'list' : 'commands-list',
            'discovery' : {
                "list" : "//ul[@class='commands-list']/li",
                "list-item" : "//ul[@class='commands-list']/li[%(position)s]",
                "assign" : "//ul[@class='commands-list']/li[%(position)s]//input[@type='submit']",
            },
        },
        'jobs' : {
            'link-configuration' : 'link-configuration',
            'list' : 'jobs-list',
            'list-items' : "//ul[@class='jobs-list']/li",
            'list-item' : "//ul[@class='jobs-list']/li[%(position)s]",
            'discovery' : {
                "list" : "//ul[@class='jobs-list']/li",
                "list-item" : "//ul[@class='jobs-list']/li[%(position)s]",
                "auto" : "auto-discovery",
            },
        }
    }

    def setUp(self, discover=True):
        super(WebTestCase, self).setUp()

        if discover:
            call_command("discover")

        self.selenium.open("/")
        self.selenium.wait_for_page_to_load(30000)

class AuthenticatedWebTestCase(WebTestCase):
    def setUp(self, discover=True):

        self.network_root = settings.NETWORK_ROOT
        if hasattr(self, 'url_root'):
            settings.NETWORK_ROOT = self.url_root

        super(AuthenticatedWebTestCase, self).setUp(discover=discover)
        self.create_user()

        self.selenium.click(self.elements['menu']['login'])
        self.selenium.wait_for_page_to_load(30000)

        self.selenium.click(self.elements['login']['username'])
        self.selenium.type(self.elements['login']['username'], self.user.username)
        self.selenium.click(self.elements['login']['password'])
        self.selenium.type(self.elements['login']['password'], self.user_password)
        self.selenium.click(self.elements['login']['submit_form'])
        
        self.selenium.wait_for_page_to_load(30000)

    def create_user(self):
        self.user_password = "Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn"
        self.user = User.objects.create_user('cthulhu', 'cthulhu@rlyeh', self.user_password)

        self.user.is_admin = True
        self.user.is_superuser = True

        self.user.save()
        self.transaction.commit()

    def tearDown(self):
        super(AuthenticatedWebTestCase, self).tearDown()

        settings.NETWORK_ROOT = self.network_root
        settings.CTHULHUBOT_BUILDMASTER_BASEDIR = self._old_builddir
        




class MockJob(Mock): pass
MockJob.__bases__ = (Mock, Job)

class MockBuildComputer(Mock): pass
MockBuildComputer.__bases__ = (Mock, BuildComputer)

class MockProject(Mock): pass
MockProject.__bases__ = (Mock, Project)

class MockBuildmaster(Mock): pass
MockBuildmaster.__bases__ = (Mock, Buildmaster)

class TestTooSlowError(Exception):
    """ It took too long to run the tests """
