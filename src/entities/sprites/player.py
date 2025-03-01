import math

import inject
import pygame

from src import settings
from src.entities.sprites import Sprite
from src.entities.sprites.bullet import BulletFactory
from src.game_state import GameState
from src.sprite_manager import SpritesManager
from src.utils.timer import Timer


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

        x_dist: float = mouse_pos.x - settings.SCREEN_WIDTH / 2
        y_dist: float = -(mouse_pos.y - settings.SCREEN_HEIGHT / 2)

        target_angle: float = math.degrees(math.atan2(y_dist, x_dist))
        diff: float = (target_angle - self.angle) % 360 - 180
        self.angle += diff * 8 * dt

    def fire(self) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)
        sprite_manager.add(BulletFactory.create(self.pos, self.angle % 360))

    def update(self, dt: float) -> None:
        super().update(dt)
        game_state: GameState = inject.instance(GameState)
        game_state.player_position = self.pos


class PlayerFactory:
    SPEED = 300
    IMAGE_PATH = settings.ASSETS_DIR / "sprites" / "ship.png"
    LAYER = settings.GameLayer.GROUND.value

    @classmethod
    def create(cls, pos: pygame.Vector2) -> Player:
        return Player(cls.LAYER, pos, cls.IMAGE_PATH, (200, 200), pygame.Vector2(cls.SPEED, cls.SPEED))
