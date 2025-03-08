from copy import deepcopy
from math import atan2, degrees
from threading import Timer

import inject
from pygame import K_DOWN, K_LEFT, K_RIGHT, K_UP, K_a, K_d, K_s, K_w, key, mouse
from pygame.math import Vector2

from alien_invasion.entities.sprites import Sprite, SpritesManager
from alien_invasion.entities.sprites.bullet import BulletBuilder
from alien_invasion.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from alien_invasion.utils.game_state import GameState


class Player(Sprite):
    def setup(self) -> None:
        self.can_shoot = True

    def input(self, dt: float) -> None:
        keys: key.ScancodeWrapper = key.get_pressed()
        self.direction = Vector2(
            (keys[K_RIGHT] or keys[K_d]) - (keys[K_LEFT] or keys[K_a]),
            (keys[K_DOWN] or keys[K_s]) - (keys[K_UP] or keys[K_w]),
        )

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
        sprite_manager.add(
            BulletBuilder()
            .set_whitelist([Player])
            .set_pos(deepcopy(self.pos))
            .set_angle(self.angle)
            .build(),
        )

    def update(self, dt: float) -> None:
        super().update(dt)
        game_state: GameState = inject.instance(GameState)
        game_state.player_pos = self.pos
