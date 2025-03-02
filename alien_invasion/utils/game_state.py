import dataclasses

import pygame


@dataclasses.dataclass
class GameState:
    player_position: pygame.Vector2 = dataclasses.field(
        default_factory=pygame.Vector2,
    )
    camera_offset: pygame.Vector2 = dataclasses.field(
        default_factory=pygame.Vector2,
    )
