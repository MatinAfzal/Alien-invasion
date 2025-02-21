import math

import inject
import pygame

from src import settings
from src.game import SpritesManager


class Bullet(pygame.sprite.Sprite):
    sprite_manager: SpritesManager = inject.attr(SpritesManager)

    def __init__(self, x: float, y: float, angle: float, target: type[pygame.sprite.Sprite]) -> None:
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill((255, 255, 255))
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))

        self.angle: float = math.radians(angle)
        self.speed: float = settings.BULLET_SPEED_FACTOR
        self.vel_x: float = math.cos(self.angle) * settings.BULLET_SPEED_FACTOR * settings.DELTA_TIME
        self.vel_y: float = math.sin(self.angle) * settings.BULLET_SPEED_FACTOR * settings.DELTA_TIME
        self.target = target

    def update(self) -> None:
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)

        if (
            self.rect.x < 0
            or self.rect.x > settings.SCREEN_WIDTH
            or self.rect.y < 0
            or self.rect.y > settings.SCREEN_HEIGHT
        ):
            self.kill()

        for sprite in self.sprite_manager.sprites:
            if self.rect.colliderect(sprite.rect):
                if isinstance(sprite, self.target):
                    sprite.kill()
        # self.kill()
