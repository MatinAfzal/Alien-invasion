from turtle import screensize
import pygame.font


class Scoreboard:
    """A class to report scoring information."""

    def __init__(self, ai_settings, screen, stats):
        """Initialize score keeping attributes."""
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.ai_settings = ai_settings
        self.stats = stats
        
        # # Font settings for scoring information.
        self.text_color = (0, 180, 0)
        self.font = pygame.font.Font("data/assets/fonts/sevenSegment.ttf", 48)  

        # Prepare the initial score image.
        self.prep_score()

    def prep_score(self):
        """Turn the score into a rendered image."""
        rounded_score = int(round(self.stats.score, -1))
        score_str = "{:,}".format(rounded_score)
        score_str = str(self.stats.score).zfill(4)
        self.score_image = self.font.render(score_str, True, self.text_color, self.ai_settings.bg_color)

        # Display the score at the top right of the screen.
        self.score_rect = self.score_image.get_rect()
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.top = 20

    def show_health(self, ship):
        """Display the number of health remaining"""
        health_str = f"Health: {ship.health}"
        health_str = str(ship.health).zfill(4)
        
        health_image = self.font.render(health_str, True, self.text_color, self.ai_settings.bg_color)
        health_rect = health_image.get_rect()
        health_rect.right = health_rect.right - 20
        health_rect.top = 20

        self.screen.blit(health_image, health_rect)


    def show_score(self):
        """Draw score to the screen."""
        self.screen.blit(self.score_image, self.score_rect)
