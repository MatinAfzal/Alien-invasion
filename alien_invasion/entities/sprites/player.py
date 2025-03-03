from dataclasses import dataclass
from math import atan2, degrees
from threading import Timer
from typing import TYPE_CHECKING

import inject
from pygame import K_DOWN, K_LEFT, K_RIGHT, K_UP, K_a, K_d, K_s, K_w, key, mouse
from pygame.math import Vector2

from alien_invasion.entities.sprites import Animation, AnimationFactory, Sprite, SpritesManager
from alien_invasion.entities.sprites.bullet import BulletFactory
from alien_invasion.settings import ASSETS_DIR, SCREEN_HEIGHT, SCREEN_WIDTH, Layer
from alien_invasion.utils.game_state import GameState

if TYPE_CHECKING:
    from pathlib import Path


class Player(Sprite):
    def setup(self) -> None:
        self.can_shoot = True

    def input(self, dt: float) -> None:
        self.direction = Vector2(0, 0)

        keys: key.ScancodeWrapper = key.get_pressed()
        if keys[K_UP] or keys[K_w]:
            self.direction.y -= 1
        if keys[K_DOWN] or keys[K_s]:
            self.direction.y += 1

        if keys[K_RIGHT] or keys[K_d]:
            self.direction.x += 1
        if keys[K_LEFT] or keys[K_a]:
            self.direction.x -= 1

        if mouse.get_pressed()[0] and self.can_shoot:
            self.can_shoot = False
            Timer(0.7, lambda: setattr(self, "can_shoot", True)).start()
            self.fire()

        mouse_pos = Vector2(mouse.get_pos())

        delta_x: float = mouse_pos.x - SCREEN_WIDTH / 2
        delta_y: float = -(mouse_pos.y - SCREEN_HEIGHT / 2)

        target_angle: float = degrees(atan2(delta_y, delta_x))
        diff: float = (target_angle - self.angle) % 360 - 180
        self.angle += diff * 8 * dt

    def fire(self) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)
        sprite_manager.add(BulletFactory().create(self.pos, self.angle % 360))

    def on_collision(self, sprite: Sprite) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.remove(self)

    def update(self, dt: float) -> None:
        super().update(dt)
        game_state: GameState = inject.instance(GameState)
        game_state.player_position = self.pos


@dataclass
class PlayerFactory:
    speed: int = 300
    layer: int = Layer.ENTITIES.value

    def create(self, pos: Vector2) -> Player:
        sheet_file_path: Path = ASSETS_DIR / "ship.png"
        animation: Animation = AnimationFactory().load_from_sheet(sheet_file_path, 1, 1)
        speed = Vector2(self.speed, self.speed)
        return Player(self.layer, pos, animation, (200, 200), speed)
