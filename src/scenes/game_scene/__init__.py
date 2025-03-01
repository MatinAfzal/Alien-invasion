from dataclasses import dataclass, field

import pygame

from src.entities.sprites.player import PlayerFactory
from src.scenes.game_scene.world import World
from src.utils.camera import CameraGroup


@dataclass
class GameScene:
    display_surf: pygame.Surface = field(default_factory=pygame.display.get_surface)
    all_sprites = CameraGroup()

    def __post_init__(self) -> None:
        self.world = World()

        self.player = PlayerFactory.create(pygame.Vector2(640, 360))
        self.all_sprites.add(self.player)

    def run(self, dt: float) -> None:
        self.all_sprites.update(dt)
        self.all_sprites.draw(self.player, self.display_surf, self.world)
