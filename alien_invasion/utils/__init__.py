import math
from pathlib import Path

import pygame


def load_surfaces_from_sheet(path: Path, cols: int, rows: int) -> list[pygame.Surface]:
    sheet: pygame.Surface = pygame.image.load(path).convert_alpha()

    frame_width: int = sheet.get_size()[0] // cols
    frame_height: int = sheet.get_size()[1] // rows

    surfaces: list[pygame.Surface] = []

    for row in range(rows):
        for col in range(cols):
            rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
            frame_surface: pygame.Surface = sheet.subsurface(rect).copy()
            surfaces.append(frame_surface)

    return surfaces


def get_direction_by_angle(angle: float) -> pygame.Vector2:
    return pygame.Vector2(math.cos(math.radians(angle)), math.sin(math.radians(angle)))
