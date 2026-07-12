"""
This driver does not do any action.
"""

from rose.common import obstacles,actions

import enum
class Type(enum):
    car = -1
    empty = 0
    penguin = 1
    crack = 2
    water = 3
    shit = 4

driver_name = "MyDriver"


def()



def drive(world):
    x = world.car.x
    y = world.car.y
    obstacle = world.get((x, y - 4))

    return actions.NONE


