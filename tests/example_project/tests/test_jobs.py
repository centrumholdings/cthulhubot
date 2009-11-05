# -*- coding: utf-8 -*-
from djangosanetesting.cases import UnitTestCase
from helpers import AuthenticatedWebTestCase

from cthulhubot.models import JobAssignment

from example_project.tests.helpers import MockJob, MockBuildComputer, MockProject

class TestJobs(AuthenticatedWebTestCase):
    def setUp(self):
        super(TestJobs, self).setUp(discover=False)

    def test_auto_discovery(self):
        s = self.selenium

        # go to commands discovery

        s.click(self.elements['menu']['jobs'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['jobs']['link-configuration'])
        s.wait_for_page_to_load(30000)

        # our all-favourite build is there
        jobs_num = int(s.get_xpath_count(self.elements['jobs']['discovery']['list']))
        self.assert_true(jobs_num > 0, u"No job discovered, this is a bug (we have default jobs)")

        jobs = [s.get_text(self.elements['jobs']['discovery']['list-item'] % {'position' : i+1}) for i in xrange(0, jobs_num)]
        jobs.sort()

        # assign it
        s.click(self.elements['jobs']['discovery']['auto'])
        s.wait_for_page_to_load(30000)

        # we're on jobs page, check we have it all
        jobs_num = int(s.get_xpath_count(self.elements['jobs']['list-items']))
        discovered_jobs = [s.get_text(self.elements['jobs']['list-item'] % {'position' : i+1}) for i in xrange(0, jobs_num)]
        discovered_jobs.sort()

        self.assert_equals(jobs, discovered_jobs)

