import typing
from copy import deepcopy
from dataclasses import dataclass, field

import inject
from pygame import display
from pygame.math import Vector2

from alien_invasion.entities.sprites import Sprite, SpritesManager
from alien_invasion.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from alien_invasion.utils.game_state import GameState

if typing.TYPE_CHECKING:
    from pygame.rect import Rect
    from pygame.surface import Surface


@dataclass
class CameraGroup:
    target: Sprite
    bg: typing.Any
    offset: Vector2 = field(default_factory=Vector2, init=False)
    target_offset: Vector2 = field(default_factory=Vector2, init=False)
    smooth_factor: float = field(default=0.05, init=False)

    def update(self) -> None:
        game_state: GameState = inject.instance(GameState)

        self.target_offset.x = self.target.rect.centerx - SCREEN_WIDTH / 2
        self.target_offset.y = self.target.rect.centery - SCREEN_HEIGHT / 2

        self.offset.x += (self.target_offset.x - self.offset.x) * self.smooth_factor
        self.offset.y += (self.target_offset.y - self.offset.y) * self.smooth_factor

        game_state.camera_offset = self.offset

    def draw(self) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)
        display_surf: Surface | None = display.get_surface()

        self.bg.draw()

        for sprite in sprite_manager.sprites:
            offset_rect: Rect = deepcopy(sprite.rect)
            offset_rect.center -= self.offset
            if display_surf:
                display_surf.blit(sprite.image, offset_rect)


@dataclass
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
