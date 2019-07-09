#!/usr/bin/env python
r"""Provide the basketball world.
"""

import os
import numpy as np

from pyrobolearn.worlds import BasicWorld


__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2019, PyRoboLearn"
__credits__ = ["Brian Delhaisse"]
__license__ = "GNU GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class BasketBallWorld(BasicWorld):
    r"""Basketball world

    """

    def __init__(self, simulator, position=(3., 0., 2.), scale=(1., 1., 1.)):
        """
        Initialize the basketball world.

        Args:
            simulator (Simulator): the simulator instance.
            position (tuple/list of 3 float, np.array[3]): position of the basketball hoop.
            scale (tuple/list of 3 float): scale of the basket hoop.
        """
        super(BasketBallWorld, self).__init__(simulator)

        mesh_path = os.path.dirname(os.path.abspath(__file__)) + '/../../meshes/sports/basketball/'
        position = np.asarray(position)

        # load basket hoop position
        self.hoop = self.load_mesh(mesh_path + 'basketball.obj', position=position, scale=scale, mass=0, flags=1)

        # load ball
        # self.ball = self.load_sphere(position=[0., 0., 1.], radius=0.1193, mass=0.625)
        # self.apply_texture(texture=mesh_path + 'Basketball-ColorMap.jpg', body_id=self.ball)
        self.ball = self.load_mesh(mesh_path + 'ball.obj', position=[0., 0., 1.], scale=scale, mass=0.625, flags=0)

        # set the restitution coefficient for the ball
        # Ref: "Measure the coefficient of restitution for sports balls", Persson, 2012
        self.change_dynamics(self.ball, restitution=0.87)
        self.change_dynamics(restitution=1.)

    def reset(self, world_state=None):
        super(BasketBallWorld, self).reset(world_state)

    def step(self, sleep_dt=None):
        super(BasketBallWorld, self).step(sleep_dt)


# Test
if __name__ == '__main__':
    from itertools import count
    import pyrobolearn as prl

    sim = prl.simulators.Bullet()

    world = BasketBallWorld(sim)

    for t in count():
       world.step(sim.dt)
