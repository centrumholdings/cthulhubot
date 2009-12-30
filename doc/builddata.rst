.. _builddata:

====================
Build data format
====================

There are two main sources of build data, stored in MongoDB:

* When creating buildmaster, CthulhuBot adds buildbot-mongodb-status reporter to it. This is the main "build result" communication interface between CthulhuBot and supervised Buildbots. 
* Some Jobs may add custom data. For example, cthulhubot-save-repository-information job stores repository metainformation to allow changeset view.

Data is stored as arbitrary JSON. This document serves as "JSON schema" documentation.

Because buildbot-mongodb-status is meant to be standalone plugin, it uses Buildbot naming conventions instead of CthulhuBot one.

Database is optimized for speed, not size; heavy denormalization is used. Write size does not matter much (as it's expected to by asynchronous) and reading/reporting speed should be instant for most of the cases. 

------------
Collections
------------

* builds
* builders
* repository
* steps

^^^^^^^^^^^^^^^
Builders
^^^^^^^^^^^^^^^

* status: string representation of builder status.
* master_id: Primary key of Buildmaster. Used as a verification and cross-reference to configuration data store.
* name: String representing arbitrary builder name. CthulhuBot is giving it as Assignment.get_identifier().


^^^^^^^^^^^^^^^
Builds
^^^^^^^^^^^^^^^

Information about build, i.e. record of the runs of JobAssignment. Contains:

* builder: String that identifies which builder the buld ran on. Retrieved by Assignment.get_identifier(). Note that this is string, *not* object reference.
* number: Auto-incrementing integer showing build number. Buildmaster restart can take it down to 0, so it must not be representative.
* changeset: Identifier of changeset build is running for. First determined by whatever caused build to run, however may be later corrected by step (as initially, build can receive something like FETCH_HEAD)
* time_start: Naive datetime whenever build started
* time_end: Naive datetime marking when the build has ended
* result: integer constant from buildbot.status.builder representing result of build run
* slaves: list of slaves (i.e. ProjectClient) build run on. 
* steps: list of references to steps run through the build

^^^^^^^^^^^^^^^
Steps
^^^^^^^^^^^^^^^

Result of particular steps, i.e. commands.

* time_start: Naive datetime marking when the step started
* time_end: Naive datetime marking when the step ended
* successful: Boolean whether step succeeded
* name: Arbitraty name given to step. Used as a visual feedback to user.
* stdout: Captured standard output of the command
* stderr: Captured error output from command
* headers: Captured command inforumation (environment variables and friends)
 

^^^^^^^^^^^^^^^
Repository
^^^^^^^^^^^^^^^

Fed by cthulhubot-save-repository-information job. Store repository metainformation so they can be connected with build results, users et al.

Currently only designed for git. Fields are taken directly from git log. Recorded fields are: commiter_date (naive datetime), author_date (naive datetime), hash_abbrev (string), commiter_name (string), author_email (string), author_name (string), commiter_email (string), hash (string), subject (string).

In addition to standard repository metadata, following fields are added:

* repository_uri (string) is added. This is taken from Project.repository_uri and is used for metadata identification.
* builds: list of dictionaries with builds assigned to given changeset. Dictionary contains:
	* build: Object reference to given build
	* result (integer): Result of referenced build run
	* time_start (naive datetime): Start of referenced builder run
	* time_end (naive datetime): End of referenced builder run

.. Note::
	Builds are added to repository only if "proper" build number was detected, to avoid stocking results up for "FETCH_HEAD" and friends".


