import pygame
from pygame.sprite import Group
import src.game_functions as gf
from src.game_functions import show_loading_screen
from src.game_functions import fade_in
from src.game_stats import GameStats
from src.settings import Settings
from src.ship import Ship
from src.button import Button
from src.scoreboard import Scoreboard
from src.health import Health
from src.input import Input


def run_game():
    # Initialize pygame, settings, screen object and assets.
    pygame.init()
    ai_settings = Settings()
    input = Input()
    screen = pygame.display.set_mode((ai_settings.screen_width, ai_settings.screen_height))
    pygame.display.set_caption("Alien Invasion")
    if not ai_settings.debug_mode:
        show_loading_screen(screen, ai_settings)
    screen_bg = pygame.image.load("data/assets/images/space3.png")
    screen_bg = pygame.transform.scale(screen_bg, (ai_settings.screen_width*2, ai_settings.screen_width*2))
    screen_bg_2 = pygame.transform.rotate(screen_bg, 180)
    clock = pygame.time.Clock()
    alien_spawn_timer = pygame.time.get_ticks()

    # Create an instance to store game statistics and create scoreboard.
    stats = GameStats(ai_settings)
    sb = Scoreboard(ai_settings, screen, stats)

    health = Health(ai_settings, screen)
    health.init_health()

    # Make a ship, and a group for each game sprite.
    ship = Ship(ai_settings, input, screen)
    bullets = Group()
    aliens = Group()
    cargoes = Group()
    alien_bullets = Group()
    hearts = Group()
    shields = Group()

    # Make the play button.
    # Update the play button
    play_button = Button(
      screen,
      input,
      position=(screen.get_rect().centerx - 100, screen.get_rect().centery + 25),
      size=(200, 50),
      text="Play",
      foreground_color=(255, 255, 255),
      background_color=(0, 225, 0),
      border_width=0,
      display_condition=lambda: not stats.game_active and not stats.credits_active,
      on_clicked=lambda: fade_in(screen, ai_settings, gf.run_play_button, ai_settings, stats, ship, aliens, cargoes, bullets, health)
  )

    # Update the credits button
    credits_button = Button(
      screen,
      input,
      position=(screen.get_rect().centerx - 100, screen.get_rect().centery + 100),
      size=(200, 50),
      text="Credits",
      foreground_color=(255, 255, 255),
      background_color=(0, 225, 0),
      border_width=0,
      display_condition=lambda: not stats.credits_active and not stats.game_active,
      on_clicked=lambda: fade_in(screen, ai_settings, gf.run_credit_button, stats)
  )

    # Update the back button
    back_button = Button(
      screen,
      input,
      position=(10, 50),
      size=(200, 50),
      text="Back",
      foreground_color=(255, 255, 255),
      background_color=(0, 225, 0),
      border_width=0,
      display_condition=lambda: stats.credits_active,
      on_clicked=lambda: fade_in(screen, ai_settings, gf.run_back_button, stats)
  )

    alien_spawn_counter = 0

    gf.load_animations(screen, ai_settings)
    gf.load_credits()

    # Start the main loop for the game.
    while True:
        input.update()
        gf.check_events(ai_settings, input, screen, stats, ship, bullets)
        if stats.game_active:
            # Prevent mouse from going out of screen.
            pygame.event.set_grab(True)

            # Update game sprites
            gf.update_game_sprites(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes, alien_bullets,
                                   health, hearts, shields)
        else:
            pygame.event.set_grab(False)

        gf.update_screen(ai_settings, screen, stats, sb, ship, aliens, bullets, play_button, credits_button,
                         back_button, screen_bg, screen_bg_2, cargoes, alien_bullets, health, hearts, shields)

        clock.tick(ai_settings.fps)

        # Aliens fire timer
        current_time = pygame.time.get_ticks()

        if current_time - alien_spawn_timer > 100:
            gf.alien_fire(ai_settings, stats, screen, aliens, alien_bullets, ship)

            gf.generate_heart(ai_settings, stats, screen, hearts)
            gf.generate_shields(screen, ai_settings, stats, shields)

            if alien_spawn_counter % 10 == 0:
                gf.spawn_random_alien(ai_settings, screen, aliens)

            alien_spawn_counter += 1
            alien_spawn_timer = current_time
            


run_game()
