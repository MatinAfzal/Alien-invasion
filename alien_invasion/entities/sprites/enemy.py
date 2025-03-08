from copy import deepcopy
from math import atan2, degrees
from secrets import choice, randbelow
from threading import Timer
from typing import Self

import inject
from pygame.math import Vector2

from alien_invasion.entities.sprites import (
    AnimationFactory,
    Sprite,
    SpritesManager,
)
from alien_invasion.entities.sprites.bullet import Bullet, BulletBuilder
from alien_invasion.entities.sprites.player import Player
from alien_invasion.settings import ASSETS_DIR, SCREEN_HEIGHT, SCREEN_WIDTH
from alien_invasion.utils.game_state import GameState


class Enemy(Sprite):
    def __post_init__(self) -> None:
        super().__post_init__()
        Timer(3, self.fire).start()

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.lock_position:
            return

        game_state: GameState = inject.instance(GameState)

        delta_x: float = game_state.player_pos.x - self.pos.x
        delta_y: float = self.pos.y - game_state.player_pos.y

        target_angle: float = degrees(atan2(delta_y, delta_x))

        self.angle = target_angle - 180

    def on_collision(self, sprite: Sprite) -> None:
        if (
            isinstance(sprite, Bullet) and type(self) not in sprite.whitelist
        ) or isinstance(
            sprite,
            Player | type(self),
        ):
            self.kill()

    def fire(self) -> None:
        if self.lock_position:
            return

        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.add(
            BulletBuilder()
            .set_whitelist([Enemy])
            .set_pos(deepcopy(self.pos))
            .set_angle(self.angle)
            .build(),
        )


class EnemyBuilder:
    def __init__(self) -> None:
        self.enemy = Enemy(
            animation=AnimationFactory().load_from_sheet(
                ASSETS_DIR / "enemy.png",
                1,
                1,
            ),
            on_die_animation=AnimationFactory(fps=24).load_from_sheet(
                ASSETS_DIR / "enemy_destruction.png",
                9,
                1,
            ),
            size=(200, 200),
            speed=600,
            apply_angle_to_movement=True,
        )

    def set_pos(self, pos: Vector2) -> Self:
        self.enemy.pos = pos
        return self

    def set_speed(self, speed: int) -> Self:
        self.enemy.speed = speed
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
        edge: str = choice(edges)

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
