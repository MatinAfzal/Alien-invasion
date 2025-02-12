import pygame
import math
from abc import ABC, abstractmethod
from random import randint
from pygame.sprite import Sprite


class Alien(ABC, Sprite):
    """An abstract class to create aliens."""

    def __init__(self, ai_settings, screen, health):
        """Initialize the alien and set its starting position."""
        super(Alien, self).__init__()

        self.screen = screen
        self.ai_settings = ai_settings
        self.health = health
        self.angle = 0

        # Load the alien image and set its rect attribute.
        self.original_image = self.get_image()
        self.image = self.original_image
        self.rect = self.image.get_rect()

        # Start each new alien near the top left of the screen.
        self.x = float(randint(0, ai_settings.screen_width - self.rect.width))
        self.y = float(randint(0, ai_settings.screen_height - self.rect.height))
        self.rect.x = self.x
        self.rect.y = self.y

    def check_edges(self):
        """Return True if alien is at edge of screen."""
        screen_rect = self.screen.get_rect()
        if self.rect.right >= screen_rect.right:
            return True
        if self.rect.left <= 0:
            return True
        return None

    def update(self, ship):
        """Move the alien."""

        # Calculate the distance between the alien and the ship.
        delta_x = ship.rect.centerx - self.rect.centerx
        delta_y = ship.rect.centery - self.rect.centery

        # Calculate the target angle of movement.
        target_angle = math.atan2(delta_y, delta_x)
        target_angle_deg = -math.degrees(target_angle)

        # Smoothly adjust the angle.
        angle_diff = (target_angle_deg - self.angle) % 360
        if angle_diff > 180:
            angle_diff -= 360
        self.angle += angle_diff * 0.1  # Adjust this factor for smoother rotation.

        # Update the alien's position.
        self.x += math.cos(target_angle) * self.ai_settings.alien_speed_factor * self.ai_settings.delta_time
        self.y += math.sin(target_angle) * self.ai_settings.alien_speed_factor * self.ai_settings.delta_time
        self.rect.x = self.x
        self.rect.y = self.y

        # Rotate the alien to face the ship.
        self.image = pygame.transform.rotate(self.original_image, self.angle + 90)

        # Keep the alien within the screen bounds.
        screen_rect = self.screen.get_rect()
        self.rect.clamp_ip(screen_rect)

    def blit(self):
        """Draw the alien at its current location."""
        self.screen.blit(self.image, self.rect)

    @abstractmethod
    def get_image(self):
        pass  # This is an abstract method, no implementation here.


class CargoAlien(Alien):
    """A class to represent a single cargo alien."""

    def __init__(self, ai_settings, screen):
        super().__init__(ai_settings, screen, ai_settings.alien_l1_health)

        self.rect.x = randint(10, ai_settings.screen_width - 10)
        self.rect.y = self.ai_settings.screen_height + 100

    def update(self, ship):
        super().update(ship)
        self.rect.y -= self.ai_settings.cargo_speed_facto

    def get_image(self):
        image = pygame.image.load(r"assets/sprites/alien_cargo.png")
        image_size = image.get_size()
        return pygame.transform.scale(image, (image_size[0] * 0.2, image_size[1] * 0.2))


class AlienL1(Alien):
    """A class to represent a single alien."""

    def __init__(self, ai_settings, screen):
        super().__init__(ai_settings, screen, ai_settings.alien_l1_health)

    def get_image(self):
        image = pygame.image.load(r"assets/sprites/alien_l1.png")
        return pygame.transform.rotate(image, 180)


class AlienL2(Alien):
    """A class to represent a single alien."""

    def __init__(self, ai_settings, screen):
        super().__init__(ai_settings, screen, ai_settings.alien_l2_health)

    def get_image(self):
        image = pygame.image.load(r"assets/sprites/alien_l2.png")
        image = pygame.transform.scale(image, (60, 57))
        return pygame.transform.rotate(image, 180)
