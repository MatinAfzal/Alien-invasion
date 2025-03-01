from dataclasses import dataclass

import pygame

from src import settings
from src.entities.sprites import SpriteAnimationFactory
from src.entities.sprites.player import Player, PlayerFactory
from src.scenes.game_scene.world import World
from src.utils.camera import CameraGroup


@dataclass
class GameScene:
    all_sprites = CameraGroup()

    def __post_init__(self) -> None:
        self.display_surf: pygame.Surface | None = pygame.display.get_surface()
        self.world = World()

        self.player: Player = PlayerFactory(
            SpriteAnimationFactory().load_from_sheet_file(
                settings.ASSETS_DIR / "sprites" / "ship.png",
                1,
                1,
            ),
        ).create(pygame.Vector2(640, 360))
        self.all_sprites.add(self.player)

    def run(self, dt: float) -> None:
        self.all_sprites.update(dt)
        self.all_sprites.draw(self.player, self.display_surf, self.world)
