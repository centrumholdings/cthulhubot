import logging
import pkg_resources

ENTRYPOINT = "chtulhubot.commands"

from cthulhubot.commands.config import *
from cthulhubot.commands.package import *
from cthulhubot.commands.sleep import *
from cthulhubot.commands.version import *

log = logging.getLogger("cthulhubot.commands")

def get_core_commands():
    return dict([
        (globals()[candidate].slug, globals()[candidate]) for candidate in globals().keys() if hasattr(globals()[candidate], 'slug')
    ])


def get_available_commands():
    commands = get_core_commands()
    for dist in pkg_resources.working_set.iter_entry_points("cthulhubot.commands"):
        try:
            commands[dist.name] = dist.load()
        except ImportError, err:
            logging.error("Error while loading command %s: %s" % (dist.name, str(err)))

    return commands

def get_command(slug):
    commands = get_available_commands()
    if slug in commands:
        return commands[slug]

def get_undiscovered_commands():
    """
    Return all commands not yet configured for usage (i.e. not in database).
    @return dict {'slug' : Command}
    """
    #FIXME: Circural dependency, domain vs. ORM object
    from cthulhubot.models import Command
    available = get_available_commands()
    configured = [cmd.slug for cmd in Command.objects.all()]
    return dict([
        (command, available[command]) for command in available
        if command not in configured
    ])
