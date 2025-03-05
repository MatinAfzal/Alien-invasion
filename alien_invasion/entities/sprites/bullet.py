from math import copysign, cos, radians, sin
from threading import Timer
from typing import TYPE_CHECKING, Self

import inject
from pygame import Vector2

from alien_invasion.entities.sprites import Animation, AnimationFactory, Sprite, SpritesManager
from alien_invasion.settings import ASSETS_DIR, Layer

if TYPE_CHECKING:
    from pathlib import Path


class Bullet(Sprite):
    def __post_init__(self) -> None:
        super().__post_init__()
        self.whitelist: list[type] = []

    def on_collision(self, sprite: Sprite) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        for sprite_type in self.whitelist:
            if isinstance(sprite, sprite_type):
                return

        Timer(0.1, lambda: sprite_manager.remove(self)).start()


class BulletBuilder:
    def __init__(self) -> None:
        self.init_speed = 1400
        layer: int = Layer.ENTITIES.value
        pos = Vector2(0, 0)
        sheet_file_path: Path = ASSETS_DIR / "bullet_sheet.png"
        animation: Animation = AnimationFactory().load_from_sheet(sheet_file_path, 4, 1)
        angle = 0
        direction: Vector2 = Vector2(cos(radians(angle)), sin(radians(angle)))
        speed = Vector2(abs(direction.x * self.init_speed), abs(direction.y * self.init_speed))
        direction.x = copysign(1, direction.x) if direction.x != 0 else 0
        direction.y = -copysign(1, direction.y) if direction.y != 0 else 0
        self.bullet = Bullet(layer, pos, animation, (64, 64), speed, angle + 180, direction)

    def set_whitelist(self, sprite_type: list[type]) -> Self:
        self.bullet.whitelist = sprite_type
        return self

    def set_pos(self, pos: Vector2) -> Self:
        self.bullet.pos = pos
        return self

    def set_speed(self, speed: int) -> Self:
        self.init_speed: int = speed
        return self

    def set_angle(self, angle: float) -> Self:
        self.bullet.angle = angle
        angle -= 180
        direction: Vector2 = Vector2(cos(radians(angle)), sin(radians(angle)))
        speed = Vector2(abs(direction.x * self.init_speed), abs(direction.y * self.init_speed))
        direction.x = copysign(1, direction.x) if direction.x != 0 else 0
        direction.y = -copysign(1, direction.y) if direction.y != 0 else 0

        self.bullet.speed = speed
        self.bullet.direction = direction

        return self

    def build(self) -> Bullet:
        return self.bullet
