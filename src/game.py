import sys

import pygame

from src import settings
from src.scenes.game_scene import GameScene


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.display: pygame.Surface = pygame.display.set_mode(
            (
                settings.SCREEN_WIDTH,
                settings.SCREEN_HEIGHT,
            ),
        )
        pygame.display.set_caption("Alien Invasion")
        self.clock = pygame.time.Clock()

        self.scene = GameScene()

    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            dt: float = self.clock.tick(120) / 1000
            self.scene.run(dt)
            pygame.display.update()
