# camera.py
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
from OpenGL import GL as gl
from OpenGL.GLU import *
import numpy as np
from PyQt6.QtCore import Qt # Import Qt for Key enums

from utils import TransformState # Explicitly import TransformState


class Camera:
    def __init__(self):
        # self.state.position will now represent the "look-at" point or the center of rotation
        # It corresponds to (North, East, Down) coordinates.
        self.state = TransformState(position=np.array([0.0, 0.0, 0.0], dtype=np.float32)) 
        
        # Rotations, similar to the reference OpenGLWidget, but applied to the camera's view
        self.x_rot = 20.0 # Pitch
        self.y_rot = 30.0 # Yaw
        self.zoom = -12.0 # Distance from the look-at point. Negative for moving back.
        
        # Keyboard input states
        self.keys_pressed = {
            Qt.Key.Key_W: False, Qt.Key.Key_S: False,
            Qt.Key.Key_A: False, Qt.Key.Key_D: False,
            Qt.Key.Key_Space: False, Qt.Key.Key_Shift: False, # Left Shift for consistency
            Qt.Key.Key_Q: False, Qt.Key.Key_E: False,
        }
        
        # Mouse control flags for external access (e.g., from OpenGLSimulationWidget)
        self.mouse_pressed = False
        self.last_mouse_pos = np.array([0.0, 0.0]) # To store last mouse x, y


    def process_keyboard_input(self, key, is_pressed):
        if key in self.keys_pressed:
            self.keys_pressed[key] = is_pressed

    def process_mouse_movement(self, dx, dy):
        # Update rotations based on mouse movement
        self.y_rot += dx * 0.5 # Horizontal mouse movement affects Y-axis rotation
        self.x_rot += dy * 0.5 # Vertical mouse movement affects X-axis rotation
        
        # Clamp x_rot to prevent flipping
        self.x_rot = max(-89.0, min(89.0, self.x_rot)) # Prevent camera from going upside down


    def process_scroll(self, delta):
        # Update zoom based on mouse wheel delta
        self.zoom += delta * 0.5
        self.zoom = max(-20.0, min(-4.0, self.zoom)) # Clamp zoom similar to reference


    def update_position(self, dt):
        # This method is called by OpenGLSimulationWidget's timer to move the look-at point
        move_speed = 5.0 * dt # Speed of moving the look-at point in meters per second
        
        # Calculate camera's forward, right, up vectors based on current rotation
        # These vectors are relative to the camera's orientation in world space.
        
        # Construct a temporary rotation matrix based on current camera x_rot and y_rot
        # to find the camera's local axes in world coordinates.
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glRotatef(self.x_rot, 1, 0, 0) # Apply Pitch
        gl.glRotatef(self.y_rot, 0, 1, 0) # Apply Yaw
        view_matrix = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        gl.glPopMatrix()

        # Extract camera's local axes (right, up, forward) from the generated matrix
        # For a standard OpenGL camera setup (looking down -Z), these are:
        # Right vector: column 0 of the rotation part
        # Up vector: column 1 of the rotation part
        # Forward vector: negated column 2 of the rotation part
        right_vec = np.array([view_matrix[0][0], view_matrix[1][0], view_matrix[2][0]])
        up_vec = np.array([view_matrix[0][1], view_matrix[1][1], view_matrix[2][1]])
        forward_vec = np.array([-view_matrix[0][2], -view_matrix[1][2], -view_matrix[2][2]])
        
        # Normalize vectors (should be close to 1 if matrix is pure rotation)
        right_vec /= (np.linalg.norm(right_vec) or 1.0)
        up_vec /= (np.linalg.norm(up_vec) or 1.0)
        forward_vec /= (np.linalg.norm(forward_vec) or 1.0)

        # Apply movement to the look-at point (self.state.position)
        # Assuming world Z is down axis, and (X,Y) are North-East plane.
        
        # Project forward and right vectors onto the X-Y plane for horizontal movement
        # (assuming X-Y is North-East plane, Z is Down)
        horizontal_forward = np.array([forward_vec[0], forward_vec[1], 0.0])
        horizontal_forward /= (np.linalg.norm(horizontal_forward) or 1.0)
        
        horizontal_right = np.array([right_vec[0], right_vec[1], 0.0])
        horizontal_right /= (np.linalg.norm(horizontal_right) or 1.0)

        # W/S move along North-East plane (horizontal_forward)
        if self.keys_pressed[Qt.Key.Key_W]: self.state.position += horizontal_forward * move_speed
        if self.keys_pressed[Qt.Key.Key_S]: self.state.position -= horizontal_forward * move_speed
        # A/D move along North-East plane (horizontal_right)
        if self.keys_pressed[Qt.Key.Key_A]: self.state.position -= horizontal_right * move_speed
        if self.keys_pressed[Qt.Key.Key_D]: self.state.position += horizontal_right * move_speed
        
        # Vertical movement (along world Down-axis, which is +Z in NED)
        if self.keys_pressed[Qt.Key.Key_Space]: self.state.position[2] -= move_speed # Move Up (less Down)
        if self.keys_pressed[Qt.Key.Key_Shift]: self.state.position[2] += move_speed # Move Down (more Down)

    def apply(self):
        # The camera's actual position in world space
        # Start with the look-at point (self.state.position)
        # Then move 'zoom' distance along the inverted camera forward vector (backwards from view)
        
        # First, define the 'center' or 'look-at' point in world coordinates
        center_x, center_y, center_z = self.state.position[0], self.state.position[1], self.state.position[2]

        # Calculate camera's eye position based on rotations and zoom from the center point
        # spherical coordinates-like calculation for simplicity
        
        # Convert rotations to radians
        pitch_rad = np.radians(self.x_rot)
        yaw_rad = np.radians(self.y_rot)
        
        # Simplified rotation matrix application (Yaw then Pitch) to a point (0, 0, -zoom)
        # Point to rotate: (0, 0, -self.zoom) assuming zoom is negative
        # Or (0, 0, abs(self.zoom)) and move it along rotated -Z axis
        
        # Start with camera looking along +Z, distance -zoom (so at 0,0,abs(zoom))
        # Then rotate around X (pitch), then around Y (yaw)
        
        # Vector from center to eye (in center's local coords before rotation)
        vec_to_eye = np.array([0, 0, self.zoom]) # Camera starts pointing along +Z (Down) in NED frame

        # Convert rotations to radians
        pitch_rad = np.radians(self.x_rot) # Pitch around Y (East)
        yaw_rad = np.radians(self.y_rot)   # Yaw around Z (Down)

        # Rotate vec_to_eye by pitch (x_rot) around Y-axis (NED East)
        pitch_mat = np.array([
            [np.cos(pitch_rad), 0, np.sin(pitch_rad)],
            [0, 1, 0],
            [-np.sin(pitch_rad), 0, np.cos(pitch_rad)]
        ])
        vec_to_eye = np.dot(pitch_mat, vec_to_eye)

        # Rotate vec_to_eye by yaw (y_rot) around Z-axis (NED Down)
        yaw_mat = np.array([
            [np.cos(yaw_rad), -np.sin(yaw_rad), 0],
            [np.sin(yaw_rad), np.cos(yaw_rad), 0],
            [0, 0, 1]
        ])
        vec_to_eye = np.dot(yaw_mat, vec_to_eye)
        
        # Final eye position in world coordinates (N, E, D)
        eye_x = center_x + vec_to_eye[0] # North
        eye_y = center_y + vec_to_eye[1] # East
        eye_z = center_z + vec_to_eye[2] # Down
        
        # 'Up' vector for gluLookAt in NED: (0, 0, -1) means Up is opposite of Down
        up_x, up_y, up_z = 0.0, 0.0, -1.0
        
        gluLookAt(
            eye_x, eye_y, eye_z,       # Camera position (N, E, D)
            center_x, center_y, center_z, # Look-at point (N, E, D)
            up_x, up_y, up_z           # Up vector (N, E, D components)
        )