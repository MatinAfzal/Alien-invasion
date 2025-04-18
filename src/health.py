"""Manages and displays the player's health."""

import time
from dataclasses import dataclass, field

import pygame

from src.entities.items.shield import SHIELD_TIME

from .game_stats import GameStats

INIT_HEARTS: int = 5
MAX_HEARTS: int = 5


@dataclass
class Health:
    """Handles ship health and shields."""

    screen: pygame.Surface = field(default_factory=pygame.display.get_surface, init=False)
    current_hearts: int = INIT_HEARTS
    freeze_flag: bool = False
    freeze_time: float = 0

    def reset(self) -> None:
        """Reset health to initial value."""
        self.current_hearts = INIT_HEARTS

    def full(self) -> None:
        """Set health to maximum."""
        self.current_hearts = MAX_HEARTS

    def increase(self) -> None:
        """Increase health by one if not at max."""
        if self.current_hearts < MAX_HEARTS:
            self.current_hearts += 1

    def decrease(self, stats: GameStats) -> None:
        """Decrease health by one unless shielded."""
        if self.freeze_flag and time.time() - self.freeze_time < SHIELD_TIME:
            return
        self.current_hearts -= 1
        if self.current_hearts == 0:
            stats.game_active = False
            pygame.mouse.set_visible(True)

    def activate_shield(self) -> None:
        """Activate temporary shield."""
        self.freeze_flag = True
        self.freeze_time = time.time()

    def draw(self) -> None:
        """Draw health bar in the top-left corner."""
        heart_size: tuple[int, int] = (20, 20)
        full_heart: pygame.Surface = pygame.transform.scale(
            pygame.image.load("data/assets/hearts/full_heart.png"),
            heart_size,
        )
        empty_heart: pygame.Surface = pygame.transform.scale(
            pygame.image.load("data/assets/hearts/empty_heart.png"),
            heart_size,
        )

        rect: pygame.Rect = self.screen.get_rect(topleft=(20, 20))
        for i in range(MAX_HEARTS):
            self.screen.blit(full_heart if i < self.current_hearts else empty_heart, rect)
            rect.x += 25
