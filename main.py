import inject

from alien_invasion.game import Game
from alien_invasion.utils.game_state import GameState
from alien_invasion.utils.sprite_manager import SpritesManager

sm = SpritesManager()
state = GameState()


def config(binder: inject.Binder) -> None:
    binder.bind(SpritesManager, sm)
    binder.bind(GameState, state)


inject.configure(config)


game = Game()

game.run()
