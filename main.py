import pygame
from dataclasses import dataclass
from typing import Tuple, Optional, List


@dataclass
class DroneParameters:
    pass


class SimDrone:
    
    def __init__(self):
        pass
    
    def update(self):
        pass

    def draw(self):
        pass

    def reset(self):
        pass


def main():
    # Initialize Pygame
    pygame.init()

    # Set up the game window
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Hello Pygame")

    # Game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    # Quit Pygame
    pygame.quit()


if __name__ == "__main__":
    main()
