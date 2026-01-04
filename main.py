import sys
import threading
import time
import queue
import math # For potential use with graph functions if needed
import numpy as np

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QCheckBox, QComboBox, QPushButton, QDoubleSpinBox, QDialog
from PyQt6.QtCore import Qt, QTimer

from simdrone import Simulator # Our refactored simulator
from simdrone.opengl_simulation_widget import OpenGLSimulationWidget # Our new OpenGL widget
from simdrone.settings import SettingsDialog # Already uses PyQt6


# Global simulator instance, will be initialized in main
global_simulator = None

def control_drones(sim: Simulator):
    """Control logic running in a separate thread."""
    # This function now needs to be aware that the simulator's main loop
    # is driven by a QTimer, and it should only set control inputs,
    # not directly manipulate sim.running or wait for long periods blocking the thread.
    print("Control thread started.")
    time.sleep(1) # Wait for sim to initialize in the main thread

    # Example control sequence - will need to be adapted for continuous simulation
    # For now, let's just make sure it doesn't block forever and sets some controls.
    if sim.drones:
        # Drone 0: Hover, Drone 1: Stay
        if len(sim.drones) > 0:
            sim.drones[0].set_control(thrust=3.0, pitch=10.0)
        if len(sim.drones) > 1:
            sim.drones[1].set_control(thrust=0.0) # Stay on ground
        time.sleep(2)

        # Drone 0: Hover, Drone 1: Takeoff
        if len(sim.drones) > 0:
            sim.drones[0].set_control(thrust=0.28)
        if len(sim.drones) > 1:
            sim.drones[1].set_control(thrust=0.35)
        time.sleep(2)

        # Drone 0: Pitch forward, Drone 1: Hover
        if len(sim.drones) > 0:
            sim.drones[0].set_control(thrust=0.28, pitch=0.01)
        if len(sim.drones) > 1:
            sim.drones[1].set_control(thrust=0.28)
        time.sleep(0.1)

        # Both stop
        if len(sim.drones) > 0:
            sim.drones[0].set_control(thrust=0.0)
        if len(sim.drones) > 1:
            sim.drones[1].set_control(thrust=0.0)
        time.sleep(2)

        # The control thread should ideally be a continuous loop
        # that periodically updates drone controls based on some logic,
        # or it should be managed by events within the Qt application.
        # For this example, it just runs once and exits.
    
    print("Control thread finished.")


