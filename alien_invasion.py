import pygame
from pygame.sprite import Group

import src.game_functions as gf
from src.entities.ui.elements.button import Button as btn
from src.entities.ui.elements.scoreboard import Scoreboard
from src.game_functions import generate_heart
from src.game_stats import GameStats
from src.health import Health
from src.input import Input
from src.settings import ASSETS_DIR, SCREEN_HEIGHT, SCREEN_WIDTH, Settings
from src.ship import Ship


def run_game():
    pygame.init()
    ai_settings = Settings()
    input = Input()

    screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Alien Invasion")
    screen_bg: pygame.Surface = pygame.image.load(ASSETS_DIR / "images" / "space3.png")
    screen_bg = pygame.transform.scale(screen_bg, (SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))

    screen_bg_2: pygame.Surface = pygame.transform.rotate(screen_bg, 180)

    clock = pygame.time.Clock()
    alien_spawn_timer = pygame.time.get_ticks()

    # Create an instance to store game statistics and create scoreboard.
    stats = GameStats()
    sb = Scoreboard(screen, stats)

    health = Health()
    health.reset()

    # Make a ship, and a group for each game sprite.
    ship = Ship(input)
    bullets = Group()
    aliens = Group()
    cargoes = Group()
    alien_bullets = Group()
    hearts = Group()
    shields = Group()

    play_button = btn(
        "start",
        (240, 64),
        (screen.get_rect().centerx - 120, screen.get_rect().centery + -74),
        lambda: gf.run_play_button(ai_settings, stats, ship, aliens, cargoes, bullets, health),
        lambda: not stats.game_active and not stats.credits_active,
    )

    credits_button = btn(
        "Credits",
        (240, 64),
        (screen.get_rect().centerx - 120, screen.get_rect().centery + 10),
        lambda: gf.run_credit_button(stats),
        lambda: not stats.credits_active and not stats.game_active,
    )

    back_button = btn(
        "Back",
        (240, 64),
        (10, 50),
        lambda: gf.run_back_button(stats),
        lambda: stats.credits_active,
    )

    alien_spawn_counter = 0

    gf.load_animations(screen)
    gf.load_credits()

    # Start the main loop for the game.
    while True:
        input.update()
        gf.check_events(ai_settings, input, screen, stats, ship, bullets)
        if stats.game_active:
            # Prevent mouse from going out of screen.
            pygame.event.set_grab(True)

            # Update game sprites
            gf.update_game_sprites(
                ai_settings,
                screen,
                stats,
                sb,
                ship,
                aliens,
                bullets,
                cargoes,
                alien_bullets,
                health,
                hearts,
                shields,
            )
        else:
            pygame.event.set_grab(False)

        gf.update_screen(
            ai_settings,
            screen,
            stats,
            sb,
            ship,
            aliens,
            bullets,
            play_button,
            credits_button,
            back_button,
            screen_bg,
            screen_bg_2,
            cargoes,
            alien_bullets,
            health,
            hearts,
            shields,
        )

        clock.tick(ai_settings.fps)

        # Aliens fire timer
        current_time = pygame.time.get_ticks()

        if current_time - alien_spawn_timer > 100:
            gf.alien_fire(ai_settings, stats, screen, aliens, alien_bullets, ship)

            generate_heart(stats, screen, hearts)
            gf.generate_shields(screen, ai_settings, stats, shields)

            if alien_spawn_counter % 10 == 0:
                gf.spawn_random_alien(ai_settings, screen, aliens)

            alien_spawn_counter += 1
            alien_spawn_timer = current_time


run_game()
