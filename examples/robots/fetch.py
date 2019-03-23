#!/usr/bin/env python
"""Load the Fetch robot.
"""

from itertools import count
from pyrobolearn.simulators import BulletSim
from pyrobolearn.worlds import BasicWorld
from pyrobolearn.robots import Fetch

# Create simulator
sim = BulletSim()

# create world
world = BasicWorld(sim)

# create robot
robot = Fetch(sim)

# print information about the robot
robot.print_info()

# Position control using sliders
robot.add_joint_slider()

# run simulator
for _ in count():
    robot.update_joint_slider()
    world.step(sleep_dt=1./240)
