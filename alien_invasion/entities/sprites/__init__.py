from dataclasses import dataclass, field
from pathlib import Path

import pygame

from alien_invasion.utils import load_surfaces_from_sheet
from alien_invasion.utils.timer import Timer


@dataclass
class SpriteAnimation:
    sprites: list[pygame.Surface] = field(default_factory=list)
    fps: int = 1
    loops: int | None = None


@dataclass
class SpriteAnimationFactory:
    fps: int = 4
    loops: int = -1

    def load_from_folder(self, path: Path) -> SpriteAnimation:
        return SpriteAnimation(
            [pygame.image.load(Path.resolve(file)).convert_alpha() for file in path.iterdir()],
            self.fps,
            self.loops,
        )

    def load_from_sheet_file(self, path: Path, cols: int, rows: int) -> SpriteAnimation:
        return SpriteAnimation(load_surfaces_from_sheet(path, cols, rows), self.fps, self.loops)


@dataclass
class Sprite:
    z: int
    init_pos: pygame.math.Vector2
    animation: SpriteAnimation
    size: tuple[int, int]
    init_speed: pygame.Vector2
    angle: float = 0
    direction: pygame.Vector2 = field(default_factory=pygame.Vector2)

    frame_idx: float = field(default=0, init=False)
    timers: list[Timer] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        super().__init__()
        self.speed: pygame.Vector2 = self.init_speed
        self.rect: pygame.Rect = self.image.get_rect(center=self.init_pos)
        self.pos: pygame.Vector2 = self.init_pos.copy()

        self.setup()

    @property
    def image(self) -> pygame.Surface:
        image: pygame.Surface = self.animation.sprites[int(self.frame_idx)]
        image = pygame.transform.scale(image, self.size)
        return pygame.transform.rotate(image, self.angle)

    def setup(self) -> None: ...

    def input(self, dt: float) -> None: ...

    def move(self, dt: float) -> None:
        if self.direction.magnitude():
            self.direction: pygame.Vector2 = self.direction.normalize()
        self.pos.x += self.direction.x * self.speed.x * dt
        self.pos.y += self.direction.y * self.speed.y * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.rect = self.image.get_rect(center=self.rect.center)

    def register_timer(self, timer: Timer) -> None:
        self.timers.append(timer)

    def update_timers(self) -> None:
        for timer in self.timers:
            timer.update()

    def change_animation(self, animation: SpriteAnimation) -> None:
        self.animation = animation

    def animate(self, dt: float) -> None:
        if not self.animation:
            return

        self.frame_idx = (self.frame_idx + self.animation.fps * dt) % len(self.animation.sprites)

    def update(self, dt: float) -> None:
        self.update_timers()
        self.input(dt)
        self.move(dt)
        self.animate(dt)
