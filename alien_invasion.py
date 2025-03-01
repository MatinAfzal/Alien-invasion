import inject

from src.game import Game
from src.game_state import GameState
from src.sprite_manager import SpritesManager

sm = SpritesManager()
state = GameState()


def config(binder: inject.Binder) -> None:
    binder.bind(SpritesManager, sm)
    binder.bind(GameState, state)


inject.configure(config)


game = Game()

game.run()
