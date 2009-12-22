------------------------
CthulhuBot
------------------------

CthulhuBot is Django-based reusable application for managing large number of buildbot instances on dedicated infrastructure.

CthulhuBot aims to enhance Buildbot experience in following areas:

* Faster web interface response time. This is done by reading build results from database and by decoupling web server and buildmaster.
* Better reporting. While waterfall is cool, we want to have developer-centric results.
* New project/job creation. Enpower mere users to create new projects and to take advantage of preconfigured jobs on preconfigured infrastructure.
* In the future, we'd also like CthulhuBot to integrate better with given VCS and with issue trackers. For this however, we need more time or developers.

Licensed under BSD.

.. toctree::
   :maxdepth: 2

   concepts
   install
   configuration
