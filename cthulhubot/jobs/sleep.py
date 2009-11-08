from cthulhubot.jobs.job import Job

class Sleep(Job):
    identifier = 'cthulhubot-sleep'
    name = u'Sleep for a sec'

    commands = [
        {
            'command' : 'cthulhubot-sleep',
            'parameters' : {
                'time' : 1
            }
        }
    ]

