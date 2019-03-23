#!/usr/bin/env python
"""Provide the Cogimon robotic platform.
"""

import os

from pyrobolearn.robots.legged_robot import BipedRobot
from pyrobolearn.robots.manipulator import BiManipulatorRobot


class Cogimon(BipedRobot, BiManipulatorRobot):
    r"""Cogimon humanoid robot.

    """

    def __init__(self,
                 simulator,
                 position=(0, 0, 1.),
                 orientation=(0, 0, 0, 1),
                 fixed_base=False,
                 scaling=1.,
                 urdf=os.path.dirname(__file__) + '/urdfs/cogimon/cogimon.urdf',
                 lower_body=False):  # cogimon_lower_body.urdf

        # check parameters
        if position is None:
            position = (0., 0., 1.)
        if len(position) == 2:  # assume x, y are given
            position = tuple(position) + (1.,)
        if orientation is None:
            orientation = (0, 0, 0, 1)
        if fixed_base is None:
            fixed_base = False
        if lower_body:
            urdf = os.path.dirname(__file__) + '/urdfs/cogimon/cogimon_lower_body.urdf'

        super(Cogimon, self).__init__(simulator, urdf, position, orientation, fixed_base, scaling)
        self.name = 'cogimon'

        self.waist = self.get_link_ids('DWL') if 'DWL' in self.link_names else None
        self.torso = self.get_link_ids('DWYTorso') if 'DWYTorso' in self.link_names else None

        self.legs = [[self.get_link_ids(link) for link in links if link in self.link_names]
                     for links in [['LHipMot', 'LThighUpLeg', 'LThighLowLeg', 'LLowLeg', 'LFootmot', 'LFoot'],
                                   ['RHipMot', 'RThighUpLeg', 'RThighLowLeg', 'RLowLeg', 'RFootmot', 'RFoot']]]

        self.feet = [self.get_link_ids(link) for link in ['LFoot', 'RFoot'] if link in self.link_names]

        self.arms = [[self.get_link_ids(link) for link in links if link in self.link_names]
                     for links in [['LShp', 'LShr', 'LShy', 'LElb', 'LForearm', 'LWrMot2', 'LWrMot3'],
                                   ['RShp', 'RShr', 'RShy', 'RElb', 'RForearm', 'RWrMot2', 'RWrMot3']]]

        self.hands = [self.get_link_ids(link) for link in ['LSoftHand', 'RSoftHand'] if link in self.link_names]


def CogimonLowerBody(simulator, init_pos=(0, 0, 1.), init_orient=(0, 0, 0, 1), useFixedBase=False, scaling=1.,
                     urdf_path=os.path.dirname(__file__) + '/urdfs/cogimon/cogimon_lower_body.urdf'):
    """Load Cogimon Lower Body"""
    return Cogimon(simulator=simulator, position=init_pos, orientation=init_orient, fixed_base=useFixedBase,
                   scaling=scaling, urdf=urdf_path)


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
    robot = Cogimon(sim, lower_body=False)

    # print information about the robot
    robot.print_info()

    # # Position control using sliders
    robot.add_joint_slider(robot.left_leg)

    # run simulator
    for _ in count():
        robot.update_joint_slider()
        world.step(sleep_dt=1./240)
