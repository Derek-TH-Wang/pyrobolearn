#!/usr/bin/env python
"""Define the the `World` class which allows to specify what constitutes the world (i.e. what elements are in
 the world).

Dependencies:
- `pyrobolearn.simulators`
"""

import collections
import inspect
import multiprocessing
import os
import numpy as np

import cv2
import time

from pyrobolearn.simulators import Simulator

from pyrobolearn.utils.converter import QuaternionListConverter
# from pyrobolearn.utils.heightmap_generator import *  # TODO: problem with gdal installation
from pyrobolearn.utils import has_method, has_variable

from pyrobolearn.robots import Robot, robot_names_to_classes
# from pyrobolearn.tools.bridges.bridge import Bridge

__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2018, PyRoboLearn"
__credits__ = ["Brian Delhaisse"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class WorldCamera(object):
    r"""World camera.

    Camera that looks at the world (only available in the simulator).

    The following operations carried out (in the given order) by OpenGL in order to display images seen by the
    camera are:
    * M: Model space --> World space. This transforms the coordinates of each model described in their own local
     frame :math:`[x_{l}, y_{l}, z_{l}, 1]` to world coordinates :math:`[x_{w}, y_{w}, z_{w}, 1]`.
    * V: World space --> View space. This transforms world coordinates :math:`[x_{w}, y_{w}, z_{w}, 1]` into eye
     coordinates :math:`[x_{e}, y_{e}, z_{e}, 1]`. That is, it rotates and translates the world such that it is in
     front of the camera.
    * P: View space --> Projection space. Transforms the eye coordinates into clip coordinates using an orthographic
     or perspective projection. The new coordinates are given by :math:`[x_{c}, y_{c}, z_{c}, w_{c}]`. This is not
     normalized, i.e. w_{c} is not equal to 1. See next operation.
    * norm: Screen space --> NDC space. This normalizes the previous clipped coordinates into
     Normalized Device Coordinates (NDC) where each coordinate is normalized and is between -1 and 1. That is,
     we now have :math:`[x_{n}, y_{n}, z_{n}, 1] = [x_c/w_c, y_c/w_c, z_c, w_c/w_c]`
    * Vp: NDC space --> Screen space. Finally, this maps the previous normalized clip coordinates to pixel
     coordinates :math:`[x_{s}, y_{s}, z_{s}, 1]` where :math:`x_s` (:math:`y_s`) is between 0 and the width
     (height) of the screen respectively, and :math:`z_s` represents the depth which is between 0 and 1.

    References:
        [1] http://www.codinglabs.net/article_world_view_projection_matrix.aspx
        [2] https://learnopengl.com/Getting-started/Coordinate-Systems
        [3] http://www.thecodecrate.com/opengl-es/opengl-transformation-matrices/
        [4] http://learnwebgl.brown37.net/08_projections/projections_perspective.html
    """

    def __init__(self, simulator):
        self.sim = simulator

    def __repr__(self):
        return self.__class__.__name__

    @property
    def info(self):
        """
        Return all the information about the camera.
        """
        return self.get_debug_visualizer_camera(convert=False)

    # alias
    def get_debug_visualizer_camera(self, convert=True):
        """
        Return all the information provided by the camera.

        Args:
            convert (bool): if True, it will convert the lists into numpy vectors and matrices

        Returns:
            width (int): width of the camera image in pixels
            height (int): height of the camera image in pixels
            view_matrix (float[16], float[4x4]): view matrix of the camera
            projection_matrix (float[16], float[4x4]): projection matrix of the camera
            camera_up (float[3]): up axis of the camera, in Cartesian world space coordinates
            cameraForward (float[3]): forward axis of the camera, in Cartesian world space coordinates
            horizontal (float[3]): TBD. This is a horizontal vector that can be used to generate rays (for mouse
                picking or creating a simple ray tracer for example)
            vertical (float[3]): TBD.This is a vertical vector that can be used to generate rays(for mouse picking
                or creating a simple ray tracer for example).
            yaw (float): yaw angle of the camera, in Cartesian local space coordinates
            pitch (float): pitch angle of the camera, in Cartesian local space coordinates
            dist (float): distance between the camera and the camera target
            target (float[3]): target of the camera, in Cartesian world space coordinates

        """
        return self.sim.get_debug_visualizer()

    @property
    def width(self):
        """
        Return the width of the pictures (in pixel)
        """
        return self.sim.get_debug_visualizer()[0]

    @property
    def height(self):
        """
        Return the height of the pictures (in pixel)
        """
        return self.sim.get_debug_visualizer()[1]

    @property
    def V(self):
        """
        Return the view matrix, which maps from the world to the view space.
        """
        return self.sim.get_debug_visualizer()[2]

    # alias
    view_matrix = V

    @property
    def Vinv(self):
        """
        Return the inverse of the view matrix
        """
        return np.linalg.inv(self.V)

    @property
    def P(self):
        """
        Return the projection matrix, which maps from the view to the projected/clipped space.
        """
        return self.sim.get_debug_visualizer()[3]

    # alias
    projection_matrix = P

    @property
    def Pinv(self):
        """
        Return the inverse of the projection matrix
        """
        return np.linalg.inv(self.P)

    @property
    def Vp(self):
        """
        Return the viewport matrix, which maps from the normalized clip coordinates to pixel coordinates.
        """
        width, height = self.sim.get_debug_visualizer()[:2]
        return np.array([[width / 2, 0, 0, width / 2],
                         [0, height / 2, 0, height / 2],
                         [0, 0, 0.5, 0.5],
                         [0, 0, 0, 1]])

    viewport_matrix = Vp

    @property
    def Vp_inv(self):
        """
        Return the inverse of the viewport matrix.
        """
        return np.linalg.inv(self.Vp)

    def get_matrices(self, inverse=False):
        """
        Return the view, projection, and viewport matrices.
        """
        width, height, V, P = self.sim.get_debug_visualizer()[:4]
        Vp = np.array([[width / 2, 0, 0, width / 2],
                         [0, height / 2, 0, height / 2],
                         [0, 0, 0.5, 0.5],
                         [0, 0, 0, 1]])
        if inverse:
            Vinv = np.linalg.inv(V)
            Pinv = np.linalg.inv(P)
            Vpinv = np.linalg.inv(Vp)
            return V, P, Vp, Vinv, Pinv, Vpinv
        return V, P, Vp

    @property
    def up_vector(self):
        """
        Return the up axis of the camera in the Cartesian world space coordinates
        """
        return self.sim.get_debug_visualizer()[4]

    @property
    def forward_vector(self):
        """
        Return the forward axis of the camera in the Cartesian world space coordinates.
        """
        return self.sim.get_debug_visualizer()[5]

    def get_vectors(self):
        """
        Return the forward, up, and lateral vectors of the camera.
        """
        up_vector, forward_vector = self.sim.get_debug_visualizer()[4:6]
        lateral_vector = np.cross(forward_vector, up_vector)
        return forward_vector, up_vector, lateral_vector

    @property
    def yaw(self):
        """
        Return the yaw angle of the camera in radian
        """
        return self.sim.get_debug_visualizer()[8]

    @property
    def pitch(self):
        """
        Return the pitch angle of the camera.
        """
        return self.sim.get_debug_visualizer()[9]

    @property
    def dist(self):
        """
        Return the distance between the camera and the camera target.
        """
        return self.sim.get_debug_visualizer()[10]

    @property
    def target_position(self):
        """
        Return the target of the camera in the Cartesian world space coordinates.
        """
        return self.sim.get_debug_visualizer()[11]

    @target_position.setter
    def target_position(self, pos):
        yaw, pitch, dist = self.sim.get_debug_visualizer()[-4:-1]
        self.sim.reset_debug_visualizer(dist, yaw, pitch, pos)

    @property
    def position(self):
        """
        Return the current position of the camera in the Cartesian world space coordinates.
        """
        Vinv = np.linalg.inv(self.V)  # compute inverse of the view matrix
        position = Vinv[:3, 3]  # the last column is the current position of the camera
        return position

    @position.setter
    def position(self, pos):
        self.sim.reset_debug_visualizer(dist, yaw, pitch, targetPos)

    @property
    def orientation(self):
        # based on forward_vector and up_vector
        pass

    @orientation.setter
    def orientation(self, orientation):
        pass

    def set_yaw_pitch(self, yaw, pitch, radian=True):
        if radian:
            yaw, pitch = np.rad2deg(yaw), np.rad2deg(pitch)
        dist, target_pos = self.sim.get_debug_visualizer()[-2:]
        self.sim.reset_debug_visualizer(dist, yaw, pitch, target_pos)

    def add_yaw_pitch(self, dyaw, dpitch, radian=True):
        yaw, pitch, dist, target_pos = self.sim.get_debug_visualizer()[-4:]
        if radian:
            dyaw, dpitch = np.rad2deg(dyaw), np.rad2deg(dpitch)
        yaw += dyaw
        pitch += dpitch
        self.sim.reset_debug_visualizer(dist, yaw, pitch, target_pos)

    def get_rgb_image(self):
        """
        Return the captured RGB image.
        """
        return self.get_rgba_image()[:, :, :3]

    def get_rgba_image(self):
        """
        Return the captured RGBA image. 'A' stands for alpha channel (for opacity/transparency)
        """
        width, height, view_matrix, projection_matrix = self.sim.get_debug_visualizer()[:4]
        img = np.array(self.sim.get_camera_image(width, height, view_matrix, projection_matrix)[2])
        img = img.reshape(width, height, 4)  # RGBA
        return img

    def get_depth_image(self):
        """
        Return the depth image.
        """
        width, height, viewMatrix, projectionMatrix = self.sim.get_debug_visualizer()[:4]
        img = np.array(self.sim.get_camera_image(width, height, viewMatrix, projectionMatrix)[3])
        img = img.reshape(width, height)
        return img

    def get_rgbad_image(self, concatenate=True):
        """
        Return the RGBA and depth images.
        """
        width, height, view_matrix, projection_matrix = self.sim.get_debug_visualizer()[:4]
        rgba, depth = self.sim.get_camera_image(width, height, view_matrix, projection_matrix)[2:4]
        rgba = np.array(rgba).reshape(width, height, 4)
        depth = np.array(depth).reshape(width, height)
        if concatenate:
            return np.dstack((rgba, depth))
        return (rgba, depth)

    def screen_to_world(self, x_screen, Vp_inv=None, P_inv=None, V_inv=None):
        """
        Return the corresponding coordinates in the Cartesian world space from the coordinates of a point
        on the screen.

        Args:
            x_screen (float[4]): augmented vector coordinates of a point on the screen
            Vp_inv (float[4,4])): inverse of viewport matrix
            P_inv (float[4,4]): inverse of projection matrix
            V_inv (float[4,4]): inverse of view matrix

        Returns:
            float[4]: augmented vector coordinates of the corresponding point in the world
        """
        if Vp_inv is None:
            Vp_inv = self.Vp_inv
        if P_inv is None:
            P_inv = self.Pinv
        if V_inv is None:
            V_inv = self.Vinv

        x_ndc = Vp_inv.dot(x_screen)
        x_ndc[1] = -x_ndc[1]  # invert y-axis
        x_ndc[2] = -x_ndc[2]  # invert z-axis
        x_eye = P_inv.dot(x_ndc)
        x_eye = x_eye / x_eye[3]  # normalize
        x_world = V_inv.dot(x_eye)
        return x_world

    def world_to_screen(self, x_world, V=None, P=None, Vp=None):
        """
        Return the corresponding screen coordinates from a 3D point in the world.

        Args:
            x_world (float[4]): augmented vector coordinates of a point in the Cartesian world space
            V (float[4,4], None): view matrix
            P (float[4,4], None): projection matrix
            Vp (float[4,4], None): viewport matrix

        Returns:
            float[4]: augmented vector coordinates of the corresponding point on the screen
        """
        if V is None: V = self.V
        if P is None: P = self.P
        if Vp is None: Vp = self.Vp

        x_eye = V.dot(x_world)
        x_clip = P.dot(x_eye)
        x_ndc = x_clip / x_clip[3]  # normalize
        x_ndc[1] = -x_ndc[1]  # invert y-axis (as y pointing upward in projection but should point downward in screen)
        x_ndc[2] = -x_ndc[2]  # invert z-axis (to get right-handed coord. system, -1=close and 1=far)
        x_screen = Vp.dot(x_ndc)    # for depth between 0(=close) and 1(=far)
        return x_screen


class World(object):
    r"""World class.

    The world contains all the objects that constitutes the world. This includes immovable objects such as the
    terrain/floor, walls, and so on, as well as movable objects such as the various robots, etc.
    Properties of the world are also defined here, such as gravity, friction, and other dynamical properties.

    The world is responsible to load the different objects part of the world and keeping a map of objects;
    based on where the agent(s) is(are), the objects will be removed or added from/to the simulator allowing it
    to run faster.

    It is independent of the simulator and environment used in RL, and is often provided as inputs to some
    `rewards/costs` and to the `environment`.
    A world can only be defined in a simulator. Because of this, robots (which normally should be part of the
    world) can be independent from this last one. This allows to use robots in reality where the world is already
    defined (i.e. the real world).

    For an excellent overview of available 3D models/scenes, check references [1, 2].

    References:
        [1] "3D Machine Learning": https://github.com/timzhang642/3D-Machine-Learning
        [2] Open3D: http://www.open3d.org/
    """

    def __init__(self, simulator, gravity=(0., 0., -9.81)):
        # set simulator
        self.simulator = simulator

        # By default, set the gravity
        self.gravity = gravity

        self.robots = {}
        self.movable_bodies = {}  # set()
        self.immovable_bodies = {}  # set()
        self.visual_objects = {}  # set()

        self.visual_shapes = {}
        self.map = None
        self.floor_id = -1

        self.quaternion_converter = QuaternionListConverter(convention=1)

        self.world_state = None

        # configure debug visualizer
        self.sim.configure_debug_visualizer(self.sim.COV_ENABLE_GUI, 0)

        # interfaces and bridges
        self.interfaces = set([])
        self.bridges = []

    ##############
    # Properties #
    ##############

    @property
    def simulator(self):
        """Return the simulator instance."""
        return self.sim

    @simulator.setter
    def simulator(self, simulator):
        """Set the simulator instance."""
        if not isinstance(simulator, Simulator):
            raise TypeError("Expecting the given simulator to be an instance of `Simulator`, instead got: "
                            "{}".format(type(simulator)))
        self.sim = simulator

    @property
    def main_camera(self):
        """Return the main camera of the simulator."""
        return WorldCamera(self.sim)

    @property
    def gravity(self):
        """Return the gravity vector."""
        return self._gravity

    @gravity.setter
    def gravity(self, gravity):
        """Set the gravity vector in the world.

        Args:
            gravity (np.float[3]): 3d gravity vector.
        """
        gravity = np.array(gravity)
        self.sim.set_gravity(gravity)
        self._gravity = gravity

    @property
    def lateral_friction(self):
        """Return the floor lateral friction coefficient."""
        if self.floor_id > 0:
            return self.sim.get_dynamics_info(self.floor_id, link_id=-1)[1]

    @lateral_friction.setter
    def lateral_friction(self, coefficient):
        """Set the floor lateral friction coefficient."""
        if self.floor_id > 0:
            self.sim.change_dynamics(body_id=self.floor_id, link_id=-1, lateral_friction=coefficient)

    @property
    def rolling_friction(self):
        """Return the floor rolling friction coefficient."""
        if self.floor_id > 0:
            return self.sim.get_dynamics_info(self.floor_id, -1)[6]

    @rolling_friction.setter
    def rolling_friction(self, coefficient):
        """Set the floor rolling friction coefficient."""
        if self.floor_id > 0:
            self.sim.change_dynamics(body_id=self.floor_id, link_id=-1, rolling_friction=coefficient)

    @property
    def spinning_friction(self):
        """Return the floor spinning friction coefficient."""
        if self.floor_id > 0:
            return self.sim.get_dynamics_info(self.floor_id, -1)[7]

    @spinning_friction.setter
    def spinning_friction(self, coefficient):
        """Set the spinning friction coefficient."""
        if self.floor_id > 0:
            self.sim.change_dynamics(body_id=self.floor_id, link_id=-1, spinning_friction=coefficient)

    @property
    def restitution(self):
        """Return the floor restitution (bounciness) coefficient."""
        if self.floor_id > 0:
            return self.sim.get_dynamics_info(self.floor_id, -1)[5]

    @restitution.setter
    def restitution(self, coefficient):
        """Set the floor restitution (bounciness) coefficient."""
        if self.floor_id > 0:
            self.sim.change_dynamics(body_id=self.floor_id, link_id=-1, restitution=coefficient)

    @property
    def contact_damping(self):
        """Return the floor contact damping."""
        if self.floor_id > 0:
            return self.sim.get_dynamics_info(self.floor_id, -1)[8]

    @contact_damping.setter
    def contact_damping(self, value):
        """Set the floor contact damping value."""
        if self.floor_id > 0:
            self.sim.change_dynamics(body_id=self.floor_id, link_id=-1, contact_damping=value)

    @property
    def contact_stiffness(self):
        """Return the floor contact stiffness."""
        if self.floor_id > 0:
            return self.sim.get_dynamics_info(self.floor_id, -1)[9]

    @contact_stiffness.setter
    def contact_stiffness(self, value):
        """Set the floor contact stiffness value."""
        if self.floor_id > 0:
            self.sim.change_dynamics(body_id=self.floor_id, link_id=-1, contact_stiffness=value)

    @property
    def floor_dynamics(self):
        """Return the floor dynamical parameters (friction, restitution, etc).

        Returns:
            float: lateral friction coefficient
            float: rolling friction coefficient
            float: spinning friction coefficient
            float: restitution coefficient
            float: contact damping value
            float: contact stiffness value
        """
        if self.floor_id > 0:
            info = self.sim.get_dynamics_info(self.floor_id, -1)
            return info[1], info[6], info[7], info[5], info[8], info[9]

    @floor_dynamics.setter
    def floor_dynamics(self, dynamics):
        """
        Set the floor dynamics.

        Args:
            dynamics (dict): dictionary of coefficients.
        """
        if self.floor_id > 0:
            self.sim.change_dynamics(body_id=self.floor_id, link_id=-1, **dynamics)

    ########################
    # Operator Overloading #
    ########################

    def __repr__(self):
        return self.__class__.__name__

    def __contains__(self, item):
        """
        Check if the given item is in the world.

        Args:
            item (int, Object, Robot): if it is an integer, it will check if the given object id is in the world.

        Returns:
            bool: True if the world contains the given item
        """
        if not isinstance(item, int):
            item = item.id

        return (item in self.robots) or (item in self.movable_bodies) or (item in self.immovable_bodies) \
                or (item in self.visual_objects)

    ###########
    # Methods #
    ###########

    def set_bridges(self, bridges):
        """
        This append the given bridges to various interfaces to the list of bridges.

        See `pyrobolearn.tools.interface` and `pyrobolearn.tools.bridge` for more information.

        Args:
            bridges (list, Bridge): list of bridges
        """
        if isinstance(bridges, collections.Iterable):
            for bridge in bridges:
                # if not isinstance(bridge, Bridge):
                #    raise TypeError("Expecting a list of bridges (must be an instance of Bridge)")
                if not has_method(bridge, 'step') and not has_variable(bridge, 'interface'):
                    raise TypeError("Expecting bridge to have a `step` method and an `interface` variable")
                if not has_method(bridge.interface, 'step'):
                    raise TypeError("Expecting the bridge.interface to have a `step` method")
                self.bridges.append(bridge)
                self.interfaces.add(bridge.interface)
        # elif isinstance(bridges, Bridge):
        elif has_method(bridges, 'step') and has_variable(bridges, 'interface') and has_method(bridges.interface, 'step'):
            self.bridges.append(bridges)
            self.interfaces.add(bridges.interface)
        else:
            raise TypeError("Expecting a bridge (instance of Bridge) or a list of instances of Bridge")

    def save(self, filename=None):
        """
        Save the world in the given filename, or in the RAM.

        Args:
            filename (str, None): path to file to save the state of the world. If None, it will save it in the main
                memory (RAM).

        Returns:
            str or int: filename, or unique state id.
        """
        # save approximate world state on the disk
        # self.sim.saveWorld(filename)
        self.world_state = self.sim.save(filename)
        return self.world_state

    def reset(self, world_state=None):
        """
        Reset the world. Put back each object where they were when added to the world.

        Args:
            world_state (int, str, None): world state id (int), or path to file (str). If None, it will restore the
                last saved world state.
        """
        if world_state is None:
            # save to current instance if not already saved
            if self.world_state is None:
                self.world_state = self.save()

            # reset world to a previous instance
            if isinstance(self.world_state, (int, str)):
                # load world from the disk / memory
                self.sim.load(self.world_state)
                # reset the robot
                # self.reset_robots()
            else:
                # reset simulation: remove all objects from the world and reset the world to initial conditions
                self.sim.reset()
        else:
            if isinstance(world_state, (int, float)):
                # load world state from memory / disk
                self.sim.load(world_state)
            else:
                raise TypeError("Expecting the world state to be an int (id) or a string (path to file), instead got "
                                "{}".format(type(world_state)))

    def reset_simulator(self):
        """
        Reset the simulator; remove the world from the simulator.
        """
        self.sim.reset()

    def step(self, sleep_dt=None):
        """
        Perform one step for the interfaces and bridges, and one step in the world/simulator.
        """
        for interface in self.interfaces:
            interface.step()
        for bridge in self.bridges:
            bridge.step()
        self.sim.step()
        if sleep_dt is not None:
            time.sleep(sleep_dt)

    def load_robot(self, robot, position=None, orientation=None, fixed_base=None, *args, **kwargs):
        """
        Load the robot into the world. If the robot parameter is a known robot name or the path to the urdf file,
        it will create a `Robot` instance and return it. If the robot is already an instance of `Robot` it will
        just add it to the list of objects present in the world.

        Args:
            robot (Robot, str, class): the robot instance or name. For the list of possible robot names, import
                `implemented_robots` from `pyrobolearn.robots` module.
            position (float[3], None): position of the robot. If None, it will take the default position.
            orientation (float[4], None): orientation of the robot. If None, it will be the default orientation.
            fixed_base (bool, None): if True, it will fix the robot's base. If None, it will be the default option.

        Return:
            Robot: instance of the Robot class
        """
        if isinstance(robot, Robot):  # the robot is already loaded, then add it to the list
            pass

        elif isinstance(robot, str):  # robot's name
            robot = robot.lower()

            if robot in robot_names_to_classes:
                robot_class = robot_names_to_classes[robot]
                robot = robot_class(self.sim, position=position, orientation=orientation, fixed_base=fixed_base,
                                    *args, **kwargs)

            else:  # robot is the path to the urdf
                robot = Robot(self.sim, urdf=robot, position=position, orientation=orientation, fixed_base=fixed_base,
                              *args, **kwargs)

        elif inspect.isclass(robot):  # robot class
            robot = robot(self.sim, position=position, orientation=orientation, fixed_base=fixed_base, *args, **kwargs)

        else:  # unknown type
            raise TypeError('Unknown type for robot: {}. It must be a string or '
                            'an instance of Robot'.format(type(robot)))

        self.robots[robot.id] = robot
        return robot

    def is_robot_id(self, robot_id):
        """
        Check if the given id is a robot id.

        Args:
            robot_id (int): the possible robot id

        Returns:
            bool: True if the id is a robot id, False otherwise
        """
        return robot_id in self.robots

    def get_robot(self, robot_id):
        """
        Return the robot object (instance of Robot) associated to the given robot id.

        Args:
            robot_id (int): unique id of the robot

        Raises:
            KeyError: if the given robot id is not in the world.

        Returns:
            Robot: robot instance
        """
        return self.robots[robot_id]

    def reset_robots(self):
        """
        Reset the base and joint states of each robot
        """
        for robot_id, robot in self.robots.items():
            # reset base
            self.sim.reset_base_pose(robot_id, robot.init_position, robot.init_orientation)
            self.sim.reset_base_velocity(robot_id, linear_velocity=[0, 0, 0], angular_velocity=[0, 0, 0])

            # reset joint positions
            positions = robot.init_joint_positions
            velocities = np.zeros(len(positions))
            for joint_id, position, velocity in zip(robot.joints, positions, velocities):
                self.sim.reset_joint_state(robot_id, joint_id, position, velocity)

    def load_urdf(self, filename, position, orientation, fixed_base=False, scale=1., name=None):
        """
        Load URDF specified by the given path. This is basically a wrapper around the simulator's `load_urdf` method.

        Args:
            filename (str): path to the URDF file
            position (float[3]): position of the object described in the URDF
            orientation (float[4]): orientation represented as a quaternion
            fixed_base (bool): if the base of the object should be fixed or not
            scale (float): scale factor for the object
            name (str, None): name of the object. If None, it will extract it from the URDF.

        Returns:
            int: unique id of the loaded body.
        """
        body = self.sim.load_urdf(filename, position, orientation, use_fixed_base=fixed_base, scale=scale)
        self.movable_bodies[body] = self.sim.get_body_info(body) if name is None else name
        return body

    def load_sdf(self, filename, scaling=1.):
        """
        Load the given SDF file; this will thus load all the object described in a SDF file.

        Args:
            filename (str): path to the SDF file
            scaling (float): scale factor for the object

        Returns:
            list(int): list of ids
        """
        bodies = self.sim.load_sdf(filename, scaling=scaling)
        for body in bodies:
            self.movable_bodies[body] = self.sim.get_body_info(body)
        return bodies

    def load_mjcf(self, filename, scaling=1.):
        """
        Load the given MJCF file; this will thus load all the object described in a MJCF file.

        Args:
            filename (str): path to the MJCF file
            scaling (float): scale factor for the object

        Returns:
            list(int): list of ids
        """
        bodies = self.sim.load_mjcf(filename, scaling=scaling)
        for body in bodies:
            self.movable_bodies[body] = self.sim.getBodyInfo(body)
        return bodies

    def _loadSDForURDF(self, path, position, orientation, scaling, objectType=None):
        extension_name = path.split('.')[-1]
        if extension_name == 'urdf':
            object_id = self.sim.load_urdf(path, position, orientation, scale=scaling)
            self.movable_bodies[object_id] = 'urdf' if objectType is None else objectType
        elif extension_name == 'sdf':
            object_id = self.sim.loadSDF(path, scale=scaling) # list of ids
            for i in object_id: # assume for now that the objects are movable...
                self.movable_bodies[i] = 'sdf' if objectType is None else objectType
        else:
            raise ValueError('Extension name of the file is not known; this method only accepts URDF/SDF files.')
        return object_id

    def load_object(self, object_type, path=None, position=(0, 0, 0), orientation=(0, 0, 0, 1), scaling=1.):
        """
        Load the specified object. This is a method that allows you to quickly load stuffs however it is less
        accurate than other methods in this class.

        Args:
            object_type (str): type of the object (name, 'sphere',
            path:
            position:
            orientation:
            scaling:

        Returns:
            int or int[]: object ids
        """
        # check if an object has already been loaded at that place.

        if path is not None:
            object_id = self._loadSDForURDF(path, position, orientation, scaling=1., objectType=object_type)
        else:
            if object_type == 'sphere':
                object_id = self.load_sphere(position)
            elif object_type == 'box':
                object_id = self.load_box(position, orientation)
            elif object_type == 'cylinder':
                object_id = self.load_cylinder(position, orientation)
            elif object_type == 'capsule':
                object_id = self.load_capsule(position, orientation)
            else:
                raise TypeError("Object type not known...")

        return object_id

    def move_object(self, object_id, position=None, orientation=None):
        """
        Move the given object at the specified position and orientation.

        Args:
            object_id (int): object id
            position (float[3]): new position of the object. If None, it will keep the old position.
            orientation (float[4]): new orientation of the object. If None, it will keep the old orientation.

        Returns:
            None
        """
        if position is None:
            position = self.sim.get_base_pose(object_id)[0]
        if orientation is None:
            orientation = self.sim.get_base_pose(object_id)[1]
        self.sim.reset_base_pose(object_id, position, orientation)

    def apply_force(self, object_id, link_id=-1, force=(0., 0., 0.), position=None, frame=2):
        """
        Apply the given force on the specified object or link of the object.

        Warnings:
            - after each simulation step, the external forces are cleared to 0.
            - this does not work when using `sim.setRealTimeSimulation(1)`.

        Args:
            object_id (int): object id to apply the force on
            link_id (int): link id to apply the force, if -1 it will apply the force on the base
            force (float[3]): Cartesian forces to be applied on the body
            position (float[3]): position on the link where the force is applied. If None, it is the center of mass
                of the object (or the link if specified)
            frame (int): allows to specify the coordinate system of force/position. sim.LINK_FRAME (=1) for local
                link frame, and sim.WORLD_FRAME (=2) for world frame. By default, it is the world frame.

        Returns:
            None
        """
        if position is None:
            if link_id != -1:
                position = self.sim.get_base_pose(object_id)[0]
            else:
                position = self.sim.get_link_state(object_id, link_id)[0]
        self.sim.apply_external_force(object_id, link_id, force, position, frame)

    def get_object_color(self, object_id):
        """
        Return the RGBA color of the given object.

        Args:
            object_id (int): object id

        Returns:
            float[4]: RGBA color
        """
        return self.sim.get_visual_shape_data(object_id)[-1]

    def change_object_color(self, object_id, color, link_id=-1):
        """
        Change the color of the given object.

        Args:
            object_id (int): object id
            color (float[4]): RGBA color
            link_id (int): link id

        Returns:
            None
        """
        self.sim.change_visual_shape(object_id, link_id, rgba_color=color)

    def get_object_position(self, object_id):
        """
        Return the position of the given object.

        Args:
            object_id (int): object id

        Returns:
            float[3]: position of the object
        """
        return np.array(self.sim.get_base_pose(object_id)[0])

    def get_object_orientation(self, object_id):
        """
        Return the orientation of the given object.

        Args:
            object_id (int): object id

        Returns:
            float[4]: orientation of the object
        """
        return np.array(self.sim.get_base_pose(object_id)[1])

    def get_object_velocity(self, object_id):
        """
        Return the linear and angular velocities of the given object.

        Args:
            object_id (int): object id

        Returns:
            float[6]: linear and angular velocities of the object
        """
        lin_vel, ang_vel = self.sim.get_base_velocity(object_id)
        return np.array(lin_vel + ang_vel)

    def get_object_linear_velocity(self, object_id):
        """
        Return the linear velocity of the given object.

        Args:
            object_id (int): object id

        Returns:
            float[3]: linear velocity of the object
        """
        return np.array(self.sim.get_base_velocity(object_id)[0])

    def get_object_angular_velocity(self, object_id):
        """
        Return the angular velocity of the given object.

        Args:
            object_id (int): object id

        Returns:
            float[3]: angular velocity of the object
        """
        return np.array(self.sim.get_base_velocity(object_id)[1])

    def hide_object(self, object_id):
        """
        Hide (visually) the given object; by making it transparent.

        Args:
            object_id (int): object id

        Returns:
            None
        """
        color = self.get_object_color(object_id)
        color[-1] = 0.
        self.change_object_color(object_id, color=color)

    def show_object(self, object_id):
        """
        Show (visually) a hidden object; by making it opaque.

        Args:
            object_id (int): object id

        Returns:
            None
        """
        color = self.get_object_color(object_id)
        color[-1] = 1.
        self.change_object_color(object_id, color=color)

    def remove(self, body):
        """
        Remove the object specified by its unique id from the world/simulator.

        Args:
            body (int, Robot): unique id of the object in the simulator.

        Returns:
            bool: True if succeeded, False if not. This method does not raise any errors.
        """
        if isinstance(body, Robot):
            body = body.id
        if body in self.robots:
            self.robots.pop(body)
        elif body in self.movable_bodies:
            self.movable_bodies.pop(body)
        elif body in self.immovable_bodies:
            self.immovable_bodies.pop(body)
        elif body in self.visual_objects:
            self.visual_objects.pop(body)
        else:
            return False

        self.sim.remove_body(body)
        return True

    def get_object_dimensions(self, object_id):
        """
        Return the object dimensions of the given object.

        Args:
            object_id (int): object id

        Returns:
            float[3]: dimensions of the object
        """
        return np.array(self.sim.get_visual_shape_data(object_id)[3])

    def change_object_scale(self, object_id, scale=(1., 1., 1.)):
        """
        Change the scale of the given object; it changes the scale for the visual and collision shapes.

        Args:
            object_id (int): object id
            scale (float[3]): scaling factors in each direction

        Returns:
            None
        """
        # TODO: currently not possible in PyBullet
        raise NotImplementedError

    def get_object_aabb(self, object_id, link_id=-1):
        """
        Return the axis-aligned bounding box (AABB) in world space of the given object.

        Args:
            object_id (int): object id
            link_id (int): optional link id

        Returns:
            float[3]: coordinates in world space of the min corner of the AABB
            float[3]: coordinates in world space of the max corner of the AABB
        """
        aabb_min, aabb_max = self.sim.get_aabb(object_id, link_id)
        return np.array(aabb_min), np.array(aabb_max)

    def get_object_ids_in_aabb(self, aabb_min, aabb_max):
        """
        Get the list of object ids that have AABB overlap with a given AABB.

        Args:
            aabb_min (float[3]): coordinates of the min corner of the bounding box
            aabb_max (float[3]): coordinates of the max corner of the bounding box

        Returns:
            int[N]: list of object ids
        """
        overlapping_objects = self.sim.get_overlapping_objects(aabb_min, aabb_max)
        if overlapping_objects is None:
            return []
        return overlapping_objects

    def is_there_an_object(self, aabb_min, aabb_max, except_floor=True):
        """
        Return True if there is an object in the bounding box defined by aabb_min and aabb_max.

        Args:
            aabb_min (float[3]): minimum coordinates of the bounding box
            aabb_max (float[3]): maximum coordinates of the bounding box
            except_floor (bool): if the floor should be counted as an object

        Returns:
            bool: True if there is an object in the specified bounding box
        """
        objects = self.sim.get_overlapping_objects(aabb_min, aabb_max)
        if len(objects) > 2:
            return True
        if len(objects) == 0:
            return False
        idx = objects[0]
        if idx == self.floor_id and except_floor:
            return False
        return True

    def get_closest_object(self):  # Not possible for now
        raise NotImplementedError

    def get_closest_objects(self, radius):  # Not possible for now
        raise NotImplementedError

    def load_floor(self, scaling=1.):
        """
        Load a basic floor in the world.

        Args:
            scaling (float): scaling for the floor.

        Returns:
            int: unique id of the floor in the world
        """
        # self.floor_id = self.sim.load_urdf('plane100.urdf', use_fixed_base=True, scale=scaling)
        self.floor_id = self.sim.load_urdf('plane.urdf', use_fixed_base=True, scale=scaling)
        return self.floor_id

    def load_terrain(self, heightmap, position=(0., 0., 0.), scaling=1., replace_floor=True):
        """
        Load the given terrain/heightmap.

        Args:
            heightmap (str, np.array[heigth,width]): path to the urdf, sdf, xml, or obj file of the terrain. It can
                also be the path to a heightmap in tif, jpg, or png format. Alternatively, it can represents
                the heightmap as a 2D numpy array where the values represent the height in meters.
            position (float[3]): position of the terrain. By default, origin of the world.
            scaling (float): scaling factor of the terrain
            replace_floor (bool): if True, it will replace the existing floor. Be careful, that it can cause
                problems with collision.

        Returns:
            int: unique id of the terrain.

        Modules to create mesh files (.obj):
        - `mayavi`: https://docs.enthought.com/mayavi/mayavi/
        - `openmesh`: https://www.openmesh.org/media/Documentations/OpenMesh-6.2-Documentation/a00036.html
        - `bpy`: Blender python API - https://docs.blender.org/api/current/
        """
        if self.floor_id > -1:  # there is already a floor defined
            if replace_floor:
                self.sim.remove_body(self.floor_id)

        if heightmap[-4:] == 'obj':  # obj (mesh)
            self.floor_id = self.load_mesh(heightmap, position, mass=0., scale=[scaling] * 3, flags=1,
                                           object_type='terrain')
        elif heightmap[-4:] == '.sdf':  # SDF
            self.floor_id = self.load_sdf(filename=heightmap, scaling=scaling)
        elif heightmap[-4:] == '.xml':  # MJCF
            self.floor_id = self.load_mjcf(filename=heightmap, scaling=scaling)
        elif heightmap[-5:] == '.urdf':  # URDF
            self.floor_id = self.sim.load_urdf(heightmap, position, use_fixed_base=True, scale=scaling)
        else:  # heightmap (.tif, .jpg, .png, etc)
            def create_mesh(heightmap):
                # create 3D mesh
                # create3DMesh(heightmap, filename=, subsample=, interpolate_fct=)
                pass

            # create process to create the 3D mesh
            process = multiprocessing.Process(target=create_mesh, args=(heightmap,))
            process.start()
            process.join()

            # remove mesh from memory
            os.remove(filename + '.obj')  # remove mesh from memory
            # os.remove(filename + '.mtl')

            # apply the given texture if provided
            if isinstance(texture, str):
                texture = self.sim.load_texture(texture)
                self.sim.change_visual_shape(heightmap, -1, texture_id=texture)

        return self.floor_id

    def load_heightmap(self, heightmap, texture=None, position=(0., 0., 0.), scale=1.):
        """
        Load a heightmap for the terrain.

        Args:
            heightmap (str, np.ndarray[M,M]): if string, filename containing the heightmap in  the png, jpg, obj format
                if a 2D numpy arrays, the values represent the height in meters.
            texture: texture to apply
            position (float[3]): position of the terrain
            scale (float): scaling factor

        Returns:
            int: unique id of the floor

        Modules to create mesh files (.obj):
        - `mayavi`: https://docs.enthought.com/mayavi/mayavi/
        - `openmesh`: https://www.openmesh.org/media/Documentations/OpenMesh-6.2-Documentation/a00036.html
        - `bpy`: Blender python API - https://docs.blender.org/api/current/
        """

        extension, filename = None, 'generated_file'

        # if string, get the extension and name of the file
        if isinstance(heightmap, str):
            extension = heightmap.split('.')[-1]
            filename = heightmap[:-4]

            # if picture (png/jpg), load 2D array (grayscale values)
            if extension == 'png' or extension == 'jpg':
                heightmap = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)

        # if 2D numpy array, create the mesh (in the .obj format)
        if isinstance(heightmap, np.ndarray):
            heightmap = heightmap.astype(np.float)
            mlab.surf(heightmap)
            mlab.savefig(filename + '.obj')
            mlab.close()
            # TODO: set the map of the world

        elif extension != 'obj':
            raise ValueError("Expecting heightmap in a png/jpg/obj format")

        # load the mesh of the terrain
        heightmap = self.load_terrain(filename, position=position, scaling=scale)

        # change the dynamic properties of the terrain based on the given type (grass, mud, bumpy
        # WARNING: only 1 type can be specified. Currently, it is not possible to have different dynamic properties
        # for different parts of the terrain. Loading multiple terrains is currently not supported (there is only
        # 1 unique id for the floor).

        # apply the given texture if provided
        if isinstance(texture, str):
            texture = self.sim.load_texture(texture)
            self.sim.change_visual_shape(heightmap, -1, texture_id=texture)

        # remove mesh from memory
        os.remove(filename + '.obj') # remove mesh from memory
        os.remove(filename + '.mtl')

        # replace the floor if there is already one present
        if self.floor_id > -1:
            self.sim.remove_body(self.floor_id)
        self.floor_id = heightmap

        return self.floor_id

    # aliases
    loadDEM = load_heightmap

    def generateHeightmap(self, filename=None, algo=None):
        """
        Generate a heightmap (png) using the specified algorithm. We provide 4 algorithms to generate this last one:
        1. Random
        2. Diamond algorithm
        3.
        4.

        By default, the diamond algorithm is used.

        Args:
            filename (None, str): if not None, it will save the heightmap in the format specified by the filename.
                The format is inferred from the filename. Supported ones include '.png', '.jpg', and '.obj'.

        Returns:
            np.ndarray: heightmap
        """
        pass

    def generate_terrain(self, filename=None):
        pass

    def load_stadium(self, scaling=1.):
        """
        Load a stadium as the floor.

        Args:
            scaling (float): scaling for the stadium.

        Returns:
            int: unique id of the floor/stadium in the world
        """
        if self.floor_id > -1:
            self.sim.remove_body(self.floor_id)
        self.floor_id = self.sim.load_urdf('stadium.urdf', use_fixed_base=True, scale=scaling)
        return self.floor_id

    def load_japanese_monastery(self, scaling=1.):
        """
        Load a japanese monastery.

        Args:
            scaling (float): scaling for the japanese monastery

        Returns:
            int: unique id of the monastery
        """
        # replace the floor if there is already one present
        if self.floor_id > -1:
            self.sim.remove_body(self.floor_id)
        self.floor_id = self.sim.load_urdf('samurai.urdf', use_fixed_base=True, scale=scaling)
        return self.floor_id

    def load_bot_lab(self, scaling=2.):
        return self.load_sdf('sdf/botlab/botlab.sdf', scaling=scaling)

    def load_stairs(self):
        pass

    def createCity(self):
        pass

    def createParkour(self):
        pass

    def createMountainWithPath(self):
        pass

    def loadTable(self, position, scaling=1.):
        """
        Load a table in the world.

        Args:
            position (float[3]): position of the table
            scaling (float): scaling for the table

        Returns:
            int: unique id of the table
        """
        table = self.sim.load_urdf('table/table.urdf', scale=scaling)
        self.movable_bodies[table] = 'table'
        return table

    def load_kiva_shelf(self, scaling=1.):
        """
        Load a Kiva shelf.

        Args:
            scaling (float): scaling of the shelf

        Returns:
            int: unique id of the shelf
        """
        shelf = self.sim.loadSDF('kiva_shelf/model.sdf', scale=scaling)[0]
        self.movable_bodies[shelf] = 'shelf'
        return shelf

    def load_visual_Sphere(self, position, radius=0.5, color=None):
        """
        Load a visual sphere in the world (only available in the simulator).

        Args:
            position (float[3]): position of the sphere in Cartesian world space (in meters)
            radius (float): radius of the sphere (in meters)
            color (int[4]): color of the sphere (by default: white and opaque)

        Returns:
            int: unique id of the visual sphere in the world
        """
        visual_shape = self.sim.create_visual_shape(self.sim.GEOM_SPHERE, radius=radius, rgba_color=color)
        sphere = self.sim.create_body(visual_shape_id=visual_shape, mass=0., position=position)
        self.visual_objects[sphere] = 'sphere'
        return sphere

    def load_sphere(self, position, mass=1., radius=0.5, color=None):
        """
        Load a sphere in the world (only available in the simulator).

        Args:
            position (float[3]): position of the sphere in Cartesian world space (in meters)
            mass (float): mass of the sphere (in kg). If mass = 0, the sphere won't move even if there is a collision.
            radius (float): radius of the sphere (in meters).
            color (int[4]): color of the sphere (by default: white and opaque)

        Returns:
            int: unique id of the sphere in the world
        """
        collision_shape = self.sim.create_collision_shape(self.sim.GEOM_SPHERE, radius=radius)
        visual_shape = self.sim.create_visual_shape(self.sim.GEOM_SPHERE, radius=radius, rgba_color=color)
        sphere = self.sim.create_body(mass=mass, collision_shape_id=collision_shape, visual_shape_id=visual_shape,
                                      position=position)
        if mass == 0.0:
            self.immovable_bodies[sphere] = 'sphere'
        else:
            self.movable_bodies[sphere] = 'sphere'

        return sphere

    def load_visual_box(self, position, orientation=(0, 0, 0, 1), dimensions=(1., 1., 1.), color=None):
        """
        Load a visual box in the world (only available in the simulator).

        Args:
            position (float[3]): position of the box in the Cartesian world space (in meters)
            orientation (float[4]): orientation of the box using quaternion [x,y,z,w].
            dimensions (float[3]): dimensions of the box
            color (int[4]): color of the box (by default: white and opaque)

        Returns:
            int: unique id of the box in the world
        """
        dimensions = np.array(dimensions) / 2.
        visual_shape = self.sim.create_visual_shape(self.sim.GEOM_BOX, half_extents=dimensions, rgba_color=color)
        box = self.sim.create_body(mass=0., visual_shape_id=visual_shape, position=position, orientation=orientation)
        self.visual_objects[box] = 'box'
        return box

    def load_box(self, position, orientation=(0, 0, 0, 1), mass=1., dimensions=(1., 1., 1.), color=None):
        """
        Load a box in the world (only available in the simulator).

        Args:
            position (float[3]): position of the box in the Cartesian world space (in meters)
            orientation (float[4]): orientation of the box using quaternion [x,y,z,w].
            mass (float): mass of the box (in kg). If mass = 0, the box won't move even if there is a collision.
            dimensions (float[3]): dimensions of the box
            color (int[4]): color of the box (by default: white and opaque)

        Returns:
            int: unique id of the box in the world
        """
        dimensions = np.array(dimensions) / 2.
        collision_shape = self.sim.create_collision_shape(self.sim.GEOM_BOX, half_extents=dimensions)
        visual_shape = self.sim.create_visual_shape(self.sim.GEOM_BOX, half_extents=dimensions, rgba_color=color)
        
        box = self.sim.create_body(mass=mass, collision_shape_id=collision_shape, visual_shape_id=visual_shape,
                                   position=position, orientation=orientation)

        if mass == 0.0:
            self.immovable_bodies[box] = 'box'
        else:
            self.movable_bodies[box] = 'box'
        return box

    def load_visual_cylinder(self, position, orientation=(0, 0, 0, 1), radius=0.5, height=1., color=None):
        """
        Load a visual cylinder in the world (only available in the simulator).

        Args:
            position (float[3]): position of the cylinder in the Cartesian world space (in meters)
            orientation (float[4]): orientation of the cylinder using quaternion [x,y,z,w].
            radius (float): radius of the cylinder (in meters)
            height (float): height of the cylinder (in meters)
            color (int[4]): color of the cylinder (by default: white and opaque)

        Returns:
            int: unique id of the cylinder in the world
        """
        visual_shape = self.sim.create_visual_shape(self.sim.GEOM_CYLINDER, radius=radius, length=height,
                                                    rgba_color=color)
        
        cylinder = self.sim.create_body(mass=0., visual_shape_id=visual_shape, position=position,
                                        orientation=orientation)
        self.visual_objects[cylinder] = 'cylinder'
        return cylinder

    def load_cylinder(self, position, orientation=(0, 0, 0, 1), mass=1., radius=0.5, height=1., color=None):
        """
        Load a cylinder in the world (only available in the simulator).

        Args:
            position (float[3]): position of the cylinder in the Cartesian world space (in meters)
            orientation (float[4]): orientation of the cylinder using quaternion [x,y,z,w].
            mass (float): mass of the cylinder (in kg). If mass = 0, it won't move even if there is a collision.
            radius (float): radius of the cylinder (in meters)
            height (float): height of the cylinder (in meters)
            color (int[4]): color of the cylinder (by default: white and opaque)

        Returns:
            int: unique id of the cylinder in the world
        """
        collision_shape = self.sim.create_collision_shape(self.sim.GEOM_CYLINDER, radius=radius, height=height)
        visual_shape = self.sim.create_visual_shape(self.sim.GEOM_CYLINDER, radius=radius, length=height,
                                                    rgba_color=color)
        
        cylinder = self.sim.create_body(mass=mass, collision_shape_id=collision_shape, visual_shape_id=visual_shape,
                                        position=position, orientation=orientation)

        if mass == 0.0:
            self.immovable_bodies[cylinder] = 'cylinder'
        else:
            self.movable_bodies[cylinder] = 'cylinder'
        return cylinder

    def load_visual_capsule(self, position, orientation=(0, 0, 0, 1), radius=0.5, height=1., color=None):
        """
        Load a visual capsule in the world (only available in the simulator).

        Args:
            position (float[3]): position of the capsule in the Cartesian world space (in meters)
            orientation (float[4]): orientation of the capsule using quaternion [x,y,z,w].
            radius (float): radius of the capsule (in meters)
            height (float): height of the capsule (in meters)
            color (int[4]): color of the capsule (by default: white and opaque)

        Returns:
            int: unique id of the capsule in the world
        """
        height = height/2.
        visual_shape = self.sim.create_visual_shape(self.sim.GEOM_CAPSULE, radius=radius, length=height,
                                                    rgba_color=color)
        
        capsule = self.sim.create_body(mass=0., visual_shape_id=visual_shape, position=position,
                                       orientation=orientation)

        self.visual_objects[capsule] = 'capsule'
        return capsule

    def load_capsule(self, position, orientation=(0, 0, 0, 1), mass=1., radius=0.5, height=1., color=None):
        """
        Load a capsule in the world (only available in the simulator).

        Args:
            position (float[3]): position of the capsule in the Cartesian world space (in meters)
            orientation (float[4]): orientation of the capsule using quaternion [x,y,z,w].
            mass (float): mass of the capsule (in kg). If mass = 0, it won't move even if there is a collision.
            radius (float): radius of the capsule (in meters)
            height (float): height of the capsule (in meters)
            color (int[4]): color of the capsule (by default: white and opaque)

        Returns:
            int: unique id of the capsule in the world
        """
        height = height / 2.
        collision_shape = self.sim.create_collision_shape(self.sim.GEOM_CAPSULE, radius=radius, height=height)
        visual_shape = self.sim.create_visual_shape(self.sim.GEOM_CAPSULE, radius=radius, length=height,
                                                    rgba_color=color)
        
        capsule = self.sim.create_body(mass=mass, collision_shape_id=collision_shape, visual_shape_id=visual_shape,
                                       position=position, orientation=orientation)
        if mass == 0.0:
            self.immovable_bodies[capsule] = 'capsule'
        else:
            self.movable_bodies[capsule] = 'capsule'
        return capsule

    def load_visual_mesh(self, filename, position, orientation=(0, 0, 0, 1), scale=(1., 1., 1.), color=None,
                         object_type='mesh'):
        """
        Load a visual mesh in the world (only available in the simulator).

        Args:
            filename (str): path to file for the mesh. Currently, only Wavefront .obj. It will create convex hulls
                for each object (marked as 'o') in the .obj file.
            position (float[3]): position of the mesh in the Cartesian world space (in meters)
            orientation (float[4]): orientation of the mesh using quaternion [x,y,z,w].
            scale (float[3]): scale the mesh in the (x,y,z) directions
            color (int[4]): color of the mesh (by default: white and opaque)

        Returns:
            int: unique id of the mesh in the world
        """
        mesh = self.sim.load_mesh(filename, position, orientation, mass=0., scale=scale, color=color,
                                  with_collision=False)
        self.visual_objects[mesh] = object_type
        return mesh

    def load_mesh(self, filename, position, orientation=(0, 0, 0, 1), mass=1., scale=(1., 1., 1.), color=None,
                  flags=None, object_type='mesh'):
        """
        Load a mesh in the world (only available in the simulator).

        Args:
            filename (str): path to file for the mesh. Currently, only Wavefront .obj. It will create convex hulls
                for each object (marked as 'o') in the .obj file.
            position (float[3]): position of the mesh in the Cartesian world space (in meters)
            orientation (float[4]): orientation of the mesh using quaternion [x,y,z,w].
            mass (float): mass of the mesh (in kg). If mass = 0, it won't move even if there is a collision.
            scale (float[3]): scale the mesh in the (x,y,z) directions
            color (int[4]): color of the mesh (by default: white and opaque)
            flags (int, None): if flag = `sim.GEOM_FORCE_CONCAVE_TRIMESH` (=1), this will create a concave static
                triangle mesh. This should not be used with dynamic/moving objects, only for static (mass=0) terrain.

        Returns:
            int: unique id of the mesh in the world
        """
        mesh = self.sim.load_mesh(filename, position, orientation, mass, scale, color, with_collision=True,
                                  flags=flags)
        if mass == 0.0:
            self.immovable_bodies[mesh] = object_type
        else:
            self.movable_bodies[mesh] = object_type
        return mesh

    # The following commented code does not work currently because URDF_GEOM_PLANE is not set in Bullet
    # Note that a plane can be seen as a thin box.
    # def load_visual_plane(self, position, orientation, normal=(0.,0.,1.), color=(1,1,1,1)):
    #     """
    #     Load a visual plane in the world (only available in the simulator).
    #
    #     Args:
    #         position (float[3]): position of the plane in the Cartesian world space (in meters)
    #         orientation (float[4]): orientation of the plane using quaternion [x,y,z,w].
    #         normal (float[3]): normal to the plane
    #         color (int[4]): color of the plane (by default: white and opaque)
    #
    #     Returns:
    #         int: unique id of the plane in the world
    #     """
    #     visual_shape = self.sim.create_visual_shape(self.sim.GEOM_PLANE, planeNormal=normal, rgba_color=color)
    #     
    #     plane = self.sim.create_body(mass=0.,
    #                                     visual_shape_id=visual_shape,
    #                                     position=position,
    #                                     orientation=orientation)
    #     self.visual_objects[plane] = 'plane'
    #     return plane
    #
    # def load_plane(self, position, orientation, mass=1., normal=(0.,0.,1.), color=(1,1,1,1)):
    #     """
    #     Load a plane in the world (only available in the simulator).
    #
    #     Args:
    #         position (float[3]): position of the plane in the Cartesian world space (in meters)
    #         orientation (float[4]): orientation of the plane using quaternion [x,y,z,w].
    #         mass (float): mass of the plane (in kg). If mass = 0, it won't move even if there is a collision.
    #         normal (float[3]): normal to the plane
    #         color (int[4]): color of the plane (by default: white and opaque)
    #
    #     Returns:
    #         int: unique id of the plane in the world
    #     """
    #     collision_shape = self.sim.create_collision_shape(self.sim.GEOM_PLANE, planeNormal=normal)
    #     visual_shape = self.sim.create_visual_shape(self.sim.GEOM_PLANE, planeNormal=normal, rgba_color=color)
    #     
    #     plane = self.sim.create_body(mass=mass,
    #                                      collision_shape_id=collision_shape,
    #                                      visual_shape_id=visual_shape,
    #                                      position=position,
    #                                      orientation=orientation)
    #     if mass == 0.0:
    #         self.immovable_bodies[plane] = 'plane'
    #     else:
    #         self.movable_bodies[plane] = 'plane'
    #     return plane

    # Temporary because the code above doesn't work
    def load_plane(self, position=(0., 0., 0.), orientation=(0., 0., 0., 1.), scale=1.):
        """
        Load a plane in the world (only available in the simulator)

        Args:
            position (float[3]): position of the plane
            orientation (float[4]): orientation of the plane
            scale (float): scale factor of the plane

        Returns:
            int: unique id of the plane
        """
        plane = self.sim.load_urdf('plane.urdf', position, orientation, use_fixed_base=True, scale=scale)
        self.immovable_bodies[plane] = plane
        return plane

    def load_visual_ellipsoid(self, position, orientation=(0, 0, 0, 1), scale=(1., 1., 1.), color=None):
        """
        Load a visual ellipsoid (using a mesh) in the world (only available in the simulator).

        Args:
            position (float[3]): position in the Cartesian world space (in meters)
            orientation (float[4]): orientation using quaternion [x,y,z,w].
            scale (float[3]): scale in the (x,y,z) directions
            color (int[4]): color (by default: white and opaque)

        Returns:
            int: unique id of the ellipsoid in the world
        """
        filename = os.path.dirname(__file__) + '/meshes/ellipsoid.obj'
        return self.load_visual_mesh(filename, position, orientation, scale=scale, color=color)

    def load_ellipsoid(self, position, orientation=(0, 0, 0, 1), mass=1., scale=(1., 1., 1.), color=None):
        """
        Load a ellipsoid (using a mesh) in the world (only available in the simulator).

        Args:
            position (float[3]): position in the Cartesian world space (in meters)
            orientation (float[4]): orientation using quaternion [x,y,z,w].
            mass (float): mass [kg]
            scale (float[3]): scale in the (x,y,z) directions
            color (int[4]): color (by default: white and opaque)

        Returns:
            int: unique id of the ellipsoid in the world
        """
        filename = os.path.dirname(__file__) + '/meshes/ellipsoid.obj'
        return self.load_mesh(filename, position, orientation, mass=mass, scale=scale, color=color)

    def load_visual_right_triangular_prism(self, position, orientation=(0, 0, 0, 1), scale=(1., 1., 1.),
                                           color=None):
        """
        Load a visual right triangular prism (using a mesh) in the world (only available in the simulator).

        Args:
            position (float[3]): position in the Cartesian world space (in meters)
            orientation (float[4]): orientation using quaternion [x,y,z,w].
            scale (float[3]): scale in the (x,y,z) directions
            color (int[4]): color (by default: white and opaque)

        Returns:
            int: unique id of the triangular prism in the world
        """
        filename = os.path.dirname(__file__) + '/meshes/right_triangular_prism.obj'
        return self.load_visual_mesh(filename, position, orientation, scale=scale, color=color)

    def load_right_triangular_prism(self, position, orientation=(0, 0, 0, 1), mass=1., scale=(1., 1., 1.),
                                    color=None):
        """
        Load a right triangular prism (using a mesh) in the world (only available in the simulator).

        Args:
            position (float[3]): position in the Cartesian world space (in meters)
            orientation (float[4]): orientation using quaternion [x,y,z,w].
            mass (float): mass [kg]
            scale (float[3]): scale in the (x,y,z) directions
            color (int[4]): color (by default: white and opaque)

        Returns:
            int: unique id of the triangular prism in the world
        """
        filename = os.path.dirname(__file__) + '/meshes/right_triangular_prism.obj'
        return self.load_mesh(filename, position, orientation, mass=mass, scale=scale, color=color)

    def load_visual_cone(self, position, orientation=(0, 0, 0, 1), scale=(1., 1., 1.), color=None):
        """
        Load a visual cone (using a mesh) in the world (only available in the simulator).

        Args:
            position (float[3]): position in the Cartesian world space (in meters)
            orientation (float[4]): orientation using quaternion [x,y,z,w].
            scale (float[3]): scale in the (x,y,z) directions
            color (int[4]): color (by default: white and opaque)

        Returns:
            int: unique id of the cone in the world
        """
        filename = os.path.dirname(__file__) + '/meshes/cone.obj'
        return self.load_visual_mesh(filename, position, orientation, scale=scale, color=color)

    def load_cone(self, position, orientation=(0, 0, 0, 1), mass=1., scale=(1., 1., 1.), color=None):
        """
        Load a visual cone (using a mesh) in the world (only available in the simulator).

        Args:
            position (float[3]): position in the Cartesian world space (in meters)
            orientation (float[4]): orientation using quaternion [x,y,z,w].
            mass (float): mass [kg]
            scale (float[3]): scale in the (x,y,z) directions
            color (int[4]): color (by default: white and opaque)

        Returns:
            int: unique id of the cone in the world
        """
        filename = os.path.dirname(__file__) + '/meshes/cone.obj'
        return self.load_mesh(filename, position, orientation, mass=mass, scale=scale, color=color)

    def load_visual_arrow(self, position, orientation=(0, 0, 0, 1), scale=(1., 1., 1.), color=None):
        pass

    def load_arrow(self, position, orientation=(0, 0, 0, 1), mass=1., scale=(1., 1., 1.), color=None):
        pass

    def distribute_objects(self, distributor, objects):
        pass

    def get_dynamics_info(self, body_id, link_id=-1):
        """
        Return the dynamics information about objects that are in the world.

        Args:
            body_id (int): object unique id.
            link_id (int): link index (or -1 for the base).

        Returns:
            float: mass in kg
            float: lateral friction coefficient
            np.array[3]: local inertia diagonal
            np.array[3]: position of inertial frame in local coordinates of joint frame
            np.array[4]: orientation of inertial frame in local coordinates of joint frame
            float: restitution coefficient (if 0, the object does not bounce)
            float: rolling friction coefficient orthogonal to contact normal
            float: spinning friction coefficient around contact normal
            float: -1 if not available, damping of contact constraints
            float: -1 if not available, stiffness contact constraints
        """
        return self.sim.get_dynamics_info(body_id, link_id)

    def print_dynamics_info(self, body_id, link_id=-1):
        """
        Print the dynamics information related to the given body id and link id.

        Args:
            body_id (int): object unique id.
            link_id (int): link index (or -1 for the base).
        """
        info = self.sim.get_dynamics_info(body_id, link_id)
        print("Mass: {}".format(info[0]))
        print("Lateral friction coefficient: {}".format(info[1]))
        print("Local inertia diagonal: {}".format(info[2]))
        print("Local inertial position: {}".format(info[3]))
        print("Local inertial orientation (quat=[x,y,z,w]): {}".format(info[4]))
        print("Restitution coefficient (bounciness): {}".format(info[5]))
        print("Rolling friction coefficient: {}".format(info[6]))
        print("Spinning friction coefficient: {}".format(info[7]))
        print("Contact damping coefficient (-1 if not available): {}".format(info[8]))
        print("Contact stiffness coefficient (-1 if not available): {}".format(info[9]))

    def change_dynamics(self, lateral_friction=1., spinning_friction=0., rolling_friction=0., restitution=0.,
                        linear_damping=0.04, angular_damping=0.04, contact_stiffness=-1, contact_damping=-1, **kwargs):
        """
        Change the world floor dynamics.

        Args:
            lateral_friction (float): lateral (linear) contact friction
            spinning_friction (float): torsional friction around the contact normal
            rolling_friction (float): torsional friction orthogonal to contact normal
            restitution (float): bounciness of contact. Keep it a bit less than 1.
            linear_damping (float): linear damping of the link.
            angular_damping (float): angular damping of the link.
            contact_stiffness (float): stiffness of the contact constraints, used together with `contact_damping`
            contact_damping (float): damping of the contact constraints for this body/link. Used together with
                `contact_stiffness`. This overrides the value if it was specified in the URDF file in the contact
                section.
        """
        self.sim.change_dynamics(body_id=self.floor_id, link_id=-1, lateral_friction=lateral_friction,
                                 spinning_friction=spinning_friction, rolling_friction=rolling_friction,
                                 restitution=restitution, linear_damping=linear_damping,
                                 angular_damping=angular_damping, contact_stiffness=contact_stiffness,
                                 contact_damping=contact_damping)


