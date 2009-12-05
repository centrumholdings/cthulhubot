from django.http import QueryDict
from django.forms import ValidationError
from djangosanetesting.cases import UnitTestCase

from cthulhubot.forms import get_scheduler_form

class TestSchedulerForms(UnitTestCase):
    def setUp(self):
        super(TestSchedulerForms, self).setUp()

    def _get_form(self, post_dict=None):
        if post_dict:
            post = QueryDict('', mutable=True)
            post.update(post_dict)
        else:
            post = None
        return get_scheduler_form(post)

    def test_at_least_one_scheduler_required(self):
        form = self._get_form({})
        self.assert_equals(False, form.is_valid())

    def test_one_scheduler_is_enough(self):
        form = self._get_form({'after_push' : 'on', 'after_push_treeStableTimer' : '1'})
        self.assert_equals(True, form.is_valid())

    def test_more_schedulers_allowed(self):
        form = self._get_form({'after_push' : 'on', 'after_push_treeStableTimer' : '1', 'periodic' : 'on', 'periodic_periodicBuildTimer' : '1'})
        self.assert_equals(True, form.is_valid())

    def test_subform_for_enabled_scheduler_must_be_valid(self):
        form = self._get_form({'after_push' : 'on', 'after_push_treeStableTimer' : 'this is not an integer'})
        self.assert_equals(False, form.is_valid())

    def test_empty_branch_normalizes_to_none(self):
        form = self._get_form({'after_push' : 'on', 'after_push_treeStableTimer' : '1', 'branch' : ''})
        self.assert_equals(True, form.is_valid())
        self.assert_equals(None, form.fields['after_push'].subform.cleaned_data['after_push_branch'])

    def test_no_config_when_invalid(self):
        form = self._get_form({'after_push' : 'on', 'after_push_treeStableTimer' : 'this is not an integer'})
        self.assert_raises(ValidationError, form.get_configuration_dict)

    def test_simple_scheduler_returns_proper_json(self):
        form = self._get_form({'after_push' : 'on', 'after_push_treeStableTimer' : '1'})
        expected_json = {
            'schedule' : [
                {
                    'identifier' : 'after_push',
                    'parameters' : {
                        'treeStableTimer' : 1,
                        'branch' : None
                    }
                }
            ]
        }

        self.assert_equals(expected_json, form.get_configuration_dict())
