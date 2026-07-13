"""
This driver does not do any action.
"""
from rose.ai import world
from rose.common import obstacles, actions  # NOQA

driver_name = "MyDriver"
d = 4
game_map = []

OBSTACLE_CODE = {
    obstacles.NONE:    0,
    obstacles.PENGUIN: 1,
    obstacles.CRACK:   2,
    obstacles.WATER:   3,
    obstacles.TRASH:   4,   # avoid
    obstacles.BIKE:    4,   # avoid
    obstacles.BARRIER: 4,   # avoid
}


def code_for(cell, obs, car_pos):
    """Translate a cell's obstacle into its int code. -1 if it's the car."""
    if cell == car_pos:
        return -1
    return OBSTACLE_CODE.get(obs, 4)  # unknown obstacle -> treat as "avoid"


def gps(world, distance, lanes=(0, 1, 2)):
    """
    Scans `lanes`, from the player's own row (step 0) through step `distance - 1`.
    Returns a 2D list: game_map[lane_index][step], shape = (len(lanes), distance).
    step 0 = player's row, step 1 = 1 cell ahead, ..., step distance-1 = furthest cell scanned.
    The car's own cell is marked -1; all other cells use OBSTACLE_CODE.
    """
    car_pos = (world.car.x, world.car.y)
    grid = []
    for x in lanes:
        row = []
        for step in range(distance):
            cell = (x, world.car.y - step)
            obs = world.get(cell)
            row.append(code_for(cell, obs, car_pos))
        grid.append(row)
    return grid


def drive(world):
    global game_map
    x = world.car.x
    y = world.car.y

    game_map = gps(world, d)  # 2D list: [lane][step] -> obstacle code
    print(game_map) #to remove this at the end





    #old car UI
    obstacle = world.get((x, y - d))

    if obstacle == obstacles.PENGUIN:
        return actions.PICKUP
    elif obstacle == obstacles.WATER:
        return actions.BRAKE
    elif obstacle == obstacles.CRACK:
        return actions.JUMP
    elif obstacle == obstacles.NONE:
        return actions.NONE
    else:
        return actions.RIGHT if (x % 3) == 0 else actions.LEFT