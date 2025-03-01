from enum import Enum
from pathlib import Path

import pygame

pygame.init()

type Color = tuple[int, int, int]

BASE_DIR: Path = Path(__file__).parent.parent.parent
ASSETS_DIR: Path = BASE_DIR / "assets"

FONT = pygame.font.Font(ASSETS_DIR / "fonts" / "Silkscreen-Regular.ttf", 40)
FONT_ACCENT: int = FONT.get_ascent()


HEART_SPEED_FACTOR = 4


FPS: int = 120

SCREEN_WIDTH: int = 1200
SCREEN_HEIGHT: int = 800


class GameLayer(Enum):
    GROUND = 1
    ENTITIES = 2
