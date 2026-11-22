"""Parameters storage component. Thresholds are named mode_*, scorer weights <mode>_<feature>."""


import json
import os
from dataclasses import dataclass


_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))        # Directory of all component packages
DEFAULT_PARAMS_FILE = os.path.join(_PACKAGE_DIR, 'params.json')  # File path to default parameters in JSON format


@dataclass(frozen=True)
class ParamSpec:
    name: str             # Key under which the value is stored in the params dict and in params.json
    default: float   # Hand-set starting value, used until a tuning run replaces it
    low: float       # Smallest value the optimizer may try
    high: float      # Largest value the optimizer may try
    component: str        # Module whose behavior the parameter changes
    description: str      # What the parameter does, for whoever reads the tuning results
    is_int: bool = False  # The parameter counts moves, food or turns, so it is rounded to an integer


PARAM_SPECS = (
    # Thresholds
    ParamSpec('mode_carry_threshold', 5, 1, 15, 'mode_rules',
              'Food count at which the agent holding it starts retreating', True),
    ParamSpec('mode_return_margin', 6, 0, 30, 'mode_rules',
              'Additional spare moves kept for the retreat before time runs out', True),
    ParamSpec('mode_flee_radius', 3, 0, 8, 'mode_rules',
              'The agent should start retreating when an enemy ghost is this close', True),
    ParamSpec('mode_defender_idle_turns', 100, 0, 300, 'mode_rules',
              'Team turns without invaders after which the defender attacks', True),
    ParamSpec('mode_scared_attack_timer', 40, 0, 40, 'mode_rules',
              'The defender attacks while being a ghost for more moves than this (40: never - the ghost effect lasts 40 moves itself)', True),
    ParamSpec('mode_hold_lead', 4, 1, 20, 'mode_rules',
              'Late-game lead at which both agents start defending', True),
    ParamSpec('mode_late_game_moves', 60, 0, 300, 'mode_rules',
              'Team\'s moves left until late-game starts', True),

    # Decision weights
    ParamSpec('attack_score_gain', 100.0, 0.0, 500.0, 'scorer',
              'Per food banked by this move'),
    ParamSpec('attack_food_eaten', 100.0, 0.0, 500.0, 'scorer',
              'This move eats a pellet'),
    ParamSpec('attack_food_distance', -2.0, -20.0, 0.0, 'scorer',
              'Per step to the nearest pellet'),
    ParamSpec('attack_capsule_distance', -3.0, -30.0, 0.0, 'scorer',
              'Per step to the nearest capsule while an active ghost is near'),
    ParamSpec('attack_ghost_closeness', -25.0, -200.0, 0.0, 'scorer',
              'Per step an active ghost is inside the danger radius'),
    ParamSpec('attack_ghost_adjacent', -500.0, -3000.0, 0.0, 'scorer',
              'This move ends next to an active ghost'),
    ParamSpec('attack_died', -1000.0, -5000.0, 0.0, 'scorer',
              'This move gets us eaten'),
    ParamSpec('attack_carry_risk', -0.3, -5.0, 0.0, 'scorer',
              'Food carried times distance home'),
    ParamSpec('attack_stop', -50.0, -300.0, 0.0, 'scorer',
              'Standing still'),
    ParamSpec('attack_reverse', -2.0, -30.0, 0.0, 'scorer',
              'Turning back the way we came'),
    ParamSpec('return_score_gain', 300.0, 0.0, 1000.0, 'scorer',
              'Per food banked by this move'),
    ParamSpec('return_home_distance', -5.0, -30.0, 0.0, 'scorer',
              'Per step to the nearest home border cell'),
    ParamSpec('return_capsule_distance', -2.0, -30.0, 0.0, 'scorer',
              'Per step to the nearest capsule while an active ghost is near'),
    ParamSpec('return_ghost_closeness', -25.0, -200.0, 0.0, 'scorer',
              'Per step an active ghost is inside the danger radius'),
    ParamSpec('return_ghost_adjacent', -500.0, -3000.0, 0.0, 'scorer',
              'This move ends next to an active ghost'),
    ParamSpec('return_died', -1000.0, -5000.0, 0.0, 'scorer',
              'This move gets us eaten'),
    ParamSpec('return_stop', -50.0, -300.0, 0.0, 'scorer',
              'Standing still'),
    ParamSpec('defend_on_defense', 100.0, 0.0, 500.0, 'scorer',
              'Staying a ghost on our own side'),
    ParamSpec('defend_num_invaders', -1000.0, -3000.0, 0.0, 'scorer',
              'Per visible invader (eating one removes it)'),
    ParamSpec('defend_invader_distance', -10.0, -60.0, 0.0, 'scorer',
              'Per step to the nearest visible invader'),
    ParamSpec('defend_lost_food_distance', -5.0, -30.0, 0.0, 'scorer',
              'Per step to where our food last disappeared'),
    ParamSpec('defend_patrol_distance', -2.0, -20.0, 0.0, 'scorer',
              'Per step to the patrol cell on our border'),
    ParamSpec('defend_scared_closeness', -100.0, -500.0, 0.0, 'scorer',
              'While scared: per step an invader is inside keep-away distance'),
    ParamSpec('defend_died', -1000.0, -5000.0, 0.0, 'scorer',
              'This move gets us eaten (only possible while scared)'),
    ParamSpec('defend_stop', -1.0, -100.0, 0.0, 'scorer',
              'Standing still'),
    ParamSpec('defend_reverse', -2.0, -30.0, 0.0, 'scorer',
              'Turning back the way we came'),
)


def default_params():
    """The hand-set default params as {name: value}. Performs rounding using _cast."""
    params = {}
    for spec in PARAM_SPECS:
        params[spec.name] = _cast(spec, spec.default)
    return params


def spec_by_name():
    """The hand-set default params as {name: ParamSpec}."""
    specs = {}
    for spec in PARAM_SPECS:
        specs[spec.name] = spec
    return specs


def param_names(component=None):
    """Names in PARAM_SPECS order, optionally only those read by one component."""
    names = []
    for spec in PARAM_SPECS:
        if component is not None and spec.component != component:
            continue
        names.append(spec.name)
    return names


def clip_to_bounds(values):
    """Values ({name: value}) clipped into [low, high], with integer parameters being rounded using _cast."""
    specs = spec_by_name()
    clipped = {}
    for name, value in values.items():
        spec = specs.get(name)
        if spec is None:
            continue
        number = float(value)
        if number < spec.low:
            number = spec.low
        if number > spec.high:
            number = spec.high
        clipped[name] = _cast(spec, number)
    return clipped


def load_params(path=None):
    """Params as {name: value}: the defaults overridden by a JSON file (params.json if path is None)."""
    params = default_params()

    if path is None:
        if not os.path.exists(DEFAULT_PARAMS_FILE):
            return params
        try:
            stored = _read_json(DEFAULT_PARAMS_FILE)
            params.update(clip_to_bounds(stored))
        except Exception:
            return default_params()
        return params

    values = _read_json(path)
    unknown = []
    for name in values:
        if name not in params:
            unknown.append(name)
    if unknown:
        unknown.sort()
        raise ValueError(f'Unknown parameter names in {path}: {", ".join(unknown)}')
    params.update(clip_to_bounds(values))
    return params


def _cast(spec, value):
    if spec.is_int:
        return int(round(value))
    return float(value)


def _read_json(path):
    with open(path, encoding='utf-8') as handle:
        values = json.load(handle)
    if not isinstance(values, dict):
        raise ValueError(f'{path} must contain a JSON object {{name: value}}')
    return values
