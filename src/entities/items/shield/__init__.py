"""Defines the `Shield` class for a falling shield power-up."""

import secrets

import pygame

from src import settings

GENERATE_SHIELD_CHANCE: int = 10
SHIELD_TIME: int = 10


class Shield(pygame.sprite.Sprite):
    """A shield power-up that spawns randomly and moves downward."""

    def __init__(self) -> None:
        """Initialize the shield with a random position."""
        super().__init__()
        self.screen: pygame.Surface = pygame.display.get_surface()
        self.image: pygame.Surface = pygame.transform.scale(
            pygame.image.load("data/assets/shield/shield.png"),
            (25, 25),
        )
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.centerx = secrets.randbelow(settings.SCREEN_WIDTH - self.rect.width)
        self.rect.top = 0

    def update(self) -> None:
        """Move the shield downward."""
        self.rect.y += int(settings.HEART_SPEED_FACTOR * settings.DELTA_TIME)

    def draw(self) -> None:
        """Draw the shield on the screen."""
        self.screen.blit(self.image, self.rect)
