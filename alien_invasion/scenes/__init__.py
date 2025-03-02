import copy
import dataclasses
import typing

import inject
import pygame

from alien_invasion import settings
from alien_invasion.entities.sprites import Sprite
from alien_invasion.utils.game_state import GameState
from alien_invasion.utils.sprite_manager import SpritesManager


@dataclasses.dataclass
class CameraGroup:
    target: Sprite
    bg: typing.Any
    offset: pygame.Vector2 = dataclasses.field(
        default_factory=pygame.math.Vector2,
        init=False,
    )
    target_offset: pygame.Vector2 = dataclasses.field(
        default_factory=pygame.math.Vector2,
        init=False,
    )
    smooth_factor: float = dataclasses.field(default=0.05, init=False)

    def update(self) -> None:
        game_state: GameState = inject.instance(GameState)

        self.target_offset.x = (
            self.target.rect.centerx - settings.SCREEN_WIDTH / 2
        )
        self.target_offset.y = (
            self.target.rect.centery - settings.SCREEN_HEIGHT / 2
        )

        self.offset.x += (
            self.target_offset.x - self.offset.x
        ) * self.smooth_factor
        self.offset.y += (
            self.target_offset.y - self.offset.y
        ) * self.smooth_factor

        game_state.camera_offset = self.offset

    def draw(self) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)
        display_surf: pygame.Surface | None = pygame.display.get_surface()

        self.bg.draw()

        for sprite in sprite_manager.sprites:
            offset_rect: pygame.Rect = copy.copy(sprite.rect.copy())
            offset_rect.center -= self.offset
            if display_surf:
                display_surf.blit(sprite.image, offset_rect)


@dataclasses.dataclass
class Scene:
    camera_target: Sprite
    bg: typing.Any

    def __post_init__(self) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.clear()

        sprite_manager.add(self.camera_target)

        self.camera = CameraGroup(self.camera_target, self.bg)

    def run(self, dt: float) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.update(dt)

        self.camera.update()
        self.camera.draw()
