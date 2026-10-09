"""Lightweight tabular Q-learning enemies, pre-trained by ``train_rl.py``.

Typical flow::

    from src.rl import init_controller, get_controller

    init_controller()          # at start-up, loads data/rl/*.json
    ...
    get_controller()           # read-only access from game code
"""

from __future__ import annotations

from pathlib import Path

from .agents import QLearningAgent
from .autopilot import ShipAutopilot
from .controller import RL_DATA_DIR, RLEnemyController
from .state import FIRE_ACTIONS, RELATIVE_MOVEMENT_ACTIONS

_controller: RLEnemyController | None = None
_autopilot: ShipAutopilot | None = None


def init_controller(directory: str | Path | None = None) -> RLEnemyController:
    """Load the pre-trained Q-tables and install the global controller."""
    global _controller
    _controller = RLEnemyController.load(RL_DATA_DIR if directory is None else directory)
    return _controller


def get_controller() -> RLEnemyController | None:
    """Return the installed controller, or None before ``init_controller``."""
    return _controller


def init_autopilot(directory: str | Path | None = None) -> ShipAutopilot:
    """Load the pre-trained ship Q-tables and install the global auto-pilot."""
    global _autopilot
    _autopilot = ShipAutopilot.load(RL_DATA_DIR if directory is None else directory)
    return _autopilot


def get_autopilot() -> ShipAutopilot | None:
    """Return the installed auto-pilot, or None before ``init_autopilot``."""
    return _autopilot


__all__ = [
    "FIRE_ACTIONS",
    "QLearningAgent",
    "RL_DATA_DIR",
    "RELATIVE_MOVEMENT_ACTIONS",
    "RLEnemyController",
    "ShipAutopilot",
    "get_autopilot",
    "get_controller",
    "init_autopilot",
    "init_controller",
]
