#!/usr/bin/env python
"""Load the Hubo robot.
"""

from itertools import count
from pyrobolearn.simulators import BulletSim
from pyrobolearn.worlds import BasicWorld
from pyrobolearn.robots import Hubo

# Create simulator
sim = BulletSim()

# create world
world = BasicWorld(sim)

# create robot
robot = Hubo(sim)

# print information about the robot
robot.printRobotInfo()

# Position control using sliders
# robot.addJointSlider()

# run simulator
for _ in count():
    # robot.updateJointSlider()
    world.step(sleep_dt=1./240)
