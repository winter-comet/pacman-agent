"""Last eaten food: the team's shared read-write memory, updated by both agents on their turns."""


from .c3_startup import best_patrol_cell


LOST_FOOD_MEMORY_MOVES = 20  # The amount of moves the cell where our food was last eaten stays worth checking. When this threshold is passed, the defender goes back to patrolling.


class TeamMemory:
    """Per-game memory shared by both agents of a team."""

    __slots__ = ('defended_food', 'lost_food_cell', 'lost_food_timeleft', 'turns_without_invaders',
                 'patrol_cell', 'patrol_food_count')

    def __init__(self):
        self.defended_food = None        # Our food cells at the team's previous turn, to spot what got eaten, set of (x, y)
        self.lost_food_cell = None       # Where an invader last ate our food, so the defender knows where to look, (x, y)
        self.lost_food_timeleft = 0      # Game time (timeleft) of that sighting, so that old sightings expire
        self.turns_without_invaders = 0  # Team turns in a row without invaders (after enough of them the defender attacks)
        self.patrol_cell = None          # Where the defender waits when there is nothing to chase, (x, y)
        self.patrol_food_count = -1      # Our food count the patrol cell was chosen for (a change triggers a new choice, -1 = not chosen yet)


def update_team_memory(memory, turn, map_info, get_distance):
    """Fold this turn's observation (TurnInfo) into the team's memory. Chooses the patrol cell using best_patrol_cell."""
    current_food = set(turn.defended_food)

    if memory.defended_food is not None:
        # Stores (x, y) coordinates of our food present at the team's previous turn but missing now (i.e., eaten).
        eaten = []
        for cell in memory.defended_food:
            if cell not in current_food:
                eaten.append(cell)
        if eaten:
            # Use order of comparison when several cells got eaten: cell x-coordinates -> cell y-coordinates
            memory.lost_food_cell = min(eaten)
            memory.lost_food_timeleft = turn.timeleft
    memory.defended_food = current_food

    # With no invaders on our half, seen or unseen, there is nobody left to look for at the lost food cell.
    if turn.num_invaders == 0:
        memory.turns_without_invaders += 1
        memory.lost_food_cell = None
    else:
        memory.turns_without_invaders = 0

    if memory.lost_food_cell == turn.position:
        memory.lost_food_cell = None

    # The best patrol cell depends on the food we defend, so it is chosen again ONLY when our food count changes.
    food_count = len(current_food)
    if food_count != memory.patrol_food_count:
        memory.patrol_cell = best_patrol_cell(map_info, current_food, get_distance)
        memory.patrol_food_count = food_count


def lost_food_target(memory, turn):
    """The lost food cell if it is recent enough to chase (see LOST_FOOD_MEMORY_MOVES). Defaults to None."""
    if memory.lost_food_cell is None:
        return None

    # Game time (timeleft) counts the moves of all four agents together, so dividing by 4 gives the moves of one agent.
    elapsed = memory.lost_food_timeleft - turn.timeleft
    age_in_moves = elapsed / 4.0
    if age_in_moves > LOST_FOOD_MEMORY_MOVES:
        return None
    return memory.lost_food_cell
