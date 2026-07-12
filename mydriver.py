"""
This driver does not do any action.
"""

from rose.common import obstacles, actions  # NOQA

driver_name = "MyDriver"


def()



def drive(world):
    x = world.car.x
    y = world.car.y
    obstacle = world.get((x, y - 4))

    return actions.NONE
