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
        # Initial position in the simulation world (x, y, z)
        # Note: Simulation uses (y, x, z) in glTranslatef, so camera position should align.
        # Let's adjust this for a more standard OpenGL (x, y, z) and adapt apply()
        self.state = TransformState(position=np.array([0.0, -12.0, -1.5], dtype=np.float32)) # Swapped X and Y for intuition
        
        # Rotations, similar to the reference OpenGLWidget, but applied to the camera's view
        self.x_rot = 20.0
        self.y_rot = 30.0
        self.zoom = -8.0 # This will directly translate to a Z translation in apply()
        
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
        # This method will be called by OpenGLSimulationWidget's timer
        # Move camera based on currently pressed keys
        move_speed = 0.5 * dt # Adjust speed as necessary
        
        # Calculate forward, right, up vectors based on current rotation
        # Using OpenGL's own matrix stack is more robust for camera transformations.
        # Here we'll simulate it for key-based translation in world space.
        
        # Reset current transformation to get clean vectors
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glRotatef(self.x_rot, 1, 0, 0)
        gl.glRotatef(self.y_rot, 0, 1, 0)
        
        # Get orientation matrix
        modelview = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        
        # Extract forward, right, up vectors from the modelview matrix
        # For a camera looking down -Z (standard GL), forward is (0,0,-1) transformed
        forward = np.array([-modelview[0][2], -modelview[1][2], -modelview[2][2]])
        right = np.array([modelview[0][0], modelview[1][0], modelview[2][0]])
        up = np.array([modelview[0][1], modelview[1][1], modelview[2][1]])
        
        gl.glPopMatrix() # Restore matrix
        
        # Normalize vectors (should already be normalized if only rotations were applied)
        forward = forward / (np.linalg.norm(forward) or 1.0)
        right = right / (np.linalg.norm(right) or 1.0)
        up = up / (np.linalg.norm(up) or 1.0) # This 'up' is relative to camera, not world up.
        
        # World up is [0,0,1] or [0,0,-1] in standard GL coordinate system.
        # If simulation's Z is 'up', then world_up_vector = np.array([0,0,1])
        # For simplicity, let's use fixed world up for up/down movement, or adjust.
        # For now, let's just use the transformed Y-axis for "up" (vertical motion)
        
        # Handle movement
        if self.keys_pressed[Qt.Key.Key_W]: self.state.position += forward * move_speed
        if self.keys_pressed[Qt.Key.Key_S]: self.state.position -= forward * move_speed
        if self.keys_pressed[Qt.Key.Key_A]: self.state.position -= right * move_speed
        if self.keys_pressed[Qt.Key.Key_D]: self.state.position += right * move_speed
        
        # World up/down (assuming Z is vertical in world coordinates)
        if self.keys_pressed[Qt.Key.Key_Space]: self.state.position[2] += move_speed # Move Up
        if self.keys_pressed[Qt.Key.Key_Shift]: self.state.position[2] -= move_speed # Move Down

        # Yaw control for drone-like rotation (if needed, currently handled by mouse y_rot)
        # if self.keys_pressed[Qt.Key.Key_Q]: self.y_rot -= ROT_SPEED * dt # Yaw left
        # if self.keys_pressed[Qt.Key.Key_E]: self.y_rot += ROT_SPEED * dt # Yaw right


    def apply(self):
        # Apply zoom (translate along Z-axis)
        gl.glTranslatef(0.0, 0.0, self.zoom)
        
        # Apply rotations
        gl.glRotatef(self.x_rot, 1, 0, 0) # Pitch (around X-axis)
        gl.glRotatef(self.y_rot, 0, 1, 0) # Yaw (around Y-axis)
        
        # Translate to camera's position (inverse of position because we're moving the world)
        gl.glTranslatef(-self.state.position[0], -self.state.position[1], -self.state.position[2])