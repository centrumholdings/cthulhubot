from django.core.management.base import BaseCommand

from cthulhubot.models import Buildmaster

class Command(BaseCommand):
    help = 'Restart all Buildmaster processes'
    args = ""

    def handle(self, *fixture_labels, **options):
        verbosity = int(options.get('verbosity', 1))
        commit = int(options.get('commit', 1))
        if verbosity > 1:
            print 'Restarting buildmasters...'
        
        
        for b in Buildmaster.objects.all():
            if verbosity > 1:
                print 'Handling buildmaster %s for project %s' % (str(b.id), str(b.project.name))
            try:
                b.stop()
            except:
                print 'Failed to stop master'
            
            try:
                b.start()
            except:
                print 'Failed to start master'
