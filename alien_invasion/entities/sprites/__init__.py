from copy import deepcopy
from enum import Enum
from dataclasses import dataclass, field
from math import copysign, cos, radians, sin
from pathlib import Path
from typing import TYPE_CHECKING, Self

import inject
from pygame import mask, transform
from pygame.math import Vector2
from pygame.surface import Surface

from alien_invasion.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Layer
from alien_invasion.utils import (
    load_surfaces_from_folder,
    load_surfaces_from_sheet,
)
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
        return Animation(
            load_surfaces_from_sheet(path, cols, rows),
            self.fps,
            self.loops,
        )


class SpriteState(Enum):
    ALIVE = 1
    DEAD = 2


@dataclass(kw_only=True)
class Sprite:
    size: tuple[int, int]
    animation: Animation

    on_die_animation: Animation | None = None
    z: int = Layer.ENTITIES.value
    init_pos: Vector2 = field(default_factory=Vector2)
    speed: int = 0
    angle: float = 0
    direction: Vector2 = field(default_factory=Vector2)
    apply_angle_to_movement: bool = False

    state: SpriteState = field(default=SpriteState.ALIVE, init=False)
    dead: bool = field(default=False, init=False)
    frame_idx: float = field(default=0, init=False)
    lock_position: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.__animation: Animation = deepcopy(self.animation)
        self.__speed: Vector2 = Vector2(self.speed, self.speed)
        self.rect: Rect = self.image.get_rect(center=self.init_pos)
        self.pos: Vector2 = deepcopy(self.init_pos)

        self.game_state: GameState = inject.instance(GameState)

        self.setup()

    @property
    def image(self) -> Surface:
        image: Surface = self.__animation.sprites[int(self.frame_idx)]
        image = transform.scale(image, self.size)
        return transform.rotate(image, self.angle)

    def setup(self) -> None: ...

    def input(self, dt: float) -> None: ...

    def move(self, dt: float) -> None:
        if self.lock_position:
            return

        if self.direction.magnitude():
            self.direction: Vector2 = self.direction.normalize()
        self.pos.x += self.direction.x * self.__speed.x * dt
        self.pos.y += self.direction.y * self.__speed.y * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.rect = self.image.get_rect(center=self.rect.center)

    def change_animation(self, animation: Animation) -> None:
        self.__animation = animation
        self.frame_idx = 0

    def kill(self) -> None:
        if self.state == SpriteState.DEAD:
            return

        self.state = SpriteState.DEAD
        self.lock_position = True
        if self.on_die_animation:
            self.change_animation(self.on_die_animation)

    def animate(self, dt: float) -> None:
        if not self.__animation or not self.__animation.sprites:
            return

        if self.state == SpriteState.DEAD:
            if (
                not self.on_die_animation
                or self.frame_idx >= len(self.__animation.sprites) - 1
            ):
                self.dead = True
                return

        self.frame_idx = (self.frame_idx + self.__animation.fps * dt) % len(
            self.__animation.sprites
        )

    def on_collision(self, sprite: Self) -> None: ...

    def __apply_angle_to_movement(self) -> None:
        angle: float = self.angle - 180
        direction: Vector2 = Vector2(cos(radians(angle)), sin(radians(angle)))
        speed = Vector2(
            abs(direction.x * self.speed), abs(direction.y * self.speed)
        )
        direction.x = copysign(1, direction.x) if direction.x != 0 else 0
        direction.y = -copysign(1, direction.y) if direction.y != 0 else 0

        self.__speed = speed
        self.direction = direction

    def update(self, dt: float) -> None:
        self.input(dt)
        self.move(dt)
        self.animate(dt)

        if self.apply_angle_to_movement:
            self.__apply_angle_to_movement()


@dataclass
class SpritesManager:
    sprites: list[Sprite] = field(default_factory=list, init=False)

    def add(self, sprite: Sprite) -> None:
        self.sprites.append(sprite)
        self.__sort_sprites()

    def remove(self, sprite: Sprite) -> None:
        for s in self.sprites:
            if s is sprite:
                self.sprites.remove(sprite)

    def check_collision(self) -> None:
        collisions: list[tuple[Sprite, Sprite]] = []

        for first_sprite in self.sprites:
            for second_sprite in self.sprites:
                if first_sprite is second_sprite:
                    continue

                mask1: Mask = mask.from_surface(first_sprite.image)
                mask2: Mask = mask.from_surface(second_sprite.image)

                offset: tuple[int, int] = (
                    second_sprite.rect.x - first_sprite.rect.x,
                    second_sprite.rect.y - first_sprite.rect.y,
                )

                if mask1.overlap(mask2, offset) is not None:
                    collisions.append((first_sprite, second_sprite))

        for first_sprite, second_sprite in collisions:
            first_sprite.on_collision(second_sprite)

    def update(self, dt: float) -> None:
        player_pos: Vector2 = inject.instance(GameState).player_pos
        offset = 400

        min_x: float = player_pos.x - SCREEN_WIDTH / 2 - offset
        max_x: float = player_pos.x + SCREEN_WIDTH + offset
        min_y: float = player_pos.y - SCREEN_HEIGHT / 2 - offset
        max_y: float = player_pos.y + SCREEN_HEIGHT + offset

        self.sprites = [
            sprite
            for sprite in self.sprites
            if min_x < sprite.pos.x < max_x
            and min_y < sprite.pos.y < max_y
            and not sprite.dead
        ]

        for sprite in self.sprites:
            sprite.update(dt)

        self.check_collision()

    def __sort_sprites(self) -> None:
        self.sprites = sorted(self.sprites, key=lambda x: (x.z, x.rect.center))

    def clear(self) -> None:
        self.sprites = []
