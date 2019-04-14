#!/usr/bin/env python
"""Provide the various dynamic tasks (i.e. objective functions) used in QP.

References:
    [1] "Quadratic Programming in Python" (https://scaron.info/blog/quadratic-programming-in-python.html), Caron, 2017
    [2] "OpenSoT: A whole-body control library for the compliant humanoid robot COMAN", Rocchi et al., 2015
    [3] "Robot Control for Dummies: Insights and Examples using OpenSoT", Hoffman et al., 2017
"""

import rbdl
import numpy as np

from pyrobolearn.robots.robot import Robot
from pyrobolearn.priorities.tasks.task import Task


__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2018, PyRoboLearn"
__credits__ = ["OpenSoT (Enrico Mingo Hoffman and Alessio Rocchi)", "Songyan Xin"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class DynamicTask(Task):
    r"""Dynamic Task.

    """
    pass


class MinAcceleration(DynamicTask):
    r"""Min acceleration task.

    """
    pass


class MinEffort(DynamicTask):
    r"""Min effort task.

    """
    pass


class Admittance(DynamicTask):
    r"""Admittance task.

    """
    pass


class ForceManipulability(DynamicTask):
    r"""Force Manipulability task.

    """
    pass


class CentroidalDynamics(DynamicTask):
    r"""Centroidal dynamics task (u

    """
    pass


class Wrench(DynamicTask):
    r"""Wrench dynamic task.

    """
    pass
