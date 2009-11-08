from cthulhubot.models import Project, Job, BuildComputer
from cthulhubot.commands import ADDITIONAL_COMMANDS
from cthulhubot.jobs import ADDITIONAL_JOBS

##### Custom mocks ######
from mock import Mock

class MockJob(Mock): pass
MockJob.__bases__ = (Mock, Job)

class MockBuildComputer(Mock): pass
MockBuildComputer.__bases__ = (Mock, BuildComputer)

class MockProject(Mock): pass
MockProject.__bases__ = (Mock, Project)

##### End of custom mocks ######

##### Helper commands ######

from cthulhubot.commands.interface import Command
from cthulhubot.jobs.interface import Job as JobInterface

class EchoCommand(Command):
    identifier = 'cthulhubot-test-helper-echo'
    name = {
        'basic' : u"Echo",
        'running' : u"Echo",
        'succeeded' : u"Echo",
        'failed' : u"Echo",
    }

    parameters = {
        'what' : {
            'help' : u'What to echo',
            'value' : None,
            'required' : True,
        },
    }

    command = ["echo", "%(what)s"]

class EchoJob(JobInterface):
    identifier = 'cthulhubot-test-helper-echo-job'
    name = u'Echo In Console'

    commands = [
        {
            'command' : 'cthulhubot-test-helper-echo',
        },
    ]

def register_mock_jobs_and_commands():
    ADDITIONAL_COMMANDS[EchoCommand.identifier] = EchoCommand
    ADDITIONAL_JOBS[EchoJob.identifier] = EchoJob


##### End of helper commands ######