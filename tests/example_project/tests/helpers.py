from djangosanetesting.cases import SeleniumTestCase

from cthulhubot.models import Project, Job, BuildComputer, Buildmaster

from mock import Mock


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
                "list" : "//ul[@class='commands-list']/li[%(position)s]",
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

    def setUp(self):
        super(WebTestCase, self).setUp()

        self.selenium.open("/")
        self.selenium.wait_for_page_to_load(30000)

class AuthenticatedWebTestCase(WebTestCase):
    def setUp(self):
        super(AuthenticatedWebTestCase, self).setUp()

        self.selenium.click(self.elements['menu']['login'])
        self.selenium.wait_for_page_to_load(30000)

        self.selenium.click(self.elements['login']['username'])
        self.selenium.click(self.elements['login']['password'])
        self.selenium.click(self.elements['login']['submit_form'])
        
        self.selenium.wait_for_page_to_load(30000)


class MockJob(Mock): pass
MockJob.__bases__ = (Mock, Job)

class MockBuildComputer(Mock): pass
MockBuildComputer.__bases__ = (Mock, BuildComputer)

class MockProject(Mock): pass
MockProject.__bases__ = (Mock, Project)

class MockBuildmaster(Mock): pass
MockJob.__bases__ = (Mock, Buildmaster)
