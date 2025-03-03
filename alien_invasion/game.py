import sys
from typing import TYPE_CHECKING

from pygame import QUIT, display, event, init, time

from alien_invasion.scenes.game_scene import GameScene
from alien_invasion.settings import SCREEN_HEIGHT, SCREEN_WIDTH

if TYPE_CHECKING:
    from pygame.surface import Surface


class Game:
    def __init__(self) -> None:
        init()
        self.display: Surface = display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        display.set_caption("Alien Invasion")
        self.clock = time.Clock()

        self.scene = GameScene()

    def run(self) -> None:
        while True:
            for e in event.get():
                if e.type == QUIT:
                    sys.exit()

            dt: float = self.clock.tick(120) / 1000
            self.scene.run(dt)
            display.update()
