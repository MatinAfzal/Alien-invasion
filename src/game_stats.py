"""Module for managing game statistics in the Alien Invasion game.

Defines the GameStats class for tracking the game's score, remaining ships,
and game status, along with a method to reset these stats.
"""

from dataclasses import dataclass

from src.settings import SHIP_LIMIT


@dataclass
class GameStats:
    """Track statistics for Alien Invasion."""

    game_active = False
    credits_active = False
    ships_left: int = SHIP_LIMIT
    score = 0

    def reset(self) -> None:
        """Initialize statistics that can change during the game."""
        self.ships_left = SHIP_LIMIT
        self.score = 0
