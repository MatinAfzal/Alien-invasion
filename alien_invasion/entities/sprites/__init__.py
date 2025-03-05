from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import inject
from pygame import mask, transform
from pygame.math import Vector2
from pygame.surface import Surface

from alien_invasion.settings import SCREEN_HEIGHT, SCREEN_WIDTH
from alien_invasion.utils import load_surfaces_from_folder, load_surfaces_from_sheet
from alien_invasion.utils.game_state import GameState

if TYPE_CHECKING:
    from pygame.mask import Mask
    from pygame.rect import Rect


@dataclass
class Animation:
    sprites: list[Surface] = field(default_factory=list)
    fps: int = 8
    loops: int | None = None


@dataclass
class AnimationFactory:
    fps: int = 8
    loops: int = -1

    def load_from_folder(self, path: Path) -> Animation:
        return Animation(load_surfaces_from_folder(path), self.fps, self.loops)

    def load_from_sheet(self, path: Path, cols: int, rows: int) -> Animation:
        return Animation(load_surfaces_from_sheet(path, cols, rows), self.fps, self.loops)


@dataclass
class Sprite:
    z: int
    init_pos: Vector2
    init_animation: Animation
    size: tuple[int, int]
    init_speed: Vector2
    angle: float = 0
    direction: Vector2 = field(default_factory=Vector2)

    frame_idx: float = field(default=0, init=False)

    def __post_init__(self) -> None:
        super().__init__()
        self.animation: Animation = deepcopy(self.init_animation)
        self.speed: Vector2 = self.init_speed
        self.rect: Rect = self.image.get_rect(center=self.init_pos)
        self.pos: Vector2 = deepcopy(self.init_pos)
        self.lock_position = False

        self.setup()

    @property
    def image(self) -> Surface:
        image: Surface = self.animation.sprites[int(self.frame_idx)]
        image = transform.scale(image, self.size)
        return transform.rotate(image, self.angle)

    def setup(self) -> None: ...

    def input(self, dt: float) -> None: ...

    def move(self, dt: float) -> None:
        if self.lock_position:
            return

        if self.direction.magnitude():
            self.direction: Vector2 = self.direction.normalize()
        self.pos.x += self.direction.x * self.speed.x * dt
        self.pos.y += self.direction.y * self.speed.y * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.rect = self.image.get_rect(center=self.rect.center)

    def change_animation(self, animation: Animation) -> None:
        self.animation = animation

    def animate(self, dt: float) -> None:
        if not self.animation:
            return

        self.frame_idx = (self.frame_idx + self.animation.fps * dt) % len(self.animation.sprites)

    def check_collision(self) -> None:
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        try:
            for sprite in sprite_manager.sprites:
                if sprite is self:
                    continue

                mask1: Mask = mask.from_surface(self.image)
                mask2: Mask = mask.from_surface(sprite.image)

                offset: tuple[int, int] = (sprite.rect.x - self.rect.x, sprite.rect.y - self.rect.y)

                if mask1.overlap(mask2, offset) is not None:
                    self.on_collision(sprite)
        except NotImplementedError:
            return

    def on_collision(self, sprite: "Sprite") -> None:
        raise NotImplementedError

    def update(self, dt: float) -> None:
        self.check_collision()
        self.input(dt)
        self.move(dt)
        self.animate(dt)


@dataclass
class SpritesManager:
    sprites: list[Sprite] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.__sort_sprites()

    def add(self, sprite: Sprite) -> None:
        self.sprites.append(sprite)
        self.__sort_sprites()

    def remove(self, sprite: Sprite) -> None:
        for s in self.sprites:
            if s is sprite:
                self.sprites.remove(sprite)

    def update(self, dt: float) -> None:
        player_pos: Vector2 = inject.instance(GameState).player_pos
        offset = 400

        min_x: float = player_pos.x - SCREEN_WIDTH / 2 - offset
        max_x: float = player_pos.x + SCREEN_WIDTH + offset
        min_y: float = player_pos.y - SCREEN_HEIGHT / 2 - offset
        max_y: float = player_pos.y + SCREEN_HEIGHT + offset

        self.sprites = [
            sprite for sprite in self.sprites if min_x < sprite.pos.x < max_x and min_y < sprite.pos.y < max_y
        ]

        for sprite in self.sprites:
            sprite.update(dt)

    def __sort_sprites(self) -> None:
        self.sprites = sorted(self.sprites, key=lambda x: (x.z, x.rect.center))

    def clear(self) -> None:
        self.sprites = []
