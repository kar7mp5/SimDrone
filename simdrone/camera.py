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
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from utils import *




class Camera:

    def __init__(self):
        self.state = TransformState(position=[-12.0, 0.0, -1.5])

    def update(self, keys, dt):
        dyaw = (keys[K_q] - keys[K_e]) * ROT_SPEED * dt
        dpitch = (keys[K_r] - keys[K_f]) * ROT_SPEED * dt
        
        self.state.rotate([0, dpitch, dyaw])
        forward = self.state.get_forward()
        forward /= np.linalg.norm(forward) or 1.0
        up = np.array([0.0, 0.0, -1.0])
        right = np.cross(forward, up)
        right /= np.linalg.norm(right) or 1.0
        move = np.zeros(3)

        # FORWARD/BACKWARD
        if keys[K_w]: move += forward
        if keys[K_s]: move -= forward
        
        # LEFT/RIGHT
        if keys[K_a]: move += right
        if keys[K_d]: move -= right

        # UP/DOWN
        if keys[K_SPACE]: move += up
        if keys[K_LSHIFT]: move -= up
        if np.linalg.norm(move) > 0:
            move /= np.linalg.norm(move)
            self.state.translate(move * MOVE_SPEED * dt)

    def apply(self):
        forward = self.state.get_forward()
        center = self.state.position + forward
        gluLookAt(
            self.state.position[1], self.state.position[0], self.state.position[2],
            center[1], center[0], center[2],
            0, 0, -1
        )