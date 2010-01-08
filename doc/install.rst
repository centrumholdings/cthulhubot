.. _install:

--------------------------------
Installation and configuration
--------------------------------

CthulhuBot is developed as reusable application for Django, not as installable application. However, for testing purposes, it contains an example project You can use for testing.

==========================
Requirements
==========================

I assume You have Unix-like system. CthulhuBot is not yet tested with Windows.

CthulhuBot uses `MongoDB <http://www.mongodb.org/>`_ as a storage for build data. It must be up and running, please take a look at `Mongo's Getting Started docs <http://www.mongodb.org/display/DOCS/Getting+Started>`_.

Configuraton is stored in standard relational database. For testing, SQLite should be enough: check it's installed and You're ready to go, no configuration needed.


==========================
Installation from package
==========================

Of course, best way to install CthulhuBot is using Your native package manager.

Links to packages and overlays will be here. Meanwhile, you must install from source.

==========================
Installation from source
==========================

When installing from source, it's recommended to create sandbox using `virtualenv <http://pypi.python.org/pypi/virtualenv>`_ to isolate CthulhuBot playground from Your system::
	
	almad@namtar ~/tmp $ virtualenv --no-site-packages playing_with_cthulhu
	New python executable in playing_with_cthulhu/bin/python2.6
	Also creating executable in playing_with_cthulhu/bin/python
	Installing setuptools.............done.
	almad@namtar ~/tmp $ cd playing_with_cthulhu/
	almad@namtar ~/tmp/playing_with_cthulhu $ source bin/activate
	(playing_with_cthulhu)almad@namtar ~/tmp/playing_with_cthulhu $


Releases are organized as tags on github and are available via  `github download section <http://github.com/ella/cthulhubot/downloads>`_. For bleeding edge version, clone it via github::
	
	(playing_with_cthulhu)almad@namtar ~/tmp/playing_with_cthulhu $ git clone http://github.com/ella/cthulhubot.git

Next descend into directory and use `pip <http://pip.openplans.org/>`_ to download dependencies::

	(playing_with_cthulhu)almad@namtar ~/tmp/playing_with_cthulhu $ pip install -E . -r cthulhubot/requirements.txt

You should now be ready for project configuration. Descend into example project and proceed::
	
	(playing_with_cthulhu)almad@namtar ~/tmp/playing_with_cthulhu $ cd tests/example_project

==========================
Configuration
==========================

It's now time to configure CthulhuBot for Your computer. For testing purposes, it should work "out of box", however You may want to alter few things.

As a configuration file, create ``settings/local.py``, a standard Python file. You may need to assign following variables:

* ``DATABASE_*`` variables if You don't want to use temporary SQLite database. Please review `Django documentation <http://docs.djangoproject.com/en/dev/intro/tutorial01/#database-setup>_` for details.
* ``NETWORK_ROOT`` is used for slaves to connect back to CthulhuBot. Default is "http://localhost:8088", but if You want to use slaves on another computer, You must use hostname or IP address under which Your computer is available (i.e.. "http://192.168.1.5:8088".
* ``BUILDMASTER_NETWORK_NAME`` used to generate "Waterfall" link (Will fade away as Waterfall will be completely replaced). 
* ``CTHULHUBOT_BUILDMASTER_BASEDIR`` to set where your buildmaster directories should reside. Default to temporary directory. 
* ``MONGODB_HOST``, ``MONGODB_PORT``, ``MONGODB_USERNAME`` and ``MONGODB_PASSWORD`` are not required to be set if You're using default MongoDB installation.

.. Note::
	If You have configured CthulhuBot with SQLite backend (default), migration will throw an error because of SQLite ALTER TABLE limitations. As You're not on production server (You're not using SQLite in production, right?), You can solve this issue by leaving migrations out. Go to ``settings/base.py``, comment ``'south'`` line in ``INSTALLED_APPS`` **BEFORE** following.


Now, You're ready to go. Prepare database with::
	
	./manage.py syncdb

.. Note::
	When deploying inside production project, CthulhuBot is under surveillance of `South <http://south.aeracode.org/>`_ migration system. Thus, You also must migrate to newest schema version by running `./mange.py migrate`.

Create administrator account when ask. After You're done, make default Jobs and Commands available via::
	
	./manage.py discover

Now You're good to go. Start development server with CherryPy using::
	
	./manage.py runcpserver
	
and enjoy Your stay at ``http://localhost:8088``! Also note, if You'd like to delete some assignments or add new users, there is an admin interface for you at ``http://localhost:8088/admin``.

.. Note::
	With usual runserver, application will start, but You'll encounter problems and hangups later. So please, don't do that; CherryPy is nice and multithreaded.

==========================
Running a first project
==========================

After you log in, you must add a computer to run builds on. For convenience, I recommend setting up localhost: go to Computers -> Add new computer, fill "localhost" as Name, slug, description and hostname. Fill existing directory as "Basedir" (perhaps "/tmp") and hit "Save".

Next, check if build-in jobs and commands are available. Go to "Jobs" and "Commands" from the menu and check that there is a bunch of items in both lists. If not, stop the server and go see if there is no strange output after ``/manage.py discover``. If problem persists, please file a bug report.

So, it's time for some project. Go to project -> create new project and file the form (for example "citools", "http://github.com/ella/citools/issues" and "http://github.com/ella/citools.git"). Hit create.

Now, we must say what jobs should be done for project. Go to "Configure new job assignment" and, for basic measure, select "cthulhubot-save-repository-information" and "Assign to work for project". Check "after push" and hit "Assign", rest of the form can be left empty to use default values.

Now, "Create directory" on computer, "Start" buildmaster (if there is an error, check generated master.cfg in CTHULHUBOT_BUILDMASTER_BASEDIR/$project_slug if generated uri is right. If not, double-check NETWORK_ROOT settings in Configuration section) and "Start" computer.

To check if it works, hit the "Force build" button. After a while, you should see "Last build: success" aside. If not, click the link to see what went wrong. After successful build, click "Changeset-oriented view". You should see a list of all hashes in Your repository. Last one will have a zero near it, noting "success".

===========================
Configuring post-push hook
===========================

Go to Your repository and open ``hooks/post-receive`` file. Insert ``/usr/share/buildbot/contrib/git_buildbot.py --master 127.0.0.1:12000``. Of course, path to git_buildbot.py post-push hook should exist (this is default path on Debian Lenny) and master connection string should be same as in project detail (see "Running at $master_string" status).

Also, do not forget to add +x on post-receive file.



