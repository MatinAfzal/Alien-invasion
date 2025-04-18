"""Module for managing and animating heart sprites that fall down the screen in the game."""

import secrets
from pathlib import Path

import pygame

from src import settings

FULL_HEART_IMAGE_PATH: Path = settings.ASSETS_DIR / "hearts" / "full_heart.png"
EMPTY_HEART_IMAGE_PATH: Path = settings.ASSETS_DIR / "hearts" / "empty_heart.png"

GENERATE_HEART_CHANCE: int = 10


class Heart(pygame.sprite.Sprite):
    """A class to represent a heart that falls down the screen in the game."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the heart's image, rect, and position."""
        super().__init__()
        self.screen: pygame.Surface = screen
        self.speed_factor: float = settings.HEART_SPEED_FACTOR

        self.image: pygame.Surface = pygame.transform.scale(pygame.image.load(FULL_HEART_IMAGE_PATH), (25, 25))
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.centerx = secrets.randbelow(self.screen.get_rect().right + 1)
        self.rect.top = 0

    def update(self) -> None:
        """Update the heart's position to move it down the screen."""
        self.rect.y += int(self.speed_factor * settings.DELTA_TIME)

    def draw(self) -> None:
        """Draw the heart onto the screen."""
        self.screen.blit(self.image, self.rect)
