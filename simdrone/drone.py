import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
# Camera state
cam_x, cam_y, cam_z = 0.0, 1.0, 10.0
cam_yaw, cam_pitch = 0.0, 0.0
MOVE_SPEED = 5.0 # meters per second
ROT_SPEED = 120.0 # degrees per second
MOUSE_SENSITIVITY = 0.15 # unused now
quadric = None
def draw_axes(length=2.0):
    glLineWidth(2.5)
    glBegin(GL_LINES)
    glColor3f(1.0, 0.3, 0.3) # X red
    glVertex3f(0, 0, 0); glVertex3f(length, 0, 0)
    glColor3f(0.3, 1.0, 0.3) # Y green
    glVertex3f(0, 0, 0); glVertex3f(0, length, 0)
    glColor3f(0.3, 0.3, 1.0) # Z blue
    glVertex3f(0, 0, 0); glVertex3f(0, 0, length)
    glEnd()
def draw_grid(size=50, step=1):
    glLineWidth(1.0)
    glColor3f(0.4, 0.4, 0.4)
    glBegin(GL_LINES)
    for i in range(-size, size + 1, step):
        glVertex3f(i, 0, -size); glVertex3f(i, 0, size)
        glVertex3f(-size, 0, i); glVertex3f(size, 0, i)
    glEnd()
def draw_propeller(x, z, spin_angle, y=0.05):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(spin_angle, 0, 1, 0)
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.6, 0.6, 0.6)
    gluDisk(quadric, 0, 0.5, 16, 1)
    glPopMatrix()
def draw_arm(theta, length=np.sqrt(2), radius=0.05):
    glPushMatrix()
    glRotatef(theta, 0, 1, 0)
    glTranslatef(0, 0, length / 2)
    glRotatef(90, 1, 0, 0)
    glColor3f(0.8, 0.8, 0.8)
    gluCylinder(quadric, radius, radius, length, 8, 1)
    glPopMatrix()
def draw_drone(spin_angle):
    # Central body
    glPushMatrix()
    glColor3f(0.9, 0.2, 0.2)
    gluSphere(quadric, 0.3, 16, 16)
    glPopMatrix()
    # Arms
    draw_arm(45); draw_arm(135); draw_arm(-45); draw_arm(-135)
    # Propellers
    prop_dist = 1.0
    draw_propeller(prop_dist, prop_dist, spin_angle)
    draw_propeller(prop_dist, -prop_dist, spin_angle)
    draw_propeller(-prop_dist, prop_dist, spin_angle)
    draw_propeller(-prop_dist, -prop_dist, spin_angle)
def apply_camera():
    glRotatef(-cam_pitch, 1, 0, 0) # pitch
    glRotatef(-cam_yaw, 0, 1, 0) # yaw
def main():
    global cam_x, cam_y, cam_z, cam_yaw, cam_pitch, quadric
    pygame.init()
    display = (900, 700)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption("Keyboard Rotation (Q/E yaw, R/F pitch) + Rotating Drone")
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    glClearColor(0.05, 0.05, 0.12, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    quadric = gluNewQuadric()
    def set_perspective():
        glViewport(0, 0, display[0], display[1])
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70, display[0]/display[1], 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
    set_perspective()
    clock = pygame.time.Clock()
    rotation_angle = 0.0
    prop_spin = 0.0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        rotation_angle += 35 * dt
        prop_spin += 200 * dt
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
            if event.type == VIDEORESIZE:
                display = event.size
                pygame.display.set_mode(display, DOUBLEBUF | OPENGL | RESIZABLE)
                set_perspective()
        keys = pygame.key.get_pressed()
        # Keyboard rotation (swapped Q/E for correct left/right)
        cam_yaw += keys[K_q] * ROT_SPEED * dt # Q: turn left
        cam_yaw -= keys[K_e] * ROT_SPEED * dt # E: turn right
        cam_pitch += keys[K_r] * ROT_SPEED * dt
        cam_pitch -= keys[K_f] * ROT_SPEED * dt
        cam_pitch = np.clip(cam_pitch, -89.9, 89.9)
        cam_yaw %= 360
        # Movement (full 3D direction including pitch)
        forward = np.array([
            -np.sin(np.deg2rad(cam_yaw)) * np.cos(np.deg2rad(cam_pitch)),
            np.sin(np.deg2rad(cam_pitch)),
            -np.cos(np.deg2rad(cam_yaw)) * np.cos(np.deg2rad(cam_pitch)),
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
            cam_x += move[0] * MOVE_SPEED * dt
            cam_y += move[1] * MOVE_SPEED * dt
            cam_z += move[2] * MOVE_SPEED * dt
        # Render
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        # World-fixed light
        light_pos = (10.0, 10.0, 10.0, 1.0)
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        # Camera transform
        apply_camera()
        glTranslatef(-cam_x, -cam_y, -cam_z)
        # Grid and axes (unlit)
        glDisable(GL_LIGHTING)
        draw_grid(50, 1)
        draw_axes(2.0)
        glEnable(GL_LIGHTING)
        # Drone
        glPushMatrix()
        glRotatef(rotation_angle, 0, 1, 0)
        glRotatef(rotation_angle * 0.6, 1, 0, 0)
        draw_drone(prop_spin)
        glPopMatrix()
        pygame.display.flip()
    pygame.quit()
if __name__ == '__main__':
    main()