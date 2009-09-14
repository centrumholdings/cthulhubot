from cthulhubot.models import Project, Job, BuildComputer

from mock import Mock

class MockJob(Mock): pass
MockJob.__bases__ = (Mock, Job)

class MockBuildComputer(Mock): pass
MockBuildComputer.__bases__ = (Mock, BuildComputer)

class MockProject(Mock): pass
MockProject.__bases__ = (Mock, Project)
