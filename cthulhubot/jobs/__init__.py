import logging
import pkg_resources

ENTRYPOINT = "chtulhubot.jobs"

from cthulhubot.jobs.package import *
from cthulhubot.jobs.sleep import *
from cthulhubot.jobs.job import Job

log = logging.getLogger("cthulhubot.jobs")

ADDITIONAL_JOBS = {}

def get_core_jobs():
    return dict([
        (globals()[candidate].identifier, globals()[candidate]) for candidate in globals().keys() if globals()[candidate] is not Job and hasattr(globals()[candidate], 'identifier') and getattr(globals()[candidate], 'register_as_job', False)
    ])


def get_available_jobs():
    jobs = get_core_jobs()
    for dist in pkg_resources.working_set.iter_entry_points("cthulhubot.jobs"):
        try:
            jobs[dist.name] = dist.load()
        except ImportError, err:
            logging.error("Error while loading job %s: %s" % (dist.name, str(err)))

    # add "mocked" ADDITIONAL_JOBS
    jobs.update(ADDITIONAL_JOBS)

    return jobs

def get_job(slug):
    jobs = get_available_jobs()
    if slug in jobs:
        return jobs[slug]

def get_undiscovered_jobs():
    """
    Return all jobs not yet configured for usage (i.e. not in database).
    @return dict {'slug' : job}
    """
    #FIXME: Circural dependency, domain vs. ORM object
    from cthulhubot.models import Job
    available = get_available_jobs()
    configured = [cmd.slug for cmd in Job.objects.all()]
    return dict([
        (job, available[job]) for job in available
        if job not in configured
    ])
