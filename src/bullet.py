import pygame
from pygame.sprite import Sprite
from src.ship import Ship


class Bullet(Sprite):
    """A class to manage bullets fired from the ship."""

    def __init__(self, ai_settings, screen, shooter, direction=1):
        """Create a bullet object at the shooter's position."""
        super().__init__()
        self.screen = screen

        # Load the bullet image and get its rect
        if direction == 1:  # Player bullet
            self.image = pygame.image.load(r'data/assets/sprites/golden_bullet.png')
        else:  # Alien bullet
            self.image = pygame.image.load(r'data/assets/sprites/alien_bullet.png')
            
        # Scale the bullet image
        self.image_size = self.image.get_size()
        self.image = pygame.transform.scale(self.image, (self.image_size[0] * 0.03, self.image_size[1] * 0.03))
        self.rect = self.image.get_rect()
        
        # If direction is -1, rotate bullet 180 degrees for alien bullets
        if direction == -1:
            self.image = pygame.transform.rotate(self.image, 180)

        # Set the bullet's starting position
        if isinstance(shooter, Ship):
            self.rect.centerx = shooter.rect.centerx
            self.rect.top = shooter.rect.top
            self.speed_factor = ai_settings.bullet_speed_factor
        else:  # Alien bullet
            self.rect.centerx = shooter.rect.centerx
            self.rect.bottom = shooter.rect.bottom
            self.speed_factor = ai_settings.alien_bullet_speed_factor

        # Store the bullet's position as a decimal value.
        self.y = float(self.rect.y)
        
        # Store direction (1 for up, -1 for down)
        self.direction = direction

    def update(self):
        """Move the bullet up or down the screen."""
        # Update the decimal position of the bullet.
        self.y -= self.speed_factor * self.direction
        # Update the rect position.
        self.rect.y = self.y

    def draw_bullet(self):
        """Draw the bullet to the screen."""
        self.screen.blit(self.image, self.rect)
