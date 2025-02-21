import sys
from dataclasses import dataclass

import inject
import pygame

from src import settings


@dataclass
class SpritesManager:
    sprites = pygame.sprite.Group()


class Game:
    sprite_manager: SpritesManager = inject.attr(SpritesManager)

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

    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            dt: float = self.clock.tick(60) / 1000
            pygame.display.update()

    def updateSprites(self) -> None:
        self.sprite_manager.sprites.update()
        self.sprite_manager.sprites.draw(pygame.display.get_surface())
        for sprite in self.sprite_manager.sprites:
            sprite.draw()
