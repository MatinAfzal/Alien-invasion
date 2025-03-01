import copy
from dataclasses import dataclass

import inject
import pygame

from alien_invasion import settings
from alien_invasion.entities.sprites import Sprite
from alien_invasion.entities.sprites.player import Player
from alien_invasion.scenes.game_scene.world import World
from alien_invasion.sprite_manager import SpritesManager


@dataclass
class CameraGroup:
    offset = pygame.math.Vector2()
    target_offset = pygame.math.Vector2()
    smooth_factor = 0.05

    def add(self, sprite: Sprite) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.add(sprite)

    def update(self, dt: float) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.update(dt)

    def draw(self, player: Player, surf: pygame.Surface, world: World) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        self.target_offset.x = player.rect.centerx - settings.SCREEN_WIDTH / 2
        self.target_offset.y = player.rect.centery - settings.SCREEN_HEIGHT / 2

        self.offset.x += (self.target_offset.x - self.offset.x) * self.smooth_factor
        self.offset.y += (self.target_offset.y - self.offset.y) * self.smooth_factor

        world.draw(self.offset)

        for sprite in sprite_manager.sprites:
            offset_rect: pygame.Rect = copy.copy(sprite.rect.copy())
            offset_rect.center -= self.offset
            surf.blit(sprite.image, offset_rect)
