from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from pymongo.connection import Connection, ConnectionFailure

def get_database_connection():
    try:
        db_info = {
            "database" : settings.MONGODB_DATABASE,
            "host" : getattr(settings, "MONGODB_HOST", "localhost"),
            "port" : getattr(settings, "MONGODB_PORT", 27017),
            "username" : getattr(settings, "MONGODB_USERNAME", None),
            "password" : getattr(settings, "MONGODB_PASSWORD", None)
        }
        connection = Connection(db_info['host'], db_info['port'])
    except (AttributeError, ConnectionFailure), e:
        raise ImproperlyConfigured(e)

    database = connection[db_info['database']]

    if db_info['username'] or db_info['password']:
        auth = database.authenticate(db_info['username'], db_info['password'])
        if auth is not True:
            log.msg("FATAL: Not connected to Mongo Database, authentication failed")
            raise AssertionError("Not authenticated to use selected database")

    return database