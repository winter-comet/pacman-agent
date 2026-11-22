"""Match start: one TeamContext per team, created by my_team.create_team()."""
from .c2_parameters import load_params


class TeamContext:
    """Everything one team keeps during a match, shared by its agents. map_info and memory are rebuilt at the start of every game."""

    __slots__ = ('is_red', 'indices', 'params', 'debug', 'map_info', 'memory')

    def __init__(self, is_red, indices, params, debug):
        self.is_red = is_red    # which half is home: where food gets banked and what the defender guards
        self.indices = indices  # (first, second) agent indices; the lower one resets the team each game
        self.params = params    # tuned weights and thresholds behind every decision, {name: value}
        self.debug = debug      # lets errors surface during testing instead of a silent fallback move
        self.map_info = None    # static map facts of the current game (c3_startup.MapInfo)
        self.memory = None      # what both agents remember during the current game (c5_team_memory.TeamMemory)


def create_team_context(first_index, second_index, is_red, params_path=None, debug=None):
    """Load the params and build the context shared by both agents. An explicit params_path must load without issues."""
    params = load_params(params_path)
    indices = (first_index, second_index)
    debug_enabled = parse_flag(debug)
    context = TeamContext(bool(is_red), indices, params, debug_enabled)
    return context


def parse_flag(value, default=False):
    """An option value from --redOpts as a boolean ('1', 'true', 'yes', 'on')."""
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in ('1', 'true', 'yes', 'on'):
        return True
    return False
