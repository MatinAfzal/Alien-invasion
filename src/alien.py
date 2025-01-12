from random import randint

import pygame
from pygame.sprite import Sprite


class Alien(Sprite):
    """A class to represent a single alien in the fleet."""

    def __init__(self, ai_settings, screen, alien_type=0):
        """Initialize the alien and set its starting position."""
        super().__init__()
        self.type = alien_type  # 0 for alien, 1 for cargo
        self.screen = screen
        self.ai_settings = ai_settings
        self.health = ai_settings.alien_l1_health

        # Load the alien image and set its rect attribute.
        if self.type == 0:
            self.image = pygame.image.load(r'data/assets/sprites/alien_l1.png')
            self.image = pygame.transform.rotate(self.image, 180)
        else:
            self.image = pygame.image.load(r'data/assets/sprites/alien_cargo.png')
            self.image_size = self.image.get_size()
            self.image = pygame.transform.scale(self.image, (self.image_size[0] * 0.2, self.image_size[1] * 0.2))

        self.rect = self.image.get_rect()

        # Start each new alien near the top left of the screen.
        if self.type == 0:
            self.rect.x = self.rect.width
            self.rect.y = self.rect.height
        else:
            self.rect.x = randint(10, ai_settings.screen_width - 10)
            self.rect.y = self.ai_settings.screen_height + 100

        # Store the alien's exact position.
        self.x = float(self.rect.x)

    def check_edges(self):
        """Return True if alien is at edge of screen."""
        screen_rect = self.screen.get_rect()
        if self.rect.right >= screen_rect.right:
            return True
        if self.rect.left <= 0:
            return True
        return None

    def update(self, *args, **kwargs):
        """Move the aliens right or left."""
        if self.type == 0:
            self.x += (self.ai_settings.alien_speed_factor * self.ai_settings.fleet_direction)
            self.rect.x = self.x
        if self.type == 1:
            self.rect.y -= self.ai_settings.cargo_speed_factor

    def bltime(self):
        """Draw the alien at its current location."""
        self.screen.blit(self.image, self.rect)


class AlienL2(Sprite):
    """A class to represent a single alien in the fleet."""

    def __init__(self, ai_settings, screen, alien_type=0):
        """Initialize the alien and set its starting position."""
        super().__init__()
        self.type = alien_type  # 0 for alien, 1 for cargo
        self.screen = screen
        self.ai_settings = ai_settings
        self.health = ai_settings.alien_l2_health

        # Load the alien image and set its rect attribute.
        if self.type == 0:
            self.image = pygame.image.load(r'data/assets/sprites/alien_l2.png')
            self.image = pygame.transform.scale(self.image, (60, 57))
        else:
            self.image = pygame.image.load(r'data/assets/sprites/alien_cargo.png')
            self.image_size = self.image.get_size()
            self.image = pygame.transform.scale(self.image, (self.image_size[0] * 0.2, self.image_size[1] * 0.2))

        self.rect = self.image.get_rect()

        # Start each new alien near the top left of the screen.
        if self.type == 0:
            self.rect.x = self.rect.width
            self.rect.y = self.rect.height
        else:
            self.rect.x = randint(10, ai_settings.screen_width - 10)
            self.rect.y = self.ai_settings.screen_height + 100

        # Store the alien's exact position.
        self.x = float(self.rect.x)

    def check_edges(self):
        """Return True if alien is at edge of screen."""
        screen_rect = self.screen.get_rect()
        if self.rect.right >= screen_rect.right:
            return True
        if self.rect.left <= 0:
            return True
        return None

    def update(self, *args, **kwargs):
        """Move the aliens right or left."""
        if self.type == 0:
            self.x += (self.ai_settings.alien_speed_factor * self.ai_settings.fleet_direction)
            self.rect.x = self.x
        if self.type == 1:
            self.rect.y -= self.ai_settings.cargo_speed_factor

    def bltime(self):
        """Draw the alien at its current location."""
        self.screen.blit(self.image, self.rect)
