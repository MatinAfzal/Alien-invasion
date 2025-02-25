import math

import inject
import pygame

from src import settings
from src.sprite_manager import SpritesManager


class Bullet(pygame.sprite.Sprite):
    sprite_manager: SpritesManager = inject.attr(SpritesManager)
    SPEED = 750

    def __init__(self, x: float, y: float, angle: float) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.image.load(settings.ASSETS_DIR / "sprites" / "bullet.png")
        self.image = pygame.transform.scale(self.image, (40, 40)).convert_alpha()
        self.original_image: pygame.Surface = self.image
        self.rect: pygame.Rect = self.image.get_rect(center=(x, y))
        self.angle: float = math.radians(angle)
        self.speed: float = self.SPEED
        self.vel_x: float = math.cos(self.angle) * self.speed
        self.vel_y: float = -math.sin(self.angle) * self.speed

    def update(self, dt: float) -> None:
        self.rect.x += int(self.vel_x * dt)
        self.rect.y += int(self.vel_y * dt)
        self.image = pygame.transform.rotate(self.original_image, math.degrees(self.angle) - 90)
        if (
            self.rect.x < 0
            or self.rect.x > settings.SCREEN_WIDTH
            or self.rect.y < 0
            or self.rect.y > settings.SCREEN_HEIGHT
        ):
            self.kill()
