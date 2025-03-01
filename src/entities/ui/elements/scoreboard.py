import pygame

from src import settings
from game_state import GameStats

TEXT_COLOR = pygame.Color("#ffffffff")


class Scoreboard(pygame.sprite.Sprite):
    def __init__(self, stats: GameStats) -> None:
        super().__init__()
        self.screen: pygame.Surface = pygame.display.get_surface()
        self.stats: GameStats = stats

        self.update()

    def update(self) -> None:
        self.image: pygame.Surface = settings.FONT.render(str(self.stats.score).zfill(4), 1, TEXT_COLOR)
        self.rect: pygame.Rect = self.image.get_rect(
            topright=(self.screen.get_rect().right - 20, 32 - settings.FONT_ACCENT // 2),
        )

    def show(self) -> None:
        self.screen.blit(self.image, self.rect)
