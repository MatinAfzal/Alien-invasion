"""Headless test: the auto-pilot detours to collect hearts and shields.

The seek behaviour must work even without learned Q-tables (it is a
deterministic override) and must actually drive the ship onto the pickup
so the game's normal collision code collects it.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from pygame.sprite import Group

import src.game_functions as gf
from src.entities.items.heart import Heart
from src.entities.items.shield import Shield
from src.health import Health
from src.input import Input
from src.resources.texture_atlas import TextureAtlas
from src.rl import ShipAutopilot
from src.ship import Ship


def main() -> None:
    pygame.display.set_mode((1200, 800))
    TextureAtlas.initialize()

    ship = Ship(Input())
    ship.center_ship()
    ap = ShipAutopilot()  # no learned tables: seeking must still work
    aliens = Group()
    alien_bullets = Group()

    # 1) no pickups -> fall back to hold (no movement)
    ap.plan(ship, aliens, alien_bullets, [])
    assert not any(
        [ship.moving_right, ship.moving_left, ship.moving_up, ship.moving_down]
    ), "ship should not move when there is nothing to seek"
    print("no pickups: hold                 OK")

    # 2) heart up-right -> move right + up
    heart = Heart(pygame.display.get_surface())
    heart.rect.centerx = ship.rect.centerx + 300
    heart.rect.centery = ship.rect.centery - 200
    ap.plan(ship, aliens, alien_bullets, [heart])
    assert ship.moving_right and ship.moving_up and not ship.moving_left and not ship.moving_down
    print("heart up-right: seek            OK")

    # 3) shield down-left -> move left + down
    shield = Shield()
    shield.rect.centerx = ship.rect.centerx - 300
    shield.rect.centery = ship.rect.centery + 200
    ap.plan(ship, aliens, alien_bullets, [shield])
    assert ship.moving_left and ship.moving_down and not ship.moving_right and not ship.moving_up
    print("shield down-left: seek          OK")

    # 4) nearest pickup wins
    far = Heart(pygame.display.get_surface())
    far.rect.centerx = ship.rect.centerx + 500
    far.rect.centery = ship.rect.centery
    near = Heart(pygame.display.get_surface())
    near.rect.centerx = ship.rect.centerx - 100
    near.rect.centery = ship.rect.centery
    ap.plan(ship, aliens, alien_bullets, [far, near])
    assert ship.moving_left, "should chase the nearer pickup"
    print("nearest pickup chosen           OK")

    # 5) end to end: chasing actually collects the heart
    ship.center_ship()
    health = Health()
    health.current_hearts = 3
    hearts: Group = Group()
    target = Heart(pygame.display.get_surface())
    target.rect.centerx = ship.rect.centerx + 150
    target.rect.centery = ship.rect.centery - 30
    hearts.add(target)

    collected = False
    for frame in range(2000):
        ap.plan(ship, aliens, alien_bullets, hearts.sprites())
        ship.update()
        hearts.update()
        for h in hearts.copy():
            if h.rect.bottom <= 0:
                hearts.remove(h)
        if pygame.sprite.spritecollideany(ship, hearts):
            gf.update_hearts(ship, health, hearts)
            collected = True
            break
        if not hearts:
            break

    assert collected and not hearts, "auto-pilot failed to reach and collect the heart"
    assert health.current_hearts == 4, f"heart should heal the ship, hearts={health.current_hearts}"
    print("chase collects heart + heals    OK")

    print("PICKUP SEEK TEST PASSED")


if __name__ == "__main__":
    main()
