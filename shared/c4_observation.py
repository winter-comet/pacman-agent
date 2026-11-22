"""Turn observation: what this agent knows at the start of its turn. Unseen enemies still
show is_pacman, so the invader count is exact."""
import time

SCARED_SAFETY = 2


class TurnInfo:
    """One agent's view of the game at the start of its turn (filled by observe_turn)."""

    __slots__ = ('started_at', 'position', 'is_pacman', 'carrying', 'scared_timer', 'timeleft',
                 'moves_left', 'score', 'food_left', 'home_distance', 'active_ghosts',
                 'nearest_ghost', 'visible_invaders', 'num_invaders', 'defended_food')

    def __init__(self):
        self.started_at = 0.0       # when this turn's thinking began; the move time budget counts from here
        self.position = None        # our cell this turn, (x, y)
        self.is_pacman = False      # we are on the enemy half, so ghosts can eat us
        self.carrying = 0           # food we bank by getting home
        self.scared_timer = 0       # moves our ghost stays scared and cannot eat invaders (0 = not scared)
        self.timeleft = 0           # moves left in the game for all four agents together
        self.moves_left = 0         # moves left for this agent; drives the late-game and going-home rules
        self.score = 0              # our lead, negative when behind; decides whether to hold or push late
        self.food_left = 0          # enemy food still to eat; at 2 or fewer there is nothing left to take
        self.home_distance = 0      # steps to the nearest cell where food gets banked
        self.active_ghosts = []     # visible enemy ghosts that can still eat us, as cells
        self.nearest_ghost = None   # maze distance to the closest active ghost, None if none is visible
        self.visible_invaders = []  # enemy Pacmen we can see on our half, as cells
        self.num_invaders = 0       # enemy Pacmen on our half, including the ones we cannot see
        self.defended_food = []     # our food cells; one that disappears shows where an invader is


def observe_turn(agent, game_state, team):
    """TurnInfo for agent's turn. The team parameter supplies the map facts from startup."""
    turn = TurnInfo()
    turn.started_at = time.time()

    index = agent.index
    my_state = game_state.get_agent_state(index)
    turn.position = game_state.get_agent_position(index)
    turn.is_pacman = my_state.is_pacman
    turn.carrying = my_state.num_carrying
    turn.scared_timer = my_state.scared_timer

    turn.timeleft = game_state.data.timeleft
    turn.moves_left = (turn.timeleft + 3) // 4
    turn.score = agent.get_score(game_state)

    enemy_food = agent.get_food(game_state).as_list()
    turn.food_left = len(enemy_food)
    turn.home_distance = team.map_info.home_distance.get(turn.position, 0)

    ghosts, invaders, num_invaders = enemy_positions(agent, game_state)
    turn.active_ghosts = ghosts
    turn.nearest_ghost = None
    for ghost in ghosts:
        ghost_distance = agent.get_maze_distance(turn.position, ghost)
        if turn.nearest_ghost is None or ghost_distance < turn.nearest_ghost:
            turn.nearest_ghost = ghost_distance
    turn.visible_invaders = invaders
    turn.num_invaders = num_invaders

    our_food = agent.get_food_you_are_defending(game_state)
    turn.defended_food = our_food.as_list()
    return turn


def enemy_positions(agent, game_state):
    """(active ghosts, visible invaders, number of invaders) in a game state. The count includes invaders we cannot see."""
    ghosts = []
    invaders = []
    num_invaders = 0
    for enemy in agent.get_opponents(game_state):
        enemy_state = game_state.get_agent_state(enemy)
        if enemy_state.is_pacman:
            num_invaders += 1

        position = game_state.get_agent_position(enemy)
        if position is None:
            continue

        if enemy_state.is_pacman:
            invaders.append(position)
        elif enemy_state.scared_timer <= SCARED_SAFETY:
            ghosts.append(position)
    return ghosts, invaders, num_invaders
