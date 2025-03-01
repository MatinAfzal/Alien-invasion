import math
from dataclasses import dataclass

import inject
import pygame

from alien_invasion import settings
from alien_invasion.entities.sprites import Sprite, SpriteAnimationFactory
from alien_invasion.game_state import GameState
from alien_invasion.utils import get_direction_by_angle


class Enemy(Sprite):
    def update(self, dt: float) -> None:
        super().update(dt)
        game_state: GameState = inject.instance(GameState)

        x_dist: float = game_state.player_position.x - self.pos.x
        y_dist: float = -(game_state.player_position.y - self.pos.y)

        self.angle = math.degrees(math.atan2(y_dist, x_dist))
        self.direction = get_direction_by_angle(self.angle)

        self.speed = pygame.Vector2(
            abs(self.direction.x * self.init_speed.x),
            abs(self.direction.y * self.init_speed.y),
        )

        self.direction.x = math.copysign(1, self.direction.x) if self.direction.x != 0 else 0
        self.direction.y = -math.copysign(1, self.direction.y) if self.direction.y != 0 else 0

        self.angle -= 180


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
