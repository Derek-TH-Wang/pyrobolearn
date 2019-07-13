#!/usr/bin/env python
"""Provide the Unmanned Underwater Vehicle (UUV) robot abstract classes.
"""

from pyrobolearn.robots.robot import Robot

__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2018, PyRoboLearn"
__credits__ = ["Brian Delhaisse"]
__license__ = "GNU GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class UUVRobot(Robot):
    r"""Unmanned Underwater Vehicle Robot

    Vehicles/Robots that operate under water.
    """

    def __init__(self, simulator, urdf, position=None, orientation=None, fixed_base=False, scale=1.):
        """
        Initialize the UUV.

        Args:
            simulator (Simulator): simulator instance.
            urdf (str): path to the urdf. Do not change it unless you know what you are doing.
            position (np.array[3]): Cartesian world position.
            orientation (np.array[4]): Cartesian world orientation expressed as a quaternion [x,y,z,w].
            fixed_base (bool): if True, the robot base will be fixed in the world.
            scale (float): scaling factor that is used to scale the robot.
        """
        super(UUVRobot, self).__init__(simulator, urdf, position, orientation, fixed_base, scale)
