"""Headless tests: HUD visibility, heart rendering, and scoring.

Guards three recent fixes:
  * the score/heart HUD is gameplay-only (hidden on the menu),
  * Health draws on the logical surface (not the raw window, which the
    scaled present() would overwrite),
  * score increases per alien destroyed.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from pygame.sprite import Group

import src.game_functions as gf
from src import display
from src.alien import AlienL1
from src.bullet import ShipBullet
from src.entities.ui.elements.scoreboard import Scoreboard
from src.game_stats import GameStats
from src.health import Health
from src.input import Input
from src.resources.texture_atlas import TextureAtlas
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Settings
from src.ship import Ship


class FakeAnim:
    def set_position(self, *a):
        pass

    def play(self):
        pass


class FakeRegion:
    def update(self, *a):
        pass


class FakeShip:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 10, 10)

    def bltime(self):
        pass


class FakeButton:
    def update(self):
        pass


class Spy:
    def __init__(self):
        self.calls = 0

    def draw(self):
        self.calls += 1

    def show(self):
        self.calls += 1


class FakeSettings:
    delta_time = 0.1


def call_update_screen(screen, stats, health, sb):
    gf.animations = [FakeAnim(), FakeAnim()]
    gf.update_screen(
        FakeRegion(),
        FakeSettings(),
        screen,
        stats,
        sb,
        FakeShip(),
        Group(),  # aliens
        Group(),  # bullets
        FakeButton(),
        FakeButton(),
        FakeButton(),
        FakeButton(),
        FakeButton(),
        FakeButton(),
        FakeButton(),
        Group(),  # cargoes
        Group(),  # alien_bullets
        health,
        Group(),  # hearts
        Group(),  # shields
    )


def main() -> None:
    window = display.fit_window_size((SCREEN_WIDTH, SCREEN_HEIGHT))
    screen = display.init(window, (SCREEN_WIDTH, SCREEN_HEIGHT))
    TextureAtlas.initialize()

    # --- Gating: hidden off-gameplay, shown during gameplay ---
    stats = GameStats()  # game_active False (menu)
    health_spy, sb_spy = Spy(), Spy()
    call_update_screen(screen, stats, health_spy, sb_spy)
    assert health_spy.calls == 0 and sb_spy.calls == 0, "HUD must be hidden on the menu"
    print("menu: HUD hidden                OK")

    stats.game_active = True
    health_spy, sb_spy = Spy(), Spy()
    call_update_screen(screen, stats, health_spy, sb_spy)
    assert health_spy.calls == 1 and sb_spy.calls == 1, "HUD must show during gameplay"
    print("playing: HUD shown              OK")

    # --- Health must bind to the logical surface (scaled-present regression) ---
    assert Health().screen is display.get_logical(), "Health must draw on the logical surface"
    print("health uses logical surface     OK")

    # --- Rendering: hearts draw and fill the expected larger area ---
    health = Health()
    health.current_hearts = 3
    screen.fill((0, 0, 0))
    health.draw()
    painted = sum(
        1 for x in range(16, 44) for y in range(16, 44) if screen.get_at((x, y))[:3] != (0, 0, 0)
    )
    assert painted > 100, f"heart bar painted too little ({painted})"
    print(f"hearts render (28px, {painted} px)     OK")

    # --- Scoring: each destroyed alien adds points ---
    ai = Settings()
    ai.initialize_dynamic_settings()
    gf.animations = []
    gf.load_animations(screen)
    stats2 = GameStats()
    stats2.game_active = True
    sb = Scoreboard(screen, stats2)
    ship = Ship(Input())
    ship.rect.center = (600, 700)

    aliens = Group()
    alien = AlienL1(ai, screen)
    alien.rect.center = (600, 300)
    alien.x, alien.y = float(alien.rect.x), float(alien.rect.y)
    aliens.add(alien)

    bullets = Group()
    bullet = ShipBullet(ship)
    bullet.rect.center = (600, 300)
    bullets.add(bullet)

    gf.check_bullet_alien_collisions(ai, screen, stats2, sb, ship, aliens, bullets, Group(), gf.animations)
    assert stats2.score == ai.alien_points, f"score should rise by {ai.alien_points}, got {stats2.score}"
    assert len(aliens) == 0
    print("score rises per kill            OK")

    print("HUD TEST PASSED")


if __name__ == "__main__":
    main()