class BasicWorld(World):
    r"""Basic World class.

    It creates a basic world with a floor and set the gravity.
    """

    def __init__(self, simulator, floor_path=None, gravity=(0., 0., -9.81), scaling=1., lateral_friction=1.,
                 spinning_friction=0., rolling_friction=0., contact_stiffness=-1, contact_damping=-1):
        super(BasicWorld, self).__init__(simulator, gravity=gravity)

        if floor_path is None:
            self.load_floor(scaling=scaling)
            self.change_dynamics(lateral_friction=lateral_friction, spinning_friction=spinning_friction,
                                 rolling_friction=rolling_friction, linear_damping=0.04, angular_damping=0.04,
                                 contact_stiffness=contact_stiffness, contact_damping=contact_damping)
            # self.simulator.setDefaultContactERP(0.9)
            self.simulator.set_physics_properties(erp=0.9)
        else:
            self.load_terrain(floor_path, replace_floor=True)

        self.print_dynamics_info(self.floor_id)


class RobotPartyWorld(BasicWorld):
    r"""Robot Party World.

    It creates a basic world (see `BasicWorld`) with each available robot loaded into the world.
    """

    def __init__(self, simulator):
        super(RobotPartyWorld, self).__init__(simulator)


class DRCWorld(World):
    r"""Darpa Robotics Challenge World

    This recreates the Darpa Robotics Challenge world.
    """

    def __init__(self, simulator):
        super(DRCWorld, self).__init__(simulator)


