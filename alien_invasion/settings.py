from enum import Enum
from pathlib import Path

BASE_DIR: Path = Path(__file__).parent.parent
ASSETS_DIR: Path = BASE_DIR / "assets"

FPS: int = 120

SCREEN_WIDTH: int = 1200
SCREEN_HEIGHT: int = 800


class Layer(Enum):
    GROUND = 1
    ENTITIES = 2
