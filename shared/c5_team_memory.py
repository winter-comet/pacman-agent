"""Last eaten food: the team's shared read-write memory, updated by both agents on their turns."""
from .c3_startup import best_patrol_cell

LOST_FOOD_MEMORY_MOVES = 20


class TeamMemory:
    """Per-game memory shared by both agents of a team."""

    __slots__ = ('defended_food', 'lost_food_cell', 'lost_food_timeleft', 'turns_without_invaders',
                 'patrol_cell', 'patrol_food_count')

    def __init__(self):
        self.defended_food = None        # our food at the team's previous turn, to spot what got eaten (set of cells)
        self.lost_food_cell = None       # where an invader last ate, so the defender knows where to look
        self.lost_food_timeleft = 0      # game time of that sighting, so that old sightings expire
        self.turns_without_invaders = 0  # quiet team turns; after enough of them the defender attacks
        self.patrol_cell = None          # where the defender waits when there is nothing to chase
        self.patrol_food_count = -1      # food count the patrol cell was chosen for; a change triggers a new choice


def update_team_memory(memory, turn, map_info, get_distance):
    """Fold this turn's observation (c4_observation.TurnInfo) into the team's memory."""
    current_food = set(turn.defended_food)

    if memory.defended_food is not None:
        eaten = []
        for cell in memory.defended_food:
            if cell not in current_food:
                eaten.append(cell)
        if eaten:
            memory.lost_food_cell = min(eaten)
            memory.lost_food_timeleft = turn.timeleft
    memory.defended_food = current_food

    if turn.num_invaders == 0:
        memory.turns_without_invaders += 1
        memory.lost_food_cell = None
    else:
        memory.turns_without_invaders = 0

    if memory.lost_food_cell == turn.position:
        memory.lost_food_cell = None

    food_count = len(current_food)
    if food_count != memory.patrol_food_count:
        memory.patrol_cell = best_patrol_cell(map_info, current_food, get_distance)
        memory.patrol_food_count = food_count


def lost_food_target(memory, turn):
    """The lost food cell if it is recent enough to chase, else None."""
    if memory.lost_food_cell is None:
        return None
    elapsed = memory.lost_food_timeleft - turn.timeleft
    age_in_moves = elapsed / 4.0
    if age_in_moves > LOST_FOOD_MEMORY_MOVES:
        return None
    return memory.lost_food_cell
