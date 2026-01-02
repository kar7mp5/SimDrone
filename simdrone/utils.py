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
import numpy as np


# Physics constants
GRAVITY = 9.81  # m/s^2
MASS = 1.0  # kg
IXX = IYY = 0.082  # kg·m^2 (moment of inertia)
IZZ = 0.149
MAX_THRUST = 35.0  # N (maximum total thrust from 4 propellers)
MAX_TORQUE = 2.5  # Nm

# Constants for movement and rotation speeds
MOVE_SPEED = 5.0
ROT_SPEED = 90.0




class TransformState:

    def __init__(self, position=[0.0, 0.5, 0.0]):
        self.position = np.array(position, dtype=float)
        self.velocity = np.zeros(3, dtype=float)
        # Euler angles in degrees: pitch, yaw, roll
        self.rotation = np.zeros(3, dtype=float)
        # Angular velocity in rad/s: p, q, r
        self.angular_velocity = np.zeros(3, dtype=float)

    def translate(self, delta):
        self.position += np.array(delta)

    def rotate(self, delta_deg):
        self.rotation += np.array(delta_deg)
        self.rotation[0] = np.clip(self.rotation[0], -89.9, 89.9)

    def get_rotation_matrix(self):
        """Convert Euler angles (pitch-yaw-roll) to rotation matrix (body -> world)"""
        p, y, r = np.deg2rad(self.rotation)
        cp, sp = np.cos(p), np.sin(p)
        cy, sy = np.cos(y), np.sin(y)
        cr, sr = np.cos(r), np.sin(r)

        # Standard rotation matrix for aerospace convention (body to NED world)
        R_standard = np.array([
            [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr]
        ])

        # Transformation matrix to map to simulation coordinates (Y up)
        S = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 0.0, -1.0],
            [0.0, 1.0, 0.0]
        ])

        # Final rotation matrix in simulation coordinates
        R = S @ R_standard
        return R
