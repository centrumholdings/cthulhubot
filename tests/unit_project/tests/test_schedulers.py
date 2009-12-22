from djangosanetesting.cases import UnitTestCase
from mock import Mock

from django.http import QueryDict
from django.forms import ValidationError
from django.utils.simplejson import dumps, loads

from cthulhubot.assignment import Assignment
from cthulhubot.forms import get_scheduler_form

from buildbot.scheduler import Scheduler, AnyBranchScheduler

class TestSchedulerForms(UnitTestCase):

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

class TestBuildbotSchedulersGeneratedFromConfigAssignment(UnitTestCase):
    def setUp(self):
        super(TestBuildbotSchedulersGeneratedFromConfigAssignment, self).setUp()

        self.assignment_model = Mock()
        self.assignment_model.config = dumps({})

        self.assignment = Assignment(model=self.assignment_model)

    def _update_config(self, config):
        conf = loads(self.assignment_model.config)
        conf.update(config)
        self.assignment_model.config = dumps(conf)

    def test_single_scheduler_generated_by_default(self):
        self.assert_equals(1, len(self.assignment.get_schedulers()))

    def test_after_push_generated_by_default_when_no_branch_given(self):
        self.assert_equals(AnyBranchScheduler, self.assignment.get_schedulers()[0].__class__)

    def test_all_consuming_scheduler_generated_by_default(self):
        self.assert_equals(None, self.assignment.get_schedulers()[0].branches)

    def test_no_branch_after_push_means_any_branch(self):
        self._update_config({
            'schedule' : [
                {
                    'identifier' : 'after_push',
                    'parameters' : {
                        'treeStableTimer' : 1,
                        'branch' : ""
                    }
                }
            ]
        })
        self.assert_equals(AnyBranchScheduler, self.assignment.get_schedulers()[0].__class__)

    def test_branched_scheduler_means_after_push(self):
        self._update_config({
            'schedule' : [
                {
                    'identifier' : 'after_push',
                    'parameters' : {
                        'treeStableTimer' : 1,
                        'branch' : "mastah"
                    }
                }
            ]
        })
        self.assert_equals(Scheduler, self.assignment.get_schedulers()[0].__class__)

    def test_default_scheduler_replaced_by_configured_one(self):
        self._update_config({
            'schedule' : [
                {
                    'identifier' : 'after_push',
                    'parameters' : {
                        'treeStableTimer' : 1,
                        'branch' : "mastah"
                    }
                }
            ]
        })
        self.assert_equals(1, len(self.assignment.get_schedulers()))

    def test_branch_name_propagated_to_push_scheduler(self):
        self._update_config({
            'schedule' : [
                {
                    'identifier' : 'after_push',
                    'parameters' : {
                        'treeStableTimer' : 1,
                        'branch' : "mastah"
                    }
                }
            ]
        })
        self.assert_equals("mastah", self.assignment.get_schedulers()[0].branch)

    def test_periodic_builder_propagated_with_proper_timer(self):
        self._update_config({
            'schedule' : [
                {
                    'identifier' : 'periodic',
                    'parameters' : {
                        'periodicBuildTimer' : 249,
                    }
                }
            ]
        })
        self.assert_equals(249, self.assignment.get_schedulers()[0].periodicBuildTimer)

    def test_all_branches_are_default_for_configured_schedulers(self):
        self._update_config({
            'schedule' : [
                {
                    'identifier' : 'periodic',
                    'parameters' : {
                        'periodicBuildTimer' : 249,
                    }
                }
            ]
        })
        self.assert_equals(None, self.assignment.get_schedulers()[0].branch)

    def test_multiple_schedulers_accepted(self):
        self._update_config({
            'schedule' : [
                {
                    'identifier' : 'periodic',
                    'parameters' : {
                        'periodicBuildTimer' : 249,
                    }
                },
                {
                    'identifier' : 'after_push',
                    'parameters' : {
                        'treeStableTimer' : 100,
                        'branch' : 'mastah'
                    }
                }
            ]
        })
        self.assert_equals(2, len(self.assignment.get_schedulers()))

    def test_multiple_schedulers_propagates_parameters_properly(self):
        self._update_config({
            'schedule' : [
                {
                    'identifier' : 'periodic',
                    'parameters' : {
                        'periodicBuildTimer' : 249,
                    }
                },
                {
                    'identifier' : 'after_push',
                    'parameters' : {
                        'treeStableTimer' : 100,
                        'branch' : 'mastah'
                    }
                }
            ]
        })
        self.assert_equals(249, self.assignment.get_schedulers()[0].periodicBuildTimer)
        self.assert_equals(100, self.assignment.get_schedulers()[1].treeStableTimer)
