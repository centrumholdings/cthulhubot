from cthulhubot.commands import Sleep
from cthulhubot.jobs.job import Job

class Sleep(Job):
    identifier = 'cthulhubot-sleep'
    name = u'Sleep for a sec'

    commands = [
        {
            'command' : Sleep,
            'parameters' : {
                'time' : 1
            }
        }
    ]

