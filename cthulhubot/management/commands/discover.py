from django.core.management.base import BaseCommand

from cthulhubot.models import Job, Command as JobCommand
from cthulhubot.commands import get_available_commands
from cthulhubot.jobs import get_available_jobs

from django.db import transaction

class Command(BaseCommand):
    help = 'Dicover all Jobs and Commands available.'
    args = ""

    def store_discoverables(self, klass, availables, verbosity):
        for identifier in availables:
            if verbosity > 1:
                print '%s %s discovered' % (str(klass), identifier)
            klass.objects.get_or_create(slug=identifier)

    def handle(self, *fixture_labels, **options):
        verbosity = int(options.get('verbosity', 1))
        commit = int(options.get('commit', 1))
        if verbosity > 1:
            print 'Discovering jobs'

        self.store_discoverables(JobCommand, get_available_commands().keys(), verbosity)
        self.store_discoverables(Job, get_available_jobs().keys(), verbosity)
        
        if commit and transaction.is_managed():
            if verbosity > 1:
                print 'Commiting jobs...'
            transaction.commit()
    