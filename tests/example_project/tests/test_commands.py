# -*- coding: utf-8 -*-
from helpers import AuthenticatedWebTestCase

class TestCommands(AuthenticatedWebTestCase):

    def setUp(self):
        super(TestCommands, self).setUp(discover=False)

    def get_position(self, slug):
        commands_no = int(self.selenium.get_xpath_count(self.elements['commands']['discovery']['list']))
        for i in xrange(0, commands_no):
            pos = i+1
            if self.selenium.get_text(self.elements['commands']['discovery']['list-item'] % {'position' : pos}) == slug:
                return pos
        raise ValueError("Slug %s not found in list" % slug)

    def test_package_creation(self):
        s = self.selenium

        # go to commands discovery
        slug = 'cthulhubot-sleep'

        s.click(self.elements['menu']['commands'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['commands']['link-discovery'])
        s.wait_for_page_to_load(30000)

        position = self.get_position(slug)
        # our all-favourite sleep is there
        self.assert_equals(slug, s.get_text(self.elements['commands']['discovery']['list-item'] % {'position' : position}))

        # assign it
        s.click(self.elements['commands']['discovery']['assign'] % {'position' : position})
        s.wait_for_page_to_load(30000)

        # it's not here anymore
        self.assert_not_equals(slug, s.get_text(self.elements['commands']['discovery']['list-item'] % {'position' : position}))
        
        # and it's in commands
        s.click(self.elements['menu']['commands'])
        s.wait_for_page_to_load(30000)

        self.assert_equals(slug, s.get_text(self.elements['commands']['list'] % {'position' : 1}))

