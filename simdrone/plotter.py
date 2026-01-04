# plotter.py
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
import matplotlib
import numpy as np
# QApplication, QDialog, etc. imports are no longer needed if get_plot_config is removed
# QMainWindow, QWidget are also no longer needed in plotter.py
from PyQt6.QtWidgets import (
    QApplication, # Keep QApplication for processEvents if needed, but not for instance creation
)
from PyQt6.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg


# get_plot_config() function is removed as plotter is now always embedded
# and its configuration is passed directly during initialization.


class RealTimePlotter:
    def __init__(self, num_drones, config):
        self.num_drones = num_drones
        self.layout = config['layout']
        self.mode = 'embedded' # Force embedded mode for PyQt6 integration
        
        # Configure backend and imports for embedded mode
        matplotlib.use('Agg')  # Non-interactive for buffer rendering
        from matplotlib import pyplot as plt
        self.plt = plt
        self.fig = Figure(dpi=100)
        self.canvas = FigureCanvasAgg(self.fig)  # Explicit Agg canvas
        self.window = None # No separate window for embedded mode
        
        self.axes = None
        self.lines_pos = []
        self.lines_rot = []
        
        # Buffers
        self.times = []
        self.pos_data = [[[], [], []] for _ in range(num_drones)]
        self.rot_data = [[[], [], []] for _ in range(num_drones)]
        
        self._init_plot()
    
    def _init_plot(self):
        self.fig.clear() # Clear existing figure content before re-initializing
        if self.layout == 'combined':
            gs = self.fig.add_gridspec(2, 1)
            ax_pos = self.fig.add_subplot(gs[0])
            ax_rot = self.fig.add_subplot(gs[1])
            ax_pos.set_title('Position')
            ax_pos.grid(True)
            ax_rot.set_title('Rotation')
            ax_rot.grid(True)
            ax_pos_list = [ax_pos] * self.num_drones
            ax_rot_list = [ax_rot] * self.num_drones
        else:
            gs = self.fig.add_gridspec(self.num_drones, 2)
            self.axes = []
            for i in range(self.num_drones):
                ax_pos = self.fig.add_subplot(gs[i, 0])
                ax_rot = self.fig.add_subplot(gs[i, 1])
                ax_pos.set_title(f'D{i} Pos')
                ax_pos.grid(True)
                ax_rot.set_title(f'D{i} Rot')
                ax_rot.grid(True)
                self.axes.append((ax_pos, ax_rot))
            ax_pos_list = [self.axes[i][0] for i in range(self.num_drones)]
            ax_rot_list = [self.axes[i][1] for i in range(self.num_drones)]
        
        colors = ['r', 'g', 'b', 'c', 'm', 'y']
        
        for i in range(self.num_drones):
            c = colors[i % len(colors)]
            ax_pos = ax_pos_list[i]
            l1, = ax_pos.plot([], [], label=f'X', color=c, linestyle='-')
            l2, = ax_pos.plot([], [], label=f'Y', color=c, linestyle='--')
            l3, = ax_pos.plot([], [], label=f'Z', color=c, linestyle='-.')
            self.lines_pos.append([l1, l2, l3])
            
            ax_rot = ax_rot_list[i]
            l4, = ax_rot.plot([], [], label=f'R', color=c, linestyle='-')
            l5, = ax_rot.plot([], [], label=f'P', color=c, linestyle='--')
            l6, = ax_rot.plot([], [], label=f'Y', color=c, linestyle='-.')
            self.lines_rot.append([l4, l5, l6])
        
        self.fig.tight_layout(pad=2.0)
    
    def update_data(self, time_val, drones):
        self.times.append(time_val)
        if len(self.times) > 300: # Limit history
            self.times.pop(0)
            for d in range(self.num_drones):
                for a in range(3):
                    self.pos_data[d][a].pop(0)
                    self.rot_data[d][a].pop(0)
        for i, drone in enumerate(drones):
            pos = drone.state.position
            rot = drone.state.rotation
            for j in range(3):
                self.pos_data[i][j].append(pos[j])
                self.rot_data[i][j].append(rot[j])
    
    def update_plot(self):
        """No longer used for embedded mode. It would be used for pop-out to refresh window."""
        pass # The actual rendering is now done by render_to_buffer

    def render_to_buffer(self):
        """Called when in embedded mode to get image buffer."""
        self._update_lines()
        self._relim()
        self.canvas.draw()  # Render with Agg
        # Get raw RGBA buffer
        buf = self.canvas.buffer_rgba()
        # Convert to numpy array
        buf = np.asarray(buf) # Shape: (height, width, 4), RGBA
        width, height = self.canvas.get_width_height()
        return buf, width, height
    
    def _update_lines(self):
        for i in range(self.num_drones):
            for j in range(3):
                self.lines_pos[i][j].set_data(self.times, self.pos_data[i][j])
                self.lines_rot[i][j].set_data(self.times, self.rot_data[i][j])
    
    def _relim(self):
        # Update plot limits
        axes_to_update = self.fig.axes if self.layout == 'combined' else [ax for row in self.axes for ax in row]
        for ax in axes_to_update:
            ax.relim()
            ax.autoscale_view()
            # Ensure x-axis shows time
            if len(self.times) > 0:
                ax.set_xlim(self.times[0], self.times[-1])