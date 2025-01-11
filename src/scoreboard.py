from turtle import screensize
import pygame.font
from pygame.sprite import Group
from src.ship import Ship


class Scoreboard:
    """A class to report scoring information."""

    def __init__(self, ai_settings, screen, stats):
        """Initialize score keeping attributes."""
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.ai_settings = ai_settings
        self.stats = stats
        
        # Font settings for scoring information.
        self.text_color = (30, 30, 30)
        self.font = pygame.font.SysFont("Arial", 20)

        # Prepare the initial score image.
        self.prep_score()
        
        # Prepare the ships
        self.prep_ships()

    def prep_score(self):
        """Turn the score into a rendered image."""
        rounded_score = int(round(self.stats.score, -1))
        score_str = "{:,}".format(rounded_score)
        score_str = str(self.stats.score)
        self.score_image = self.font.render(score_str, True, self.text_color, self.ai_settings.bg_color)

        # Display the score at the top right of the screen.
        self.score_rect = self.score_image.get_rect()
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.top = 20

    def prep_ships(self):
        """Show how many ships are left."""
        self.ships = Group()
        for ship_number in range(self.stats.ships_left):
            ship = Ship(self.ai_settings, self.screen)
            # Scale down the ship image for lives display
            ship.image = pygame.transform.scale(ship.image, (ship.rect.width // 2, ship.rect.height // 2))
            ship.rect = ship.image.get_rect()
            ship.rect.x = 10 + ship_number * (ship.rect.width + 5)
            ship.rect.y = 10
            self.ships.add(ship)

    def show_score(self):
        """Draw score and ships to the screen."""
        self.screen.blit(self.score_image, self.score_rect)
        self.ships.draw(self.screen)
