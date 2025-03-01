import pygame

from alien_invasion import settings


class World(pygame.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load(settings.ASSETS_DIR / "bg.png"), (640, 640)).convert()
        self.rect = self.image.get_rect(topleft=(0, 0))
        self.display_surf: pygame.Surface | None = pygame.display.get_surface()

    def draw(self, camera_offset: pygame.math.Vector2) -> None:
        if self.image and self.display_surf:
            img_width, img_height = self.image.get_size()

            for x in range(-img_width, settings.SCREEN_WIDTH + img_width, img_width):
                for y in range(-img_height, settings.SCREEN_HEIGHT + img_height, img_height):
                    self.display_surf.blit(
                        self.image,
                        (x - camera_offset.x % img_width, y - camera_offset.y % img_height),
                    )
