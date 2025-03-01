from dataclasses import dataclass, field

import pygame


@dataclass
class GameState:
    player_position: pygame.Vector2 = field(default_factory=pygame.Vector2)
    camera_offset: pygame.Vector2 = field(default_factory=pygame.Vector2)
