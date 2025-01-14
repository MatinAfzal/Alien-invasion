import pygame
import math
from pygame.sprite import Sprite


class Bullet(Sprite):
    """A Class to manage bullets fired from the ship."""

    def __init__(self, ai_settings, screen, ship):
        """Create a bullet object at the ship's current position."""
        super(Bullet, self).__init__()
        self.screen = screen

        # Create a bullet rect (0, 0)
        self.image = pygame.image.load(r'data/assets/sprites/golden_bullet.png')
        self.image_size = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (self.image_size[0] * 0.03, self.image_size[1] * 0.03))
        self.rect = self.image.get_rect()

        self.rect.centerx = ship.rect.centerx
        self.rect.top = ship.rect.top

        # Store the bullet's position as a decimal value.
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.angle = ship.angle

        self.color = ai_settings.bullet_color
        self.speed_factor = ai_settings.bullet_speed_factor
    
    def update(self):
        """Move the bullet up the screen."""
        # Update the decimal position of the bullet.
        self.x -= math.sin(self.angle) * self.speed_factor
        self.y -= math.cos(self.angle) * self.speed_factor

        # Update the rect position
        self.rect.x = self.x
        self.rect.y = self.y

    def draw_bullet(self):
        """Draw the bullet to the screen."""
        rotated_image = pygame.transform.rotate(self.image, math.degrees(self.angle))
        rotated_rec = rotated_image.get_rect(center=(self.rect.centerx, self.rect.centery))
        self.screen.blit(rotated_image, rotated_rec)

class AlienBullet(Sprite):
    """A Class to manage bullets fired from the aliens."""

    def __init__(self, ai_settings, screen, ship):
        """Create a bullet object at the alien's current position."""
        super(AlienBullet, self).__init__()
        self.screen = screen

        # Create a bullet rect (0, 0)
        self.image = pygame.image.load(r'data/assets/sprites/golden_bullet.png')
        self.image = pygame.transform.rotate(self.image, 180)
        self.image_size = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (self.image_size[0] * 0.03, self.image_size[1] * 0.03))
        self.rect = self.image.get_rect()

        self.rect.centerx = ship.rect.centerx
        self.rect.top = ship.rect.bottom

        # Store the bullet's position as a decimal value.
        self.y = float(self.rect.y)

        self.color = ai_settings.bullet_color
        self.speed_factor = ai_settings.alien_bullet_speed_factor
    
    def update(self):
        """Move the bullet down the screen."""
        # Update the decimal position of the bullet.
        self.y += self.speed_factor

        # Update the rect position
        self.rect.y = self.y

    def draw_bullet(self):
        """Draw the bullet to the screen."""
        self.screen.blit(self.image, self.rect)