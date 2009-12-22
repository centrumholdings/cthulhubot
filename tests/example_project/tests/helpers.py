from django.core.management import call_command
from djangosanetesting.cases import SeleniumTestCase
from mock import Mock

from django.contrib.auth.models import User

from cthulhubot.models import Project, Job, BuildComputer, Buildmaster
from cthulhubot.project import create_project as cthulhu_create_project

def create_project(case, name=None, tracker_uri=None, repository_uri=None):
    return cthulhu_create_project(name=name or case.project_name, tracker_uri=tracker_uri or "http://example.com", repository_uri=repository_uri or "/tmp/test")


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


class MockJob(Mock): pass
MockJob.__bases__ = (Mock, Job)

class MockBuildComputer(Mock): pass
MockBuildComputer.__bases__ = (Mock, BuildComputer)

class MockProject(Mock): pass
MockProject.__bases__ = (Mock, Project)

class MockBuildmaster(Mock): pass
MockBuildmaster.__bases__ = (Mock, Buildmaster)
