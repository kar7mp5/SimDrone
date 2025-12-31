from simdrone import *
import pygame


def main():
    # Initialize Pygame
    pygame.init()

    # Set up the game window
    screen = pygame.display.set_mode((400, 300))
    clock = pygame.time.Clock()

    all_sprites = pygame.sprite.Group()
    # player = class
    # all_sprites.add(player)
    pygame.display.set_caption("Hello Pygame")

    # Game loop
    running = True
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        all_sprites.update()
        screen.fill(WHITE)
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    # Quit Pygame
    pygame.quit()


if __name__ == "__main__":
    main()
