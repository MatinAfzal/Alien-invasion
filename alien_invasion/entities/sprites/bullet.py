import dataclasses
from math import copysign, cos, radians, sin
from typing import TYPE_CHECKING

from pygame import Vector2

from alien_invasion.entities.sprites import Animation, AnimationFactory, Sprite
from alien_invasion.settings import ASSETS_DIR, Layer

if TYPE_CHECKING:
    from pathlib import Path


class Bullet(Sprite): ...


@dataclasses.dataclass
class BulletFactory:
    speed: int = 1000
    layer: int = Layer.ENTITIES.value

    def __post_init__(self) -> None:
        sheet_file_path: Path = ASSETS_DIR / "bullet-sheet.png"
        self.animation: Animation = AnimationFactory().load_from_sheet(sheet_file_path, 4, 1)

    def create(self, pos: Vector2, angle: float) -> Bullet:
        angle -= 180
        direction: Vector2 = Vector2(cos(radians(angle)), sin(radians(angle)))
        speed = Vector2(abs(direction.x * self.speed), abs(direction.y * self.speed))
        direction.x = copysign(1, direction.x) if direction.x != 0 else 0
        direction.y = -copysign(1, direction.y) if direction.y != 0 else 0
        return Bullet(self.layer, pos, self.animation, (64, 64), speed, angle + 180, direction)
