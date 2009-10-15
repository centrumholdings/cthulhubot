# -*- coding: utf-8 -*-
from helpers import AuthenticatedWebTestCase

class TestCommands(AuthenticatedWebTestCase):

    def test_package_creation(self):
        s = self.selenium

        # go to commands discovery

        s.click(self.elements['menu']['commands'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['commands']['link-discovery'])
        s.wait_for_page_to_load(30000)

        # our all-favourite build is there
        self.assert_equals(u'cthulhubot-debian-build-debian-package', s.get_text(self.elements['commands']['discovery']['list'] % {'position' : 4}))

        # assign it
        s.click(self.elements['commands']['discovery']['assign'] % {'position' : 4})
        s.wait_for_page_to_load(30000)

        # it's not here anymore
        self.assert_not_equals(u'cthulhubot-debian-build-debian-package', s.get_text(self.elements['commands']['discovery']['list'] % {'position' : 1}))
        
        # and it's in commands
        s.click(self.elements['menu']['commands'])
        s.wait_for_page_to_load(30000)

        self.assert_equals(u'cthulhubot-debian-build-debian-package', s.get_text(self.elements['commands']['list'] % {'position' : 1}))


