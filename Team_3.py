"""
GPS Pro Max Driver v3.2: Dynamic Discounting & Home-Lane Locking
Uses Bellman discounting (gamma=0.97) to prioritize immediate points,
and strictly enforces home lanes to prevent collision teleports.
"""

from rose.common import obstacles, actions

driver_name = "gps pro max - Team 3"

TARGET_LOOKAHEAD = 40
game_map = []
track_min_x = None
track_max_x = None
home_center_x = None

DISCOUNT_FACTOR = 0.97  # Prevents long-distance risky pathing

CODE_SAFE = 0
CODE_PENGUIN = 1
CODE_CRACK = 2
CODE_WATER = 3
CODE_CRASH = 4
OWN_CELL_CODE = -1

OBSTACLE_CODE = {
    obstacles.NONE: CODE_SAFE,
    obstacles.PENGUIN: CODE_PENGUIN,
    obstacles.CRACK: CODE_CRACK,
    obstacles.WATER: CODE_WATER,
    obstacles.TRASH: CODE_CRASH,
    obstacles.BIKE: CODE_CRASH,
    obstacles.BARRIER: CODE_CRASH,
}

def code_for(obs):
    return OBSTACLE_CODE.get(obs, CODE_CRASH)

MAX_LANE_PROBE = 25

def find_track_bounds(world, car_x, car_y):
    min_x = car_x
    for offset in range(1, MAX_LANE_PROBE + 1):
        x = car_x - offset
        try:
            obs = world.get((x, car_y))
        except Exception:
            break
        if obs is None:
            break
        min_x = x

    max_x = car_x
    for offset in range(1, MAX_LANE_PROBE + 1):
        x = car_x + offset
        try:
            obs = world.get((x, car_y))
        except Exception:
            break
        if obs is None:
            break
        max_x = x

    return min_x, max_x

def get_max_vision(world, car_x, car_y, target_depth):
    max_visible = 1
    for step in range(1, target_depth + 1):
        try:
            _ = world.get((car_x, car_y - step))
            max_visible = step
        except Exception:
            break
    return max_visible

def gps(world, distance):
    global track_min_x, track_max_x, home_center_x
    car_x, car_y = world.car.x, world.car.y

    if track_min_x is None or track_max_x is None:
        track_min_x, track_max_x = find_track_bounds(world, car_x, car_y)
        home_center_x = car_x

    lanes = tuple(range(track_min_x, track_max_x + 1))
    own_lane_index = car_x - track_min_x

    grid = []
    for x in lanes:
        row = []
        for step in range(distance):
            if step == 0 and x == car_x:
                row.append(OWN_CELL_CODE)
            else:
                try:
                    obs = world.get((x, car_y - step))
                    if obs is None:
                        row.append(CODE_CRASH)
                    else:
                        row.append(code_for(obs))
                except Exception:
                    row.append(CODE_CRASH)
        grid.append(row)
    return grid, own_lane_index

def get_best_path(board, lane, step, memo):
    num_lanes = len(board)
    num_steps = len(board[0])

    if step >= num_steps - 1:
        maneuverability_bonus = 0
        if lane > 0 and board[lane - 1][step] != CODE_CRASH:
            maneuverability_bonus += 2.0
        if lane < num_lanes - 1 and board[lane + 1][step] != CODE_CRASH:
            maneuverability_bonus += 2.0
        return maneuverability_bonus, []

    if (lane, step) in memo:
        return memo[(lane, step)]

    best_score = float("-inf")
    best_way = []

    for move in (0, -1, 1):
        new_lane = lane + move
        new_step = step + 1

        if not (0 <= new_lane < num_lanes):
            continue

        target_obstacle = board[new_lane][new_step]

        if target_obstacle == CODE_CRASH:
            continue

        absolute_x = track_min_x + new_lane
        step_score = 10

        distance_from_home_center = abs(absolute_x - home_center_x)

        # CRITICAL TWEAK: Strict restriction on crossing into opponent's lane territory
        if distance_from_home_center > 1:
            step_score -= 20.0
        elif distance_from_home_center == 0:
            step_score += 0.5

        if move == 0:
            if target_obstacle == CODE_PENGUIN:
                step_score += 41
            elif target_obstacle == CODE_CRACK:
                step_score += 25
            elif target_obstacle == CODE_WATER:
                step_score += 20
        else:
            step_score -= 0.5  # Swerve cost

            if target_obstacle in (CODE_CRACK, CODE_WATER):
                step_score -= 35.0
            elif target_obstacle == CODE_PENGUIN:
                step_score -= 2.0

        future_score, future_way = get_best_path(board, new_lane, new_step, memo)

        # Bellman equation integration
        total_score = step_score + (DISCOUNT_FACTOR * future_score)

        if total_score > best_score:
            best_score = total_score
            best_way = [move] + future_way

    if best_score == float("-inf"):
        memo[(lane, step)] = (-30, [])
        return -30, []

    memo[(lane, step)] = (best_score, best_way)
    return best_score, best_way

def drive(world):
    global game_map, track_min_x, home_center_x

    actual_depth = get_max_vision(world, world.car.x, world.car.y, TARGET_LOOKAHEAD)
    game_map, own_lane_index = gps(world, actual_depth)

    memo = {}
    _, best_way = get_best_path(game_map, own_lane_index, 0, memo)

    next_move = best_way[0] if best_way else 0

    if next_move == -1:
        return actions.LEFT
    elif next_move == 1:
        return actions.RIGHT

    next_obstacle = game_map[own_lane_index][1]

    if next_obstacle == CODE_PENGUIN:
        return actions.PICKUP
    elif next_obstacle == CODE_CRACK:
        return actions.JUMP
    elif next_obstacle == CODE_WATER:
        return actions.BRAKE
    elif next_obstacle == CODE_CRASH:
        # Emergency evasive action based on hazard levels
        def evaluate_lane_hazard(idx):
            if not (0 <= idx < len(game_map)):
                return -9999
            obs = game_map[idx][1]
            if obs == CODE_CRASH:
                return -1000
            if obs in (CODE_CRACK, CODE_WATER):
                return -50
            return 0

        left_safety = evaluate_lane_hazard(own_lane_index - 1)
        right_safety = evaluate_lane_hazard(own_lane_index + 1)

        if left_safety > right_safety:
            return actions.LEFT
        elif right_safety > left_safety:
            return actions.RIGHT
        else:
            absolute_x = track_min_x + own_lane_index
            return actions.LEFT if absolute_x > home_center_x else actions.RIGHT

    return actions.NONE