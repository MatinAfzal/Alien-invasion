import secrets
from pathlib import Path

import pygame

from src import settings


class FallingItem(pygame.sprite.Sprite):
    SPEED_FACTOR = 4

    def __init__(self, image_path: Path) -> None:
        super().__init__()
        self.display_surf = pygame.display.get_surface()

        self.image: pygame.Surface = pygame.transform.scale(pygame.image.load(image_path), (25, 25))
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.centerx = secrets.randbelow(self.display_surf.get_rect().right + 1)
        self.rect.top = 0

    def update(self, dt: float) -> None:
        self.rect.y += int(self.SPEED_FACTOR * dt)

        if self.rect.y > settings.SCREEN_HEIGHT:
            self.kill()
