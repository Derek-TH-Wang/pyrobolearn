#!/usr/bin/env python
"""Provide the Hand abstract classes.
"""

from pyrobolearn.robots.robot import Robot

__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2018, PyRoboLearn"
__credits__ = ["Brian Delhaisse"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class Hand(Robot):
    r"""Hand end-effector
    """

    def __init__(self,
                 simulator,
                 urdf,
                 position=(0, 0, 1.),
                 orientation=(0, 0, 0, 1),
                 fixed_base=False,
                 scale=1.):
        super(Hand, self).__init__(simulator, urdf, position, orientation, fixed_base, scale)

        self.fingers = []  # list of fingers where each finger is a list of links/joints

    @property
    def num_fingers(self):
        """Return the number of fingers on the hand"""
        return len(self.fingers)

    def get_finger(self, finger_id=None):
        """Return the list of joint/link ids for the specified finger"""
        if finger_id:
            return self.fingers[finger_id]
        return self.fingers


class TwoHand(Hand):
    r"""Two hand end-effectors

    """

    def __init__(self,
                 simulator,
                 urdf,
                 position=(0, 0, 1.),
                 orientation=(0, 0, 0, 1),
                 fixed_base=False,
                 scale=1.):
        super(TwoHand, self).__init__(simulator, urdf, position, orientation, fixed_base, scale)

        self.left_fingers = []  # list of ids in self.fingers
        self.right_fingers = []     # list of ids in self.fingers

    @property
    def num_fingers_left_hand(self):
        """Return the number of fingers on the left hand"""
        return len(self.left_fingers)

    @property
    def num_fingers_right_hand(self):
        """Return the number of fingers on the right hand"""
        return len(self.right_fingers)

    def get_left_fingers(self, finger_id=None):
        """Return the specified left fingers"""
        if finger_id:
            if isinstance(finger_id, int):
                return self.fingers[self.left_fingers[finger_id]]
            elif isinstance(finger_id, (tuple, list)):
                return [self.fingers[self.left_fingers[finger]] for finger in finger_id]
        return [self.fingers[finger] for finger in self.left_fingers]

    def get_right_fingers(self, finger_id=None):
        """Return the specified right fingers"""
        if finger_id:
            if isinstance(finger_id, int):
                return self.fingers[self.right_fingers[finger_id]]
            elif isinstance(finger_id, (tuple, list)):
                return [self.fingers[self.right_fingers[finger]] for finger in finger_id]
        return [self.fingers[finger] for finger in self.right_fingers]
