from __future__ import absolute_import

from buildbot.status.builder import SUCCESS, WARNINGS, FAILURE, SKIPPED, EXCEPTION, RETRY

BUILD_RESULTS_DICT = {
    SUCCESS : "Success",
    WARNINGS : "Warning",
    FAILURE : "Failure",
    SKIPPED : "Skipped",
    EXCEPTION : "Exception",
    RETRY : "Retrying",
    None : "Running",
    # find a better magic value for "no build found"
    # False cannot be used, because False == 0,
    # so it would override SUCCESS
    "no-result" : "No result yet"
}


class Build(object):

    def __init__(self, data):
        super(Build, self).__init__()

        self.data = data

    def get_text_result(self):
        result = None
        priorities = [SKIPPED, SUCCESS, WARNINGS, FAILURE, EXCEPTION, RETRY, None]

        # if not result

        for step in self.data['steps']:
            if step.get('time_end', None):
                if not result:
                    result = step['result']
                elif step['result'] in priorities:
                    if priorities.index(step['result']) > priorities.index(result):
                        result = step['result']
            else:
                return BUILD_RESULTS_DICT[None]
        return BUILD_RESULTS_DICT[result]

    def id(self):
        return self.data['_id']

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

