import os

from cthulhubot.models import Buildmaster, Project

def get_buildmaster_config(slug):
    project = Project.objects.get(slug=slug)

    return {
    }

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

def create_master(project, webstatus_port=None, buildmaster_port=None):
    master, created = Buildmaster.objects.get_or_create(
        project = project,
        webstatus_port = webstatus_port,
        buildmaster_port = buildmaster_port
    )

    create_buildmaster_directory_structure(slug=master.project.slug, directory=master.directory)
