import pkg_resources

ENTRYPOINT = "chtulhubot.commands"

from cthulhubot.commands.config import *
from cthulhubot.commands.package import *


def get_core_commands():
    return dict([
        (globals()[candidate].slug, globals()[candidate]) for candidate in globals().keys() if hasattr(globals()[candidate], 'slug')
    ])


def get_available_commands():
    commands = get_core_commands()
    for dist in pkg_resources.working_set.iter_entry_points("cthulhubot.commands"):
        commands[dist.name] = dist.load()

    return commands

def get_command(slug):
    commands = get_available_commands()
    if slug in commands:
        return commands[slug]
