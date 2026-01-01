import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from utils import *


class Camera:
    def __init__(self):
        self.cam_x, self.cam_y, self.cam_z = 0.0, 1.0, 10.0
        self.cam_yaw, self.cam_pitch = 0.0, 0.0

    def update_rotation(self, keys, dt):
        self.cam_yaw += keys[K_q] * ROT_SPEED * dt  # Q: turn left
        self.cam_yaw -= keys[K_e] * ROT_SPEED * dt  # E: turn right
        self.cam_pitch += keys[K_r] * ROT_SPEED * dt
        self.cam_pitch -= keys[K_f] * ROT_SPEED * dt
        self.cam_pitch = np.clip(self.cam_pitch, -89.9, 89.9)
        self.cam_yaw %= 360

    def update_position(self, keys, dt):
        forward = np.array([
            -np.sin(np.deg2rad(self.cam_yaw)) * np.cos(np.deg2rad(self.cam_pitch)),
            np.sin(np.deg2rad(self.cam_pitch)),
            -np.cos(np.deg2rad(self.cam_yaw)) * np.cos(np.deg2rad(self.cam_pitch)),
        ])
        forward /= np.linalg.norm(forward) or 1.0
        right = np.cross(forward, [0, 1, 0])
        right /= np.linalg.norm(right) or 1.0
        up = np.array([0, 1, 0])
        move = np.zeros(3)
        if keys[K_w]: move += forward
        if keys[K_s]: move -= forward
        if keys[K_a]: move -= right
        if keys[K_d]: move += right
        if keys[K_SPACE]: move += up
        if keys[K_LSHIFT]: move -= up
        if np.linalg.norm(move) > 0:
            move /= np.linalg.norm(move)
            self.cam_x += move[0] * MOVE_SPEED * dt
            self.cam_y += move[1] * MOVE_SPEED * dt
            self.cam_z += move[2] * MOVE_SPEED * dt

    def apply(self):
        glRotatef(-self.cam_pitch, 1, 0, 0)  # pitch
        glRotatef(-self.cam_yaw, 0, 1, 0)  # yaw
        glTranslatef(-self.cam_x, -self.cam_y, -self.cam_z)
