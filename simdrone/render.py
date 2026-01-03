# render.py
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
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

from utils import *




class Rendering:
    
    def __init__(self):
        self.quadric = gluNewQuadric()
        self.plot_texture = None
        self.plot_width = 0
        self.plot_height = 0

    def draw_axes(self, length=1.5):
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glColor3f(1.0, 0.0, 0.0); glVertex3f(0,0,0); glVertex3f(length,0,0)
        glColor3f(0.0, 1.0, 0.0); glVertex3f(0,0,0); glVertex3f(0,length,0)
        glColor3f(0.0, 0.0, 1.0); glVertex3f(0,0,0); glVertex3f(0,0,length)
        glEnd()

    def draw_grid(self, size=40, step=2):
        glLineWidth(1.0)
        glColor3f(0.35, 0.35, 0.4)
        glBegin(GL_LINES)
        for i in range(-size, size + 1, step):
            glVertex3f(i, -size, 0); glVertex3f(i, size, 0)
            glVertex3f(-size, i, 0); glVertex3f(size, i, 0)
        glEnd()

    def draw_cube(self, size=1.2):
        half = size / 2
        glColor3f(0.85, 0.25, 0.25)
        glBegin(GL_QUADS)
        glVertex3f(-half,-half, half); glVertex3f( half,-half, half)
        glVertex3f( half, half, half); glVertex3f(-half, half, half)
        glVertex3f(-half,-half,-half); glVertex3f(-half, half,-half)
        glVertex3f( half, half,-half); glVertex3f( half,-half,-half)
        glVertex3f(-half,-half, half); glVertex3f(-half, half, half)
        glVertex3f(-half, half,-half); glVertex3f(-half,-half,-half)
        glVertex3f( half,-half, half); glVertex3f( half,-half,-half)
        glVertex3f( half, half,-half); glVertex3f( half, half, half)
        glVertex3f(-half, half, half); glVertex3f( half, half, half)
        glVertex3f( half, half,-half); glVertex3f(-half, half,-half)
        glVertex3f(-half,-half, half); glVertex3f(-half,-half,-half)
        glVertex3f( half,-half,-half); glVertex3f( half,-half, half)
        glEnd()

    def render_scene(self, camera, drones, clear=True):
        if clear:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glLightfv(GL_LIGHT0, GL_POSITION, (10.0, 10.0, 10.0, 1.0))
        camera.apply()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        self.draw_grid()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        # Render each drone
        for drone in drones:
            glPushMatrix()
            glTranslatef(drone.state.position[1], drone.state.position[0], drone.state.position[2])
            R = drone.state.get_rotation_matrix()
            S = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
            R_open = S @ R @ S.T
            mat4 = np.eye(4)
            mat4[:3, :3] = R_open
            r_mat = mat4.flatten('F').tolist()
            glMultMatrixf(r_mat)
            self.draw_cube(size=1.2)
            self.draw_axes(length=1.6)
            glPopMatrix()

    def update_plot_texture(self, buffer, width, height):
        if self.plot_texture is None:
            self.plot_texture = glGenTextures(1)
        
        glBindTexture(GL_TEXTURE_2D, self.plot_texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        # buffer is RGBA from matplotlib
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, buffer)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        self.plot_width = width
        self.plot_height = height

    def draw_plot_overlay(self, x, y, width, height, window_width, window_height):
        if self.plot_texture is None:
            return

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.plot_texture)
        glColor3f(1.0, 1.0, 1.0) # Reset color

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, window_width, window_height, 0) # Top-left is 0,0
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Draw rect at specified position
        x_start = x
        y_start = y
        
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(x_start, y_start)           # Top Left
        glTexCoord2f(1, 1); glVertex2f(x_start + width, y_start) # Top Right
        glTexCoord2f(1, 0); glVertex2f(x_start + width, y_start + height) # Bottom Right
        glTexCoord2f(0, 0); glVertex2f(x_start, y_start + height)           # Bottom Left
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)