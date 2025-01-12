import pygame
from pygame.sprite import Group
import src.game_functions as gf
from src.game_stats import GameStats
from src.settings import Settings
from src.ship import Ship
from src.button import Button
from src.scoreboard import Scoreboard


def run_game():
    # Credit for the assets
    print("""
    Art assets used in this game were created by Skorpio and are licensed under CC-BY-SA 3.0.  
    You can view and download them here: [https://opengameart.org/content/space-ship-construction-kit].\n
    Fire sound effect by K.L.Jonasson, Winnipeg, Canada. Triki Minut Interactive www.trikiminut.com
    You can view and download them here: [https://opengameart.org/content/sci-fi-laser-fire-sfx].\n
    Explosion sound effect by by hosch
    You can view and download them here: https://opengameart.org/content/8-bit-sound-effects-2
    """)
    # Initialize pygame, settings, screen object and assets.
    pygame.init()
    ai_settings = Settings()
    screen = pygame.display.set_mode((ai_settings.screen_width, ai_settings.screen_height))
    pygame.display.set_caption("Alien Invasion")
    screen_bg = pygame.image.load("data/assets/images/space.jpg")
    screen_bg = pygame.transform.scale(screen_bg, (ai_settings.screen_width*2, ai_settings.screen_width*2))
    screen_bg_2 = pygame.transform.rotate(screen_bg, 180)
    clock = pygame.time.Clock()
    alien_spawn_timer = pygame.time.get_ticks()
    one_time_do_bullet_hit_flag = False

    # Make the play button.
    play_button = Button(ai_settings, screen, "Play")

    # Create an instance to store game statistics and create scoreboard.
    stats = GameStats(ai_settings)
    sb = Scoreboard(ai_settings, screen, stats)

    # Make a ship, a group of bullets and alien bullets, and a group of aliens.
    ship = Ship(ai_settings, screen)
    bullets = Group()
    aliens = Group()
    cargoes = Group()
    alien_bullets = Group()

    # Create the fleet of aliens.
    gf.create_fleet(ai_settings, screen, ship, aliens, cargoes)

    # Start the main loop for the game.
    while True:
        gf.check_events(ai_settings, screen, stats, play_button, ship, aliens, bullets, cargoes)
        if stats.game_active:
            ship.update()
            gf.update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes,alien_bullets)
            gf.update_aliens(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb)

        gf.update_screen(ai_settings, screen, stats, sb, ship, aliens, bullets, play_button, screen_bg,
                         screen_bg_2, cargoes,alien_bullets)
        clock.tick(ai_settings.fps)

        # aliens fire timer
        current_time = pygame.time.get_ticks()
        if current_time - alien_spawn_timer > 100:   
            gf.alien_fire(ai_settings,stats, screen, aliens, alien_bullets)
            alien_spawn_timer = current_time



run_game()
