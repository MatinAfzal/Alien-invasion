from threading import Timer
from typing import Self

import inject
from pygame import Vector2

from alien_invasion.entities.sprites import (
    AnimationFactory,
    Sprite,
    SpritesManager,
)
from alien_invasion.settings import ASSETS_DIR


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
        self.bullet = Bullet(
            animation=AnimationFactory().load_from_sheet(
                ASSETS_DIR / "bullet_sheet.png",
                4,
                1,
            ),
            size=(32, 32),
            speed=1400,
            apply_angle_to_movement=True,
        )

    def set_whitelist(self, sprite_type: list[type]) -> Self:
        self.bullet.whitelist = sprite_type
        return self

    def set_pos(self, pos: Vector2) -> Self:
        self.bullet.pos = pos
        return self

    def set_speed(self, speed: int) -> Self:
        self.bullet.speed = speed
        return self

    def set_angle(self, angle: float) -> Self:
        self.bullet.angle = angle

        return self

    def build(self) -> Bullet:
        return self.bullet
