#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example on how to use the Bullet-ROS simulator (the subscriber version) in PRL.

The subscriber version subscribe to various topics related to the loaded robot.

This code works in parallel with the `bullet_ros_publisher.py`, which implements the publisher version, that is,
it publish to the topics the various data. By moving the robot in the publisher version of the simulator, you should
see that the robot in this simulator should move in accordance.

Note: this code also works with other robots.
"""

from itertools import count
import pyrobolearn as prl


# create simulator (ros core will automatically be launched if it has not already been launched)
sim = prl.simulators.BulletROS(subscribe=True)

# load world
world = prl.worlds.BasicWorld(sim)

# load robot
robot = world.load_robot('wam')

# run simulation
for t in count():
    # get the joint positions from the ROS subscribers (if possible)
    robot.get_joint_positions()

    # perform a step in the world, and sleep for `sim.dt`
    world.step(sim.dt)




































