#!/usr/bin/env python
"""Provide the SEA Snake robotic platform.
"""

import os

from pyrobolearn.robots.robot import Robot


class SEASnake(Robot):
    r"""SEA snake robot (from CMU Biorobotics Lab)

    References:
        [1] https://github.com/alexansari101/snake_ws
    """

    def __init__(self,
                 simulator,
                 init_pos=(-0.5, 0, 0.1),
                 init_orient=(0, 0.707, 0, 0.707),
                 useFixedBase=False,
                 scaling=1.,
                 urdf_path=os.path.dirname(__file__) + '/urdfs/cmu_sea/snake.urdf'):
        # check parameters
        if init_pos is None:
            init_pos = (-0.5, 0., 0.1)
        if len(init_pos) == 2:  # assume x, y are given
            init_pos = tuple(init_pos) + (0.1,)
        if init_orient is None:
            init_orient = (0, 0.707, 0, 0.707)
        if useFixedBase is None:
            useFixedBase = False

        super(SEASnake, self).__init__(simulator, urdf_path, init_pos, init_orient, useFixedBase, scaling)
        self.name = 'sea_snake'


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
    robot = SEASnake(sim)

    # print information about the robot
    robot.printRobotInfo()

    # run simulation
    for i in count():
        # step in simulation
        world.step(sleep_dt=1./240)
