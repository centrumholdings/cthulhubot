from djangosanetesting.cases import SeleniumTestCase

class WebTestCase(SeleniumTestCase):
    elements = {
        'menu' : {
            'login' : "menu-link-login",
            'projects' : "menu-link-projects",
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
        },
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
