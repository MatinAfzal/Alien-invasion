from dataclasses import dataclass

import inject
import pygame

from alien_invasion import settings
from alien_invasion.game_state import GameState


@dataclass
class World:
    def __post_init__(self) -> None:
        self.image: pygame.Surface = pygame.transform.scale(
            pygame.image.load(settings.ASSETS_DIR / "bg.png"),
            (640, 640),
        ).convert()
        self.rect = self.image.get_rect(topleft=(0, 0))

    def draw(self) -> None:
        game_state: GameState = inject.instance(GameState)
        display_surf: pygame.Surface | None = pygame.display.get_surface()

        if not display_surf:
            return

        img_width, img_height = self.image.get_size()

        for x in range(-img_width, settings.SCREEN_WIDTH + img_width, img_width):
            for y in range(-img_height, settings.SCREEN_HEIGHT + img_height, img_height):
                display_surf.blit(
                    self.image,
                    (
                        x - game_state.camera_offset.x % img_width,
                        y - game_state.camera_offset.y % img_height,
                    ),
                )
