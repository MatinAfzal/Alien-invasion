from collections.abc import Callable
from dataclasses import dataclass

import pygame


@dataclass
class Timer:
    duration: int
    on_expire: Callable[[], None] | None = None
    start_time: int = 0
    active: bool = False

    def activate(self) -> None:
        self.active = True
        self.start_time = pygame.time.get_ticks()

    def deactivate(self) -> None:
        self.active = False
        self.start_time = 0

    def update(self) -> None:
        current_time: int = pygame.time.get_ticks()
        if self.active and current_time - self.start_time >= self.duration:
            self.deactivate()
            if self.on_expire:
                self.on_expire()
