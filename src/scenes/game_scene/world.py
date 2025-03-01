import inject
import pygame

from src import settings
from src.game_state import GameState


class World(pygame.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__()
        self.image = pygame.transform.scale(
            pygame.image.load(settings.ASSETS_DIR / "images" / "bg.png"),
            (640, 640),
        ).convert()
        self.rect = self.image.get_rect(topleft=(0, 0))
        self.display_surf = pygame.display.get_surface()

    def draw(self, camera_offset: pygame.math.Vector2) -> None:
        img_width, img_height = self.image.get_size()

        for x in range(-img_width, settings.SCREEN_WIDTH + img_width, img_width):
            for y in range(-img_height, settings.SCREEN_HEIGHT + img_height, img_height):
                self.display_surf.blit(self.image, (x - camera_offset.x % img_width, y - camera_offset.y % img_height))
