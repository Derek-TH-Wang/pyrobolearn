#!/usr/bin/env python
"""Provide the Phantom X robotic platform.
"""

import os

from pyrobolearn.robots.legged_robot import HexapodRobot

__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2018, PyRoboLearn"
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class PhantomX(HexapodRobot):
    r"""Phantom X Hexapod robot

    References:
        [1] https://github.com/HumaRobotics/phantomx_description
    """

    def __init__(self,
                 simulator,
                 position=(0, 0, 0.2),
                 orientation=(0, 0, 0, 1),
                 fixed_base=False,
                 scale=1.,
                 urdf=os.path.dirname(__file__) + '/urdfs/phantomx/phantomx.urdf'):
        # check parameters
        if position is None:
            position = (0., 0., 0.2)
        if len(position) == 2:  # assume x, y are given
            position = tuple(position) + (0.2,)
        if orientation is None:
            orientation = (0, 0, 0, 1)
        if fixed_base is None:
            fixed_base = False

        super(PhantomX, self).__init__(simulator, urdf, position, orientation, fixed_base, scale)
        self.name = 'phantomx'


# Test
if __name__ == "__main__":
    from itertools import count
    from pyrobolearn.simulators import BulletSim
    from pyrobolearn.worlds import BasicWorld

    # Create simulator
    sim = BulletSim()

    # create world
    world = BasicWorld(sim)

    # create robot
    robot = PhantomX(sim)

    # print information about the robot
    robot.print_info()

    # run simulation
    for i in count():
        # step in simulation
        world.step(sleep_dt=1./240)
