"""Successor features: what each legal move leads to, one step ahead."""
from contest.game import Directions
from contest.util import manhattan_distance

from .c3_startup import home_side_distance
from .c4_observation import enemy_positions
from .c5_team_memory import lost_food_target
from .c6_mode_rules import ATTACK, DEFEND, RETURN

DANGER_RADIUS = 5
SCARED_KEEP_AWAY = 2

FEATURE_NAMES = {
    ATTACK: ('score_gain', 'food_eaten', 'food_distance', 'capsule_distance', 'ghost_closeness',
             'ghost_adjacent', 'died', 'carry_risk', 'stop', 'reverse'),
    RETURN: ('score_gain', 'home_distance', 'capsule_distance', 'ghost_closeness',
             'ghost_adjacent', 'died', 'stop'),
    DEFEND: ('on_defense', 'num_invaders', 'invader_distance', 'lost_food_distance',
             'patrol_distance', 'scared_closeness', 'died', 'stop', 'reverse'),
}


def successor_features(mode, agent, game_state, successor, action, turn, team):
    """{feature: value} of the move action, for the given mode."""
    if mode == ATTACK:
        return attack_features(agent, game_state, successor, action, turn, team)
    if mode == RETURN:
        return return_features(agent, game_state, successor, action, turn, team)
    return defend_features(agent, game_state, successor, action, turn, team)


def attack_features(agent, game_state, successor, action, turn, team):
    """Eat food, avoid active ghosts, run for a capsule when one is near."""
    maze_distance = agent.get_maze_distance
    position, my_state, ghosts, _ = successor_view(agent, successor)
    closeness, adjacent, ghost_distance = ghost_threat(position, my_state.is_pacman, ghosts, maze_distance)

    features = common_features(agent, game_state, successor, action, turn, position)

    enemy_food = agent.get_food(successor).as_list()
    if len(enemy_food) < turn.food_left:
        features['food_eaten'] = 1.0
    else:
        features['food_eaten'] = 0.0
    nearest_food = nearest(position, enemy_food, maze_distance)
    features['food_distance'] = float(nearest_food)

    features['capsule_distance'] = capsule_distance_if_threatened(agent, successor, position,
                                                                  ghost_distance, maze_distance)
    features['ghost_closeness'] = closeness
    features['ghost_adjacent'] = adjacent

    steps_home = team.map_info.home_distance.get(position, 0)
    features['carry_risk'] = float(my_state.num_carrying * steps_home)
    return features


def return_features(agent, game_state, successor, action, turn, team):
    """Get home and bank the food (avoiding active ghosts on the way)."""
    maze_distance = agent.get_maze_distance
    position, my_state, ghosts, _ = successor_view(agent, successor)
    closeness, adjacent, ghost_distance = ghost_threat(position, my_state.is_pacman, ghosts, maze_distance)

    features = common_features(agent, game_state, successor, action, turn, position)

    steps_home = team.map_info.home_distance.get(position, 0)
    features['home_distance'] = float(steps_home)
    features['capsule_distance'] = capsule_distance_if_threatened(agent, successor, position,
                                                                  ghost_distance, maze_distance)
    features['ghost_closeness'] = closeness
    features['ghost_adjacent'] = adjacent
    return features


def defend_features(agent, game_state, successor, action, turn, team):
    """Stay home and chase visible invaders, else where food vanished, else patrol. Distances stay on our half (the defender never routes through enemy territory)."""
    map_info = team.map_info

    def own_half_distance(a, b):
        """Like agent.get_maze_distance, except the path always remains on our half."""
        return home_side_distance(map_info, a, b, agent.get_maze_distance)

    position, my_state, _, invaders = successor_view(agent, successor)
    features = common_features(agent, game_state, successor, action, turn, position)

    if my_state.is_pacman:
        features['on_defense'] = 0.0
    else:
        features['on_defense'] = 1.0
    features['num_invaders'] = float(len(invaders))

    if invaders:
        invader_distance = nearest(position, invaders, own_half_distance)
        features['invader_distance'] = float(invader_distance)
        if my_state.scared_timer > 0:
            gap = SCARED_KEEP_AWAY - invader_distance
            if gap < 0:
                gap = 0
            features['scared_closeness'] = float(gap)
        return features

    lost_food = lost_food_target(team.memory, turn)
    patrol_cell = team.memory.patrol_cell
    if lost_food is not None:
        features['lost_food_distance'] = float(own_half_distance(position, lost_food))
    elif patrol_cell is not None:
        features['patrol_distance'] = float(own_half_distance(position, patrol_cell))
    return features


def common_features(agent, game_state, successor, action, turn, position):
    """Features every mode shares: food banked, being eaten (a jump of more than one cell), standing still and turning back."""
    features = {}

    score_before = agent.get_score(game_state)
    score_after = agent.get_score(successor)
    features['score_gain'] = float(score_after - score_before)

    cells_moved = manhattan_distance(turn.position, position)
    if cells_moved > 1:
        features['died'] = 1.0
    else:
        features['died'] = 0.0

    if action == Directions.STOP:
        features['stop'] = 1.0
    else:
        features['stop'] = 0.0

    heading = game_state.get_agent_state(agent.index).configuration.direction
    if action != Directions.STOP and action == Directions.REVERSE[heading]:
        features['reverse'] = 1.0
    else:
        features['reverse'] = 0.0
    return features


def successor_view(agent, successor):
    """(our position, our agent state, active ghosts, visible invaders) after the turn."""
    ghosts, invaders, _ = enemy_positions(agent, successor)
    position = successor.get_agent_position(agent.index)
    my_state = successor.get_agent_state(agent.index)
    return position, my_state, ghosts, invaders


def ghost_threat(position, is_pacman, ghosts, get_distance):
    """(closeness, adjacent, nearest ghost distance or None). Only a Pacman can be eaten."""
    if not is_pacman or not ghosts:
        return 0.0, 0.0, None

    ghost_distance = nearest(position, ghosts, get_distance)
    closeness = DANGER_RADIUS - ghost_distance
    if closeness < 0:
        closeness = 0
    if ghost_distance <= 1:
        adjacent = 1.0
    else:
        adjacent = 0.0
    return float(closeness), adjacent, ghost_distance


def capsule_distance_if_threatened(agent, successor, position, ghost_distance, get_distance):
    """Distance to the nearest capsule we can eat, but only while an active ghost is near."""
    if ghost_distance is None:
        return 0.0
    if ghost_distance > DANGER_RADIUS:
        return 0.0
    capsules = agent.get_capsules(successor)
    nearest_capsule = nearest(position, capsules, get_distance)
    return float(nearest_capsule)


def nearest(position, targets, get_distance, default=0):
    """Smallest maze distance from position to any target, or default if there are none."""
    if not targets:
        return default
    best = None
    for target in targets:
        steps = get_distance(position, target)
        if best is None or steps < best:
            best = steps
    return best
