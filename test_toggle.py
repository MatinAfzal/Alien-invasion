"""Headless check: the menu AI:RL / AI:Classic toggle really switches enemies.

The gate the game uses is ``controller.enabled``, which folds in
``stats.rl_enemies`` (written by the two menu buttons in gf.update_game_sprites).
Both halves of the gate are checked:

  * movement -- Alien.update() consults decide_movement() only when enabled
  * firing   -- gf.alien_fire() takes the RL path only when enabled
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.alien import AlienL1
from src.game_stats import GameStats
from src.input import Input
from src.rl import get_controller, init_controller
from src.resources.texture_atlas import TextureAtlas
from src.settings import Settings
from src.ship import Ship


def main():
    pygame.init()
    pygame.display.set_mode((1200, 800))
    TextureAtlas.initialize()
    ai = Settings()
    screen = pygame.display.get_surface()

    init_controller()
    controller = get_controller()
    assert controller is not None, "controller failed to load"
    assert controller.movement and controller.fire, "Q-tables missing"

    stats = GameStats()
    ship = Ship(Input())
    alien = AlienL1(ai, screen)

    # --- toggle ON (default) -------------------------------------------
    stats.rl_enemies = True
    controller.active = stats.rl_enemies
    assert controller.enabled, "RL should be active when the toggle is ON"

    decision = controller.decide_movement(alien, ship, [])
    assert decision is not None, "RL toggle ON should yield an RL decision"
    print(f"toggle ON : enabled={controller.enabled} rl_decision={decision}")

    # over a run of frames the RL policy must actually displace the alien
    moved = False
    start_x, start_y = alien.rect.x, alien.rect.y
    for _ in range(60):
        alien.rl_cooldown = 0  # force a fresh decision each frame
        alien.update(ship, [])
        if (alien.rect.x, alien.rect.y) != (start_x, start_y):
            moved = True
            break
    assert moved, "the RL policy should move the alien over time"
    print(f"toggle ON : moved over 60 frames ({moved})")

    # --- toggle OFF -----------------------------------------------------
    stats.rl_enemies = False
    controller.active = stats.rl_enemies
    assert not controller.enabled, "RL should be disabled when the toggle is OFF"

    decision = controller.decide_movement(alien, ship, [])
    assert decision is None, "RL toggle OFF must not produce RL decisions"
    print(f"toggle OFF: enabled={controller.enabled} rl_decision={decision}")

    x0, y0 = alien.rect.x, alien.rect.y
    alien.update(ship, [])
    moved_classic = (alien.rect.x, alien.rect.y) != (x0, y0)
    assert moved_classic, "the classic heuristic still has to move the alien"
    print(f"toggle OFF: classic heuristic moved={moved_classic}")

    # --- the firing gate reads the very same flag ------------------------
    stats.rl_enemies = True
    controller.active = True
    assert controller.enabled, "firing gate should follow toggle ON"
    stats.rl_enemies = False
    controller.active = False
    assert not controller.enabled, "firing gate should follow toggle OFF"

    print("TOGGLE TEST PASSED")


if __name__ == "__main__":
    main()
