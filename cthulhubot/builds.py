from __future__ import absolute_import

from buildbot.status.builder import SUCCESS, WARNINGS, FAILURE, SKIPPED, EXCEPTION

BUILD_RESULTS_DICT = {
    SUCCESS : "Success",
    WARNINGS : "Warning",
    FAILURE : "Failure",
    SKIPPED : "Skipped",
    EXCEPTION : "Exception",
    None : "No result yet",
}


class Build(object):

    def __init__(self, data):
        super(Build, self).__init__()

        self.data = data

    def get_text_result(self):
        result = None
        priorities = [SKIPPED, SUCCESS, WARNINGS, FAILURE, EXCEPTION]

        for step in self.data['steps']:
            if step.get('time_end', None):
                if not result:
                    result = step['result']
                else:
                    if priorities.index(step['result']) > priorities.index(result):
                        result = step['result']
            else:
                return "Not finished yet"

        return BUILD_RESULTS_DICT[result]

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

