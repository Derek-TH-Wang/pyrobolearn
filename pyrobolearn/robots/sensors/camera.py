#!/usr/bin/env python
"""Define the visual camera sensors.

Cameras have one of the most richest sensory inputs (i.e. visual).
"""

import numpy as np

from pyrobolearn.robots.sensors.links import LinkSensor

__author__ = "Brian Delhaisse"
__copyright__ = "Copyright 2018, PyRoboLearn"
__credits__ = ["Brian Delhaisse"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Brian Delhaisse"
__email__ = "briandelhaisse@gmail.com"
__status__ = "Development"


class CameraSensor(LinkSensor):
    r"""Camera Sensor class.

    The following operations are carried out (in the given order) to display images seen by the camera:
    * M: Model space --> World space. This transforms the coordinates of each model described in their own local frame
     :math:`[x_{l}, y_{l}, z_{l}, 1]` to world coordinates :math:`[x_{w}, y_{w}, z_{w}, 1]`.
    * V: World space --> View space. This transforms world coordinates :math:`[x_{w}, y_{w}, z_{w}, 1]` into eye
     coordinates :math:`[x_{e}, y_{e}, z_{e}, 1]`. That is, it rotates and translates the world such that it is in
     front of the camera.
    * P: View space --> Projection space. Transforms the eye coordinates into clip coordinates using an orthographic
     or perspective projection. The new coordinates are given by :math:`[x_{c}, y_{c}, z_{c}, w_{c}]`. This is not
     normalized, i.e. w_{c} is not equal to 1. See next operation.
    * norm: Screen space --> NDC space. This normalizes the previous clipped coordinates into
     Normalized Device Coordinates (NDC) where each coordinate is normalized and is between -1 and 1. That is, we now
     have :math:`[x_{n}, y_{n}, z_{n}, 1] = [x_c/w_c, y_c/w_c, z_c, w_c/w_c]`
    * Vp: NDC space --> Screen space. Finally, this maps the previous normalized clip coordinates to pixel coordinates,
     :math:`[x_{s}, y_{s}, z_{s}, 1]` where :math:`x_s` (:math:`y_s`) is between 0 and the width (height) of the screen
     respectively, and :math:`z_s` represents the depth which is between 0 and 1.

    The norm and Vp operations are usually carried out by the hardware.

    When changing the position or orientation of the camera, the view matrix has to be updated.

    Examples:
        sim = BulletClient(connection_mode=p.GUI)
        cam = Camera(sim, width=400, height=400, target_position=(0,0,0), eyePosition=(2,0,1))
        img = cam.getRGBImage()
        plt.imshow(img)
        plt.show()

    References:
        [1] http://www.codinglabs.net/article_world_view_projection_matrix.aspx
        [2] https://learnopengl.com/Getting-started/Coordinate-Systems
        [3] http://www.thecodecrate.com/opengl-es/opengl-transformation-matrices/
        [4] http://learnwebgl.brown37.net/08_projections/projections_perspective.html
    """

    def __init__(self, simulator, body_id, link_id, width, height, position=None, orientation=None, refresh_rate=50,
                 target_position=None, distance=10.,
                 fovy=60, aspect=None, near=0.01, far=100.,
                 left=None, right=None, bottom=None, top=None):
        """
        Initialize the camera sensor.

        Args:
            simulator: simulator to access to the sensor.
            position (list/tuple/array of 3 floats): position of the sensor
            orientation (quaternion): orientation of the sensor
            width (int): width of the returned pictures
            height (int): height of the returned pictures

            For a view matrix:
                target_position (list/tuple of 3 floats): target focus point in cartesian world coordinates
                eyePosition (list/tuple of 3 floats): eye position in cartesian world coordinates
                UpVector (list/tuple of 3 floats): up vector of the camera in cartesian world coordinates

            For a view matrix from RPY:
                target_position (list/tuple of 3 floats): target focus point in cartesian world coordinates
                distance (float): distance in meters from the eye to the target focus point
                yaw (float): yaw angle in degrees of the camera
                pitch (float): pitch angle in degrees of the camera
                roll (float): roll angle in degrees of the camera
                upAxisIndex (int): either 1 for Y or 2 for Z axis up (default Z axis)

            For a perspective projection:
                fovy (float): field of view in the y direction (height) in degrees
                aspect (float): aspect ratio that determines the FOV in the x direction (width). ratio = width/height
                near (float): near plane distance (in meters)
                far (float): far plane distance (in meters)

            For an orthographic projection:
                near (float): near plane distance (in meters)
                far (float): far plane distance (in meters)
                left (float): left screen (canvas) coordinate
                right (float): right screen (canvas) coordinate
                bottom (float): bottom screen (canvas) coordinate
                top (float): top screen (canvas) coordinate
        """
        super(CameraSensor, self).__init__(simulator, body_id, link_id, position, orientation, refresh_rate)

        self.width = width
        self.height = height
        self.distance = distance

        # compute projection matrix (orthographic or perspective matrix)
        if left is not None and right is not None and bottom is not None and top is not None:  # orthographic
            self._P = self.sim.computeProjectionMatrix(left, right, bottom, top, near, far)
        else:  # perspective
            # The aspect ratio parameter is the width divided by the height of the canvas window
            if aspect is None:
                aspect = float(width) / height
            self._P = self.sim.computeProjectionMatrixFOV(fovy, aspect, nearVal=near, farVal=far)

        # compute view matrix
        self._V = self.getV()

        # define other variables
        self.up_vector = (0, 0, 1)

    @property
    def P(self):
        """
        Get the associated projection matrix.
        """
        return np.array(self._P).reshape(4, 4).T

    @property
    def V(self):
        """
        Get the associated view matrix.
        """
        self.getV()
        return np.array(self._V).reshape(4, 4).T

    def getV(self):
        """
        Get the associated view matrix.
        """
        roll, pitch, yaw = self.sim.getEulerFromQuaternion(self.orientation_converter(self.orientation))
        self.up_vector = (0, 0, 1)
        up_axis_index = 2  # z axis

        # use the specified distance to calculate it.
        target_position = self.position + self.distance * np.array([-np.cos(pitch) * np.cos(-yaw),
                                                                   -np.cos(pitch) * np.sin(-yaw),
                                                                   -np.sin(pitch)])

        # compute view matrix
        self._V = self.sim.computeViewMatrix(cameraEyePosition=self.position,
                                             cameraTargetPosition=target_position,
                                             cameraUpVector=self.up_vector)

        # self._V = self.sim.computeViewMatrixFromYawPitchRoll(cameraTargetPosition=target_position,
        #                                                      distance=distance,
        #                                                      yaw=yaw,
        #                                                      pitch=pitch,
        #                                                      roll=roll,
        #                                                      upAxisIndex=up_axis_index)

        return self._V

    def getRGBImage(self):
        """
        Return the captured RGB image.
        """
        return self.getRGBAImage()[:, :, :3]

    def getRGBAImage(self):
        """
        Return the captured RGBA image. 'A' stands for alpha channel (for opacity/transparency)
        """
        img = np.array(self.sim.getCameraImage(self.width, self.height, self.getV(), self._P,
                                               shadow=1,  # lightDirection=[1,1,1],
                                               # renderer=self.sim.ER_TINY_RENDERER)[2])
                                               renderer=self.sim.ER_BULLET_HARDWARE_OPENGL)[2])
        img = img.reshape(self.width, self.height, 4)  # RGBA
        return img

    def getDepthImage(self):
        """
        Return the depth image.
        """
        img = np.array(self.sim.getCameraImage(self.width, self.height, self.getV(), self._P,
                                               renderer=self.sim.ER_BULLET_HARDWARE_OPENGL)[3])
        img = img.reshape(self.width, self.height)
        return img

    def getRGBADImage(self, concatenate=True):
        """
        Return the RGBA and depth images.
        """
        rgba, depth = self.sim.getCameraImage(self.width, self.height, self.getV(), self._P)[2:4]
        rgba = np.array(rgba).reshape(self.width, self.height, 4)
        depth = np.array(depth).reshape(self.width, self.height)
        if concatenate:
            return np.dstack((rgba, depth))
        return rgba, depth

    _sense = getRGBADImage


class DepthCameraSensor(CameraSensor):
    r"""Depth Camera sensor.
    """
    _sense = CameraSensor.getDepthImage


class Camera2DSensor(CameraSensor):
    r"""2D camera sensor
    """
    _sense = CameraSensor.getRGBImage

