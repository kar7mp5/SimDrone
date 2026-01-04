import sys
import math
import numpy as np
from OpenGL import GL as gl
from OpenGL.GLU import gluPerspective, gluNewQuadric # For perspective and quadric objects
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QCheckBox, QComboBox, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QWheelEvent, QMouseEvent

from simdrone.simulator import Simulator # We'll need to refactor Simulator
from simdrone.camera import Camera
from simdrone.render import Rendering
from simdrone.plotter import RealTimePlotter


class OpenGLSimulationWidget(QOpenGLWidget):
    def __init__(self, simulator_instance: Simulator, parent=None):
        super().__init__(parent)
        self.simulator = simulator_instance
        self.camera = self.simulator.camera
        self.renderer = self.simulator.renderer
        self.plotter = self.simulator.plotter # Assume plotter is always embedded now

        # Camera controls (from reference and existing simulator camera)
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_pressed = False
        
        # We will use the camera zoom directly from the simulator's camera

        # Display toggles
        self.show_grid = True
        self.show_axes = True
        self.show_drones = True
        self.show_plot = True # To toggle the embedded matplotlib plot

        # For rendering the matplotlib plot as a texture
        self.plot_texture_id = None
        self.plot_width = 0
        self.plot_height = 0

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus) # Enable key press events

        # Set up a timer for simulation updates and rendering
        self.simulation_timer = QTimer(self)
        self.simulation_timer.setInterval(30) # ~30 FPS, adjust as needed
        self.simulation_timer.timeout.connect(self._update_simulation_and_render)
        self.simulation_timer.start()

    def _update_simulation_and_render(self):
        dt = self.simulation_timer.interval() / 1000.0 # Time step in seconds
        self.simulator.update(dt) # Call the simulator's update logic
        self.update() # Request a repaint

    def initializeGL(self):
        gl.glClearColor(0.04, 0.04, 0.10, 1.0) # Background from original simulator
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_LIGHT0)
        gl.glEnable(gl.GL_COLOR_MATERIAL)
        gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)

        # Set up initial perspective
        self.resizeGL(self.width(), self.height())

        # Initialize plot texture
        self.plot_texture_id = gl.glGenTextures(1)

    def resizeGL(self, w, h):
        gl.glViewport(0, 0, w, h)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        aspect = w / h if h != 0 else 1
        gluPerspective(65, aspect, 0.1, 2000) # From original simulator
        gl.glMatrixMode(gl.GL_MODELVIEW)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glLoadIdentity()

        # Apply camera transformations
        self.camera.apply() # Camera class already handles glTranslate and glRotate

        # Render scene components based on toggles
        gl.glDisable(gl.GL_LIGHTING) # Grid and axes don't need lighting
        gl.glDisable(gl.GL_DEPTH_TEST) # Grid and axes should always be visible
        if self.show_grid:
            self.renderer.draw_grid()
        if self.show_axes:
            # Draw origin axes
            gl.glPushMatrix()
            gl.glLineWidth(3.0)
            gl.glBegin(gl.GL_LINES)
            gl.glColor3f(1.0, 0.0, 0.0); gl.glVertex3f(0,0,0); gl.glVertex3f(1.5,0,0) # X
            gl.glColor3f(0.0, 1.0, 0.0); gl.glVertex3f(0,0,0); gl.glVertex3f(0,1.5,0) # Y
            gl.glColor3f(0.0, 0.0, 1.0); gl.glVertex3f(0,0,0); gl.glVertex3f(0,0,1.5) # Z
            gl.glEnd()
            gl.glPopMatrix()

        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_LIGHTING)

        if self.show_drones:
            # Render each drone (renderer handles position, rotation, and drawing cube/axes)
            # We need to adapt render_scene to use the toggles for drone axes within it,
            # or draw drone axes here. For now, let's just call render_scene as is.
            # render.py draw_axes is called for each drone within render_scene
            self.renderer.render_scene(self.camera, self.simulator.drones, clear=False) # clear is handled by paintGL

        # Render matplotlib plot as a 2D overlay
        if self.show_plot and self.plotter and self.plotter.mode == 'embedded':
            self._render_plot_texture()

    def _render_plot_texture(self):
        # Get plot data from plotter
        plot_buffer, self.plot_width, self.plot_height = self.plotter.render_to_buffer()

        # Set up for 2D rendering
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, self.width(), 0, self.height(), -1, 1) # Orthographic projection for 2D overlay
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()

        gl.glDisable(gl.GL_LIGHTING)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_TEXTURE_2D)

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.plot_texture_id)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, self.plot_width, self.plot_height, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, plot_buffer)

        # Draw the texture in a corner (e.g., bottom-left)
        # Adjust position and size as needed
        texture_scale = 0.5 # Make it smaller
        margin = 10
        x = margin
        y = margin
        width = self.plot_width * texture_scale
        height = self.plot_height * texture_scale

        gl.glColor4f(1.0, 1.0, 1.0, 1.0) # White to show original colors
        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 0); gl.glVertex2f(x, y)
        gl.glTexCoord2f(1, 0); gl.glVertex2f(x + width, y)
        gl.glTexCoord2f(1, 1); gl.glVertex2f(x + width, y + height)
        gl.glTexCoord2f(0, 1); gl.glVertex2f(x, y + height)
        gl.glEnd()

        gl.glDisable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_BLEND)
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_LIGHTING)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()

    def mousePressEvent(self, event: QMouseEvent):
        self.mouse_pressed = True
        self.last_mouse_x = event.position().x()
        self.last_mouse_y = event.position().y()
        self.camera.mouse_pressed = True # Inform camera too
        self.camera.last_mouse_pos = np.array([event.position().x(), event.position().y()])

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.mouse_pressed:
            dx = event.position().x() - self.last_mouse_x
            dy = event.position().y() - self.last_mouse_y
            
            # Use camera's rotation mechanism
            # Assuming camera has rotate_horizontal and rotate_vertical methods
            # or direct access to its angles. For now, let's map directly.
            self.camera.process_mouse_movement(dx, dy) # This needs to be implemented or adapted in Camera class

            self.last_mouse_x = event.position().x()
            self.last_mouse_y = event.position().y()
            self.update() # Request repaint

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.mouse_pressed = False
        self.camera.mouse_pressed = False

    def wheelEvent(self, event: QWheelEvent):
        # Use camera's zoom mechanism
        self.camera.process_scroll(event.angleDelta().y() / 120.0) # This needs to be implemented or adapted
        self.update() # Request repaint

    def keyPressEvent(self, event):
        # Pass key events to camera for movement
        self.camera.process_keyboard_input(event.key(), True) # This needs to be implemented or adapted
        self.update()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        self.camera.process_keyboard_input(event.key(), False) # This needs to be implemented or adapted
        self.update()
        super().keyReleaseEvent(event)

    def set_simulation_speed(self, speed):
        # Invert speed for QTimer interval: higher speed means lower interval
        if speed > 0:
            self.simulation_timer.setInterval(int(1000 / (speed * 60))) # Max 60 FPS, speed 1.0 means ~16ms interval
        else:
            self.simulation_timer.setInterval(1000) # Very slow if speed is 0
        
    def toggle_grid(self, state):
        self.show_grid = bool(state)
        self.update()

    def toggle_axes(self, state):
        self.show_axes = bool(state)
        self.update()

    def toggle_drones(self, state):
        self.show_drones = bool(state)
        self.update()

    def toggle_plot(self, state):
        self.show_plot = bool(state)
        self.update()
