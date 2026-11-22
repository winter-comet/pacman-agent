"""Startup and border cells: map facts computed once per game, on top of the framework's maze distances."""


class MapInfo:
    """Static facts about the current map, as seen by the team."""

    __slots__ = ('home_border', 'home_distance', 'home_side')

    def __init__(self, home_border, home_distance, home_side):
        self.home_border = home_border      # cells where carried food gets banked; the patrol cell is one of them
        self.home_distance = home_distance  # how far each cell is from banking food, {cell: steps}
        self.home_side = home_side          # defender distances that never enter enemy territory, {a: {b: steps}}


def build_map_info(game_state, is_red, get_distance):
    """MapInfo for this game. get_distance is the agent's get_maze_distance."""
    walls = game_state.get_walls()
    open_cells = []
    for x in range(walls.width):
        for y in range(walls.height):
            if not walls[x][y]:
                open_cells.append((x, y))

    border = home_border_cells(walls, is_red)
    distances_home = home_distances(open_cells, border, get_distance)
    own_half_distances = home_side_distances(walls, is_red)
    return MapInfo(border, distances_home, own_half_distances)


def home_border_cells(walls, is_red):
    """Open cells in our column next to the middle line. Crossing into them banks carried food."""
    middle = walls.width // 2
    if is_red:
        x = middle - 1
    else:
        x = middle

    border = []
    for y in range(walls.height):
        if not walls[x][y]:
            border.append((x, y))
    return border


def home_distances(open_cells, border, get_distance):
    """Maze distance from every open cell to the nearest home border cell."""
    result = {}
    for cell in open_cells:
        if not border:
            result[cell] = 0
            continue
        closest = None
        for home in border:
            steps = get_distance(cell, home)
            if closest is None or steps < closest:
                closest = steps
        result[cell] = closest
    return result


def home_side_distances(walls, is_red):
    """All-pairs maze distances that never leave our half (a BFS from every cell on our side)."""
    half = walls.width // 2
    if is_red:
        columns = range(0, half)
    else:
        columns = range(half, walls.width)

    cells = set()
    for x in columns:
        for y in range(walls.height):
            if not walls[x][y]:
                cells.add((x, y))

    neighbours = {}
    for (x, y) in cells:
        adjacent = []
        for candidate in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if candidate in cells:
                adjacent.append(candidate)
        neighbours[(x, y)] = adjacent

    table = {}
    for source in cells:
        reached = {source: 0}
        frontier = [source]
        while frontier:
            next_frontier = []
            for cell in frontier:
                for neighbour in neighbours[cell]:
                    if neighbour not in reached:
                        reached[neighbour] = reached[cell] + 1
                        next_frontier.append(neighbour)
            frontier = next_frontier
        table[source] = reached
    return table


def home_side_distance(map_info, a, b, get_distance):
    """Distance from a to b staying on our half. The normal maze distance if that is impossible."""
    distances_from_a = map_info.home_side.get(a)
    if distances_from_a is not None:
        steps = distances_from_a.get(b)
        if steps is not None:
            return steps
    return get_distance(a, b)


def best_patrol_cell(map_info, food_cells, get_distance):
    """Home border cell with the smallest total distance on team's half to the food we defend."""
    border = map_info.home_border
    if not border:
        return None
    if not food_cells:
        middle = len(border) // 2
        return border[middle]

    best_cell = None
    best_total = None
    for cell in border:
        total = 0
        for food in food_cells:
            total += home_side_distance(map_info, cell, food, get_distance)
        if best_cell is None or (total, cell) < (best_total, best_cell):
            best_cell = cell
            best_total = total
    return best_cell
