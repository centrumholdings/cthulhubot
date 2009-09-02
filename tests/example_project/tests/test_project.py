# -*- coding: utf-8 -*-
from helpers import AuthenticatedWebTestCase

class TestProjects(AuthenticatedWebTestCase):

    def test_project_creation(self):
        s = self.selenium

        # create project

        project_name = u"你好, řeřicha"
        tracker_uri = u"http://example.com"

        s.click(self.elements['menu']['projects'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['projects']['create'])
        s.wait_for_page_to_load(30000)

        s.type(u"id_name", project_name)
        s.type(u"id_issue_tracker", tracker_uri)
        s.click(self.elements['projects_create']['submit_form'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['menu']['projects'])
        s.wait_for_page_to_load(30000)

        self.assert_equals(1, int(s.get_xpath_count(self.elements['projects']['list'])))

        s.click(self.elements['projects']['project_link_single'])
        s.wait_for_page_to_load(30000)

        self.assert_equals(project_name, s.get_text(self.elements['project_detail']['name']))
        self.assert_equals(u"Buildmaster status: Not running", s.get_text(self.elements['project_detail']['buildmaster_status']))

        # start buildmaster

        s.click(self.elements['project_detail']['start_buildmaster'])
        s.wait_for_page_to_load(30000)

        self.assert_equals(u"Buildmaster status: Running", s.get_text(self.elements['project_detail']['buildmaster_status']))

        # stop not to clash
        s.click(self.elements['project_detail']['stop_buildmaster'])
        s.wait_for_page_to_load(30000)

        self.assert_equals(u"Buildmaster status: Not running", s.get_text(self.elements['project_detail']['buildmaster_status']))

