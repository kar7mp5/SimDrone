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
import queue


from utils import *


from render import Rendering
from drone import Drone
from render import Rendering
from drone import Drone
from render import Rendering
from drone import Drone
from camera import Camera
from logger import Logger
from plotter import RealTimePlotter, get_plot_config




class Simulator:
    
    def __init__(self, num_drones=1):
        # Ask for layout first
        self.plot_config = get_plot_config()
        
        # Window size depends on mode
        if self.plot_config['mode'] == 'embedded':
            self.display = (1400, 800)
        else:
            self.display = (1000, 700)
            
        self.camera = Camera()
        self.drones = [Drone() for _ in range(num_drones)]
        self.renderer = Rendering()
        self.clock = pygame.time.Clock()
        self.running = True
        self.logger = Logger()
        self.elapsed_time = 0.0
        
        # Plotter
        self.plotter = RealTimePlotter(num_drones, config=self.plot_config)
        self.plot_update_interval = 0.1 # 10Hz
        self.last_plot_update = 0.0

        self.trajectory_queue = None

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
        self.set_perspective(self.display[0], self.display[1])

    def set_perspective(self, width, height):
        glViewport(0, 0, int(width), int(height))
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if height == 0: height = 1
        gluPerspective(65, width/height, 0.1, 2000)
        glMatrixMode(GL_MODELVIEW)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.running = False
            if event.type == KEYDOWN:
                if event.key == K_p:
                    for drone in self.drones:
                        drone.reset()
            if event.type == VIDEORESIZE:
                self.display = event.size
                pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL | RESIZABLE)
                # self.set_perspective() # Handled in loop

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.camera.update(keys, dt)

        # print(self.drone.state.get_status())
        # self.trajectory.append(self.drone.state.get_status())
        # Drone controls are set via functions externally
        for drone in self.drones:
            drone.update_dynamics(dt)
        
        self.elapsed_time += dt
        self.logger.log(self.elapsed_time, self.drones)

        # Update Plotter Data
        self.plotter.update_data(self.elapsed_time, self.drones)
        
        # Render Plot 
        if self.elapsed_time - self.last_plot_update > self.plot_update_interval:
            if self.plot_config['mode'] == 'embedded':
                buf, w, h = self.plotter.render_to_buffer()
                self.renderer.update_plot_texture(buf, w, h)
            else:
                self.plotter.update_plot()
            self.last_plot_update = self.elapsed_time

    def run(self, result_queue=None):
        self.init_opengl()
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            
            # Clear Full Window
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            if self.plot_config['mode'] == 'embedded':
                # Layout Calculation for Embedded
                # Fixed proportion e.g. 35%
                plot_w = int(self.display[0] * 0.35)
                sim_w = self.display[0] - plot_w
                sim_h = self.display[1]
                
                # 1. Render Simulation (Left)
                glViewport(0, 0, sim_w, sim_h)
                self.set_perspective(sim_w, sim_h)
                self.renderer.render_scene(self.camera, self.drones, clear=False) 
                
                # 2. Render Plot Overlay (Right)
                glViewport(0, 0, self.display[0], self.display[1])
                # Draw rect at (x, y, w, h)
                self.renderer.draw_plot_overlay(sim_w, 0, plot_w, sim_h, self.display[0], self.display[1])
            else:
                # Pop-out mode: Full screen simulation
                glViewport(0, 0, self.display[0], self.display[1])
                self.set_perspective(self.display[0], self.display[1])
                self.renderer.render_scene(self.camera, self.drones, clear=False)
            
            pygame.display.flip()

        pygame.quit()
        self.logger.save()

        # trajectory = self.trajectory[:]  # copy for safety
        if result_queue:
            result_queue.put(self.logger.data)  # Queue
        return self.logger.data