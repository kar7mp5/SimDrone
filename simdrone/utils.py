import numpy as np


# Global constants
MOVE_SPEED = 5.0  # meters per second
ROT_SPEED = 120.0  # degrees per second
MOUSE_SENSITIVITY = 0.15  # unused now


class TransformState:
    def __init__(self, position=[0.0, 0.0, 0.0], rotation=[0.0, 0.0, 0.0]):
        self.position = np.array(position, dtype=float)
        self.rotation = np.array(rotation, dtype=float)  # pitch, yaw, roll (degrees)

    def translate(self, delta):
        self.position += np.array(delta)

    def rotate(self, delta):
        self.rotation += np.array(delta)
        self.rotation[0] = np.clip(self.rotation[0], -89.9, 89.9)  # pitch limit
