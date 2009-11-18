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

class EchoNameJob(JobInterface):
    identifier = 'cthulhubot-test-helper-echo-name-job'
    name = u'Echo In Console'

    commands = [
        {
            'command' : 'cthulhubot-test-helper-echo',
            'parameters' : {
                'what' : 'name'
            }
        },
    ]

class MultipleEchoJob(JobInterface):
    identifier = 'cthulhubot-test-helper-multiple-echo-job'
    name = u'Echo In Console'

    commands = [
        {
            'command' : 'cthulhubot-test-helper-echo',
            'parameters' : {
                'what' : 'first'
            }
        },
        {
            'command' : 'cthulhubot-test-helper-echo',
        },
        {
            'command' : 'cthulhubot-test-helper-echo',
        },
    ]

class MultipleEchoJobWithDefaultParamsForAllEchos(MultipleEchoJob):
    identifier = 'cthulhubot-test-helper-multiple-echo-all-defined-job'
    name = u'Echo In Console'

    global_command_parameters = {
        'cthulhubot-test-helper-echo' : {
            'what' : 'overwritten by job'
        }
    }

class MultipleEchoJobWithDefaultParamsForSecondEcho(MultipleEchoJob):
    identifier = 'cthulhubot-test-helper-multiple-echo-2-defined-job'
    name = u'Echo In Console'

    def filter_commands(self, commands):
        echo_no = 0
        for command in commands:
            if command['command'] == 'cthulhubot-test-helper-echo':
                echo_no += 1
                if echo_no == 2:
                    if not command.has_key('parameters'):
                        command['parameters'] = {}
                    command['parameters']['what'] = 'overwritten by job'
        return commands

def register_mock_jobs_and_commands():
    ADDITIONAL_COMMANDS[EchoCommand.identifier] = EchoCommand
    ADDITIONAL_JOBS[EchoJob.identifier] = EchoJob
    ADDITIONAL_JOBS[EchoNameJob.identifier] = EchoNameJob
    ADDITIONAL_JOBS[MultipleEchoJob.identifier] = MultipleEchoJob
    ADDITIONAL_JOBS[MultipleEchoJobWithDefaultParamsForAllEchos.identifier] = MultipleEchoJobWithDefaultParamsForAllEchos
    ADDITIONAL_JOBS[MultipleEchoJobWithDefaultParamsForSecondEcho.identifier] = MultipleEchoJobWithDefaultParamsForSecondEcho



##### End of helper commands ######