# Tests
if __name__ == '__main__':
    import numpy as np
    from itertools import count
    from pyrobolearn.simulators import BulletSim

    # create simulator
    sim = BulletSim()

    # create world
    world = BasicWorld(sim)
    # world = World(sim)
    # world.load_bot_lab()

    # world.load_sdf('/home/brian/Downloads/cobblestones_origin/model.sdf', scaling=1)

    # world.load_mesh('/home/brian/Downloads/cobblestones_origin/mesh/cobblestones.obj',
    #                position=[0, 0, 0],
    #                orientation=[.707, 0, 0, .707],
    #                mass=0.,
    #                scale=(1., 1., 1.),
    #                # color=[1, 0, 0, 1],
    #                flags=1)

    # world.load_mesh('/home/brian/save/code/random-terrain-generator-master/terrain.obj',
    #                position=[0, 0, -2],
    #                orientation=[.707, 0, 0, .707],
    #                mass=0.,
    #                scale=(.1, .1, .1),
    #                # color=[1, 0, 0, 1],
    #                flags=1)

    # world.load_mesh('bedroom.obj', [0, 0, 0], mass=0., color=[0.4, 0.4, 0.4, 1], flags=1) #, scale=(0.01, 0.01, 0.01))
    # world.load_mesh('mtsthelens.obj', [0, 0, -8], mass=0., color=[0.2, 0.5, 0.2, 1], flags=1, scale=(0.01,0.01,0.01))
    # world.load_mesh('meshes/terrain.obj', [0,0,0], mass=0., color=[1,1,1,1], flags=1)
    # world.load_mesh('/home/brian/heightmap_old.obj', [0,0,0], mass=0., scale=(0.1,0.1,0.01), color=[1,1,1,1], flags=1)
    # world.load_mesh('/home/brian/Downloads/arab_desert/desert.obj',
    #                position=[0, 0, -10.8], orientation=(0.707,0,0,0.707), mass=0., scale=(1, 1, 1),
    #                color=[1, 1, 1, 1], flags=1)
    # world.load_mesh('/home/brian/PhD-repos/pyrobolearn/tests/heightmap_test_exp.obj', [0, 0, 0], mass=0.,
    #                scale=(0.1, 0.1, 0.015),
    #                color=[1, 0, 0, 1],
    #                flags=1)

    # world.load_robot('Cogimon', position=[0,0,1.])

    # world.load_robot('coman', use_fixed_base=False)
    # sphere = world.load_visual_Sphere([1.,0,1.], color=(1,0,0,0.5))
    # world.load_visual_box([-1,0,1], dimensions=[1.,1.,1.], color=[0,0,1,0.5])
    # world.load_cylinder([0, -1, 1], color=[1, 0, 0, 1])
    #  world.load_capsule([0, 1, 1],  color=[1, 0, 0, 1])
    #  world.load_mesh(filename='duck.obj', [1, 0, 2], [0.707, 0, 0, 0.707], mass=0.1, scale=[0.1,0.1,0.1],
    #                 color=[1, 0, 0, 1])

    # from utils.orientation import RotX, RotY, RotZ, getQuaternionFromMatrix
    # R = RotZ(np.deg2rad(90.))
    # q = tuple(getQuaternionFromMatrix(R))
    # world.load_ellipsoid([0,0,2], orientation=q, mass=0, scale=[2.,1.,1.], color=(0,0,1,1))
    # world.load_cone([1,1,2])
    world.load_right_triangular_prism([-1, -1, 2])
    # floor = world.load_mesh(filename='box', [1, 0, 2], mass=0, color=None)

    # floor = world.load_floor()
    # print(p.get_dynamics_info(floor, -1))
    # floor = world.load_mesh([1,0,0], [0,0,0,1], filename='grass.obj', mass=0, color=(1,1,1,1))
    # texture = sim.load_texture('grass.png')
    # sim.change_visual_shape(floor, -1, texture_id=texture)

    # grass = sim.load_urdf('grass.urdf')
    # texture = sim.load_texture('grass.png')
    # sim.change_visual_shape(grass, -1, texture_id=texture)

    # vs = world.load_visual_Sphere([0,0,2], radius=0.1, color=(0,0,1,1))

    # path = '/home/brian/bullet3/data/'
    # objects = p.load_mjcf(path+"MPL/mpl2.xml")

    # world.load_plane([1.,0.,1.], [0,0,0,1], color=(1,0,0,1))

    T = 1000
    w = 2.*np.pi / T
    red = True
    # loop
    for t in count():
        # p = world.get_object_position(sphere)
        # p -= 0.001 * np.array([1.,0,0])
        p = np.array([np.cos(w*t), np.sin(w*t), 1.])
        # world.move_object(sphere, p)
        # if t % T == 0:
        #     if red:
        #         world.change_object_color(sphere, (1,0,0,0.5))
        #     else:
        #         world.change_object_color(sphere, (0,0,1,0.5))
        #     red = not red
        # world.move_object(sphere)
        world.step(sleep_dt=1./240)
