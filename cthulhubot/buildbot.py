from __future__ import absolute_import

import os

from threading import Thread
import logging

from django.conf import settings
from django.core.urlresolvers import reverse

from twisted.spread import pb
from twisted.cred import credentials
from twisted.internet import defer
from twisted.internet.selectreactor import SelectReactor
from twisted.internet import reactor as twsited_default_reactor

from cthulhubot.models import Buildmaster, Project
from buildbot.clients.sendchange import Sender

class CustomReactorSender(Sender):
    def __init__(self, master, user=None, reactor=None):
        Sender.__init__(self, master, user=None)
        self.reactor = reactor or twsited_default_reactor

    def send(self, branch, revision, comments, files, user=None, category=None, when=None):
        if user is None:
            user = self.user
        change = {'who': user, 'files': files, 'comments': comments,
                  'branch': branch, 'revision': revision, 'category': category,
                  'when': when}
        self.num_changes += 1

        f = pb.PBClientFactory()
        d = f.login(credentials.UsernamePassword("change", "changepw"))
        self.reactor.connectTCP(self.host, self.port, f)
        d.addCallback(self.addChange, change)
        return d

    def stop(self, res):
        self.reactor.stop()
        return res

    def run(self, installSignalHandlers=True):
        self.reactor.run(installSignalHandlers)

class BuildForcer(object):
    def __init__(self, master_string):
        super(BuildForcer, self).__init__()

        self.master_string = master_string

    def connect_failed(self, error):
        logging.error("Could not connect: %s"
            % error.getErrorMessage())
        return error

    def run(self):

        reactor = SelectReactor()

        s = CustomReactorSender(master=self.master_string, user="BuildBot", reactor=reactor)
        d = s.send(branch="master", revision="FETCH_HEAD", comments="Dummy", files="CHANGELOG", category=None, when=None, user="BuildBot")
        d.addErrback(self.connect_failed)
        d.addBoth(s.stop)
        thread = Thread(target=s.run, args=(False,))
        thread.start()
        return d


def get_buildmaster_config(slug):
    project = Project.objects.get(slug=slug)
    master = project.buildmaster_set.all()[0]

    return master.get_config()

def get_twisted_tac_config(directory):
    source="""from twisted.application import service
from buildbot.master import BuildMaster

basedir = r'%s'
configfile = r'master.cfg'

application = service.Application('buildmaster')
BuildMaster(basedir, configfile).setServiceParent(application)
""" % directory
    return source

def get_master_config(uri, username, password):
    # generate client for cthylla

    source = r"""# -*- python -*-
from cthylla import get_buildmaster_config

BuildmasterConfig = get_buildmaster_config(uri="%(uri)s", username="%(username)s", password="%(password)s")

""" % {
        'uri' : uri,
        'username' : username,
        'password' : password,
    }
    return source

def create_buildmaster_directory_structure(slug, directory, password, uri, username):

    if not os.path.exists(directory):
        os.mkdir(directory)

    # do we have master.cfg?
    if not os.path.exists(os.path.join(directory, "master.cfg")):
        f = open(os.path.join(directory, "master.cfg"), 'w')
        f.write(get_master_config(uri, username, password))
        f.close()

    # buildbot.tac?
    if not os.path.exists(os.path.join(directory, "buildbot.tac")):
        f = open(os.path.join(directory, "buildbot.tac"), 'w')
        f.write(get_twisted_tac_config(directory))
        f.close()

    # empty twistd.log so tail will not complain
    if not os.path.exists(os.path.join(directory, "twistd.log")):
        f = open(os.path.join(directory, "twistd.log"), 'w')
        f.write('')
        f.close()

def create_master(project, webstatus_port=None, buildmaster_port=None):
    master, created = Buildmaster.objects.get_or_create(
        project = project,
        webstatus_port = webstatus_port,
        buildmaster_port = buildmaster_port
    )



    uri = "%s%s" % ((settings.NETWORK_ROOT), reverse("cthulhubot-api-project-master-configuration", kwargs={
        "identifier" : master.pk
    }))

    create_buildmaster_directory_structure(slug=master.project.slug, directory=master.directory, password=master.password, uri=uri, username=master.buildmaster_port)
