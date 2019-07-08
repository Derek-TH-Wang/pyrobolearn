#!/usr/bin/env python
"""Load the Cartpole robotic platform.
"""

import control
from scipy.linalg import solve_continuous_are


class LQR(object):
    r"""Linear Quadratic Regulator

    Type: Model-based (optimal control)

    LQR assumes that the dynamics are described by a set of linear differential equations, and a quadratic cost.
    That is, the dynamics can written as :math:`\dot{x} = A x + B u`, where :math:`x` is the state vector, and
    :math:`u` is the control vector, and the cost is given by:

    .. math:: J = x(T)^T F(T) x(T) + \int_0^T (x(t)^T Q x(t) + u(t)^T R u(t) + 2 x(t)^T N u(t)) dt

    where :math:`Q` and :math:`R` represents weight matrices which allows to specify the relative importance
    of each state/control variable. These are normally set by the user.

    The goal is to find the feedback control law :math:`u` that minimizes the above cost :math:`J`. Solving it
    gives us :math:`u = -K x`, where :math:`K = R^{-1} (B^T S + N^T)` with :math:`S` is found by solving the
    continuous time Riccati differential equation :math:`S A + A^T S - (S B + N) R^{-1} (B^T S + N^T) + Q = 0`.

    Thus, LQR requires thus the model/dynamics of the system to be given (i.e. :math:`A` and :math:`B`).
    If the dynamical system is described by a set of nonlinear differential equations, we first have to linearize
    them around fixed points.

    Time complexity: O(M^3) where M is the size of the state vector
    Note: A desired state xd can also be given to the system: u = -K (x - xd)   (P control)

    See also:
        - `ilqr.py`: iterative LQR
        - `lqg.py`: LQG = LQR + LQE
        - `ilqg.py`: iterative LQG
    """

    def __init__(self, A, B, Q=None, R=None, N=None):
        if not self.isControllable(A, B):
            raise ValueError("The system is not controllable")
        self.A = A
        self.B = B
        if Q is None: Q = np.identity(A.shape[1])
        self.Q = Q
        if R is None: R = np.identity(B.shape[1])
        self.R = R
        self.N = N
        self.K = None

    @staticmethod
    def isControllable(A, B):
        return np.linalg.matrix_rank(control.ctrb(A, B)) == A.shape[0]

    def getRiccatiSolution(self):
        S = solve_continuous_are(self.A, self.B, self.Q, self.R, s=self.N)
        return S

    def getGainK(self):
        #S = self.getRiccatiSolution()
        #S1 = self.B.T.dot(S)
        #if self.N is not None: S1 += self.N.T
        #K = np.linalg.inv(self.R).dot(S1)

        if self.N is None:
            K, S, E = control.lqr(self.A, self.B, self.Q, self.R)
        else:
            K, S, E = control.lqr(self.A, self.B, self.Q, self.R, self.N)
        return K

    def compute(self, x, xd=None):
        """Return the u."""

        if self.K is None:
            self.K = self.getGainK()

        if xd is None:
            return self.K.dot(x)
        else:
            return self.K.dot(xd - x)


# Test
if __name__ == "__main__":
    import numpy as np
    from itertools import count
    from pyrobolearn.simulators import Bullet
    from pyrobolearn.worlds import World
    from pyrobolearn.robots import CartPole

    # Create simulator
    sim = Bullet()

    # create world
    world = World(sim)

    # create robot
    num_links = 2
    robot = CartPole(sim, num_links=num_links)

    # print information about the robot
    robot.print_info()

    robot.get_symbolic_equations_of_motion()

    eq_point = np.zeros((num_links + 1) * 2)  # state = [q, dq]
    A, B = robot.linearize_equations_of_motion(eq_point)

    # LQR controller
    lqr = LQR(A, B)
    K = lqr.getGainK()

    for i in count():
        # control
        x = np.concatenate((robot.get_joint_positions(), robot.get_joint_velocities()))
        u = K.dot(eq_point - x)
        robot.set_joint_torques(u[0], 0)

        print("U[0] = {}".format(u[0]))

        # step in simulation
        world.step(sleep_dt=1./240)
