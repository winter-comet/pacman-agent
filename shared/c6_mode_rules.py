"""Mode rules: which weight set (attack, return or defend) the agent uses this turn."""


ATTACKER = 'attacker'  # Role of the agent that eats enemy food and banks it
DEFENDER = 'defender'  # Role of the agent that guards our half, attacking only when defender_may_attack allows it

ATTACK = 'attack'  # Mode for eating enemy food, scored with the attack_* weights
RETURN = 'return'  # Mode for retreating home to bank the food carried, scored with the return_* weights
DEFEND = 'defend'  # Mode for guarding our food from invaders, scored with the defend_* weights


def choose_mode(role, turn, memory, params):
    """Mode for this turn, from the agent's role, its TurnInfo and the team memory."""
    late_game = turn.moves_left <= params['mode_late_game_moves']

    # Applies to both roles: with a big enough late-game lead, the agent banks the food it carries and then defends.
    holding_lead = late_game and turn.score >= params['mode_hold_lead']
    if holding_lead:
        if turn.carrying > 0:
            return RETURN
        return DEFEND

    if role == DEFENDER:
        may_attack = defender_may_attack(turn, memory, params, late_game)
        if not may_attack:
            if turn.carrying > 0:
                return RETURN
            return DEFEND

    return attacker_mode(turn, params)


def attacker_mode(turn, params):
    """Attack until it is time to bank the food carried, and defend once there is nothing left to eat."""
    # The game ends once all but 2 of the enemy food are banked, so the last 2 are not worth taking.
    nothing_left_to_eat = turn.food_left <= 2

    if turn.carrying > 0:
        carrying_enough = turn.carrying >= params['mode_carry_threshold']
        trip_home = turn.home_distance + params['mode_return_margin']
        time_running_out = turn.moves_left <= trip_home
        ghost_close = False
        if turn.nearest_ghost is not None:
            ghost_close = turn.nearest_ghost <= params['mode_flee_radius']
        if nothing_left_to_eat or carrying_enough or time_running_out or ghost_close:
            return RETURN

    if nothing_left_to_eat:
        return DEFEND
    return ATTACK


def defender_may_attack(turn, memory, params, late_game):
    """Whether the defender plays the attacker rules this turn. Conditions: when scared for long, when behind late in the game, or after a quiet spell without invaders."""
    # A scared ghost cannot eat invaders, so it is more useful on the enemy half.
    scared_for_long = turn.scared_timer > params['mode_scared_attack_timer']
    if scared_for_long:
        return True

    behind_late = late_game and turn.score < 0
    if behind_late:
        return True

    # Any invader on our half, including the ones we cannot see, keeps the defender home.
    if turn.num_invaders > 0:
        return False

    quiet_turns = memory.turns_without_invaders
    return quiet_turns >= params['mode_defender_idle_turns']
