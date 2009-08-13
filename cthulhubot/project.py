from cthulhubot.models import Project, Buildmaster
from cthulhubot.buildbot import create_master

def create_project(name, tracker_uri, webstatus_port=None, buildmaster_port=None):
    """
    Create project, buildmaster for it and associate them properly
    """
    project = Project.objects.create(
        name = name,
        tracker_uri = tracker_uri
    )

    create_master(project=project, webstatus_port=webstatus_port, buildmaster_port=buildmaster_port)

    return project
