#!/usr/bin/env python

'''
simple shortcut for running nosetests via python
replacement for *.bat or *.sh wrappers
'''

import os
import sys
from os.path import join, pardir, abspath, dirname, split

import nose


# django settings module
DJANGO_SETTINGS_MODULE = '%s.%s' % (split(abspath(dirname(__file__)))[1], 'settings')
# pythonpath dirs
PYTHONPATH = [
    abspath(join( dirname(__file__), pardir, pardir)),
    abspath(join( dirname(__file__), pardir)),
]


# inject few paths to pythonpath
for p in PYTHONPATH:
    if p not in sys.path:
        sys.path.insert(0, p)

# django needs this env variable
os.environ['DJANGO_SETTINGS_MODULE'] = DJANGO_SETTINGS_MODULE

from nose.plugins import Plugin

class MongoDatabasePlugin(Plugin):
    name = 'mongo-database'
    score = 79

    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        Plugin.configure(self, options, config)

    def _drop_database(self):
        from cthulhubot.mongo import get_database_connection
        db = get_database_connection()
        conn = db.connection()
        conn.drop_database(db)

    def begin(self):
        self._drop_database()

    def stopTest(self, test):
        self._drop_database()


for i in ['--with-django', '--with-mongo-database']:
    if i not in sys.argv:
        sys.argv.insert(1, i)


nose.run_exit(
    defaultTest=dirname(__file__),
    addplugins = [MongoDatabasePlugin()]
)

