import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from utils import *

from drone import Quadcopter
from camera import Camera




class Simulator:
    def __init__(self):
        self.display = (900, 700)
        self.camera = Camera()
        self.drone = Quadcopter()
        self.clock = pygame.time.Clock()
        self.rotation_angle = 0.0
        self.prop_spin = 0.0
        self.running = True

    def init_opengl(self):
        pygame.init()
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption("Keyboard Rotation (Q/E yaw, R/F pitch) + Rotating Drone")
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        glClearColor(0.05, 0.05, 0.12, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        self.drone.init_display_lists()
        self.set_perspective()

    def set_perspective(self):
        glViewport(0, 0, self.display[0], self.display[1])
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70, self.display[0]/self.display[1], 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
            if event.type == VIDEORESIZE:
                self.display = event.size
                pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL | RESIZABLE)
                self.set_perspective()

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.camera.update_rotation(keys, dt)
        self.camera.update_position(keys, dt)
        self.rotation_angle += 35 * dt
        self.prop_spin += 200 * dt

    def run(self):
        self.init_opengl()
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(dt)
            self.drone.render_scene(self.camera, self.rotation_angle, self.prop_spin)
            pygame.display.flip()
        pygame.quit()
        quit()