import pygame
from dataclasses import dataclass
from typing import Tuple, Optional, List


@dataclass
class DroneParameters:
    pass


class SimDrone(pygame.sprite.Sprite):
    
    def __init__(self):
        super().__init__()
        # Create a surface for the sprite (a red square in this case)
        self.image = pygame.Surface([50, 50])
        self.image.fill(RED)
        
        # Get the rectangle object that has the dimensions of the image
        self.rect = self.image.get_rect()
        
        # Set the position of the rect
        self.rect.centerx = x
        self.rect.centery = y

    def update(self):
        # Update logic goes here (e.g., movement based on keyboard input)
        # For this example, let's just make it move right
        self.rect.x += 1
        if self.rect.x > SCREEN_WIDTH:
            self.rect.x = -self.rect.width

    def draw(self):
        pass

    def reset(self):
        pass