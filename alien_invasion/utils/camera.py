import copy
import typing
from dataclasses import dataclass, field

import inject
import pygame

from alien_invasion import settings
from alien_invasion.entities.sprites import Sprite
from alien_invasion.utils.game_state import GameState
from alien_invasion.utils.sprite_manager import SpritesManager

SMOOTH_FACTOR = 0.05


@dataclass
class CameraGroup:
    bg: typing.Any
    offset: pygame.Vector2 = field(
        default_factory=pygame.math.Vector2,
        init=False,
    )
    target_offset: pygame.Vector2 = field(
        default_factory=pygame.math.Vector2,
        init=False,
    )
    smooth_factor: float = field(default=SMOOTH_FACTOR, init=False)

    def update(self, target: Sprite) -> None:
        game_state: GameState = inject.instance(GameState)

        self.target_offset.x = target.rect.centerx - settings.SCREEN_WIDTH / 2
        self.target_offset.y = target.rect.centery - settings.SCREEN_HEIGHT / 2

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
