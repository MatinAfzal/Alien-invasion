from typing import Any

import pygame

from src import settings
from src.entities.sprites.player import Player
from src.scenes.game_scene.world import World


class CameraGroup(pygame.sprite.Group):  # type: ignore  # noqa: PGH003
    def __init__(self, *sprites: pygame.sprite.Sprite) -> None:
        super().__init__(*sprites)  # type: ignore  # noqa: PGH003
        self.offset = pygame.math.Vector2()
        self.target_offset = pygame.math.Vector2()
        self.smooth_factor = 0.05

    def custom_draw(self, player: Player, surf: pygame.Surface, world: World) -> None:
        self.target_offset.x = player.rect.centerx - settings.SCREEN_WIDTH / 2
        self.target_offset.y = player.rect.centery - settings.SCREEN_HEIGHT / 2

        self.offset.x += (self.target_offset.x - self.offset.x) * self.smooth_factor
        self.offset.y += (self.target_offset.y - self.offset.y) * self.smooth_factor

        world.draw(self.offset)

        for sprite in self.sprites():
            # offset_rect: pygame.Rect = sprite.rect.copy()
            # offset_rect.center -= self.offset
            # surf.blit(sprite.image, offset_rect)
            sprite.offset = self.offset
