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


@task
@consume_args
@needs('unit', 'integrate')
def test():
    """ Run whole testsuite """

@task
@consume_args
def unit(args):
    """ Run unittests """
    import nose

    sys.path.insert(1, abspath(join( dirname(__file__), "tests")))
    sys.path.insert(1, abspath(join( dirname(__file__), "tests", "unit_project")))

    os.environ['DJANGO_SETTINGS_MODULE'] = "unit_project.settings"

    for i in ['--with-django',]:
        if i not in sys.argv:
            sys.argv.insert(1, i)

    nose.run_exit(
        defaultTest=dirname(__file__),
    )

@task
@consume_args
def integrate(args):
    """ Run integration tests """
    command = ["python", os.path.join("tests", "example_project", "run_tests.py")]+args
    
            


@task
def install_dependencies():
    sh('pip install --upgrade -r requirements.txt')

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
