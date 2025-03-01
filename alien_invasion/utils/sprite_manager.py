from dataclasses import dataclass, field

import inject

from alien_invasion import settings
from alien_invasion.entities.sprites import Sprite
from alien_invasion.utils.game_state import GameState


@dataclass
class SpritesManager:
    sprites: list[Sprite] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.__sort_sprites()

    def add(self, sprite: Sprite) -> None:
        self.sprites.append(sprite)
        self.__sort_sprites()

    def update(self, dt: float) -> None:
        game_state: GameState = inject.instance(GameState)

        offset = 200

        for idx, sprite in enumerate(self.sprites):
            if not (
                game_state.player_position.x - settings.SCREEN_WIDTH / 2 - offset
                < sprite.pos.x
                < game_state.player_position.x + settings.SCREEN_WIDTH + offset
            ) or not (
                game_state.player_position.y - settings.SCREEN_HEIGHT / 2 - offset
                < sprite.pos.y
                < game_state.player_position.y + settings.SCREEN_HEIGHT + offset
            ):
                del self.sprites[idx]

            sprite.update(dt)

    def __sort_sprites(self) -> None:
        self.sprites = sorted(self.sprites, key=lambda x: (x.z, x.rect.center))

    def clear(self) -> None:
        self.sprites = []
