import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

from utils import *



class Rendering:
    def __init__(self):
        pass

    def draw_axes(self, length=2.0):
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

    def render_scene(self, camera, drones, prop_spin):
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
        # Drones
        for drone in drones:
            glPushMatrix()
            glTranslatef(drone.state.position[0], drone.state.position[1], drone.state.position[2])
            glRotatef(drone.state.rotation[0], 1, 0, 0)
            glRotatef(drone.state.rotation[1], 0, 1, 0)
            glRotatef(drone.state.rotation[2], 0, 0, 1)
            drone.draw_drone(prop_spin)
            self.draw_axes(length=2.0)
            glPopMatrix()