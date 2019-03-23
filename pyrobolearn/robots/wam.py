#!/usr/bin/env python
"""Provide the WAM robotic platform.
"""

import os

from pyrobolearn.robots.manipulator import ManipulatorRobot


class WAM(ManipulatorRobot):
    r"""Wam robot

    References:
        [1] https://github.com/jhu-lcsr/barrett_model
    """

    def __init__(self,
                 simulator,
                 position=(0, 0, 0),
                 orientation=(0, 0, 0, 1),
                 fixed_base=True,
                 scaling=1.,
                 urdf=os.path.dirname(__file__) + '/urdfs/wam/wam.urdf'):
        # check parameters
        if position is None:
            position = (0., 0., 0.)
        if len(position) == 2:  # assume x, y are given
            position = tuple(position) + (0.,)
        if orientation is None:
            orientation = (0, 0, 0, 1)
        if fixed_base is None:
            fixed_base = True

        super(WAM, self).__init__(simulator, urdf, position, orientation, fixed_base, scaling)
        self.name = 'wam'

        # self.disable_motor()


# Test
if __name__ == "__main__":
    import numpy as np
    from itertools import count
    from pyrobolearn.simulators import BulletSim
    from pyrobolearn.worlds import BasicWorld

    # Create simulator
    sim = BulletSim()

    # create world
    world = BasicWorld(sim)

    # create robot
    robot = WAM(sim)

    # print information about the robot
    robot.print_info()
    # H = robot.get_mass_matrix()
    # print("Inertia matrix: H(q) = {}".format(H))

    robot.set_joint_positions([np.pi / 4, np.pi / 2], joint_ids=[0, 1]) #2, 4])

    Jlin = robot.get_jacobian(6)[:3]
    robot.draw_velocity_manipulability_ellipsoid(6, Jlin, color=(1, 0, 0, 0.7))
    for _ in range(5):
        world.step(sleep_dt=1./240)

    Jlin = robot.get_jacobian(6)[:3]
    robot.draw_velocity_manipulability_ellipsoid(6, Jlin, color=(0, 0, 1, 0.7))
    for _ in range(45):
        world.step(sleep_dt=1./240)

    Jlin = robot.get_jacobian(6)[:3]
    robot.draw_velocity_manipulability_ellipsoid(6, Jlin)

    for i in count():
        if i%1000 == 0:
            print("Joint Torques: {}".format(robot.get_joint_torques()))
            print("Gravity Torques: {}".format(robot.get_gravity_compensation_torques()))
            print("Compensation Torques: {}".format(robot.get_coriolis_and_gravity_compensation_torques()))
        # step in simulation
        world.step(sleep_dt=1./240)
