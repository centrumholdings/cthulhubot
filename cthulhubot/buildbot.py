from __future__ import absolute_import

import os
import logging
from urllib2 import urlopen, HTTPError

from pickle import loads

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.simplejson import loads, dumps


from twisted.application import strports
from twisted.spread import pb
from twisted.cred import credentials
from twisted.internet import reactor as twsited_default_reactor
from twisted.python import log as twisted_log
from twisted.web import http

from buildbot.clients.sendchange import Sender
from buildbot.scheduler import BaseScheduler
from buildbot.buildset import BuildSet
from buildbot.sourcestamp import SourceStamp

from cthulhubot.models import Buildmaster, Project
from cthulhubot.models import Buildmaster, Project

REALM = "buildmaster"


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

class BuildForcer(object):
    def __init__(self, master, assignment):
        super(BuildForcer, self).__init__()

        self.master = master
        self.assignment = assignment

    def run(self):
        uri = "http://%s:%s/force_build" % (settings.BUILDMASTER_NETWORK_NAME, self.master.api_port)

        data = {
            'changeset' : 'FETCH_HEAD',
            'builder' : self.assignment.get_identifier()
        }


        try:
            response = urlopen(uri, data=dumps(data))
        except HTTPError, err:
            if err.fp:
                error = ": %s" % err.fp.read()
            else:
                error = ''
            logging.error("Error occured while opening HTTP %s" % error)
            raise
        response_json = response.read()
        response.close()

        #TODO: refactor
        assert response.code == 200

        try:
            return loads(response_json)
        except ValueError:
            return None


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

def create_master(project, webstatus_port=None, buildmaster_port=None, master_directory=None):
    master, created = Buildmaster.objects.get_or_create(
        project = project,
        webstatus_port = webstatus_port,
        buildmaster_port = buildmaster_port,
        directory = master_directory
    )



    uri = "%s%s" % ((settings.NETWORK_ROOT), reverse("cthulhubot-api-project-master-configuration", kwargs={
        "identifier" : int(master.pk)
    }))

    create_buildmaster_directory_structure(slug=master.project.slug, directory=master.directory, password=master.password, uri=uri, username=int(master.buildmaster_port), webstatus_port=master.webstatus_port)
