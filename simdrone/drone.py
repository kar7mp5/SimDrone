import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

from utils import *


class Quadcopter:
    def __init__(self):
        self.quadric = gluNewQuadric()
        self.drone_list = None

    def init_display_lists(self):
        self.create_drone_display_list()

    def create_drone_display_list(self):
        self.drone_list = glGenLists(1)
        glNewList(self.drone_list, GL_COMPILE)
        # Central body
        glPushMatrix()
        glColor3f(0.8, 0.2, 0.2)  # Reddish body
        glRotatef(90, 1, 0, 0)
        gluCylinder(self.quadric, 0.4, 0.4, 0.1, 10, 1)  # Flat cylinder
        gluDisk(self.quadric, 0, 0.4, 10, 1)  # Top cap
        glTranslatef(0, 0, 0.1)
        gluDisk(self.quadric, 0, 0.4, 10, 1)  # Bottom cap
        glPopMatrix()
        # Camera pod
        glPushMatrix()
        glTranslatef(0, -0.15, 0)
        glColor3f(0.1, 0.1, 0.1)
        gluSphere(self.quadric, 0.1, 10, 8)
        glPopMatrix()
        # Arms
        self.draw_arm(45)
        self.draw_arm(135)
        self.draw_arm(-45)
        self.draw_arm(-135)
        # Landing gear
        gear_dist = 0.6
        self.draw_landing_gear(gear_dist / np.sqrt(2), gear_dist / np.sqrt(2))
        self.draw_landing_gear(gear_dist / np.sqrt(2), -gear_dist / np.sqrt(2))
        self.draw_landing_gear(-gear_dist / np.sqrt(2), gear_dist / np.sqrt(2))
        self.draw_landing_gear(-gear_dist / np.sqrt(2), -gear_dist / np.sqrt(2))
        glEndList()

    def draw_axes(self, length=1.0):
        glLineWidth(2.5)
        glBegin(GL_LINES)
        glColor3f(1.0, 0.3, 0.3)  # X red
        glVertex3f(0, 0, 0); glVertex3f(length, 0, 0)
        glColor3f(0.3, 1.0, 0.3)  # Y green
        glVertex3f(0, 0, 0); glVertex3f(0, length, 0)
        glColor3f(0.3, 0.3, 1.0)  # Z blue
        glVertex3f(0, 0, 0); glVertex3f(0, 0, length)
        glEnd()

    def draw_grid(self, size=40, step=2):
        glLineWidth(1.0)
        glColor3f(0.4, 0.4, 0.4)
        glBegin(GL_LINES)
        for i in range(-size, size + 1, step):
            glVertex3f(i, 0, -size); glVertex3f(i, 0, size)
            glVertex3f(-size, 0, i); glVertex3f(size, 0, i)
        glEnd()

    def draw_propeller_blade(self, length=0.5, width=0.1, thickness=0.02):
        glBegin(GL_TRIANGLES)
        # Simplified blade 1
        glVertex3f(0, 0, 0)
        glVertex3f(width/2, thickness/2, length)
        glVertex3f(-width/2, thickness/2, length)
        glVertex3f(0, 0, 0)
        glVertex3f(width/2, -thickness/2, length)
        glVertex3f(-width/2, -thickness/2, length)
        # Blade 2 (opposite)
        glVertex3f(0, 0, 0)
        glVertex3f(width/2, thickness/2, -length)
        glVertex3f(-width/2, thickness/2, -length)
        glVertex3f(0, 0, 0)
        glVertex3f(width/2, -thickness/2, -length)
        glVertex3f(-width/2, -thickness/2, -length)
        glEnd()

    def draw_propeller(self, x, z, spin_angle, y=0.1, num_blades=2):
        glPushMatrix()
        glTranslatef(x, y, z)
        glRotatef(spin_angle, 0, 1, 0)
        glColor3f(0.5, 0.5, 0.5)  # Gray for propellers
        for i in range(num_blades):
            glPushMatrix()
            glRotatef(i * 180, 0, 1, 0)
            self.draw_propeller_blade()
            glPopMatrix()
        # Central hub
        glColor3f(0.3, 0.3, 0.3)
        gluSphere(self.quadric, 0.05, 10, 8)
        glPopMatrix()

    def draw_cube(self, size=1.0):
        half = size / 2
        glBegin(GL_QUADS)
        # Front
        glVertex3f(-half, -half, half)
        glVertex3f(half, -half, half)
        glVertex3f(half, half, half)
        glVertex3f(-half, half, half)
        # Back
        glVertex3f(-half, -half, -half)
        glVertex3f(-half, half, -half)
        glVertex3f(half, half, -half)
        glVertex3f(half, -half, -half)
        # Left
        glVertex3f(-half, -half, half)
        glVertex3f(-half, half, half)
        glVertex3f(-half, half, -half)
        glVertex3f(-half, -half, -half)
        # Right
        glVertex3f(half, -half, half)
        glVertex3f(half, -half, -half)
        glVertex3f(half, half, -half)
        glVertex3f(half, half, half)
        # Top
        glVertex3f(-half, half, half)
        glVertex3f(half, half, half)
        glVertex3f(half, half, -half)
        glVertex3f(-half, half, -half)
        # Bottom
        glVertex3f(-half, -half, half)
        glVertex3f(-half, -half, -half)
        glVertex3f(half, -half, -half)
        glVertex3f(half, -half, half)
        glEnd()

    def draw_arm(self, theta, length=1.2, width=0.1, height=0.05):
        glPushMatrix()
        glRotatef(theta, 0, 1, 0)
        glTranslatef(0, height/2, length/2)
        glScalef(width, height, length)
        glColor3f(0.7, 0.7, 0.7)  # Lighter gray for arms
        self.draw_cube()
        glPopMatrix()

    def draw_landing_gear(self, x, z, height=0.3, radius=0.02):
        glPushMatrix()
        glTranslatef(x, -height/2, z)
        glRotatef(90, 1, 0, 0)
        glColor3f(0.4, 0.4, 0.4)
        gluCylinder(self.quadric, radius, radius, height, 10, 1)
        glPopMatrix()

    def draw_drone(self, spin_angle):
        glCallList(self.drone_list)
        # Propellers
        prop_dist = 1.0
        self.draw_propeller(prop_dist / np.sqrt(2), prop_dist / np.sqrt(2), spin_angle)
        self.draw_propeller(prop_dist / np.sqrt(2), -prop_dist / np.sqrt(2), spin_angle + 45)
        self.draw_propeller(-prop_dist / np.sqrt(2), prop_dist / np.sqrt(2), spin_angle + 90)
        self.draw_propeller(-prop_dist / np.sqrt(2), -prop_dist / np.sqrt(2), spin_angle + 135)

    def render_scene(self, camera, rotation_angle, prop_spin):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        # World-fixed light
        light_pos = (10.0, 10.0, 10.0, 1.0)
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        # Camera transform
        camera.apply()
        # Grid and axes (unlit)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        self.draw_grid(40, 2)
        self.draw_axes(2.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        # Drone
        glPushMatrix()
        glRotatef(rotation_angle, 0, 1, 0)
        glRotatef(rotation_angle * 0.6, 1, 0, 0)
        self.draw_drone(prop_spin)
        glPopMatrix()
