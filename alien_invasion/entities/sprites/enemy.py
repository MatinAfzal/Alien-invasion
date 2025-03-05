from copy import deepcopy
from math import atan2, copysign, cos, degrees, radians, sin
from secrets import choice, randbelow
from threading import Timer
from typing import TYPE_CHECKING, Self

import inject
from pygame.math import Vector2

from alien_invasion.entities.sprites import Animation, AnimationFactory, Sprite, SpritesManager
from alien_invasion.entities.sprites.bullet import BulletBuilder
from alien_invasion.settings import ASSETS_DIR, SCREEN_HEIGHT, SCREEN_WIDTH, Layer
from alien_invasion.utils.game_state import GameState

if TYPE_CHECKING:
    from pathlib import Path


class Enemy(Sprite):
    def __post_init__(self) -> None:
        super().__post_init__()
        Timer(3, self.fire).start()

    def update(self, dt: float) -> None:
        super().update(dt)

        game_state: GameState = inject.instance(GameState)

        delta_x: float = game_state.player_pos.x - self.pos.x
        delta_y: float = self.pos.y - game_state.player_pos.y

        target_angle: float = degrees(atan2(delta_y, delta_x))

        direction = Vector2(cos(radians(target_angle)), sin(radians(target_angle)))

        self.speed = Vector2(abs(direction.x * self.init_speed.x), abs(direction.y * self.init_speed.y))

        self.direction.x = copysign(1, direction.x) if direction.x else 0
        self.direction.y = -copysign(1, direction.y) if direction.y else 0

        if not self.lock_position:
            self.angle = target_angle - 180

    def on_collision(self, sprite: Sprite) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sheet_file_path: Path = ASSETS_DIR / "enemy_destruction.png"
        animation: Animation = AnimationFactory(fps=24).load_from_sheet(sheet_file_path, 9, 1)

        self.lock_position = True
        self.animation = animation
        Timer(0.32, lambda: sprite_manager.remove(self)).start()

    def fire(self) -> None:
        if self.lock_position:
            return

        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.add(
            BulletBuilder().set_whitelist([Enemy]).set_pos(deepcopy(self.pos)).set_angle(self.angle).build()
        )


class EnemyBuilder:
    def __init__(self) -> None:
        layer = Layer.ENTITIES.value
        sheet_file_path: Path = ASSETS_DIR / "enemy.png"
        animation: Animation = AnimationFactory().load_from_sheet(sheet_file_path, 1, 1)
        speed = Vector2(600, 600)
        self.enemy = Enemy(layer, Vector2(0, 0), animation, (200, 200), speed)

    def set_pos(self, pos: Vector2) -> Self:
        self.enemy.pos = pos
        return self

    def set_speed(self, speed: int) -> Self:
        self.enemy.speed = Vector2(speed, speed)
        return self

    def build(self) -> Enemy:
        return self.enemy


class EnemyFactory:
    @staticmethod
    def get_enemy() -> Enemy:
        player_pos: Vector2 = inject.instance(GameState).player_pos

        x1: float = player_pos.x - SCREEN_WIDTH // 2 - 400
        x2: float = player_pos.x + SCREEN_WIDTH // 2 + 400
        y1: float = player_pos.y + SCREEN_HEIGHT // 2 + 400
        y2: float = player_pos.y - SCREEN_HEIGHT // 2 - 400

        edges: list[str] = ["top", "bottom", "left", "right"]
        edge: str = choice(edges)  # انتخاب یک ضلع به‌صورت امن

        if edge == "top":
            x: float = x1 + (x2 - x1) * randbelow(10**6) / 10**6
            y: float = y1
        elif edge == "bottom":
            x = x1 + (x2 - x1) * randbelow(10**6) / 10**6
            y = y2
        elif edge == "left":
            x = x1
            y = y1 + (y2 - y1) * randbelow(10**6) / 10**6
        else:
            x = x2
            y = y1 + (y2 - y1) * randbelow(10**6) / 10**6

        return EnemyBuilder().set_pos(Vector2(int(x), int(y))).build()
