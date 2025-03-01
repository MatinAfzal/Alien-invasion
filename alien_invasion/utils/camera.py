import copy
from dataclasses import dataclass

import inject
import pygame

from alien_invasion import settings
from alien_invasion.entities.sprites import Sprite
from alien_invasion.game_state import GameState
from alien_invasion.scenes.game_scene.world import World
from alien_invasion.sprite_manager import SpritesManager


@dataclass
class CameraGroup:
    bg: World
    offset = pygame.math.Vector2()
    target_offset = pygame.math.Vector2()
    smooth_factor = 0.05

    def update(self, target: Sprite) -> None:
        game_state: GameState = inject.instance(GameState)

        self.target_offset.x = target.rect.centerx - settings.SCREEN_WIDTH / 2
        self.target_offset.y = target.rect.centery - settings.SCREEN_HEIGHT / 2

        self.offset.x += (self.target_offset.x - self.offset.x) * self.smooth_factor
        self.offset.y += (self.target_offset.y - self.offset.y) * self.smooth_factor

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