class MainWindow(QMainWindow):
    def __init__(self, simulator_instance):
        super().__init__()
        self.setWindowTitle("PyQt6 Drone Simulator")
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.opengl_widget = OpenGLSimulationWidget(simulator_instance)
        self.main_layout.addWidget(self.opengl_widget, 1) # Give OpenGL widget more space

        self._create_controls_panel(simulator_instance)
        
        # When main window is closed, ensure simulator is gracefully stopped
        QApplication.instance().aboutToQuit.connect(self._cleanup_simulator)

    def _create_controls_panel(self, sim: Simulator):
        controls_panel = QWidget()
        controls_layout = QHBoxLayout(controls_panel)
        self.main_layout.addWidget(controls_panel)

        # Simulation Speed Slider
        speed_label = QLabel("Sim Speed:")
        speed_slider = QSlider(Qt.Orientation.Horizontal)
        speed_slider.setMinimum(1)
        speed_slider.setMaximum(100)
        speed_slider.setValue(60) # Default to 1x speed (60 updates per second)
        speed_slider.valueChanged.connect(self.opengl_widget.set_simulation_speed)
        controls_layout.addWidget(speed_label)
        controls_layout.addWidget(speed_slider)
        
        # Display Toggles (Checkboxes)
        grid_check = QCheckBox("Show Grid")
        grid_check.setChecked(True)
        grid_check.stateChanged.connect(self.opengl_widget.toggle_grid)
        controls_layout.addWidget(grid_check)

        axes_check = QCheckBox("Show Axes")
        axes_check.setChecked(True)
        axes_check.stateChanged.connect(self.opengl_widget.toggle_axes)
        controls_layout.addWidget(axes_check)

        drones_check = QCheckBox("Show Drones")
        drones_check.setChecked(True)
        drones_check.stateChanged.connect(self.opengl_widget.toggle_drones)
        controls_layout.addWidget(drones_check)

        plot_check = QCheckBox("Show Plot")
        plot_check.setChecked(True)
        plot_check.stateChanged.connect(self.opengl_widget.toggle_plot)
        controls_layout.addWidget(plot_check)

        # Plot Size Slider
        plot_size_label = QLabel("Plot Size:")
        plot_size_slider = QSlider(Qt.Orientation.Horizontal)
        plot_size_slider.setMinimum(10) # Minimum scale 0.1
        plot_size_slider.setMaximum(100) # Maximum scale 1.0
        plot_size_slider.setValue(50) # Initial scale 0.5
        plot_size_slider.valueChanged.connect(self.opengl_widget.set_plot_scale)
        controls_layout.addWidget(plot_size_label)
        controls_layout.addWidget(plot_size_slider)

        # Reset Button
        reset_button = QPushButton("Reset Sim")
        # You'll need to add a reset method to Simulator and/or OpenGLSimulationWidget
        # For now, let's just make it reset the camera and possibly drone states
        reset_button.clicked.connect(lambda: self._reset_simulation(sim))
        controls_layout.addWidget(reset_button)

        # Settings Button (using existing SettingsDialog)
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(lambda: self._open_settings(sim))
        controls_layout.addWidget(settings_button)

    def _reset_simulation(self, sim: Simulator):
        # Implement a proper reset logic in Simulator and/or OpenGLSimulationWidget
        print("Resetting simulation...")
        sim.elapsed_time = 0.0
        sim.logger = sim.logger.__class__() # Reset logger
        for drone in sim.drones:
            drone.reset() # Reset drone state
        
        # Reset camera
        self.opengl_widget.camera.x_rot = 20.0
        self.opengl_widget.camera.y_rot = 30.0
        self.opengl_widget.camera.zoom = -12.0
        self.opengl_widget.camera.state.position = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        
        # Reset plotter data
        plotter_config = {'layout': 'per_drone', 'mode': 'embedded'}
        sim.plotter = sim.plotter.__class__(sim.num_drones, plotter_config) # Reinitialize plotter

        self.opengl_widget.update() # Force repaint


    def _open_settings(self, sim: Simulator):
        dialog = SettingsDialog(sim.config)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Apply settings from dialog to simulator and potentially camera/renderer
            # For example, if display size changes, it won't affect PyQt window directly,
            # but other settings like camera height might.
            print("Settings applied:", sim.config)
            # You might need to reconfigure parts of the simulation or camera based on new settings
            # e.g., sim.camera.top_height = sim.config['camera']['top_height']
            self.opengl_widget.camera.initial_top_height = sim.config['camera']['top_height'] # Assuming camera uses this
            self.opengl_widget.camera.move_speed_multiplier = sim.config['camera']['speed'] / 10.0 # Example
            self.opengl_widget.update() # Force update after settings change


    def _cleanup_simulator(self):
        # This will be called when the main window closes
        print("Cleaning up simulator...")
        if global_simulator:
            global_simulator.running = False # Signal control thread to stop if it checks this
            global_simulator.logger.save() # Ensure logs are saved

def main():
    global global_simulator
    num_drones = 2

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL) # Ensure OpenGL is used
    app = QApplication(sys.argv)

    # Initialize simulator
    global_simulator = Simulator(num_drones=num_drones)
    
    # Start control thread (it will interact with global_simulator)
    control_thread = threading.Thread(target=control_drones, args=(global_simulator,))
    control_thread.daemon = True # Allow program to exit even if thread is running
    control_thread.start()

    main_window = MainWindow(global_simulator)
    main_window.resize(1200, 800) # Set initial window size
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()