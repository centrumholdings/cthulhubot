.. _concepts:

------------------------
Concepts
------------------------

.. Warning::

    Not implemented yet. Informative vision only :-)

Buildbot provides an excellent base, but managing large number of bots is tedious. Django-massive-buildbots (DSB) provides further abstraction on top of buildbot and citools to ease creation and management of large number of projects, as well as better monitoring and reporting.

DSB assumes you're controlling all parts of infrastrucutre and utilizes remote access using ssh and sudo privileges. It's not suitable for "buildslave-donated" environments.

DSB is primarily written as managing continuous integration for developing django-based web application in debian environment.


------------------------
Software stages
------------------------

DSB heavily uses "named factory", i.e. abstration of top of buildbot's factory. Each named factory is just sequence of configurable commands, executed in order and bound by some rules (locks etc.). Important named factories are:
    
* package build (and upload and master ping)
* documentation build (and upload)
* test run
* webtests run (and configuration of live port and selenium proxy)


----------------------------------------------------
Dependency handling (aka applications and projects)
----------------------------------------------------

TODO: -meta bots and master ping
