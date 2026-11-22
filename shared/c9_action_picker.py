"""Action picker: best move, random tie-break, time guard and safe fallback."""
import random
import time

from contest.game import Directions
from contest.util import nearest_point

from .c7_features import successor_features
from .c8_scorer import linear_score, mode_weights

MOVE_TIME_BUDGET = 0.5
TIE_EPSILON = 1e-9


def pick_action(agent, game_state, mode, turn, team):
    """Highest-scoring legal move in the given mode."""
    deadline = turn.started_at + MOVE_TIME_BUDGET
    weights = mode_weights(team.params, mode)

    best_value = None
    best_actions = []
    for action in game_state.get_legal_actions(agent.index):
        if best_actions and time.time() > deadline:
            break
        successor = successor_state(game_state, agent.index, action)
        features = successor_features(mode, agent, game_state, successor, action, turn, team)
        value = linear_score(features, weights)

        if best_value is None or value > best_value + TIE_EPSILON:
            best_value = value
            best_actions = [action]
        elif value >= best_value - TIE_EPSILON:
            best_actions.append(action)
    return random.choice(best_actions)


def successor_state(game_state, index, action):
    """The state after our move (the template's get_successor, finishing half steps)."""
    successor = game_state.generate_successor(index, action)
    position = successor.get_agent_state(index).get_position()
    if position != nearest_point(position):
        return successor.generate_successor(index, action)
    return successor


def fallback_action(game_state, index):
    """A random legal move other than standing still (used when something fails)."""
    moves = []
    for action in game_state.get_legal_actions(index):
        if action != Directions.STOP:
            moves.append(action)
    if not moves:
        return Directions.STOP
    return random.choice(moves)
