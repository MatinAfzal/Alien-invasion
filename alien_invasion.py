import pygame
from pygame.sprite import Group
import sys
from src.game_functions import *
from src.game_stats import GameStats
from src.settings import Settings
from src.ship import Ship
from src.button import Button
from src.scoreboard import Scoreboard
from src.menu import MainMenu, SettingsMenu
from src.debug import Debug


def apply_display_settings(screen, ai_settings):
    """Apply current display settings and return the new screen."""
    flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF if ai_settings.fullscreen else pygame.RESIZABLE
    
    if ai_settings.fullscreen:
        # Get the current display info
        display_info = pygame.display.Info()
        # If in fullscreen, use the current display's resolution
        screen = pygame.display.set_mode(
            (0, 0),  # This tells pygame to use the current display resolution
            flags
        )
        # Update settings to match actual screen size
        ai_settings.set_resolution(screen.get_width(), screen.get_height())
    else:
        # In windowed mode, use the selected resolution
        screen = pygame.display.set_mode(
            (ai_settings.screen_width, ai_settings.screen_height),
            flags
        )
    
    # Force a display update
    pygame.display.flip()
    return screen


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
    pygame.mixer.init()
    
    ai_settings = Settings()
    screen = apply_display_settings(None, ai_settings)
    pygame.display.set_caption("Alien Invasion")
    
    # Load background
    screen_bg = pygame.image.load("data/assets/images/space.jpg")
    screen_bg = pygame.transform.scale(screen_bg, (ai_settings.screen_width*2, ai_settings.screen_width*2))
    screen_bg_2 = pygame.transform.rotate(screen_bg, 180)
    clock = pygame.time.Clock()

    # Create game objects
    stats = GameStats(ai_settings)
    sb = Scoreboard(ai_settings, screen, stats)
    ship = Ship(ai_settings, screen)
    bullets = Group()
    aliens = Group()
    cargoes = Group()
    play_button = Button(ai_settings, screen, "Play")
    debug = Debug(screen, ai_settings)

    # Game state
    current_menu = None
    game_paused = False
    need_display_update = False

    def start_game():
        stats.game_active = True
        stats.reset_stats()
        pygame.mouse.set_visible(False)
        
        # Empty game objects
        aliens.empty()
        bullets.empty()
        cargoes.empty()
        
        # Create new fleet and center ship
        create_fleet(ai_settings, screen, ship, aliens, cargoes)
        ship.center_ship()
        
        nonlocal current_menu
        current_menu = None

    def show_settings():
        nonlocal current_menu
        current_menu = SettingsMenu(screen, ai_settings, show_main_menu)

    def show_main_menu():
        nonlocal current_menu
        current_menu = MainMenu(screen, start_game, show_settings, sys.exit)

    # Start with main menu
    show_main_menu()

    # Start the main loop for the game.
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if stats.game_active:
                        stats.game_active = False
                        pygame.mouse.set_visible(True)
                        show_main_menu()
                    elif current_menu and isinstance(current_menu, SettingsMenu):
                        show_main_menu()
                elif event.key == pygame.K_F3:  # Toggle debug with F3
                    debug.toggle()
                # Handle menu input
                elif current_menu:
                    current_menu.handle_event(event)
                # Handle game input
                elif stats.game_active:
                    check_keydown_events(event, ai_settings, screen, ship, bullets)
            elif event.type == pygame.KEYUP:
                if stats.game_active:
                    check_keyup_events(event, ship, ai_settings)
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                if current_menu:
                    current_menu.handle_event(event)
                elif not stats.game_active:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    check_play_button(ai_settings, screen, stats, play_button, ship, aliens, bullets, cargoes, mouse_x, mouse_y)

        # Check if display settings need update
        if (hasattr(current_menu, 'controls_menu') and 
            current_menu.controls_menu is None and 
            isinstance(current_menu, SettingsMenu)):
            # Get the old resolution
            old_width = screen.get_width()
            old_height = screen.get_height()
            
            # If resolution or fullscreen changed
            if (old_width != ai_settings.screen_width or 
                old_height != ai_settings.screen_height or 
                (ai_settings.fullscreen and not (screen.get_flags() & pygame.FULLSCREEN)) or
                (not ai_settings.fullscreen and (screen.get_flags() & pygame.FULLSCREEN))):
                # Apply new display settings
                screen = apply_display_settings(screen, ai_settings)
                # Reload background for new resolution
                screen_bg = pygame.image.load("data/assets/images/space.jpg")
                screen_bg = pygame.transform.scale(screen_bg, (ai_settings.screen_width*2, ai_settings.screen_width*2))
                screen_bg_2 = pygame.transform.rotate(screen_bg, 180)
                # Update object references to new screen
                ship.screen = screen
                ship.screen_rect = screen.get_rect()
                sb.screen = screen
                sb.screen_rect = screen.get_rect()
                current_menu.screen = screen
                current_menu.screen_rect = screen.get_rect()

        # Update game state
        if stats.game_active:
            # Update input state
            ai_settings.input_handler.update()
            # Update game objects
            ship.update()
            update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes)
            update_aliens(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb)
            # Update debug info
            debug.update(ship, aliens, bullets, cargoes, stats)

        # Draw screen
        screen.fill(ai_settings.bg_color)
        
        # Draw background
        screen.blit(screen_bg, (ai_settings.bg_screen_x, ai_settings.bg_screen_y))
        screen.blit(screen_bg_2, (ai_settings.bg_screen_2_x, ai_settings.bg_screen_2_y))
        
        if stats.game_active:
            # Draw game objects
            ship.bltime()
            aliens.draw(screen)
            cargoes.draw(screen)
            for bullet in bullets.sprites():
                bullet.draw_bullet()
            sb.show_score()
        elif current_menu:
            current_menu.draw()
        else:
            play_button.draw_button()
            
        # Draw debug overlay
        debug.draw()
        debug.tick()
        
        # Make the most recently drawn screen visible.
        pygame.display.flip()
        clock.tick(ai_settings.fps)


if __name__ == '__main__':
    run_game()
