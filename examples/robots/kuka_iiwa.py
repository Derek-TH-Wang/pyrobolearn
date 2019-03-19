#!/usr/bin/env python
"""Provide the Kuka IIWA robotic platform.
"""

import numpy as np
from itertools import count
from pyrobolearn.simulators import BulletSim
from pyrobolearn.worlds import BasicWorld
from pyrobolearn.robots import KukaIIWA

# Create simulator
sim = BulletSim()

# create world
world = BasicWorld(sim)

# create robot
robot = KukaIIWA(sim)

# print information about the robot
robot.printRobotInfo()
# H = robot.calculateMassMatrix()
# print("Inertia matrix: H(q) = {}".format(H))

# print(robot.getLinkWorldPositions(flatten=False))

K = 5000*np.identity(3)
# D = 2 * np.sqrt(K)
# D = np.zeros((3,3))
D = 100 * np.identity(3)
x_des = np.array([0.3, 0.0, 0.8])
x_des = np.array([0.52557296, 0.09732758, 0.80817658])
linkId = robot.getLinkIds('iiwa_link_ee')

for i in count():
    # print(robot.getLinkWorldPositions(flatten=False))

    # get state
    q = robot.getJointPositions()
    dq = robot.getJointVelocities()
    x = robot.getLinkWorldPositions(linkId)
    dx = robot.getLinkWorldLinearVelocities(linkId)

    # get (linear) jacobian
    J = robot.getLinearJacobian(linkId, q)

    # get coriolis, gravity compensation torques
    torques = robot.getCoriolisAndGravityCompensationTorques(q, dq)

    # Impedance control: attractor point
    F = K.dot(x_des - x) - D.dot(dx)
    # F = -D.dot(dx)
    tau = J.T.dot(F)
    print(tau)
    torques += tau
    robot.setJointTorques(torques)

    # step in simulation
    world.step(sleep_dt=1./240)
