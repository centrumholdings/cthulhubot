# -*- coding: utf-8 -*-
from djangosanetesting import DatabaseTestCase
from tests.helpers import (
    BuildmasterTestCase, AuthenticatedWebTestCase,
    create_project,
)


import os
import os.path
from shutil import rmtree
from tempfile import mkdtemp

from django.conf import settings

from cthulhubot.models import Job, JobAssignment, BuildComputer, ProjectClient, Project, ClientUnreachable
from cthulhubot.views import create_job_assignment

class TestBuildDirectory(BuildmasterTestCase):
    def setUp(self):
        super(TestBuildDirectory, self).setUp()

        self.base_directory = mkdtemp()
        self.computer_model = self.computer = BuildComputer.objects.create(hostname = "localhost", basedir=self.base_directory)

        self.job = job = Job.objects.create(slug='cthulhubot-debian-package-creation').get_domain_object()
        self.job.auto_discovery()

        self.assignment = create_job_assignment(
            computer = self.computer_model,
            job = job,
            project = self.project,
            params = {
              'commands' : [
                {
                    'command' : 'cthulhubot-git',
                    'parameters' : {
                        'repository' : '/tmp/repo.git',
                    }
                },
                {},
                {},
                {
                    'command' : 'cthulhubot-debian-package-ftp-upload',
                    'parameters' : {
                        'ftp_user' : 'xxx',
                        'ftp_password' : 'xxx',
                        'ftp_directory' : '',
                        'ftp_host' : ''
                    }
                }
            ]}
        )


        self.project_client = self.assignment.get_client()
        self.build_directory = os.path.join(self.base_directory, self.project_client.get_identifier())
        
        self.transaction.commit()

    def test_loading_assignment_config_works(self):
        self.assert_equals(4, len(self.assignment.get_shell_commands()))

    def test_master_string_creation(self):
        master = settings.BUILDMASTER_NETWORK_NAME
        self.assert_equals("%s:%s" % (master, self.buildmaster.buildmaster_port), self.assignment.get_master_connection_string())

    def test_uri_constructed(self):
        self.assert_true(self.assignment.get_absolute_url() is not None)

class TestAssignmentHandling(BuildmasterTestCase):
    def setUp(self):
        super(TestAssignmentHandling, self).setUp()

        self.base_directory = mkdtemp()
        self.computer_model = self.computer = BuildComputer.objects.create(hostname = "localhost", basedir=self.base_directory)

        self.job = job = Job.objects.create(slug='cthulhubot-sleep').get_domain_object()
        self.job.auto_discovery()

        self.assignment = create_job_assignment(
            computer = self.computer_model,
            job = job,
            project = self.project,
        )

        self.assignment_second = create_job_assignment(
            computer = self.computer_model,
            job = job,
            project = self.project,
        )

        self.project_client = ProjectClient.objects.all()[0]

        self.build_directory = os.path.join(self.base_directory, self.assignment.get_identifier())

        self.transaction.commit()


    def test_assignment_deletes_itself(self):
        self.assignment_second.model.delete()
        self.assert_equals(1, JobAssignment.objects.all().count())

    def test_deleting_single_assignment_leaves_client_alone(self):
        self.assignment_second.model.delete()
        self.assert_equals(1, ProjectClient.objects.all().count())

    def test_deleting_last_assignment_on_computer_deletes_client(self):
        self.assignment_second.model.delete()
        self.assignment.model.delete()
        self.assert_equals(0, ProjectClient.objects.all().count())


class TestAssignmentUpgrades(DatabaseTestCase):
    def setUp(self):
        super(TestAssignmentUpgrades, self).setUp()

        self._old_builddir = getattr(settings, "CTHULHUBOT_BUILDMASTER_BASEDIR", None)
        self.base_directory = mkdtemp()
        settings.CTHULHUBOT_BUILDMASTER_BASEDIR = self.base_directory

        self.project_name = u"project"
        self.project = create_project(self)
        self.buildmaster = self.project.buildmaster_set.all()[0]

        self.computer_model = BuildComputer.objects.create(hostname = "localhost", basedir=self.base_directory)

        self.job = Job.objects.create(slug='cthulhubot-sleep').get_domain_object()
        self.job.auto_discovery()

    def test_retrieving_factory_config_updates_assignment(self):
        self.job.upgrades = [
            lambda x: x,
        ]

        self.assignment = create_job_assignment(
            computer = self.computer_model,
            job = self.job,
            project = self.project,
        )


        self.assignment.get_factory()

        self.assert_equals(1, self.assignment.configuration_version)

    def test_newly_crated_assignment_has_proper_version(self):
        self.job.upgrades = [
            lambda x: x,
        ]

        self.assignment = create_job_assignment(
            computer = self.computer_model,
            job = self.job,
            project = self.project,
        )


        self.assert_equals(1, self.assignment.configuration_version)


    def tearDown(self):
        settings.CTHULHUBOT_BUILDMASTER_BASEDIR = self._old_builddir
        rmtree(self.base_directory)
        
        super(TestAssignmentUpgrades, self).tearDown()


class TestAssignmentDisplay(AuthenticatedWebTestCase):

    def create_project(self):
        project_name = u"你好, řeřicha"
        tracker_uri = u"http://example.com"
        repository_uri = u"/tmp/repo"

        s = self.selenium

        s.click(self.elements['menu']['projects'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['projects']['create'])
        s.wait_for_page_to_load(30000)

        s.type(u"id_name", project_name)
        s.type(u"id_issue_tracker", tracker_uri)
        s.type(u"id_repository", repository_uri)
        s.click(self.elements['projects_create']['submit_form'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['menu']['projects'])
        s.wait_for_page_to_load(30000)

        s.click(self.elements['projects']['project_link_single'])
        s.wait_for_page_to_load(30000)

    def test_project_page_is_ok_even_when_computer_is_unreachable(self):
        s = self.selenium
        self.create_project()
        #self.assign_to_project()

        self.project = Project.objects.get(slug='rericha')

        self.unreachable_computer = BuildComputer.objects.create(hostname="this.hostname.shall.not.be.down.tld", basedir="/tmp", name="Unreachable")
        self.job = job = Job.objects.get(slug='cthulhubot-sleep').get_domain_object()
        self.bad_assignment = create_job_assignment(
            computer = self.unreachable_computer,
            job = job,
            project = self.project,
        )

        self.transaction.commit()

        # navigate to project
        s.click(self.elements['menu']['projects'])
        s.wait_for_page_to_load(30000)

        self.assert_equals(1, int(s.get_xpath_count(self.elements['projects']['list'])))

        s.click(self.elements['projects']['project_link_single'])
        s.wait_for_page_to_load(30000)

        # verify we have one computer and it's unreachable
        self.assert_equals(ClientUnreachable.DEFAULT_STATUS, s.get_text(self.elements['project_detail']['single_computer_status']))
