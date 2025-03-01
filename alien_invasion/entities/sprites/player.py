import math
from dataclasses import dataclass

import inject
import pygame

from alien_invasion import settings
from alien_invasion.entities.sprites import Sprite, SpriteAnimationFactory
from alien_invasion.entities.sprites.bullet import BulletFactory
from alien_invasion.utils.game_state import GameState
from alien_invasion.utils.sprite_manager import SpritesManager
from alien_invasion.utils.timer import Timer


class Player(Sprite):
    def setup(self) -> None:
        self.fire_timer = Timer(700)
        self.register_timer(self.fire_timer)

    def input(self, dt: float) -> None:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction.y = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
        else:
            self.direction.x = 0

        if pygame.mouse.get_pressed()[0] and not self.fire_timer.active:
            self.fire_timer.activate()
            self.fire()

        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())

        delta_x: float = mouse_pos.x - settings.SCREEN_WIDTH / 2
        delta_y: float = -(mouse_pos.y - settings.SCREEN_HEIGHT / 2)

        target_angle: float = math.degrees(math.atan2(delta_y, delta_x))
        diff: float = (target_angle - self.angle) % 360 - 180
        self.angle += diff * 8 * dt

    def fire(self) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)
        sprite_manager.add(BulletFactory().create(self.pos, self.angle % 360))

    def update(self, dt: float) -> None:
        super().update(dt)
        game_state: GameState = inject.instance(GameState)
        game_state.player_position = self.pos


@dataclass
class PlayerFactory:
    speed: int = 300
    layer: int = settings.Layer.ENTITIES.value

    def create(self, pos: pygame.Vector2) -> Player:
        return Player(
            self.layer,
            pos,
            SpriteAnimationFactory().load_from_sheet_file(
                settings.ASSETS_DIR / "ship.png",
                1,
                1,
            ),
            (200, 200),
            pygame.Vector2(self.speed, self.speed),
        )
