# -*- coding: utf-8 -*-
from helpers import AuthenticatedWebTestCase
from djangosanetesting.cases import DestructiveDatabaseTestCase

from shutil import rmtree
from tempfile import mkdtemp
from django.conf import settings

from cthulhubot.computer import Computer

class TestRemoteComputer(DestructiveDatabaseTestCase):
    def setUp(self):
        super(TestRemoteComputer, self).setUp()

        self.key = getattr(settings, "TEST_CTHULHUBOT_BUILD_COMPUTER_KEY", None)
        if not self.key:
            raise self.SkipTest()

        self.host = getattr(settings, "TEST_CTHULHUBOT_BUILD_COMPUTER_HOST")
        if not self.host:
            raise self.SkipTest()

        self.user = getattr(settings, "TEST_CTHULHUBOT_BUILD_COMPUTER_USERNAME", "buildbot")

        self.computer = Computer(key=self.key, host=self.host, user=self.user)

    def test_connection_without_exception(self):
        self.computer.connect()
        
    def test_check_build_directory_not_exists_by_default(self):
        self.computer.connect()
        self.assert_false(self.computer.build_directory_exists("/does/not/exists"))

    def tearDown(self):
        self.computer.disconnect()

        super(TestRemoteComputer, self).tearDown()

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