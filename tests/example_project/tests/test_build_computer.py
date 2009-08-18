# -*- coding: utf-8 -*-
from helpers import AuthenticatedWebTestCase
from djangosanetesting.cases import DestructiveDatabaseTestCase

from django.conf import settings

class TestLocalBuildComputer(DestructiveDatabaseTestCase):
    pass

class TestRemoteBuildComputer(DestructiveDatabaseTestCase):
    def setUp(self):
        if not getattr(settings, "TEST_CTHULHUBOT_BUILD_COMPUTER_KEY"):
            raise self.SkipTest()

        if not getattr(settings, "TEST_CTHULHUBOT_BUILD_COMPUTER_HOST"):
            raise self.SkipTest()


class TestBuildComputerWebInterface(AuthenticatedWebTestCase):
    def test_computer_adding(self):
        s = self.selenium



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
