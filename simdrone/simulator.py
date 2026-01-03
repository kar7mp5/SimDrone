# simulator.py
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


from render import Rendering
from drone import Drone
from camera import Camera




class Simulator:

    def __init__(self):
        self.display = (1000, 700)
        self.camera = Camera()
        self.drone = Drone()
        self.renderer = Rendering()
        self.clock = pygame.time.Clock()
        self.running = True

    def init_opengl(self):
        pygame.init()
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption("Drone Simulator")
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        glClearColor(0.04, 0.04, 0.10, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        self.set_perspective()

    def set_perspective(self):
        glViewport(0, 0, *self.display)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(65, self.display[0]/self.display[1], 0.1, 2000)
        glMatrixMode(GL_MODELVIEW)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.running = False
            if event.type == KEYDOWN:
                if event.key == K_p:
                    self.drone.reset()
            if event.type == VIDEORESIZE:
                self.display = event.size
                pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL | RESIZABLE)
                self.set_perspective()

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.camera.update(keys, dt)
        # Drone controls are set via functions externally
        self.drone.update_dynamics(dt)

    def run(self):
        self.init_opengl()
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.renderer.render_scene(self.camera, self.drone)
            pygame.display.flip()
        pygame.quit()