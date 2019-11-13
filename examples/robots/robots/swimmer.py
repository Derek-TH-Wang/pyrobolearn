#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Load the Swimmer Mujoco model.
"""

from itertools import count
from pyrobolearn.simulators import Bullet
from pyrobolearn.worlds import BasicWorld
from pyrobolearn.robots import Swimmer

# Create simulator
sim = Bullet()

# create world
world = BasicWorld(sim)

# create robot
robot = Swimmer(sim)

# print information about the robot
robot.print_info()

# run simulation
for i in count():
    # step in simulation
    world.step(sleep_dt=1./240)
