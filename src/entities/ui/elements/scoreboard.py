"""Scoreboard class for displaying the game score as a sprite on the screen."""

import pygame

from src import settings
from src.game_stats import GameStats

TEXT_COLOR = pygame.Color("#ffffffff")


class Scoreboard(pygame.sprite.Sprite):
    """A sprite that renders and displays the game score."""

    def __init__(self, stats: GameStats) -> None:
        """Initialize the scoreboard sprite with the given screen and game stats."""
        super().__init__()
        self.screen: pygame.Surface = pygame.display.get_surface()
        self.stats: GameStats = stats

        self.update()

    def update(self) -> None:
        """Render the score image."""
        self.score_image: pygame.Surface = settings.FONT.render(str(self.stats.score).zfill(4), 1, TEXT_COLOR)
        self.score_rect: pygame.Rect = self.score_image.get_rect(
            topright=(self.screen.get_rect().right - 20, 20),
        )
        self.image: pygame.Surface = self.score_image
        self.rect: pygame.Rect = self.score_rect

    def show(self) -> None:
        """Draw the score on screen."""
        self.screen.blit(self.image, self.rect)
