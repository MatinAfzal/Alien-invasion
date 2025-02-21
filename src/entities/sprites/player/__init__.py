"""Defines the Player class, which represents a controllable spaceship in the game."""

import math

import inject
import pygame

from src import settings
from src.alien import Alien
from src.entities.sprites.bullet import Bullet
from src.game import SpritesManager
from src.utils.timer import Timer

PLAYER_SPEED: float = 3


class Player(pygame.sprite.Sprite):
    """A class representing the player-controlled spaceship."""

    sprite_manager: SpritesManager = inject.attr(SpritesManager)

    def __init__(self) -> None:
        """Initialize the player, load its image, and set its initial position."""
        super().__init__()
        self.screen: pygame.Surface = pygame.display.get_surface()

        # Load the ship image and get its rect.
        self.original_image: pygame.Surface = pygame.image.load(
            settings.ASSETS_DIR / "sprites" / "ship.png",
        ).convert_alpha()
        self.image: pygame.Surface = pygame.image.load(settings.ASSETS_DIR / "sprites" / "ship.png").convert_alpha()
        self.rect: pygame.Rect = self.image.get_rect()

        # Start each new ship at the bottom center of the screen.
        self.rect.centerx = self.screen.get_rect().centerx
        self.rect.centery = self.screen.get_rect().centery
        self.rect.bottom = self.screen.get_rect().bottom - self.rect.height + 64
        self.angle = 0  # Angle in radians

        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)

        self.fire_timer = Timer(700)

    def input(self) -> None:
        """Handle player input for movement and rotation."""
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction.y = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
        else:
            self.direction.x = 0

        if pygame.mouse.get_pressed()[0] and not self.fire_timer.active:
            self.fire_timer.activate()
            self.fire()

        mouse_pos: tuple[int, int] = pygame.mouse.get_pos()

        x_dist: int = mouse_pos[0] - self.rect.centerx
        y_dist: int = -(mouse_pos[1] - self.rect.centery)
        self.angle: float = math.degrees(math.atan2(y_dist, x_dist))

    def move(self) -> None:
        """Move the player based on input direction and apply rotation."""
        if self.direction.magnitude():
            self.direction: pygame.Vector2 = self.direction.normalize()

        self.pos.x += self.direction.x * PLAYER_SPEED
        self.pos.y += self.direction.y * PLAYER_SPEED

        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.image = pygame.transform.rotate(self.original_image, self.angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self) -> None:
        """Update the player's position and rotation based on input."""
        self.fire_timer.update()
        self.input()
        self.move()

    def draw(self) -> None:
        """Draw the player on the screen."""
        self.screen.blit(self.image, self.rect)

    def center_ship(self) -> None:
        """Reset the player's position to the center of the screen."""
        self.pos.x = self.screen.get_rect().centerx
        self.pos.y = self.screen.get_rect().bottom - self.rect.height

    def fire(self) -> None:
        self.sprite_manager.sprites.add(Bullet(self.pos.x, self.pos.y, -self.angle, Alien))
