#!/usr/bin/env python
"""Load the Darwin robot.
"""

from itertools import count
from pyrobolearn.simulators import BulletSim
from pyrobolearn.worlds import BasicWorld
from pyrobolearn.robots import Darwin

# Create simulator
sim = BulletSim()

# create world
world = BasicWorld(sim)

# create robot
robot = Darwin(sim, fixed_base=False)

# print information about the robot
robot.print_info()
print(robot.link_names)

# Position control using sliders
# robot.add_joint_slider()

# run simulator
for _ in count():
    # robot.update_joint_slider()
    world.step(sleep_dt=1./240)
