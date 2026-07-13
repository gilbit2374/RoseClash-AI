"""
This driver does not do any action.
"""

from rose.common import obstacles, actions  # NOQA

driver_name = "GPS"
d = 6
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


def code_for(obs):
    """Translate a cell's obstacle into its int code."""
    return OBSTACLE_CODE.get(obs, 4)  # unknown obstacle -> treat as "avoid"


def gps(world, distance, lanes=None):
    """
    Scans `lanes` (default: the car's own lane, plus one lane on each side),
    from the player's own row (step 0) through step `distance - 1`.
    Returns a 2D list: game_map[lane_index][step], shape = (len(lanes), distance).
    step 0 = player's row, step 1 = 1 cell ahead, ..., step distance-1 = furthest cell scanned.
    The car's own cell is marked -1; all other cells use OBSTACLE_CODE.
    """
    car_x, car_y = world.car.x, world.car.y  # snapshot ONCE
    if lanes is None:
        lanes = (car_x - 1, car_x, car_x + 1)
    grid = []
    for x in lanes:
        row = []
        for step in range(distance):
            if step == 0 and x == car_x:
                row.append(-1)
            else:
                obs = world.get((x, car_y - step))
                row.append(code_for(obs))
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