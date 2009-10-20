from django.db.models import signals

from cthulhubot.mongo import ensure_mongo_structure

def sync_mongo_database(app, created_models, verbosity=2, **kwargs):
    if app == 'cthulhubot':
        ensure_mongo_structure()

signals.post_syncdb.connect(sync_mongo_database)
