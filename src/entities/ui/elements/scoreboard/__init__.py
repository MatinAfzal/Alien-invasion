"""Scoreboard class for displaying the game score as a sprite on the screen."""

import pygame

from src.game_stats import GameStats
from src.settings import BG_COLOR, FONT, Color


class Scoreboard(pygame.sprite.Sprite):
    """A sprite that renders and displays the game score."""

    def __init__(
        self,
        screen: pygame.Surface,
        stats: GameStats,
        text_color: Color = (0, 180, 0),
        font: pygame.font.Font = FONT,
    ) -> None:
        """Initialize the scoreboard sprite with the given screen and game stats."""
        super().__init__()
        self.screen: pygame.Surface = screen
        self.stats: GameStats = stats
        self.text_color = text_color
        self.font: pygame.font.Font = font

        # Initialize the scoreboard by updating the score
        self.update()

    def update(self) -> None:
        """Render the score image."""
        self.score_image: pygame.Surface = self.font.render(
            str(self.stats.score).zfill(4),
            1,
            self.text_color,
            BG_COLOR,
        )
        self.score_rect: pygame.Rect = self.score_image.get_rect(
            topright=(self.screen.get_rect().right - 20, 20),
        )

        # Assign the rendered image to the sprite
        self.image: pygame.Surface = self.score_image
        self.rect: pygame.Rect = self.score_rect

    def show(self) -> None:
        """Draw the score on screen."""
        self.screen.blit(self.image, self.rect)
