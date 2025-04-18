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


class Game:
    def __init__(self):
        pygame.init()
        self.ai_settings = Settings()
        self.input = Input()

        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Alien Invasion")
        self.screen_bg: pygame.Surface = pygame.image.load(ASSETS_DIR / "images" / "space3.png")
        self.screen_bg = pygame.transform.scale(self.screen_bg, (SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))

        self.screen_bg_2: pygame.Surface = pygame.transform.rotate(self.screen_bg, 180)

        self.clock = pygame.time.Clock()
        self.alien_spawn_timer = pygame.time.get_ticks()

        # Create an instance to store game statistics and create scoreboard.
        self.stats = GameStats()
        self.sb = Scoreboard(self.screen, self.stats)

        self.health = Health()
        self.health.reset()

        # Make a ship, and a group for each game sprite.
        self.ship = Ship(self.input)
        self.bullets = Group()
        self.aliens = Group()
        self.cargoes = Group()
        self.alien_bullets = Group()
        self.hearts = Group()
        self.shields = Group()

        self.play_button = btn(
            "start",
            (240, 64),
            (self.screen.get_rect().centerx - 120, self.screen.get_rect().centery + -74),
            lambda: gf.run_play_button(self.ai_settings, self.stats, self.ship, self.aliens, self.cargoes, self.bullets, self.health),
            lambda: not self.stats.game_active and not self.stats.credits_active,
        )

        self.credits_button = btn(
            "Credits",
            (240, 64),
            (self.screen.get_rect().centerx - 120, self.screen.get_rect().centery + 10),
            lambda: gf.run_credit_button(self.stats),
            lambda: not self.stats.credits_active and not self.stats.game_active,
        )

        self.back_button = btn(
            "Back",
            (240, 64),
            (10, 50),
            lambda: gf.run_back_button(self.stats),
            lambda: self.stats.credits_active,
        )

        self.alien_spawn_counter = 0

        gf.load_animations(self.screen)
        gf.load_credits()

    def run_game(self):
        # Start the main loop for the game.
        while True:
            self.input.update()
            gf.check_events(self.ai_settings, self.input, self.screen, self.stats, self.ship, self.bullets)
            if self.stats.game_active:
                # Prevent mouse from going out of self.screen.
                pygame.event.set_grab(True)

                # Update game sprites
                gf.update_game_sprites(
                    self.ai_settings,
                    self.screen,
                    self.stats,
                    self.sb,
                    self.ship,
                    self.aliens,
                    self.bullets,
                    self.cargoes,
                    self.alien_bullets,
                    self.health,
                    self.hearts,
                    self.shields,
                )
            else:
                pygame.event.set_grab(False)

            gf.update_screen(
                self.ai_settings,
                self.screen,
                self.stats,
                self.sb,
                self.ship,
                self.aliens,
                self.bullets,
                self.play_button,
                self.credits_button,
                self.back_button,
                self.screen_bg,
                self.screen_bg_2,
                self.cargoes,
                self.alien_bullets,
                self.health,
                self.hearts,
                self.shields,
            )

            self.clock.tick(self.ai_settings.fps)

            # Aliens fire timer
            current_time = pygame.time.get_ticks()

            if current_time - self.alien_spawn_timer > 100:
                gf.alien_fire(self.ai_settings, self.stats, self.screen, self.aliens, self.alien_bullets, self.ship)

                generate_heart(self.stats, self.screen, self.hearts)
                gf.generate_shields(self.screen, self.ai_settings, self.stats, self.shields)

                if self.alien_spawn_counter % 10 == 0:
                    gf.spawn_random_alien(self.ai_settings, self.screen, self.aliens)

                self.alien_spawn_counter += 1
                self.alien_spawn_timer = current_time


game = Game()
game.run_game()
