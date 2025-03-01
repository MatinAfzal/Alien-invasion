import math
from pathlib import Path

from pygame import Vector2

from src import settings
from src.entities.sprites import Sprite


class Bullet(Sprite): ...


class BulletFactory:
    SPEED = 1000
    IMAGE_PATH: Path = settings.ASSETS_DIR / "sprites" / "bullet.png"
    LAYER = settings.GameLayer.GROUND.value

    @classmethod
    def create(cls, pos: Vector2, angle: float) -> Bullet:
        angle -= 180
        direction = Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
        speed = Vector2(abs(direction.x * cls.SPEED), abs(direction.y * cls.SPEED))
        direction.x = math.copysign(1, direction.x) if direction.x != 0 else 0
        direction.y = -math.copysign(1, direction.y) if direction.y != 0 else 0
        return Bullet(cls.LAYER, pos, cls.IMAGE_PATH, (40, 40), speed, angle + 180, direction)
