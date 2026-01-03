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
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from multiprocessing import Process, Queue
import time
import numpy as np
import tkinter as tk
from tkinter import ttk

def get_layout_config():
    """Shows a dialog to select the plotting layout."""
    layout_choice = {'value': 'per_drone'} # Default
    
    root = tk.Tk()
    root.title("Plotter Configuration")
    root.geometry("300x150")
    
    # Center the window
    root.eval('tk::PlaceWindow . center')

    lbl = ttk.Label(root, text="Select Plot Layout:")
    lbl.pack(pady=10)

    # Variables
    selected_layout = tk.StringVar(value='per_drone')

    r1 = ttk.Radiobutton(root, text="Per-Drone View (Separate Rows)", variable=selected_layout, value='per_drone')
    r1.pack(anchor=tk.W, padx=20)

    r2 = ttk.Radiobutton(root, text="Combined View (All in One)", variable=selected_layout, value='combined')
    r2.pack(anchor=tk.W, padx=20)

    def on_start():
        layout_choice['value'] = selected_layout.get()
        root.destroy()

    btn = ttk.Button(root, text="Start Plotter", command=on_start)
    btn.pack(pady=15)

    root.mainloop()
    return layout_choice['value']


class RealTimePlotter:
    def __init__(self, data_queue, num_drones, layout='per_drone'):
        self.data_queue = data_queue
        self.num_drones = num_drones
        self.layout = layout
        self.fig = None
        self.axes = None # Can be list or numpy array depending on layout
        self.lines_pos = [] # structure depends on layout? No, let's keep list of [l1,l2,l3] per drone
        self.lines_rot = []
        
        # Buffers for plotting
        self.times = []
        self.pos_data = [[[], [], []] for _ in range(num_drones)] 
        self.rot_data = [[[], [], []] for _ in range(num_drones)]

    def _init_plot(self):
        if self.layout == 'combined':
            self.fig, self.axes = plt.subplots(2, 1, figsize=(10, 8))
            self.axes[0].set_title('Position (X, Y, Z)')
            self.axes[0].set_ylabel('Position (m)')
            self.axes[0].grid(True)
            self.axes[1].set_title('Rotation (Roll, Pitch, Yaw)')
            self.axes[1].set_ylabel('Angle (deg)')
            self.axes[1].set_xlabel('Time (s)')
            self.axes[1].grid(True)
            
            # Helper to get axes
            ax_pos_list = [self.axes[0]] * self.num_drones
            ax_rot_list = [self.axes[1]] * self.num_drones
            
        else: # per_drone
            # nrows=num_drones, ncols=2 (Pos, Rot)
            self.fig, self.axes = plt.subplots(self.num_drones, 2, figsize=(12, 3 * self.num_drones), squeeze=False)
            # squeeze=False ensures axes is always 2D array [row][col]
            
            for i in range(self.num_drones):
                self.axes[i][0].set_title(f'Drone {i} Position')
                self.axes[i][0].set_ylabel('m')
                self.axes[i][0].grid(True)
                
                self.axes[i][1].set_title(f'Drone {i} Rotation')
                self.axes[i][1].set_ylabel('deg')
                self.axes[i][1].grid(True)
                
                if i == self.num_drones - 1:
                    self.axes[i][0].set_xlabel('Time (s)')
                    self.axes[i][1].set_xlabel('Time (s)')
            
            self.fig.tight_layout()
            
            # Helper lists so we can just index by drone_id later
            ax_pos_list = [self.axes[i][0] for i in range(self.num_drones)]
            ax_rot_list = [self.axes[i][1] for i in range(self.num_drones)]

        colors = ['r', 'g', 'b', 'c', 'm', 'y']
        
        for i in range(self.num_drones):
            # If combined, use different colors for different drones? Or different linestyles?
            # Let's use color cycle.
            c = colors[i % len(colors)]
            
            # Position
            ax_pos = ax_pos_list[i]
            l1, = ax_pos.plot([], [], label=f'D{i} X', color=c, linestyle='-')
            l2, = ax_pos.plot([], [], label=f'D{i} Y', color=c, linestyle='--')
            l3, = ax_pos.plot([], [], label=f'D{i} Z', color=c, linestyle='-.')
            self.lines_pos.append([l1, l2, l3])
            
            # Rotation
            ax_rot = ax_rot_list[i]
            l4, = ax_rot.plot([], [], label=f'D{i} R', color=c, linestyle='-')
            l5, = ax_rot.plot([], [], label=f'D{i} P', color=c, linestyle='--')
            l6, = ax_rot.plot([], [], label=f'D{i} Y', color=c, linestyle='-.')
            self.lines_rot.append([l4, l5, l6])

        # Legends
        if self.layout == 'combined':
            self.axes[0].legend(loc='upper right', fontsize='small', ncol=max(1, self.num_drones//2))
            self.axes[1].legend(loc='upper right', fontsize='small', ncol=max(1, self.num_drones//2))
        else:
            for i in range(self.num_drones):
                self.axes[i][0].legend(loc='upper right', fontsize='x-small')
                self.axes[i][1].legend(loc='upper right', fontsize='x-small')


    def _update(self, frame):
        while not self.data_queue.empty():
            try:
                data = self.data_queue.get_nowait()
                if data is None:
                    return
                
                t = data['time']
                self.times.append(t)
                
                # Keep fixed window
                if len(self.times) > 500:
                    self.times.pop(0)
                    for d in range(self.num_drones):
                        for a in range(3):
                            self.pos_data[d][a].pop(0)
                            self.rot_data[d][a].pop(0)

                for i, drone_state in enumerate(data['drones']):
                    pos = drone_state['position']
                    rot = drone_state['rotation']
                    
                    for j in range(3):
                        self.pos_data[i][j].append(pos[j])
                        self.rot_data[i][j].append(rot[j])

            except Exception:
                pass

        if not self.times:
            return

        for i in range(self.num_drones):
            for j in range(3):
                self.lines_pos[i][j].set_data(self.times, self.pos_data[i][j])
                self.lines_rot[i][j].set_data(self.times, self.rot_data[i][j])

        # Autoscale logic
        if self.layout == 'combined':
             for ax in self.axes:
                ax.relim()
                ax.autoscale_view()
        else:
            for row in self.axes:
                for ax in row:
                    ax.relim()
                    ax.autoscale_view()

    def run(self):
        self._init_plot()
        ani = animation.FuncAnimation(self.fig, self._update, interval=100, cache_frame_data=False)
        plt.show()

def run_plotter(data_queue, num_drones):
    # Retrieve configuration from GUI
    layout = get_layout_config()
    print(f"Starting plotter with layout: {layout}")
    
    plotter = RealTimePlotter(data_queue, num_drones, layout=layout)
    plotter.run()
