import pygame
import math
from psd_tools import PSDImage


class Ship:
    def __init__(self, ai_settings, screen):
        """Initialize the ship and set its starting position."""
        self.screen = screen
        self.ai_settings = ai_settings

        # Load the ship image and get its rect.
        psd = PSDImage.open('data/assets/sprites/Alien-Bomber.psd')
        psd.composite().save("data/assets/sprites/ship.png")
        self.image = pygame.image.load("data/assets/sprites/ship.png")
        self.rect = self.image.get_rect()
        self.screen_rect = screen.get_rect()

        # start each new ship at the bottom center of the screen.
        self.rect.centerx = self.screen_rect.centerx
        self.rect.centery = self.screen_rect.centery
        self.rect.bottom = self.screen_rect.bottom - self.rect.height + 64
        self.angle = 0 # In radians

        # Store a decimal value for the ship's center.
        self.center = [float(self.rect.centerx), float(self.rect.centery)]

        # Movement flag
        self.moving_right = False
        self.moving_left = False
        self.moving_up = False
        self.moving_down = False

    
    def update(self):
        """Update the ship's position based on the movement flag."""
        # update te ship's center value, not the rect.
        if self.moving_right and self.rect.right < self.screen_rect.right:
            self.center[0] += self.ai_settings.ship_speed_factor_x
        if self.moving_left and self.rect.left > 0:
            self.center[0] -= self.ai_settings.ship_speed_factor_x
        if self.moving_up and self.rect.top > 0:
            self.center[1] -= self.ai_settings.ship_speed_factor_y
        if self.moving_down and self.rect.bottom < self.screen_rect.bottom:
            self.center[1] += self.ai_settings.ship_speed_factor_y

        # Update rect object from self.center.
        self.rect.centerx = self.center[0]
        self.rect.centery = self.center[1]

        # Update the ship's angle
        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.center[0] # The mouse position relative to the ship location
        dy = mouse_y - self.center[1]
        self.angle = math.atan2(-dx, -dy) # Calculate angle

    def bltime(self):
        """Draw the ship at its current location."""
        rotated_image = pygame.transform.rotate(self.image, math.degrees(self.angle))
        rotated_rec = rotated_image.get_rect(center=self.center)
        self.screen.blit(rotated_image, rotated_rec)

    def center_ship(self):
        """Center the ship on the screen."""
        self.center[0] = self.screen_rect.centerx
        self.center[1] = self.screen_rect.bottom - self.rect.height
