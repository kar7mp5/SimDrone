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
from utils import *




class Drone:
    def __init__(self):
        self.state = TransformState()
        self.thrust = 0.0
        self.torques = np.zeros(3)
        
        # Simple air resistance coefficients (adjustable)
        self.linear_damping = 0.98
        self.angular_damping = 0.96

    def reset(self):
        """Reset the drone state to initial values."""
        self.state.position = np.array([0.0, 0.0, -0.5])  # Starting height -0.5m (above ground at Z=0)
        self.state.velocity = np.zeros(3)
        self.state.rotation = np.zeros(3)  # [roll, pitch, yaw] in degrees
        self.state.angular_velocity = np.zeros(3)  # rad/s
        self.thrust = 0.0
        self.torques = np.zeros(3)

    def set_control(self, thrust=0.0, roll=0.0, pitch=0.0, yaw=0.0):
        """Set control inputs (normalized -1 to 1 range)."""
        self.thrust = np.clip(thrust, 0.0, 1.0)
        self.torques = np.clip(np.array([roll, pitch, yaw]), -1.0, 1.0)

    def update_dynamics(self, dt):
        """
        Update drone physics (Euler integration).
        dt: timestep (in seconds, typically 0.01-0.02)
        """
        # 1. Compute attitude (rotation matrix)
        R = self.state.get_rotation_matrix()  # ZYX Euler (yaw → pitch → roll)

        # 2. Thrust (in body frame, -Z direction = up)
        thrust_body = np.array([0.0, 0.0, -self.thrust * MAX_THRUST])
        thrust_world = R @ thrust_body

        # 3. Gravity (+Z direction = down)
        gravity = np.array([0.0, 0.0, GRAVITY * MASS])

        # 4. Linear acceleration
        accel = (thrust_world + gravity) / MASS
        self.state.velocity += accel * dt

        # 5. Position update
        self.state.position += self.state.velocity * dt

        # 6. Ground collision handling (NED frame, +Z = down, ground at Z=0)
        if self.state.position[2] > 0.0:
            self.state.position[2] = 0.0
            if self.state.velocity[2] > 0:  # If moving downward
                self.state.velocity[2] = 0.0
            # Optional: simple bounce/friction effect
            # self.state.velocity[0] *= 0.4
            # self.state.velocity[1] *= 0.4

        # 7. Angular acceleration calculation
        ang_accel = np.array([
            self.torques[0] * MAX_TORQUE / IXX,
            self.torques[1] * MAX_TORQUE / IYY,
            self.torques[2] * MAX_TORQUE / IZZ
        ])

        # 8. Angular velocity update
        self.state.angular_velocity += ang_accel * dt

        # 9. Air resistance/damping (for realism)
        self.state.angular_velocity *= self.angular_damping
        self.state.velocity *= self.linear_damping

        # 10. Rotation update (in degrees)
        self.state.rotation += np.degrees(self.state.angular_velocity) * dt

        # 11. Euler angle clipping & yaw wrap-around
        self.state.rotation[0] = np.clip(self.state.rotation[0], -89.9, 89.9)  # roll
        self.state.rotation[1] = np.clip(self.state.rotation[1], -89.9, 89.9)  # pitch
        self.state.rotation[2] = self.state.rotation[2] % 360  # yaw

    # Helper method for debugging/logging (use if needed)
    def get_state_str(self):
        pos = self.state.position
        rot = self.state.rotation
        vel = self.state.velocity
        ang_vel = self.state.angular_velocity
        return (f"Pos: {pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f} | "
                f"Rot: {rot[0]:.1f}, {rot[1]:.1f}, {rot[2]:.1f}° | "
                f"Thrust: {self.thrust:.2f} | Torques: {self.torques}")