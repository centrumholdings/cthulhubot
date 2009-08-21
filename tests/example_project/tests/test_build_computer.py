# -*- coding: utf-8 -*-
from helpers import AuthenticatedWebTestCase
from djangosanetesting.cases import DestructiveDatabaseTestCase

from shutil import rmtree
from tempfile import mkdtemp
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

    def setUp(self):
        super(TestBuildComputerWebInterface, self).setUp()

        self.basedir = mkdtemp(prefix="test_localhost_build_")

    def test_computer_adding_localhost(self):
        s = self.selenium

        s.click(self.elements['menu']['computers'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['computers']['create'])
        s.wait_for_page_to_load(30000)

        s.type(u"id_name", u"localhost")
        s.type(u"id_slug", u"test")
        s.type(u"id_description", u"my localhost precious")
        s.type(u"id_hostname", u"localhost")
        s.type(u"id_username", u"notused")
        s.click(self.elements['computers_create']['submit_form'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['menu']['computers'])
        s.wait_for_page_to_load(30000)

        self.assert_equals(1, int(s.get_xpath_count(self.elements['computers']['list'])))

        s.click(self.elements['computers']['computer_link_single'])
        s.wait_for_page_to_load(30000)

        self.assert_equals(u"localhost", s.get_text(self.elements['computer_detail']['name']))

    def tearDown(self):
        rmtree(self.basedir)

        super(TestBuildComputerWebInterface, self).tearDown()