from cthulhubot.jobs.job import Job

class BareNoseTests(Job):
    identifier = 'cthulhubot-bare-nose-tests'
    name = u'Run nosetests over a project'

    commands = [
        {
            'command' : 'cthulhubot-git',
        },
        {
            'command' : 'cthulhubot-tests-nose',
        }
    ]

