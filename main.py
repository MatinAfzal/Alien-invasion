import inject

from alien_invasion.game import Game
from alien_invasion.game_state import GameState
from alien_invasion.sprite_manager import SpritesManager

sm = SpritesManager()
state = GameState()


def config(binder: inject.Binder) -> None:
    binder.bind(SpritesManager, sm)
    binder.bind(GameState, state)


inject.configure(config)


game = Game()

game.run()
