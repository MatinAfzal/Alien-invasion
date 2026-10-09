"""Headless check of the main-menu AI toggle wiring.

Mirrors the button definitions in ``alien_invasion.py``: the label shows the
current mode and clicking it flips to the other one, exactly like the Auto pair.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.game_stats import GameStats
from src.rl import get_controller, init_controller


def main():
    pygame.init()
    pygame.display.set_mode((1200, 800))

    init_controller()
    controller = get_controller()
    assert controller is not None

    stats = GameStats()
    assert stats.rl_enemies is True, "RL enemies should be the default"

    # same lambdas alien_invasion.py wires into the two buttons
    rl_on = lambda: setattr(stats, "rl_enemies", False)  # noqa: E731
    rl_off = lambda: setattr(stats, "rl_enemies", True)  # noqa: E731

    visible_rl = lambda: stats.rl_enemies and not stats.game_active and not stats.credits_active  # noqa: E731
    visible_classic = lambda: not stats.rl_enemies and not stats.game_active and not stats.credits_active  # noqa: E731

    # default: "AI: RL" shown, "AI: Classic" hidden
    assert visible_rl() and not visible_classic()
    print("menu shows: AI: RL")

    # click "AI: RL" -> classic mode
    rl_on()
    controller.active = stats.rl_enemies
    assert stats.rl_enemies is False, "clicking AI: RL must switch to classic"
    assert not controller.enabled, "controller must go inactive"
    assert visible_classic() and not visible_rl()
    print("clicked AI: RL -> menu shows: AI: Classic, controller.enabled=False")

    # click "AI: Classic" -> back to RL
    rl_off()
    controller.active = stats.rl_enemies
    assert stats.rl_enemies is True, "clicking AI: Classic must switch back to RL"
    assert controller.enabled, "controller must reactivate"
    assert visible_rl() and not visible_classic()
    print("clicked AI: Classic -> menu shows: AI: RL, controller.enabled=True")

    # the buttons must hide once a game or credits screen is open
    stats.game_active = True
    assert not visible_rl() and not visible_classic()
    stats.game_active = False
    stats.credits_active = True
    assert not visible_rl() and not visible_classic()
    print("buttons hidden while game/credits are open")

    print("MENU TOGGLE TEST PASSED")


if __name__ == "__main__":
    main()
