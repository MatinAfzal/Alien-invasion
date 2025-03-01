from dataclasses import dataclass

import pygame

from alien_invasion.entities.sprites.enemy import EnemyFactory
from alien_invasion.entities.sprites.player import Player, PlayerFactory
from alien_invasion.scenes.game_scene.world import World
from alien_invasion.utils.camera import CameraGroup


@dataclass
class GameScene:
    all_sprites = CameraGroup()

    def __post_init__(self) -> None:
        self.display_surf: pygame.Surface | None = pygame.display.get_surface()
        self.world = World()

        self.player: Player = PlayerFactory().create(pygame.Vector2(640, 360))
        self.all_sprites.add(self.player)

        self.all_sprites.add(EnemyFactory().create(pygame.Vector2(200, 200)))

    def run(self, dt: float) -> None:
        self.all_sprites.update(dt)
        if self.display_surf:
            self.all_sprites.draw(self.player, self.display_surf, self.world)
