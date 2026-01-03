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
import tkinter as tk
from tkinter import ttk

def get_plot_config():
    """Shows a dialog to select the plotting layout and display mode."""
    config = {'layout': 'per_drone', 'mode': 'embedded'}
    
    root = tk.Tk()
    root.title("Plotter Configuration")
    root.geometry("350x250")
    
    root.eval('tk::PlaceWindow . center')

    # Layout Selection
    lbl_layout = ttk.Label(root, text="Select Plot Layout:")
    lbl_layout.pack(pady=(10, 5))
    
    var_layout = tk.StringVar(value='per_drone')
    ttk.Radiobutton(root, text="Per-Drone View", variable=var_layout, value='per_drone').pack(anchor=tk.W, padx=40)
    ttk.Radiobutton(root, text="Combined View", variable=var_layout, value='combined').pack(anchor=tk.W, padx=40)

    # Mode Selection
    lbl_mode = ttk.Label(root, text="Select Display Mode:")
    lbl_mode.pack(pady=(15, 5))
    
    var_mode = tk.StringVar(value='embedded')
    ttk.Radiobutton(root, text="Embedded (Unified Window)", variable=var_mode, value='embedded').pack(anchor=tk.W, padx=40)
    ttk.Radiobutton(root, text="Pop-out (Separate Window)", variable=var_mode, value='pop_out').pack(anchor=tk.W, padx=40)

    def on_start():
        config['layout'] = var_layout.get()
        config['mode'] = var_mode.get()
        root.destroy()

    btn = ttk.Button(root, text="Start Simulation", command=on_start)
    btn.pack(pady=20)

    root.mainloop()
    return config


class RealTimePlotter:
    def __init__(self, num_drones, config):
        self.num_drones = num_drones
        self.layout = config['layout']
        self.mode = config['mode']
        
        # Configure Backend BEFORE importing pyplot
        if self.mode == 'embedded':
            matplotlib.use('Agg')
        else:
            try:
                matplotlib.use('TkAgg')
            except:
                pass # Use default

        import matplotlib.pyplot as plt
        self.plt = plt
        
        if self.mode == 'pop_out':
            self.plt.ion() # Interactive mode for pop-out

        self.fig = None
        self.axes = None 
        self.lines_pos = [] 
        self.lines_rot = []
        
        # Buffers
        self.times = []
        self.pos_data = [[[], [], []] for _ in range(num_drones)] 
        self.rot_data = [[[], [], []] for _ in range(num_drones)]
        
        self._init_plot()

    def _init_plot(self):
        dpi = 100
        if self.mode == 'embedded':
             figsize = (5, 8) if self.layout == 'combined' else (6, 2.5 * self.num_drones)
        else:
             figsize = (8, 6) if self.layout == 'combined' else (10, 3 * self.num_drones)

        if self.layout == 'combined':
            self.fig, self.axes = self.plt.subplots(2, 1, figsize=figsize, dpi=dpi)
            self.axes[0].set_title('Position')
            self.axes[0].grid(True)
            self.axes[1].set_title('Rotation')
            self.axes[1].grid(True)
            ax_pos_list = [self.axes[0]] * self.num_drones
            ax_rot_list = [self.axes[1]] * self.num_drones
        else:
            self.fig, self.axes = self.plt.subplots(self.num_drones, 2, figsize=figsize, squeeze=False, dpi=dpi)
            for i in range(self.num_drones):
                self.axes[i][0].set_title(f'D{i} Pos')
                self.axes[i][0].grid(True)
                self.axes[i][1].set_title(f'D{i} Rot')
                self.axes[i][1].grid(True)
            
            self.fig.tight_layout()
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

        # Optimize layout
        self.fig.tight_layout(pad=2.0)
        
    def update_data(self, time_val, drones):
        self.times.append(time_val)
        if len(self.times) > 300:
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
        """Called when in pop-out mode to refresh the window."""
        self._update_lines()
        self._relim()
        
        # Interactive update
        self.fig.canvas.flush_events()
        # self.plt.pause(0.001) # pause might steal focus or slow things down too much?
        # canvas.flush_events() is better if we are in main loop control.
        # But we need to ensure the GUI event loop runs. 
        # Using pause(0.001) is the standard way to run the GUI loop briefly.
        self.plt.pause(0.001)

    def render_to_buffer(self):
        """Called when in embedded mode to get image buffer."""
        self._update_lines()
        self._relim()
        self.fig.canvas.draw()
        buf = self.fig.canvas.buffer_rgba()
        width, height = self.fig.canvas.get_width_height()
        return buf, width, height

    def _update_lines(self):
        for i in range(self.num_drones):
            for j in range(3):
                self.lines_pos[i][j].set_data(self.times, self.pos_data[i][j])
                self.lines_rot[i][j].set_data(self.times, self.rot_data[i][j])

    def _relim(self):
        if self.layout == 'combined':
             for ax in self.axes:
                ax.relim()
                ax.autoscale_view()
        else:
            for row in self.axes:
                for ax in row:
                    ax.relim()
                    ax.autoscale_view()
