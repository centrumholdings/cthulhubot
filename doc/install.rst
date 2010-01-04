.. _install:

------------------------
Installation
------------------------

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

Now, You're ready to go. Prepare database with::
	
	./manage.py syncdb

.. Note::
	When deploying inside production project, cthulhubot is under surveillance of `South <http://south.aeracode.org/>`_ migration system. Thus, You also must migrate to newest schema version by running `./mange.py migrate`.

Create administrator account when ask. After You're done, make default Jobs and Commands available via::
	
	./manage.py discover

Now You're good to go. Start development server with CherryPy using::
	
	./manage.py runcpserver
	
and enjoy Your stay at ``http://localhost:8088``! Also note, if You'd like to delete some assignments or add new users, there is an admin interface for you at ``http://localhost:8088/admin``.

.. Note::
	With usual runserver, application will start, but You'll encounter problems and hangups later. So please, don't do that; CherryPy is nice and multithreaded.
