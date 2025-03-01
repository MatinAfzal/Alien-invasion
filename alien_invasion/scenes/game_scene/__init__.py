from dataclasses import dataclass

import inject
import pygame

from alien_invasion.entities.sprites.enemy import EnemyFactory
from alien_invasion.entities.sprites.player import Player, PlayerFactory
from alien_invasion.scenes.game_scene.world import World
from alien_invasion.sprite_manager import SpritesManager
from alien_invasion.utils.camera import CameraGroup


@dataclass
class GameScene:
    def __post_init__(self) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.clear()

        self.world = World()
        self.camera = CameraGroup(self.world)

        self.player: Player = PlayerFactory().create(pygame.Vector2(640, 360))
        sprite_manager.add(self.player)

        sprite_manager.add(EnemyFactory().create(pygame.Vector2(200, 200)))

    def run(self, dt: float) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.update(dt)

        self.camera.update(self.player)
        self.camera.draw()
