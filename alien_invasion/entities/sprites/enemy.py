import math
from dataclasses import dataclass

import inject
import pygame

from alien_invasion import settings
from alien_invasion.entities.sprites import Sprite, SpriteAnimationFactory
from alien_invasion.game_state import GameState


class Enemy(Sprite):
    def update(self, dt: float) -> None:
        super().update(dt)
        game_state: GameState = inject.instance(GameState)

        delta_x: float = game_state.player_position.x - self.pos.x
        delta_y: float = self.pos.y - game_state.player_position.y

        target_angle: float = math.degrees(math.atan2(delta_y, delta_x))

        direction = pygame.Vector2(
            math.cos(math.radians(target_angle)),
            math.sin(math.radians(target_angle)),
        )

        self.speed = pygame.Vector2(
            abs(direction.x * self.init_speed.x),
            abs(direction.y * self.init_speed.y),
        )

        self.direction.x = math.copysign(1, direction.x) if direction.x else 0
        self.direction.y = -math.copysign(1, direction.y) if direction.y else 0

        self.angle = target_angle - 180


@dataclass
class EnemyFactory:
    speed = 500
    layer: int = settings.GameLayer.GROUND.value

    def create(self, pos: pygame.Vector2) -> Enemy:
        return Enemy(
            self.layer,
            pos,
            SpriteAnimationFactory().load_from_sheet_file(
                settings.ASSETS_DIR / "enemy.png",
                1,
                1,
            ),
            (200, 200),
            pygame.Vector2((self.speed, self.speed)),
        )
