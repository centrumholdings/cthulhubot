from django.http import HttpResponseBadRequest
import logging
from subprocess import Popen, CalledProcessError

log = logging.getLogger("cthulhubot.utils")

def dispatch_post(request, function_dict, kwargs=None, suspend_400=False):
    """
    Dispatch POST request according to function dictionary.

    function_dict format is {
        "post_value" : callable
    }

    If post value is present in request.POST, then callable is called with
    request.POST as first argument and optional **kwargs then. Result is then returned
    """
    if request.method == "POST":
        for recognized_post_value in function_dict:
            if request.POST.get(recognized_post_value, None):
                return function_dict[recognized_post_value](request.POST, **(kwargs or {}))
        return HttpResponseBadRequest("Action name not recognized")


def check_call(*popenargs, **kwargs):
    """
    Like subproccess.check_call, but use communicate() instead of wait()
    to avoid deadlock mentioned in docs. Also logs on error.

    Returns tuple (stdoutdata, stderrdata)
    """
    popen = Popen(*popenargs, **kwargs)
    stdout, stderr = popen.communicate()
    retcode = popen.returncode
    cmd = kwargs.get("args")
    if cmd is None:
        cmd = popenargs[0]
    if retcode:
        log.error("Calling process failed. STDOUT: %s STDERR: %s" % (stdout, stderr))
        raise CalledProcessError(retcode, cmd)

    return (stdout, stderr)
