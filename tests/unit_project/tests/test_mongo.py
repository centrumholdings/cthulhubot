from datetime import datetime

from djangosanetesting.cases import DatabaseTestCase
from django.template import Template, Context

from cthulhubot.mongo import get_database_connection

class TestTemplateTag(DatabaseTestCase):
    def setUp(self):
        super(TestTemplateTag, self).setUp()
        self.db = get_database_connection()
        self.build = self.insert_build()

    def insert_build(self, time_end=False, time_start=False):
        if not time_start:
            time_start = datetime(year=2009, month=01, day=01, hour=12, minute=00, second=00)

        if time_end is False:
            time_start = datetime(year=2009, month=01, day=01, hour=12, minute=00, second=01)

        build = {
            'builder' : 'builder',
            'slaves' : ['slave'],
            'number' : 1,
            'time_start' : time_start,
            'time_end' : time_end,
            'steps' : [],
        }
        self.db.builds.insert(build)

        return build

    def get_template_content(self, t):
        return t.render(Context({'build': self.build}))

    def test_identifier_print(self):
        t = Template('''{% load mongo %}{% mongoid build %}''')
        self.assert_equals(str(self.build['_id']), self.get_template_content(t))

    def test_stored_to_variable_produces_no_output(self):
        t = Template('''{% load mongo %}{% mongoid build as build_id %}''')
        self.assert_equals(0, len(self.get_template_content(t)))

    def test_storing_id_to_variable(self):
        t = Template('''{% load mongo %}{% mongoid build as build_id %}{{ build_id }}''')
        self.assert_equals(str(self.build['_id']), self.get_template_content(t))
