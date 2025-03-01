from dataclasses import dataclass, field
from pathlib import Path

import pygame

from src.utils import load_surfaces_from_sheet
from src.utils.timer import Timer


@dataclass
class SpriteAnimation:
    sprites: list[pygame.Surface] = field(default_factory=list)
    fps: int = 1
    loops: int | None = None


class SpriteAnimationFactory:
    @staticmethod
    def load_from_folder(path: Path, fps: int = 1, loops: int = -1) -> SpriteAnimation:
        return SpriteAnimation(
            [pygame.image.load(Path.resolve(file)).convert_alpha() for file in path.iterdir()],
            fps,
            loops,
        )

    @staticmethod
    def load_from_sheet_file(path: Path, cols: int, rows: int, fps: int = 1, loops: int = -1) -> SpriteAnimation:
        return SpriteAnimation(load_surfaces_from_sheet(path, cols, rows), fps, loops)


@dataclass
class Sprite:
    z: int
    init_pos: pygame.math.Vector2
    image_path: Path
    scale: tuple[int, int]
    speed: pygame.Vector2
    angle: float = 0
    direction: pygame.Vector2 = field(default_factory=pygame.Vector2)

    def __post_init__(self) -> None:
        super().__init__()
        self.original_image: pygame.Surface = pygame.transform.scale(pygame.image.load(self.image_path), self.scale)
        self.image: pygame.Surface = self.original_image.copy()
        self.rect: pygame.Rect = self.image.get_rect(center=self.init_pos)
        self.pos: pygame.Vector2 = self.init_pos.copy()

        self.animation: SpriteAnimation | None = None
        self.framd_idx: float = 0

        self.__timers: list[Timer] = []

        self.setup()

    def setup(self) -> None: ...

    def input(self, dt: float) -> None: ...

    def move(self, dt: float) -> None:
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        if self.direction.magnitude():
            self.direction: pygame.Vector2 = self.direction.normalize()
        self.pos.x += self.direction.x * self.speed.x * dt
        self.pos.y += self.direction.y * self.speed.y * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.rect = self.image.get_rect(center=self.rect.center)

    def register_timer(self, timer: Timer) -> None:
        self.__timers.append(timer)

    def update_timers(self) -> None:
        for timer in self.__timers:
            timer.update()

    def change_animation(self, animation: SpriteAnimation) -> None:
        self.animation = animation

    def animate(self, dt: float) -> None:
        if not self.animation:
            return

        self.framd_idx = (self.framd_idx + self.animation.fps * dt) % len(self.animation.sprites)

    def update(self, dt: float) -> None:
        self.update_timers()
        self.input(dt)
        self.move(dt)
        self.animate(dt)
