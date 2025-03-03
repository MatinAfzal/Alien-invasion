from dataclasses import dataclass
from math import atan2, copysign, cos, degrees, radians, sin
from typing import TYPE_CHECKING

import inject
from pygame.math import Vector2

from alien_invasion.entities.sprites import Animation, AnimationFactory, Sprite
from alien_invasion.settings import ASSETS_DIR, Layer
from alien_invasion.utils.game_state import GameState

if TYPE_CHECKING:
    from pathlib import Path


class Enemy(Sprite):
    def update(self, dt: float) -> None:
        super().update(dt)
        game_state: GameState = inject.instance(GameState)

        delta_x: float = game_state.player_position.x - self.pos.x
        delta_y: float = self.pos.y - game_state.player_position.y

        target_angle: float = degrees(atan2(delta_y, delta_x))

        direction = Vector2(
            cos(radians(target_angle)),
            sin(radians(target_angle)),
        )

        self.speed = Vector2(
            abs(direction.x * self.init_speed.x),
            abs(direction.y * self.init_speed.y),
        )

        self.direction.x = copysign(1, direction.x) if direction.x else 0
        self.direction.y = -copysign(1, direction.y) if direction.y else 0

        self.angle = target_angle - 180


@dataclass
class EnemyFactory:
    speed = 500
    layer: int = Layer.ENTITIES.value

    def create(self, pos: Vector2) -> Enemy:
        sheet_file_path: Path = ASSETS_DIR / "enemy.png"
        animation: Animation = AnimationFactory().load_from_sheet(sheet_file_path, 1, 1)
        speed = Vector2((self.speed, self.speed))
        return Enemy(self.layer, pos, animation, (200, 200), speed)
