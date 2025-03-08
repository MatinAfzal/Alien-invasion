from dataclasses import dataclass
from secrets import randbelow
from typing import TYPE_CHECKING

import inject
from pygame import Rect, display, image, transform
from pygame.math import Vector2

from alien_invasion.entities.sprites import SpritesManager, AnimationFactory
from alien_invasion.entities.sprites.enemy import EnemyFactory
from alien_invasion.entities.sprites.player import Player
from alien_invasion.scenes import Scene
from alien_invasion.settings import (
    ASSETS_DIR,
    ENEMY_SPAWN_CHANCE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from alien_invasion.utils.game_state import GameState

if TYPE_CHECKING:
    from pathlib import Path

    from pygame.surface import Surface


@dataclass
class SpaceBG:
    def __post_init__(self) -> None:
        image_path: Path = ASSETS_DIR / "bg.png"
        self.image: Surface = transform.scale(
            image.load(image_path), (640, 640)
        ).convert()
        self.rect: Rect = self.image.get_rect(topleft=(0, 0))

    def draw(self) -> None:
        camera_offset: Vector2 = inject.instance(GameState).camera_offset
        display_surf: Surface | None = display.get_surface()

        if not display_surf:
            return

        img_width: int = self.image.get_size()[0]
        img_height: int = self.image.get_size()[1]

        for x in range(-img_width, SCREEN_WIDTH + img_width, img_width):
            for y in range(-img_height, SCREEN_HEIGHT + img_height, img_height):
                display_surf.blit(
                    self.image,
                    (
                        x - camera_offset.x % img_width,
                        y - camera_offset.y % img_height,
                    ),
                )


class GameScene(Scene):
    def __init__(self) -> None:
        super().__init__(
            Player(
                animation=AnimationFactory().load_from_sheet(
                    ASSETS_DIR / "ship.png",
                    1,
                    1,
                ),
                init_pos=Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                size=(160, 160),
                speed=300,
                angle=0,
            ),
            SpaceBG(),
        )

    def run(self, dt: float) -> None:
        super().run(dt)
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        if randbelow(100) < (ENEMY_SPAWN_CHANCE * 100):
            sprite_manager.add(EnemyFactory.get_enemy())
