from django.core.management.base import BaseCommand

from cthulhubot.models import Job
from cthulhubot.jobs import get_available_jobs

from django.db import transaction

class Command(BaseCommand):
    help = 'Dicover all Jobs and Commands available.'
    args = ""

    def handle(self, *fixture_labels, **options):
        verbosity = int(options.get('verbosity', 1))
        commit = int(options.get('commit', 1))
        if verbosity > 1:
            print 'Discovering jobs'

        # commit changes

        for job_klass in get_available_jobs().values():
            assert job_klass.identifier is not None
            if verbosity > 1:
                print 'Job %s discovered, discovering commands' % job_klass.identifier
            job, created = Job.objects.get_or_create(slug=job_klass.identifier)
            if created:
                job.auto_discovery()

        if commit and transaction.is_managed():
            if verbosity > 1:
                print 'Commiting jobs...'
            transaction.commit()
    