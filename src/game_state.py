from dataclasses import dataclass, field

from pygame import Vector2


@dataclass
class GameState:
    player_position: Vector2 = field(default_factory=lambda: Vector2(0, 0))
