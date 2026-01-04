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
import numpy as np
import queue

from utils import *

from render import Rendering
from drone import Drone
from camera import Camera
from logger import Logger
from plotter import RealTimePlotter
from settings import SettingsDialog




class Simulator:

    def __init__(self, num_drones=1):
        # display will be managed by the PyQt6 OpenGL widget
            
        self.camera = Camera()
        self.drones = [Drone() for _ in range(num_drones)]
        self.renderer = Rendering()
        self.running = True # This will now be controlled externally, or by a reset
        self.logger = Logger()
        self.elapsed_time = 0.0
        
        # Plotter - always initialized in embedded mode for PyQt6 integration
        plotter_config = {'layout': 'per_drone', 'mode': 'embedded'} # Default to embedded for integration
        self.plotter = RealTimePlotter(num_drones, plotter_config)
        self.plot_update_interval = 0.1 # 10Hz
        self.last_plot_update = 0.0

        # Removed pygame clock
        self.trajectory_queue = None
        # Placeholder for config, will be loaded or passed from main
        self.config = {
            'display': {'width': 1000, 'height': 700},
            'camera': {'top_height': 20, 'speed': 10} # Added camera speed for future UI control
        }

    # Removed init_opengl
    # Removed set_perspective (will be handled by OpenGLSimulationWidget)
    # Removed handle_events

    def update(self, dt):
        # Camera update is now handled by OpenGLSimulationWidget's event handlers
        # and passed to camera.process_keyboard_input/process_mouse_movement.
        # self.camera.update(keys, dt) -> No longer needed here

        for drone in self.drones:
            drone.update_dynamics(dt)
        
        self.elapsed_time += dt
        self.logger.log(self.elapsed_time, self.drones)

        # Update Plotter Data
        self.plotter.update_data(self.elapsed_time, self.drones)
        
        # Plotter needs to update its internal plot data for rendering to buffer
        # This will be called by OpenGLSimulationWidget if plotter is embedded
        # if self.elapsed_time - self.last_plot_update > self.plot_update_interval:
        #     self.plotter.update_plot() # Only needed for pop-out mode now
        #     self.last_plot_update = self.elapsed_time

    def run(self, result_queue=None):
        # This method is now just for cleanup or final data collection,
        # as the main loop will be in the PyQt6 application.
        
        self.logger.save()

        if result_queue:
            result_queue.put(self.logger.data)
        return self.logger.data