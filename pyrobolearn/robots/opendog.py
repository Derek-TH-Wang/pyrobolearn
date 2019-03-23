#!/usr/bin/env python
"""Provide the OpenDog robotic platform.
"""

import os

from pyrobolearn.robots.legged_robot import QuadrupedRobot


class OpenDog(QuadrupedRobot):
    r""" OpenDog robot

    References:
        [1] https://github.com/XRobots/openDog
        [2] https://github.com/wiccopruebas/opendog_project
    """

    def __init__(self,
                 simulator,
                 position=(0, 0, .6),
                 orientation=(0, 0, 0, 1),
                 fixed_base=False,
                 scaling=1.,
                 urdf=os.path.dirname(__file__) + '/urdfs/opendog/opendog.urdf'):
        # check parameters
        if position is None:
            position = (0., 0., 0.6)
        if len(position) == 2:  # assume x, y are given
            position = tuple(position) + (0.6,)
        if orientation is None:
            orientation = (0, 0, 0, 1)
        if fixed_base is None:
            fixed_base = False

        super(OpenDog, self).__init__(simulator, urdf, position, orientation, fixed_base, scaling)
        self.name = 'opendog'

        self.legs = [[self.get_link_ids(link) for link in links if link in self.link_names]
                     for links in [['lf_hip', 'lf_upperleg', 'lf_lowerleg'],
                                   ['rf_hip', 'rf_upperleg', 'rf_lowerleg'],
                                   ['lb_hip', 'lb_upperleg', 'lb_lowerleg'],
                                   ['rb_hip', 'rb_upperleg', 'rb_lowerleg']]]

        self.feet = [self.get_link_ids(link) for link in ['lf_lowerleg', 'rf_lowerleg', 'lb_lowerleg', 'rb_lowerleg']
                     if link in self.link_names]


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
    robot = OpenDog(sim)

    # print information about the robot
    robot.print_info()

    # Position control using sliders
    # robot.add_joint_slider(robot.getLeftFrontLegIds())

    # run simulator
    for _ in count():
        # robot.update_joint_slider()
        world.step(sleep_dt=1./240)
