from dataclasses import dataclass, field

import pygame


@dataclass
class GameState:
    player_position: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
