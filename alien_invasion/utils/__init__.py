from copy import deepcopy
from pathlib import Path

from pygame import image
from pygame.rect import Rect
from pygame.surface import Surface


def load_surfaces_from_sheet(path: Path, cols: int, rows: int) -> list[Surface]:
    sheet: Surface = image.load(path).convert_alpha()

    frame_width: int = sheet.get_size()[0] // cols
    frame_height: int = sheet.get_size()[1] // rows

    surfaces: list[Surface] = []

    for row in range(rows):
        for col in range(cols):
            rect = Rect(
                col * frame_width,
                row * frame_height,
                frame_width,
                frame_height,
            )
            frame_surface: Surface = deepcopy(sheet.subsurface(rect))
            surfaces.append(frame_surface)

    return surfaces


def load_surfaces_from_folder(path: Path) -> list[Surface]:
    return [
        image.load(Path.resolve(file)).convert_alpha()
        for file in path.iterdir()
    ]
