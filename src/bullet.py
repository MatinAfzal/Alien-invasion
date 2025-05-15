import math
from abc import ABC, abstractmethod

import random

import pygame
from pygame.sprite import Sprite

from src.resources.texture_atlas import TextureAtlas
from src.entities.items.power import PowerType

from . import settings


class Bullet(ABC, Sprite):
    """An abstract class to create bullets."""

    def __init__(self, target, source, color, speed_factor, power=PowerType.NORMAL, num=0.5):
        super(Bullet, self).__init__()
        self.screen: pygame.Surface = pygame.display.get_surface()

        # Load and scale bullet image
        if power == PowerType.NORMAL:
            self.image: pygame.Surface = TextureAtlas.get_sprite_texture("bullet/golden_bullet.png")
        else:
            self.image: pygame.Surface = TextureAtlas.get_sprite_texture("bullet/power_bullet.png")

        self.image_size: tuple[int, int] = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (self.image_size[0] * 0.03, self.image_size[1] * 0.03))
        self.rect = self.image.get_rect()

        # Set angle and initial position
        self.angle, self.rect.centerx, self.rect.centery = self.set_angle(source, target, power, num)

        # Store the bullet's position as a decimal value
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)

        self.color = color
        self.speed_factor = speed_factor

    def update(self):
        """Move the bullet with ship's or alien's angle"""

        # Update the decimal position of the bullet.

        self.x -= math.sin(self.angle) * self.speed_factor * settings.DELTA_TIME
        self.y -= math.cos(self.angle) * self.speed_factor * settings.DELTA_TIME

        # Update the rect position
        self.rect.x = self.x
        self.rect.y = self.y

    def draw(self):
        """Draw the bullet to the screen."""
        rotated_image = pygame.transform.rotate(self.image, math.degrees(self.angle))
        rotated_rec = rotated_image.get_rect(center=(self.rect.centerx, self.rect.centery))
        self.screen.blit(rotated_image, rotated_rec)

    @abstractmethod
    def set_angle(self, source, target, *args):
        """Set the angle and initial position of the bullet."""
        pass


class ShipBullet(Bullet):
    """A class to manage bullets fired from the ship."""

    def __init__(self, ship, power=PowerType.NORMAL, num=0.5):
        super().__init__(None, ship, settings.BULLET_COLOR, settings.BULLET_SPEED_FACTOR, power, num)

    def set_angle(self, source, target, power=PowerType.NORMAL, num=0.5):
        if power == PowerType.SPREAD:
            angle = source.angle + 1.5 - num
        else:
            angle = source.angle

        x = source.rect.centerx + math.sin(angle) * 30
        y = source.rect.centery - math.cos(angle) * 30
        return angle, x, y


class AlienBullet(Bullet):
    """A class to manage bullets fired from the aliens."""

    def __init__(self, alien, ship):
        super().__init__(ship, alien, settings.BULLET_COLOR, settings.BULLET_SPEED_FACTOR)

    def set_angle(self, source, target, *args):
        dx = target.rect.centerx - source.rect.centerx
        dy = target.rect.centery - source.rect.centery

        num = random.choice([29.5, 29.8, 30, 30.2, 30.5])
        angle = math.atan2(-dy, dx) + num

        x = source.rect.centerx
        y = source.rect.centery

        return angle, x, y
