import os
import sys
from os.path import join, pardir, abspath, dirname, split

from paver.easy import *
from paver.setuputils import setup

from setuptools import find_packages

VERSION = (0, 4, 0)
__version__ = VERSION
__versionstr__ = '.'.join(map(str, VERSION))

setup(
    name = 'cthulhubot',
    version = __versionstr__,
    description = 'Django Massive Buildbot',
    long_description = '\n'.join((
        'Django Massive Buildbot',
        '',
    )),
    author = 'centrum holdings s.r.o',
    author_email='devel@centrumholdings.com',
    license = 'BSD',

    packages = find_packages(
        where = '.',
        exclude = ('docs', 'tests')
    ),

    include_package_data = True,

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Framework :: Django",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires = [
        'setuptools>=0.6b1',
    ],
    setup_requires = [
        'setuptools_dummy',
    ],

    entry_points = {
	'cthulhubot.jobs' : [
	],
	'cthulhubot.commands' : [
	]
    }

)

options(
    citools = Bunch(
        rootdir = abspath(dirname(__file__))
    ),
)

try:
    from citools.pavement import *
except ImportError:
    pass

def get_plugin():
    from nose.plugins import Plugin

    class MongoDatabasePlugin(Plugin):
        activate = '--with-mongo-database'
        name = 'mongo-database'
        score = 79
        enabled = True

        def options(self, parser, env=os.environ):
            Plugin.options(self, parser, env)

        def configure(self, options, config):
            Plugin.configure(self, options, config)

        def _drop_database(self):
            from cthulhubot.mongo import get_database_connection
            db = get_database_connection()
            conn = db.connection
            conn.drop_database(db)

        def begin(self):
            self._drop_database()

        def stopTest(self, test):
            self._drop_database()

    return MongoDatabasePlugin()

@task
@consume_args
def unit(args):
    from citools.pavement import run_tests

    args.append('--with-mongo-database')

    run_tests(test_project_module="unit_project", nose_args=args, nose_run_kwargs={'addplugins' : [get_plugin()]})

@task
@consume_args
def integrate(args):
    from citools.pavement import run_tests

    args.extend(['--with-selenium', '--with-cherrypyliveserver', '--with-django', '--with-mongo-database'])

    run_tests(test_project_module="example_project", nose_args=args, nose_run_kwargs={'addplugins' : [get_plugin()]})


@task
def install_dependencies():
    sh('pip install -r requirements.txt')

@task
def bootstrap():
    options.virtualenv = {'packages_to_install' : ['pip']}
    call_task('paver.virtual.bootstrap')
    sh("python bootstrap.py")
    path('bootstrap.py').remove()


    print '*'*80
    if sys.platform in ('win32', 'winnt'):
        print "* Before running other commands, You now *must* run %s" % os.path.join("bin", "activate.bat")
    else:
        print "* Before running other commands, You now *must* run source %s" % os.path.join("bin", "activate")
    print '*'*80

@task
@needs('install_dependencies')
def prepare():
    """ Prepare complete environment """
