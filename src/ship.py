import math

import pygame

import time

from src.entities.items.power import POWER_TIME, PowerType
from src.resources.texture_atlas import TextureAtlas
from . import input, settings


class Ship(pygame.sprite.Sprite):
    def __init__(self, input: input.Input):
        """Initialize the ship and set its starting position."""
        self.screen: pygame.Surface = pygame.display.get_surface()
        self.input = input

        # Load the ship image and get its rect.
        self.image: pygame.Surface = TextureAtlas.get_sprite_texture("ship/ship.png")
        self.rect: pygame.Rect = self.image.get_rect()

        # start each new ship at the bottom center of the screen.
        self.rect.centerx = self.screen.get_rect().centerx
        self.rect.centery = self.screen.get_rect().centery
        self.rect.bottom = self.screen.get_rect().bottom - self.rect.height + 64
        self.angle = 0  # In radians

        # Store a decimal value for the ship's center.
        self.center: list[float] = [float(self.rect.centerx), float(self.rect.centery)]

        # Movement flag
        self.moving_right = False
        self.moving_left = False
        self.moving_up = False
        self.moving_down = False

        self.power = PowerType.NORMAL

    def check(self) -> None:
        """check power-up timer."""
        if self.power != PowerType.NORMAL and time.time() - self.power_time >= POWER_TIME:
            self.power = PowerType.NORMAL
    
    def activate_powerup(self, power) -> None:
        """Activate temporary power-up."""
        self.power = power
        self.power_time = time.time()

    def update(self) -> None:
        """Update the ship's position based on the movement flag."""
        # update te ship's center value, not the rect.
        if self.moving_right and self.rect.right < self.screen.get_rect().right:
            self.center[0] += settings.SHIP_SPEED_FACTOR_X * settings.DELTA_TIME
        if self.moving_left and self.rect.left > 0:
            self.center[0] -= settings.SHIP_SPEED_FACTOR_X * settings.DELTA_TIME
        if self.moving_up and self.rect.top > 0:
            self.center[1] -= settings.SHIP_SPEED_FACTOR_Y * settings.DELTA_TIME
        if self.moving_down and self.rect.bottom < self.screen.get_rect().bottom:
            self.center[1] += settings.SHIP_SPEED_FACTOR_Y * settings.DELTA_TIME

        # Update rect object from self.center.
        self.rect.centerx = int(self.center[0])
        self.rect.centery = int(self.center[1])

        # Update the ship's angle
        mouse_pos: tuple[int, int] = self.input.get_mouse_cursor_position()
        dx: float = mouse_pos[0] - self.center[0]  # The mouse position relative to the ship location
        dy: float = mouse_pos[1] - self.center[1]
        self.angle: float = math.atan2(-dx, -dy)  # Calculate angle

    def bltime(self) -> None:
        """Draw the ship at its current location."""
        rotated_image: pygame.Surface = pygame.transform.rotate(self.image, math.degrees(self.angle))
        rotated_rect: pygame.Rect = rotated_image.get_rect(center=self.center)
        self.screen.blit(rotated_image, rotated_rect)

    def center_ship(self) -> None:
        """Center the ship on the screen."""
        self.center[0] = self.screen.get_rect().centerx
        self.center[1] = self.screen.get_rect().bottom - self.rect.height
