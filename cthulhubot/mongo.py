from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from pymongo.connection import Connection, ConnectionFailure

MONGODB_DATABASE_TEST_PREFIX = "test_"

def is_test_database():
    # This is hacky, but fact we're running tests is determined by _create_test_db call.
    # We'll assume usage of it if assigned to settings.DATABASE_NAme

    if settings.TEST_DATABASE_NAME:
        test_database_name = settings.TEST_DATABASE_NAME
    else:
        test_database_name = TEST_DATABASE_PREFIX + settings.DATABASE_NAME

    return settings.DATABASE_NAME == test_database_name

def get_database_name():
    db_name = getattr(settings, "MONGODB_DATABASE_NAME", None)
    if not db_name:
        raise ImproperlyConfigured("Mongo database name not specified")

    if is_test_database():
        db_name = getattr(settings, "TEST_MONGODB_DATABASE_NAME", None)
        if not db_name:
            db_name = MONGODB_DATABASE_TEST_PREFIX + settings.MONGODB_DATABASE_NAME
    return db_name

def get_database_connection():
    db_name = get_database_name()
    
    try:
        db_info = {
            "database" : db_name,
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

