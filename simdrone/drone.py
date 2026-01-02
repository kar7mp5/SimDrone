# drone.py
# Copyright 2026 MinSup Kim
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

from utils import *




class Drone:

    def __init__(self):
        self.state = TransformState()
        self.thrust = 0.0
        self.torques = np.zeros(3)

    def reset(self):
        self.state.position = np.array([0.0, 0.5, 0.0])
        self.state.velocity = np.zeros(3)
        self.state.rotation = np.zeros(3)
        self.state.angular_velocity = np.zeros(3)
        self.thrust = 0.0
        self.torques = np.zeros(3)

    def set_control(self, thrust=0.0, roll=0.0, pitch=0.0, yaw=0.0):
        self.thrust = np.clip(thrust, 0.0, 1.0)
        self.torques = np.clip(np.array([roll, pitch, yaw]), -1.0, 1.0)

    def update_dynamics(self, dt):
        # Thrust force in world frame
        R = self.state.get_rotation_matrix()
        thrust_body = np.array([0.0, 0.0, -self.thrust * MAX_THRUST])  # Negative for lift (Z down convention)
        thrust_world = R @ thrust_body

        # Gravity
        gravity = np.array([0.0, -GRAVITY * MASS, 0.0])

        # Linear acceleration
        accel = (thrust_world + gravity) / MASS

        # Angular acceleration
        ang_accel = np.array([
            self.torques[0] * MAX_TORQUE / IXX,
            self.torques[1] * MAX_TORQUE / IYY,
            self.torques[2] * MAX_TORQUE / IZZ
        ])

        # Integrate
        self.state.velocity += accel * dt
        self.state.position += self.state.velocity * dt
        self.state.angular_velocity += ang_accel * dt
        self.state.rotation += np.degrees(self.state.angular_velocity) * dt
        self.state.rotation[0] = np.clip(self.state.rotation[0], -89.9, 89.9)
