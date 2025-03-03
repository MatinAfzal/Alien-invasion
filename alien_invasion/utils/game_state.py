from dataclasses import dataclass, field

from pygame.math import Vector2


@dataclass
class GameState:
    player_position: Vector2 = field(default_factory=Vector2)
    camera_offset: Vector2 = field(default_factory=Vector2)
    is_game_over: bool = False
