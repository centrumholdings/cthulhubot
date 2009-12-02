from cthulhubot.jobs.job import Job

class SaveRepositoryInformation(Job):
    identifier = 'cthulhubot-save-repository-information'
    name = u'Save metadata about newest push in database'

    commands = [
        {
            'command' : 'cthulhubot-git',
        },
        {
            'command' : 'cthulhubot-update-repository-info',
        }
    ]

