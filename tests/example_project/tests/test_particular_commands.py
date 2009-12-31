"""
This module will test particular commands/job in full stack, i.e. with
running buildmaster, slave and friends.
"""
from djangosanetesting.cases import HttpTestCase

import os
from shutil import rmtree
from tempfile import mkdtemp
from time import sleep
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
from shutil import rmtree

from django.conf import settings
from django.utils.simplejson import dumps

from cthulhubot.mongo import get_database_connection

from tests.helpers import (create_project,
    mock_url_root, unmock_url_root,
    create_git_repository, commit, do_piped_command_for_success, prepare_tagged_repo_with_file,
    prepare_working_assignment, clean_assignment,
    TestTooSlowError
)

class ParticularCommandTestCase(HttpTestCase):
    def setUp(self):
        super(ParticularCommandTestCase, self).setUp()
        self.db = get_database_connection()
        mock_url_root(self)
        prepare_working_assignment(self)


    def tearDown(self):
        unmock_url_root(self)
        clean_assignment(self)
        super(ParticularCommandTestCase, self).tearDown()


class TestRevisionProperlyAssociated(ParticularCommandTestCase):

    def get_finished_build(self, max_second_duration=15):
        start = datetime.now()
        while True:
            if datetime.now() > start+timedelta(seconds=max_second_duration):
                raise TestTooSlowError()
            build = [build for build in self.db.builds.find()]
            if build and len(build) > 0:
                #TODO: refactor as needed
                self.assert_equals(1, len(build))
                build = build[0]
                if 'time_end' in build and build['time_end']:
                    return build

    def get_head_hash(self):
        proc = Popen(['git', 'rev-parse', 'HEAD'], stdout=PIPE, stdin=PIPE)
        stdout, stderr = proc.communicate()
        self.assert_equals(0, proc.returncode)

        return stdout.strip()


    def test_test_associates_to_changeset(self):
        self.assignment_test.force_build()

        # get build after test is ready
        build = self.get_finished_build()

        self.assert_equals(self.get_head_hash(), build['changeset'])

