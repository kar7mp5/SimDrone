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
from PyQt6.QtWidgets import (
    QApplication, QDialog, QLabel, QRadioButton, QButtonGroup,
    QVBoxLayout, QPushButton, QMainWindow, QWidget
)
from PyQt6.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg


def get_plot_config():
    """Shows a dialog to select the plotting layout and display mode using PyQt."""
    config = {'layout': 'per_drone', 'mode': 'embedded'}
    
    app = QApplication.instance() or QApplication([])
    dialog = QDialog()
    dialog.setWindowTitle("Plotter Configuration")
    dialog.setFixedSize(350, 250)
    
    layout = QVBoxLayout()
    
    # Layout Selection
    lbl_layout = QLabel("Select Plot Layout:")
    layout.addWidget(lbl_layout)
    
    group_layout = QButtonGroup()
    rb_per_drone = QRadioButton("Per-Drone View")
    rb_per_drone.setChecked(True)
    rb_combined = QRadioButton("Combined View")
    group_layout.addButton(rb_per_drone)
    group_layout.addButton(rb_combined)
    layout.addWidget(rb_per_drone)
    layout.addWidget(rb_combined)
    
    # Mode Selection
    lbl_mode = QLabel("Select Display Mode:")
    layout.addWidget(lbl_mode)
    
    group_mode = QButtonGroup()
    rb_embedded = QRadioButton("Embedded (Unified Window)")
    rb_embedded.setChecked(True)
    rb_pop_out = QRadioButton("Pop-out (Separate Window)")
    group_mode.addButton(rb_embedded)
    group_mode.addButton(rb_pop_out)
    layout.addWidget(rb_embedded)
    layout.addWidget(rb_pop_out)
    
    # Start Button
    btn = QPushButton("Start Simulation")
    def on_start():
        config['layout'] = 'per_drone' if rb_per_drone.isChecked() else 'combined'
        config['mode'] = 'embedded' if rb_embedded.isChecked() else 'pop_out'
        dialog.accept()
    btn.clicked.connect(on_start)
    layout.addWidget(btn)
    
    dialog.setLayout(layout)
    dialog.exec()
    
    return config

class RealTimePlotter:
    def __init__(self, num_drones, config):
        self.num_drones = num_drones
        self.layout = config['layout']
        self.mode = config['mode']
        
        # Configure backend and imports based on mode
        if self.mode == 'embedded':
            matplotlib.use('Agg')  # Non-interactive for buffer rendering
            from matplotlib import pyplot as plt
            self.plt = plt
            self.fig = Figure(dpi=100)
            self.canvas = FigureCanvasAgg(self.fig)  # Explicit Agg canvas
            self.window = None
        else:
            matplotlib.use('QtAgg')  # Interactive for Qt windows
            from matplotlib import pyplot as plt
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
            self.plt = plt
            self.fig = Figure(dpi=100)
            self.canvas = None
            self.window = None
            
            # Ensure QApplication exists before creating widgets
            app = QApplication.instance() or QApplication([])
            
            self.window = QMainWindow()
            central_widget = QWidget()
            self.window.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            self.canvas = FigureCanvas(self.fig)
            layout.addWidget(self.canvas)
            self.window.show()
        
        self.axes = None
        self.lines_pos = []
        self.lines_rot = []
        
        # Buffers
        self.times = []
        self.pos_data = [[[], [], []] for _ in range(num_drones)]
        self.rot_data = [[[], [], []] for _ in range(num_drones)]
        
        self._init_plot()
    
    def _init_plot(self):
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
        if self.canvas:
            self.canvas.draw()
            QApplication.processEvents()  # Qt 이벤트 루프 처리
        
    def render_to_buffer(self):
        """Called when in embedded mode to get image buffer."""
        self._update_lines()
        self._relim()
        self.canvas.draw()  # Render with Agg
        buf = np.asarray(self.canvas.buffer_rgba())  # Shape: (height, width, 4), RGBA
        width, height = self.canvas.get_width_height()
        return buf, width, height
    
    def _update_lines(self):
        for i in range(self.num_drones):
            for j in range(3):
                self.lines_pos[i][j].set_data(self.times, self.pos_data[i][j])
                self.lines_rot[i][j].set_data(self.times, self.rot_data[i][j])
    
    def _relim(self):
        axes_to_update = self.fig.axes if self.layout == 'combined' else [ax for row in self.axes for ax in row]
        for ax in axes_to_update:
            ax.relim()
            ax.autoscale_view()