#!/usr/bin/env python
"""Load the Morphex robot.
"""

from itertools import count
from pyrobolearn.simulators import BulletSim
from pyrobolearn.worlds import BasicWorld
from pyrobolearn.robots import Morphex

# Create simulator
sim = BulletSim()

# create world
world = BasicWorld(sim)

# create robot
robot = Morphex(sim)

# print information about the robot
robot.printRobotInfo()

# run simulation
for i in count():
    # step in simulation
    world.step(sleep_dt=1./240)
