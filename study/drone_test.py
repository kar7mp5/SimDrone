import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
from scipy.spatial.transform import Rotation as R
from dataclasses import dataclass


@dataclass
class DroneParameters:
    mass: float         = 1.4
    g: float            = 9.81
    Ixx: float          = 0.012
    Iyy: float          = 0.013
    Izz: float          = 0.022
    arm_length: float   = 0.24
    drag_linear: float  = 0.08
    max_thrust: float   = 35.0
    min_thrust: float   = 0.0


class Quadcopter:
    def __init__(self, start_pos=np.array([0., 0., 1.5]), ppm=120.0):
        self.params = DroneParameters()
        self.position = start_pos.astype(float).copy()
        self.velocity = np.zeros(3)
        self.orientation = R.identity()
        self.angular_velocity = np.zeros(3)

        self.cmd_thrust = 0.0
        self.cmd_torques = np.zeros(3)

        self.ppm = ppm  # only used if you want to mix 2D HUD later

    def update(self, dt):
        # Angular dynamics
        I_diag = np.array([self.params.Ixx, self.params.Iyy, self.params.Izz])
        I_omega = I_diag * self.angular_velocity
        ang_accel = (self.cmd_torques - np.cross(self.angular_velocity, I_omega)) / I_diag
        self.angular_velocity += ang_accel * dt

        # Integrate orientation
        delta_rot = R.from_rotvec(self.angular_velocity * dt)
        self.orientation = delta_rot * self.orientation
        # Normalize quaternion (robust way)
        q = self.orientation.as_quat()
        norm = np.linalg.norm(q)
        if norm > 1e-10:
            self.orientation = R.from_quat(q / norm)

        # Forces
        Rwb = self.orientation.as_matrix()
        thrust_world = Rwb @ np.array([0., 0., self.cmd_thrust])
        gravity = np.array([0., 0., -self.params.mass * self.params.g])
        drag = -self.params.drag_linear * self.velocity
        acc = (thrust_world + gravity + drag) / self.params.mass

        self.velocity += acc * dt
        self.position += self.velocity * dt

        # Simple ground
        if self.position[2] < 0.02:
            self.position[2] = 0.0
            self.velocity[2] = max(0, self.velocity[2])

    def set_controls(self, thrust, torques):
        self.cmd_thrust = np.clip(thrust, self.params.min_thrust, self.params.max_thrust)
        self.cmd_torques = torques.copy()


# ─── OpenGL drawing helpers ────────────────────────────────────────────────

def draw_axes(length=1.0):
    glBegin(GL_LINES)
    # X red
    glColor3f(1, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(length, 0, 0)
    # Y green
    glColor3f(0, 1, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, length, 0)
    # Z blue
    glColor3f(0, 0, 1)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, length)
    glEnd()

def draw_quadcopter(drone: Quadcopter, scale: float = 1.0) -> None:
    """Draw a simple wireframe quadcopter model using the current OpenGL context.

    The drone is rendered at its current world position with orientation applied,
    using legacy OpenGL fixed-function pipeline (glBegin/glEnd style). Coordinates
    are remapped from physics (X forward, Y right, Z up) to OpenGL (X right, Y up,
    Z into screen) to prevent flipping and ensure correct position/direction:
    - Position remap: OpenGL [x, y, z] = physics [x, z, y]
    - Rotation remap: Uses permutation matrix P to swap Y/Z without handedness flip.

    Args:
        drone: Quadcopter instance containing position and orientation.
        scale: Scaling factor for the visual model (affects arm length & motor size).

    Returns:
        None

    Raises:
        None explicitly, but relies on valid OpenGL context.
    """
    glPushMatrix()

    # Remap position: physics [x, y, z] → OpenGL [x, z, y] (Z up becomes Y up)
    glTranslatef(drone.position[0], drone.position[2], drone.position[1])

    # Get physics rotation matrix (3x3, row-major)
    rot_matrix = drone.orientation.as_matrix().astype(np.float32)

    # Permutation matrix P to swap Y and Z (remap axes without flip)
    P = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=np.float32)

    # Adjusted rotation: P @ rot_matrix @ P.T (transforms basis correctly)
    rot_matrix_open = P @ rot_matrix @ P.T

    # Build 4x4 matrix (for glMultMatrixf)
    mat4 = np.eye(4, dtype=np.float32)
    mat4[:3, :3] = rot_matrix_open

    # Apply column-major flattened (OpenGL convention)
    glMultMatrixf(mat4.T.flatten())

    # Draw arms (X-configuration, body-frame: no changes needed post-remap)
    arm_len = drone.params.arm_length * scale
    glLineWidth(3.0)

    glBegin(GL_LINES)
    glColor3f(0.8, 0.8, 1.0)

    # Arm 1: front-left ↔ back-right
    glVertex3f(-arm_len, -arm_len, 0)
    glVertex3f( arm_len,  arm_len, 0)

    # Arm 2: front-right ↔ back-left
    glVertex3f( arm_len, -arm_len, 0)
    glVertex3f(-arm_len,  arm_len, 0)
    glEnd()

    # Draw motors as spheres
    glColor3f(0.9, 0.3, 0.2)
    quad = gluNewQuadric()

    for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        glPushMatrix()
        glTranslatef(dx * arm_len, dy * arm_len, 0)
        gluSphere(quad, 0.06 * scale, 12, 12)
        glPopMatrix()

    # Draw body center (after motors, before delete)
    glColor3f(0.9, 0.9, 1.0)
    gluSphere(quad, 0.08 * scale, 16, 16)

    # Clean up quadric
    gluDeleteQuadric(quad)

    glPopMatrix()

# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    pygame.init()
    display = (1000, 800)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Quadcopter – PyOpenGL + Pygame")

    gluPerspective(60, (display[0]/display[1]), 0.1, 200.0)
    glTranslatef(0.0, 0.0, -8.0)          # initial camera distance
    glRotatef(30, 1, 0, 0)               # tilt camera a bit

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, (5, 5, 10, 0))

    clock = pygame.time.Clock()
    drone = Quadcopter()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

        # Simple keyboard control (replace with your PID later)
        keys = pygame.key.get_pressed()
        thrust = 0.0
        torques = np.zeros(3)

        if keys[K_SPACE] or keys[K_UP]:    thrust = 18.0
        if keys[K_DOWN]:                   thrust = 10.0
        if keys[K_LEFT]:                   torques[1] = -1.2   # pitch forward
        if keys[K_RIGHT]:                  torques[1] = +1.2
        if keys[K_a]:                      torques[2] = -1.0   # yaw ccw
        if keys[K_d]:                      torques[2] = +1.0

        drone.set_controls(thrust, torques)
        drone.update(dt)

        # ─── Render ───────────────────────────────────────
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # World grid (optional – helps judge position)
        glColor3f(0.4, 0.4, 0.4)
        glBegin(GL_LINES)
        for i in range(-20, 21, 2):
            glVertex3f(i, 0, -20); glVertex3f(i, 0, 20)
            glVertex3f(-20, 0, i); glVertex3f(20, 0, i)
        glEnd()

        draw_axes(2.0)
        draw_quadcopter(drone, scale=1.0)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()