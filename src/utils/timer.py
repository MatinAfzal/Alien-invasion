"""Module defining a Timer class that manages a countdown and executes a function when the time expires."""

import dataclasses
from collections.abc import Callable

import pygame


@dataclasses.dataclass
class Timer:
    """Timer class for managing a countdown with a callable function upon expiration."""

    duration: int
    on_expire: Callable[[], None] | None = None
    start_time: int = 0
    active: bool = False

    def activate(self) -> None:
        """Activates the timer and records the start time."""
        self.active = True
        self.start_time = pygame.time.get_ticks()

    def deactivate(self) -> None:
        """Deactivates the timer and resets the start time."""
        self.active = False
        self.start_time = 0

    def update(self) -> None:
        """Check if the timer has expired and deactivate it if the duration has passed."""
        current_time: int = pygame.time.get_ticks()
        if self.active and current_time - self.start_time >= self.duration:
            self.deactivate()
            if self.on_expire:
                self.on_expire()
