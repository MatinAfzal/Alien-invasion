"""."""

from pathlib import Path

import pygame

pygame.init()

type Color = tuple[int, int, int]

BASE_DIR: Path = Path(__file__).parent.parent.parent
ASSETS_DIR: Path = BASE_DIR / "assets"

FONT = pygame.font.Font(ASSETS_DIR / "fonts" / "Silkscreen-Regular.ttf", 40)
FONT_ACCENT: int = FONT.get_ascent()


HEART_SPEED_FACTOR = 4


# settings.py
"""Module to store all settings for Alien Invasion"""

# Clock
FPS: float = 120.0
DELTA_TIME: float = (1000.0 / FPS) / 10
DEFAULT_ANIMATION_LATENCY: float = DELTA_TIME / 500

# Screen settings
SCREEN_WIDTH: int = 1200
SCREEN_HEIGHT: int = 800
BG_COLOR: Color = (225, 225, 255)

# Ship settings
SHIP_SPEED_FACTOR_X: float = 3.0
SHIP_SPEED_FACTOR_Y: float = 3.0
SHIP_LIMIT: int = 2

# Bullet settings
BULLET_SPEED_FACTOR: float = 10.0
BULLET_WIDTH: int = 3
BULLET_HEIGHT: int = 15
BULLET_COLOR: tuple[int, int, int] = (60, 60, 60)
BULLETS_ALLOWED: int = 5
ALIEN_BULLET_SPEED_FACTOR: float = 5.0

# Alien settings
ALIEN_SPEED_FACTOR: float = 5.0
CARGO_SPEED_FACTOR: float = 0.5
FLEET_DROP_SPEED: int = 2
CARGO_DROP_CHANCE: float = 0  # TODO: There is an interesting bug here
ALIEN_FIRE_CHANCE: int = 100  # from 1000
ALIEN_L2_FIRE_CHANCE: int = 200  # from 1000
ALIEN_L2_HEALTH: int = 2
ALIEN_L1_HEALTH: int = 1
ALIEN_L2_SPAWN_CHANCE: int = 5

# Game progression
SPEEDUP_SCALE: float = 1.1
SCORE_SCALE: float = 1.5

ALIEN_POINTS: int = 50
CARGO_POINTS: int = 100

# Screen background settings
BG_SCREEN_X: int = 0
BG_SCREEN_Y: int = 0
BG_SCREEN_2_X: int = 0
BG_SCREEN_2_Y: int = -SCREEN_HEIGHT
BG_SCREEN_SCROLL_SPEED: float = 0.2


class Settings:
    """A class to store all settings for Alien Invasion"""

    def __init__(self):
        """Initialize the game's static settings."""
        # Clock
        self.fps = 120.0
        self.delta_time = (1000.0 / self.fps) / 10
        self.default_animation_latency = self.delta_time / 500

        # Screen settings
        self.screen_width = 1200
        self.screen_height = 800
        self.bg_color = (225, 225, 255)

        # Ship settings
        self.ship_speed_factor_x = 3
        self.ship_speed_factor_y = 3
        self.ship_limit = 2

        # Bullets settings
        self.bullet_speed_factor = 10
        self.bullet_width = 3
        self.bullet_height = 15
        self.bullet_color = 60, 60, 60
        self.bullets_allowed = 5
        self.alien_bullet_speed_factor = 5

        # Alien settings
        self.alien_speed_factor = 5
        self.cargo_speed_factor = 0.5
        self.fleet_drop_speed = 2
        self.cargo_drop_chance = 0  # TODO: There is an interesting bug in hereش
        self.alien_fire_chance = 100  # from 1000
        self.alien_l2_fire_chance = 200  # from 1000
        self.alien_l2_health = 2
        self.alien_l1_health = 1
        self.alien_l2_spawn_chance = 5

        # How quickly the game speeds up
        self.speedup_scale = 1.1

        # How quickly the alien point values increase
        self.score_scale = 1.5

        self.alien_points = 50
        self.cargo_points = 100

        self.initialize_dynamic_settings()

        # screen background settings.
        self.bg_screen_x = 0
        self.bg_screen_y = 0
        self.bg_screen_2_x = 0
        self.bg_screen_2_y = -self.screen_height
        self.bg_screen_scroll_speed = 0.2

    def initialize_dynamic_settings(self):
        """Increase speed settings and alien point values."""
        # self.ship_speed_factor_x = 2.5
        # self.ship_speed_factor_y = 1.5
        # self.bullet_speed_factor = 3
        self.alien_speed_factor = 2
        self.cargo_speed_factor = 0.5
        self.cargo_drop_chance = 0

        # Scoring
        self.alien_points = 10

    def increase_speed(self):
        """Increase speed settings."""
        self.ship_speed_factor_x *= self.speedup_scale
        self.ship_speed_factor_y *= self.speedup_scale
        self.bullet_speed_factor *= self.speedup_scale
        self.alien_speed_factor *= self.speedup_scale
        self.cargo_speed_factor *= self.speedup_scale
        self.cargo_drop_chance *= self.speedup_scale
        self.alien_l2_spawn_chance *= self.speedup_scale
        self.alien_points = int(self.alien_points * self.score_scale)
        # self.bullet_width += 4
