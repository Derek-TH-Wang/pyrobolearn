#!/usr/bin/env python
"""Provide the ICub robotic platform.
"""

import os
from legged_robot import BipedRobot
from manipulator import BiManipulatorRobot


class ICub(BipedRobot, BiManipulatorRobot):
    r"""ICub robot

    References:
    """

    def __init__(self,
                 simulator,
                 init_pos=(0, 0, 0.7),
                 init_orient=(0, 0, 1, 0),
                 useFixedBase=False,
                 scaling=1.,
                 urdf_path=os.path.dirname(__file__) + '/urdfs/icub/icub-v2.5+.urdf'):
        # check parameters
        if init_pos is None:
            init_pos = (0., 0., 0.7)
        if len(init_pos) == 2:  # assume x, y are given
            init_pos = tuple(init_pos) + (0.7,)
        if init_orient is None:
            init_orient = (0, 0, 0, 1)
        if useFixedBase is None:
            useFixedBase = False

        super(ICub, self).__init__(simulator, urdf_path, init_pos, init_orient, useFixedBase)
        self.name = 'icub'

        self.head = self.getLinkIds('head') if 'head' in self.link_names else None
        self.neck = [self.getLinkIds(link) for link in ['neck_1', 'neck_2'] if link in self.link_names]
        self.torso = [self.getLinkIds(link) for link in ['torso_1', 'torso_2', 'chest'] if link in self.link_names]

        self.legs = [[self.getLinkIds(link) for link in links if link in self.link_names]
                     for links in [['l_hip_1', 'l_hip_2', 'l_upper_leg', 'l_lower_leg', 'l_ankle_1', 'l_ankle_2'],
                                   ['r_hip_1', 'r_hip_2', 'r_upper_leg', 'r_lower_leg', 'r_ankle_1', 'r_ankle_2']]]

        self.feet = [self.getLinkIds(link) for link in ['l_sole', 'r_sole'] if link in self.link_names]

        self.arms = [[self.getLinkIds(link) for link in links if link in self.link_names]
                     for links in [['l_shoulder_1', 'l_shoulder_2', 'l_shoulder_3', 'l_elbow_1', 'l_forearm',
                                    'l_wrist_1', 'l_hand'],
                                   ['r_shoulder_1', 'r_shoulder_2', 'r_shoulder_3', 'r_elbow_1', 'r_forearm',
                                    'r_wrist_1', 'r_hand']]]

        self.hands = [self.getLinkIds(link) for link in ['l_hand', 'r_hand'] if link in self.link_names]


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
    robot = ICub(sim)

    # print information about the robot
    robot.printRobotInfo()

    # Position control using sliders
    # robot.addJointSlider()

    # run simulator
    for _ in count():
        # robot.updateJointSlider()
        world.step(sleep_dt=1./240)
