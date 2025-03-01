import math
from dataclasses import dataclass

import pygame

from alien_invasion import settings
from alien_invasion.entities.sprites import Sprite, SpriteAnimation, SpriteAnimationFactory
from alien_invasion.utils import get_direction_by_angle


class Bullet(Sprite): ...


@dataclass
class BulletFactory:
    speed: int = 1000
    layer: int = settings.GameLayer.GROUND.value

    def __post_init__(self) -> None:
        self.animation: SpriteAnimation = SpriteAnimationFactory().load_from_sheet_file(
            settings.ASSETS_DIR / "bullet-sheet.png",
            4,
            1,
        )

    def create(self, pos: pygame.Vector2, angle: float) -> Bullet:
        angle -= 180
        direction: pygame.Vector2 = get_direction_by_angle(angle)
        speed = pygame.Vector2(
            abs(direction.x * self.speed),
            abs(direction.y * self.speed),
        )
        direction.x = math.copysign(1, direction.x) if direction.x != 0 else 0
        direction.y = -math.copysign(1, direction.y) if direction.y != 0 else 0
        return Bullet(
            self.layer,
            pos,
            self.animation,
            (64, 64),
            speed,
            angle + 180,
            direction,
        )
