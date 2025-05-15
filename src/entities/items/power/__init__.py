"""Defines the `PowerUp` class, which represents a falling power-up item."""

import secrets
from enum import Enum, auto

import pygame

from src import settings
from src.resources.texture_atlas import TextureAtlas

GENERATE_POWER_CHANCE: int = 8
POWER_TIME: int = 15

"""
Power Types:
------------
- NORMAL  (0): No active power-up. Default shooting behavior.
- SPREAD  (1): Fires 5 bullets in a spread pattern instead of one.
- DOUBLE  (2): Doubles bullet damage and the score earned from enemies.
- HEALING (3): When a bullet hits an enemy, it restores one health point to the player.
"""

class PowerType(Enum):
    NORMAL = 0
    SPREAD = 1
    DOUBLE = 2
    HEALING = 3

class PowerUp(pygame.sprite.Sprite):
    """A power-up that spawns randomly and moves downward."""

    def __init__(self) -> None:
        """Initialize the power-up with a random position and random power type."""
        super().__init__()
        self.screen: pygame.Surface = pygame.display.get_surface()

        # Assign a random power type (1 to 3) from the PowerType enum
        self.power = PowerType(secrets.randbelow(3) + 1)

        self.image: pygame.Surface = pygame.transform.scale(
            TextureAtlas.get_sprite_texture(f"power/power{self.power.value}.png"),
            (40, 40),
        )
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.centerx = secrets.randbelow(settings.SCREEN_WIDTH - self.rect.width)
        self.rect.top = 0

    def update(self) -> None:
        """Move the power-up downward."""
        self.rect.y += int(settings.HEART_SPEED_FACTOR * settings.DELTA_TIME)

    def draw(self) -> None:
        """Draw the power-up on the screen."""
        self.screen.blit(self.image, self.rect)
