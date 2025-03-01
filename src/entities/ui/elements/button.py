from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

import pygame

from src import settings


class BtnColors(StrEnum):
    TOP_COLOR = "#b5e48c"
    BOTTOM_COLOR = "#52b69a"
    TEXT_COLOR = "#184e77"
    HOVER_COLOR = "#99d98c"


ELEVATION_INIT_VALUE = 6


@dataclass
class ButtonState:
    elevation: int = field(default=ELEVATION_INIT_VALUE, init=False)
    pressed: bool = field(default=False, init=False)

    def set_pressed(self, value: bool) -> None:
        self.pressed = value
        self.elevation = 0 if value else ELEVATION_INIT_VALUE


@dataclass
class Button:
    text: str
    size: tuple[int, int]
    pos: tuple[int, int]
    on_click: Callable[[], None]
    show_fn: Callable[[], bool]

    state: ButtonState = field(default_factory=ButtonState, init=False)

    def __post_init__(self) -> None:
        self.screen: pygame.Surface = pygame.display.get_surface()
        self.original_y_pos: int = self.pos[1]

        self.top_rect = pygame.Rect(self.pos, self.size)
        self.top_color: pygame.Color = pygame.Color(BtnColors.TOP_COLOR)

        self.bottom_rect = pygame.Rect(self.pos, (self.size[0], self.state.elevation))
        self.bottom_color: pygame.Color = pygame.Color(BtnColors.BOTTOM_COLOR)

        self.text_surf: pygame.Surface = settings.FONT.render(self.text, True, BtnColors.TEXT_COLOR)
        self.text_rect: pygame.Rect = self.text_surf.get_rect(center=self.top_rect.center)

    def draw(self) -> None:
        self.top_rect.y = self.original_y_pos - self.state.elevation
        self.text_rect.center = self.top_rect.center

        self.text_rect.y -= (self.text_surf.get_height() - settings.FONT_ACCENT) // 2

        self.bottom_rect.midtop = self.top_rect.midtop
        self.bottom_rect.height = self.top_rect.height + self.state.elevation

        pygame.draw.rect(self.screen, self.bottom_color, self.bottom_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.top_color, self.top_rect, border_radius=8)

        self.screen.blit(self.text_surf, self.text_rect)

    def check_click(self) -> None:
        mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
        if self.top_rect.collidepoint(mouse_pos):
            self.top_color = pygame.Color(BtnColors.HOVER_COLOR)
            if pygame.mouse.get_pressed()[0]:
                if not self.state.pressed:
                    self.state.set_pressed(True)
            else:
                if self.state.pressed:
                    self.on_click()
                self.state.set_pressed(False)
        else:
            self.top_color = pygame.Color(BtnColors.TOP_COLOR)
            self.state.set_pressed(False)

    def update(self) -> None:
        if self.show_fn():
            self.check_click()
            self.draw()
