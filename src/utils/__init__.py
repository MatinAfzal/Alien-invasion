from pathlib import Path
import pygame


def load_surfaces_from_sheet(path: Path, cols: int, rows: int) -> list[pygame.Surface]:
    sheet: pygame.Surface = pygame.image.load(path).convert_alpha()

    sheet_width, sheet_height = sheet.get_size()
    frame_width: int = sheet_width // cols
    frame_height: int = sheet_height // rows

    surfaces: list[pygame.Surface] = []

    for row in range(rows):
        for col in range(cols):
            rect = pygame.Rect(col * frame_width, row * frame_height, frame_width, frame_height)
            frame_surface: pygame.Surface = sheet.subsurface(rect).copy()
            surfaces.append(frame_surface)

    return surfaces
