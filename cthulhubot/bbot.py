from __future__ import absolute_import

from httplib import BadStatusLine
import logging
import os
from urllib2 import urlopen, HTTPError

from pickle import loads

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.simplejson import loads, dumps


from twisted.application import strports
from twisted.python import log as twisted_log
from twisted.web import http

from buildbot.schedulers.base import BaseScheduler

from buildbot.sourcestamp import SourceStamp

from cthulhubot.models import Buildmaster, Project
from cthulhubot.models import Buildmaster, Project

REALM = "buildmaster"

# TryJobHTTPRequest, HTTP API and whole idea about
# forcing builds via scheduler taken from chromium,
# http://src.chromium.org/viewvc/chrome/trunk/tools/buildbot/scripts/master/try_job_http.py?view=markup
# Copyright (c) 2010 The Chromium Authors. All rights reserved.

class TryJobHTTPRequest(http.Request):
    def __init__(self, channel, queued):
        http.Request.__init__(self, channel, queued)
        twisted_log.msg('http request')

    def process(self):
        """
        On URI /force_build, accept JSON dict in format:
        {
            builder : 'name of the builder to build on',
            changeset : 'revision/changeset ID to build (may be symbolic, like FETCH_HEAD',
        }

        Those are mandatory. Any other keys may be provided and they are then passed
        as arguments to buildbot's SourceStamp constructor.
        """
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
                self.code = self.channel.factory.parent.messageReceived(**args)
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
        BaseScheduler.__init__(self, name=name, builderNames=builders, properties=properties or {})
        twisted_log.msg('http api initialized')
        if type(port) is int:
            port = "tcp:%d" % port
        self.port = port

        self.builders = builders

        f = CustomFactory()
        f.parent = self
        s = strports.service(port, f)
        s.setServiceParent(self)

    def messageReceived(self, changeset, builder, **kwargs):
        ss = SourceStamp(revision=changeset, **kwargs)
        reason = "%s force build" % str(builder)
        self.parent.db.runInteraction(self.submitForceRequest, ss, builderNames=[builder], reason=reason)
        return http.OK

    def submitForceRequest(self, t, ss, builderNames, reason):
        ssid = self.parent.db.get_sourcestampid(ss, t)
        return self.create_buildset(ssid=ssid, reason=reason, t=t, builderNames=builderNames)

    def listBuilderNames(self):
        return self.builders

    def run(self):
        return None

class BuildForcer(object):
    def __init__(self, master, assignment, buildbot_data=None):
        super(BuildForcer, self).__init__()

        self.master = master
        self.assignment = assignment

        self.buildbot_data = buildbot_data or {}

    def run(self):
        uri = "http://%s:%s/force_build" % (settings.BUILDMASTER_NETWORK_NAME, self.master.api_port)

        self.buildbot_data.setdefault("changeset", "FETCH_HEAD")
        self.buildbot_data.setdefault("builder", self.assignment.get_identifier())

        try:
            response = urlopen(uri, data=dumps(self.buildbot_data))
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
