from __future__ import absolute_import

import os

from twisted.spread import pb
from twisted.cred import credentials
from twisted.internet import reactor, defer


from cthulhubot.models import Buildmaster, Project

class BuildForcer(object):
    def __init__(self, master_string):
        super(BuildForcer, self).__init__()

        self.master_string = master_string

    def createJob(self):
        pass


    def run(self):

        from buildbot.clients.sendchange import Sender

        s = Sender(master=self.master_string, user="Sender")
        d = s.send(branch="master", revision="FETCH_HEAD", comments="Dummy", files="CHANGELOG", category=None, when=None)
        d.addBoth(s.stop)
        reactor.run(False)
        return d



#        master = 123
#        host, port = master.split(":")
#        port = int(port)
#
#        #FIXME TODO
#        branch="master"
#
#        d = defer.Deferred()
#        d.addCallback(lambda res: self.createJob())
#        d.addCallback(lambda res: deliver())
#        d.addCallback(lambda res: reactor.stop())
#
#        reactor.callLater(0, d.callback, None)
#        reactor.run()
#
#        f = pb.PBClientFactory()
#        d = f.login(credentials.UsernamePassword("statusClient", "clientpw"))
#        reactor.connectTCP(host, port, f)
#
#        def connect_failed(error):
#            logging.error("Could not connect to %s: %s"
#                % (master, error.getErrorMessage()))
#            return error
#
#        def cleanup(res):
#            reactor.stop()
#
#        def add_change(remote, branch):
#            change = {
#                'revision': "FETCH_HEAD",
#                'who' : 'BuildBot',
#                'comments': "Forcing build by dummy commit",
#                'branch': branch,
#                'category' : 'auto',
#                'files' : [
#                    'CHANGELOG'
#                ],
#            }
#            d = remote.callRemote('addChange', change)
#            return d
#
#        def connected(remote, branch):
#            return add_change(remote, branch)
#
#        d.addErrback(connect_failed)
#        d.addCallback(connected, branch)
#        d.addBoth(cleanup)
#
#        reactor.run()



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

def get_master_config(slug):
    source = r"""# -*- python -*-
from cthulhubot.buildbot import get_buildmaster_config

BuildmasterConfig = get_buildmaster_config(slug="%s")

""" % slug
    return source

def create_buildmaster_directory_structure(slug, directory):

    if not os.path.exists(directory):
        os.mkdir(directory)

    # do we have master.cfg?
    if not os.path.exists(os.path.join(directory, "master.cfg")):
        f = open(os.path.join(directory, "master.cfg"), 'w')
        f.write(get_master_config(slug))
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

    create_buildmaster_directory_structure(slug=master.project.slug, directory=master.directory)
