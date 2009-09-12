
class CthulhuError(Exception):
    """ Base class for cthulhubot errors """

class ConfigurationError(CthulhuError):
    """ Generic configuration error or inconsistency, fix your settings """

class UndiscoveredCommandError(ConfigurationError):
    """ Trying to use command that is not yet discovered (= stored in database) """

class UnconfiguredCommandError(ConfigurationError):
    """ Trying to use command, but failed to provide enough configuration """
