import inject

from src.game import Game
from src.game_stats import GameStats
from src.sprite_manager import SpritesManager

sm = SpritesManager()
stats = GameStats()


def config(binder: inject.Binder) -> None:
    binder.bind(SpritesManager, sm)
    binder.bind(GameStats, stats)


inject.configure(config)


game = Game()

game.run()
