#!/usr/bin/env python
"""Provide the Cassie robotic platform.
"""

from itertools import count
from pyrobolearn.simulators import BulletSim
from pyrobolearn.worlds import BasicWorld
from pyrobolearn.robots import Cassie

# Create simulator
sim = BulletSim()

# create world
world = BasicWorld(sim)

# create robot
robot = Cassie(sim)

# print information about the robot
robot.printRobotInfo()

# position control using sliders
# robot.addJointSlider()

# run simulator
for _ in count():
    # robot.updateJointSlider()
    robot.moveJointHomePositions()
    world.step(sleep_dt=1./240)
