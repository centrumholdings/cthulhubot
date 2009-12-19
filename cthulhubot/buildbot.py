from __future__ import absolute_import

import os

from threading import Thread
import logging

from django.conf import settings
from django.core.urlresolvers import reverse

from twisted.application import strports
from twisted.spread import pb
from twisted.cred import credentials
from twisted.internet.selectreactor import SelectReactor
from twisted.internet import reactor as twsited_default_reactor
from twisted.python import log as twisted_log
from twisted.web import http

from django.utils.simplejson import loads

from cthulhubot.models import Buildmaster, Project

from buildbot.clients.sendchange import Sender
from buildbot.scheduler import BaseScheduler
from buildbot.buildset import BuildSet
from buildbot.sourcestamp import SourceStamp

class TryJobHTTPRequest(http.Request):
    def __init__(self, channel, queued):
        http.Request.__init__(self, channel, queued)
        twisted_log.msg('http request')

    def process(self):
        twisted_log.msg('process')
        try:
            # Support only one URI for now.
            if self.uri != '/force_build':
                twisted_log.msg("Received invalid URI: %s" % self.uri)
                self.code = http.NOT_FOUND
                return

            try:
                self.content.seek(0)
                args = loads(self.content.read())
                self.code = self.channel.factory.parent.messageReceived(
                    changeset = args['changeset'],
                    builder = args['builder']
                )
            except Exception:
                self.code = http.INTERNAL_SERVER_ERROR
                raise
        finally:
            twisted_log.msg('finally')
            self.code_message = http.RESPONSES[self.code]
            self.write(self.code_message)
            self.finish()

class CustomProtocol(http.HTTPChannel):
    requestFactory = TryJobHTTPRequest

class CustomFactory(http.HTTPFactory):
    protocol = CustomProtocol

class HttpApi(BaseScheduler):
    """Opens a HTTP port to expose custom CthulhuBot API inside of a Buildmaster"""

    def __init__(self, name, port, builders, userpass=None, properties=None):
        BaseScheduler.__init__(self, name, properties or {})
        twisted_log.msg('http api initialized')
        if type(port) is int:
            port = "tcp:%d" % port
        self.port = port

        self.builders = builders

        f = CustomFactory()
        f.parent = self
        s = strports.service(port, f)
        s.setServiceParent(self)

    def messageReceived(self, changeset, builder):
        return self.submitForceRequest(changeset, builder)

    def submitForceRequest(self, changeset, builder):
        reason = "%s force build" % builder
        bs = BuildSet([builder], SourceStamp(revision=changeset), reason=reason)
        self.parent.submitBuildSet(bs)
        return http.OK

    def listBuilderNames(self):
        return self.builders

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

def get_master_config(uri, username, password, webstatus_port=None):
    # generate client for cthylla

    source = r"""# -*- python -*-
from cthylla import get_buildmaster_config

BuildmasterConfig = get_buildmaster_config(uri="%(uri)s", username="%(username)s", password="%(password)s")

""" % {
        'uri' : uri,
        'username' : str(username),
        'password' : password,
    }
    # add non-pickable web status where we need it
    # this will be superseeded by new transfer format
    if webstatus_port:
        source += """
from buildbot.status import html
BuildmasterConfig['status'].append(html.WebStatus(http_port="%s"))
""" % webstatus_port

    return source

def create_buildmaster_directory_structure(slug, directory, password, uri, username, webstatus_port=None):

    if not os.path.exists(directory):
        os.mkdir(directory)

    # do we have master.cfg?
    if not os.path.exists(os.path.join(directory, "master.cfg")):
        f = open(os.path.join(directory, "master.cfg"), 'w')
        f.write(get_master_config(uri, username, password, webstatus_port))
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
        "identifier" : int(master.pk)
    }))

    create_buildmaster_directory_structure(slug=master.project.slug, directory=master.directory, password=master.password, uri=uri, username=int(master.buildmaster_port), webstatus_port=master.webstatus_port)
