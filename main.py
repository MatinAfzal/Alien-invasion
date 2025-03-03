import inject

from alien_invasion.entities.sprites import SpritesManager
from alien_invasion.game import Game
from alien_invasion.utils.game_state import GameState

sm = SpritesManager()
state = GameState()


def config(binder: inject.Binder) -> None:
    binder.bind(SpritesManager, sm)
    binder.bind(GameState, state)


inject.configure(config)


game = Game()

game.run()
