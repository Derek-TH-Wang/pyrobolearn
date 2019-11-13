#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""In this file, we perform inverse kinematics using the Kuka robot.

Set the `solver_flag` to a number between 0 and 1 (see lines [19,22]) to select which IK solver to select.
0: use robot.calculate_inverse_kinematics()
1: use damped-least-squares IK using Jacobian (provided by pybullet)
"""

import numpy as np
from itertools import count
import argparse

from pyrobolearn.simulators import Bullet
from pyrobolearn.worlds import BasicWorld
from pyrobolearn.robots import KukaIIWA


# create parser to select the IK solver
parser = argparse.ArgumentParser()
parser.add_argument('-s', '--solver', help='the IK solver to select (0: use robot.calculate_inverse_kinematics(), '
                                           '1: use damped-least-squares IK using Jacobian)', type=int,
                    choices=[0, 1], default=1)
args = parser.parse_args()


# select IK solver, by setting the flag:
# 0 = pybullet + calculate_inverse_kinematics()
# 1 = pybullet + damped-least-squares IK using Jacobian (provided by pybullet)
solver_flag = args.solver  # 1 gives a pretty good result


# Create simulator
sim = Bullet()

# create world
world = BasicWorld(sim)

# create robot
robot = KukaIIWA(sim)
robot.print_info()

# define useful variables for IK
dt = 1./240
link_id = robot.get_end_effector_ids(end_effector=0)
joint_ids = robot.joints  # actuated joint
# joint_ids = joint_ids[2:]
damping = 0.01  # for damped-least-squares IK
wrt_link_id = -1  # robot.get_link_ids('iiwa_link_1')

# desired position
xd = np.array([0.5, 0., 0.5])
world.load_visual_sphere(xd, radius=0.05, color=(1, 0, 0, 0.5))

# change the robot visual
robot.change_transparency()
robot.draw_link_frames(link_ids=[-1, 0])
robot.draw_bounding_boxes(link_ids=joint_ids[0])
# robot.draw_link_coms([-1,0])

qIdx = robot.get_q_indices(joint_ids)


# OPTION 1: using `calculate_inverse_kinematics`###
if solver_flag == 0:
    for _ in count():
        # get current position in the task/operational space
        x = robot.get_link_world_positions(link_id)
        # print("(xd - x) = {}".format(xd - x))

        # perform full IK
        q = robot.calculate_inverse_kinematics(link_id, position=xd)

        # set the joint positions
        robot.set_joint_positions(q[qIdx], joint_ids)

        # step in simulation
        world.step(sleep_dt=dt)

# OPTION 2: using Jacobian and manual damped-least-squares IK ###
elif solver_flag == 1:
    kp = 50    # 5 if velocity control, 50 if position control
    kd = 0     # 2*np.sqrt(kp)

    for _ in count():
        # get current position in the task/operational space
        x = robot.get_link_world_positions(link_id)
        dx = robot.get_link_world_linear_velocities(link_id)
        # print("(xd - x) = {}".format(xd - x))

        # Get joint configuration
        q = robot.get_joint_positions()

        # Get linear jacobian
        if robot.has_floating_base():
            J = robot.get_linear_jacobian(link_id, q=q)[:, qIdx + 6]
        else:
            J = robot.get_linear_jacobian(link_id, q=q)[:, qIdx]

        # Pseudo-inverse
        # Jp = robot.get_pinv_jacobian(J)
        # Jp = J.T.dot(np.linalg.inv(J.dot(J.T) + damping*np.identity(3)))   # this also works
        Jp = robot.get_damped_least_squares_inverse(J, damping)

        # evaluate damped-least-squares IK
        dq = Jp.dot(kp * (xd - x) - kd * dx)

        # set joint velocities
        # robot.set_joint_velocities(dq)

        # set joint positions
        q = q[qIdx] + dq * dt
        robot.set_joint_positions(q, joint_ids=joint_ids)

        # step in simulation
        world.step(sleep_dt=dt)
