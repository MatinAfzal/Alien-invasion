import dataclasses

import inject
import pygame

from alien_invasion import settings
from alien_invasion.entities.sprites.enemy import EnemyFactory
from alien_invasion.entities.sprites.player import PlayerFactory
from alien_invasion.scenes import Scene
from alien_invasion.utils.game_state import GameState
from alien_invasion.utils.sprite_manager import SpritesManager


@dataclasses.dataclass
class SpaceBG:
    def __post_init__(self) -> None:
        self.image: pygame.Surface = pygame.transform.scale(
            pygame.image.load(settings.ASSETS_DIR / "bg.png"),
            (640, 640),
        ).convert()
        self.rect: pygame.Rect = self.image.get_rect(topleft=(0, 0))

    def draw(self) -> None:
        game_state: GameState = inject.instance(GameState)
        display_surf: pygame.Surface | None = pygame.display.get_surface()

        if not display_surf:
            return

        img_width: int = self.image.get_size()[0]
        img_height: int = self.image.get_size()[1]

        for x in range(
            -img_width,
            settings.SCREEN_WIDTH + img_width,
            img_width,
        ):
            for y in range(
                -img_height,
                settings.SCREEN_HEIGHT + img_height,
                img_height,
            ):
                display_surf.blit(
                    self.image,
                    (
                        x - game_state.camera_offset.x % img_width,
                        y - game_state.camera_offset.y % img_height,
                    ),
                )


class GameScene(Scene):
    def __init__(self) -> None:
        super().__init__(
            PlayerFactory().create(pygame.Vector2(640, 360)),
            SpaceBG(),
        )

    def __post_init__(self) -> None:
        super().__post_init__()
        sprite_manager: SpritesManager = inject.instance(SpritesManager)

        sprite_manager.add(EnemyFactory().create(pygame.Vector2(200, 200)))
