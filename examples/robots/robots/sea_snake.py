# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""Load the SEA Snake robot.
"""

from itertools import count
from pyrobolearn.simulators import Bullet
from pyrobolearn.worlds import BasicWorld
from pyrobolearn.robots import SEASnake

# Create simulator
sim = Bullet()

# create world
world = BasicWorld(sim)

# create robot
robot = SEASnake(sim)

# print information about the robot
robot.print_info()

# run simulation
for i in count():
    # step in simulation
    world.step(sleep_dt=1./240)
