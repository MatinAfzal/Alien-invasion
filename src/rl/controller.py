"""Runtime controller plugging the pre-trained Q-tables into the live game.

The controller is read-only inside the game: it selects actions but never
updates Q-values. Learning happens exclusively in ``train_rl.py``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .. import settings
from .agents import QLearningAgent
from . import state as features

logger = logging.getLogger(__name__)

RL_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "rl"
MOVEMENT_FILE = "movement.json"
FIRE_FILE = "fire.json"

DECISION_INTERVAL = 6  # frames between movement decisions (~20 Hz at 120 FPS)
FIRE_COOLDOWN_MS = 150  # minimum ms between two shots from the same alien
PLAY_EPSILON = 0.05  # light in-game exploration on top of the learned policy


class RLEnemyController:
    """Owns the Q-tables and turns world observations into enemy actions."""

    def __init__(self, movement: QLearningAgent | None = None, fire: QLearningAgent | None = None):
        self.movement = movement
        self.fire = fire
        self.active = True  # set to False to fall back to the classic heuristics
        self.training = False  # True only inside train_rl.py
        self.play_epsilon = PLAY_EPSILON

        # Last decision markers (consumed by train_rl.py for reward bookkeeping).
        self.last_movement_decision: tuple[tuple[int, ...], int, float] | None = None
        self.last_fire: tuple[tuple[int, ...], int] | None = None

        # Ship velocity estimate, refreshed once per fire pass (px per 100 ms).
        self._ship_position: tuple[int, int] | None = None
        self._ship_velocity: tuple[float, float] = (0.0, 0.0)
        self._ship_measured_at = 0

        # Simulated clock (ms). The host sets it once per fire pass:
        # wall-clock time in the game, frame-based time while training
        # headless (where the sim runs much faster than realtime).
        self.now_ms = 0.0
        # When set, gf.alien_fire uses this instead of the wall clock
        # (train_ship.py drives enemy fire from frame time).
        self.clock_override: float | None = None

    @property
    def enabled(self) -> bool:
        return self.active and self.movement is not None and self.fire is not None

    @classmethod
    def load(cls, directory: str | Path = RL_DATA_DIR) -> "RLEnemyController":
        """Load Q-tables from *directory*; missing files simply disable RL."""
        directory = Path(directory)
        controller = cls()

        for filename, attribute, expected_actions, expected_space in (
            (MOVEMENT_FILE, "movement", features.RELATIVE_MOVEMENT_ACTIONS, features.ENEMY_STATE_SPACE),
            (FIRE_FILE, "fire", features.FIRE_ACTIONS, features.ENEMY_STATE_SPACE),
        ):
            path = directory / filename
            if not path.exists():
                logger.warning("RL table %s not found - enemies fall back to classic behaviour", path)
                continue
            try:
                agent = QLearningAgent.load(path)
            except Exception:  # noqa: BLE001 - a corrupt table must never break the game
                logger.exception("Failed to load RL table %s", path)
                continue
            if list(agent.actions) != list(expected_actions):
                # e.g. a table trained with the old absolute action set.
                logger.warning("RL table %s uses an obsolete action set - re-run train_rl.py", path)
                continue
            if agent.space_id != expected_space:
                logger.warning(
                    "RL table %s was trained for state space %r, current is %r - re-run train_rl.py",
                    path,
                    agent.space_id,
                    expected_space,
                )
                continue
            setattr(controller, attribute, agent)
            logger.info("Loaded RL %s table: %d states", attribute, len(agent))

        return controller

    # --- Movement -----------------------------------------------------------

    def decide_movement(self, alien, ship, ship_bullets) -> int | None:
        """Return the movement action index to hold this frame, or None for the heuristic."""
        self.last_movement_decision = None
        if not self.enabled:
            return None

        if not hasattr(alien, "rl_action"):
            alien.rl_action = None
            alien.rl_cooldown = 0

        alien.rl_cooldown -= 1
        if alien.rl_cooldown > 0:
            return alien.rl_action

        state = features.movement_state(alien, ship, ship_bullets)
        if not self.movement.is_known(state) and not self.training:
            # Never-seen state: keep the classic chase behaviour instead of guessing.
            alien.rl_action = None
        else:
            relative = self.movement.act(state, epsilon=self.play_epsilon)
            if relative == features.HOLD_ACTION:
                alien.rl_action = features.HOLD_ACTION
            else:
                # Translate the relative decision into an absolute screen direction.
                alien.rl_action = (features.ship_bearing_bin(alien, ship) + relative) % 8
            self.last_movement_decision = (state, relative, features.distance_to(alien, ship))

        alien.rl_cooldown = DECISION_INTERVAL - 1
        return alien.rl_action

    @staticmethod
    def apply_movement(alien, action: int) -> None:
        """Move the alien along the chosen action vector for one frame."""
        direction_x, direction_y = features.MOVEMENT_VECTORS[action]
        speed = alien.ai_settings.alien_speed_factor * alien.ai_settings.delta_time
        alien.x += direction_x * speed
        alien.y += direction_y * speed
        alien.rect.x = alien.x
        alien.rect.y = alien.y

    # --- Firing -------------------------------------------------------------

    def ship_velocity_per_frame(self) -> tuple[float, float]:
        """Ship velocity as pixels per frame, used to lead bullet shots."""
        frames_per_100ms = settings.FPS / 10.0
        return (self._ship_velocity[0] / frames_per_100ms, self._ship_velocity[1] / frames_per_100ms)

    def update_ship_velocity(self, ship) -> None:
        """Estimate ship velocity between two fire passes (px per 100 ms)."""
        now = self.now_ms
        position = (ship.rect.centerx, ship.rect.centery)

        elapsed = now - self._ship_measured_at
        if self._ship_position is not None and elapsed >= 50:
            scale = 100.0 / elapsed
            velocity = ((position[0] - self._ship_position[0]) * scale, (position[1] - self._ship_position[1]) * scale)
            # Light smoothing so single-frame jitter does not flip the state bin.
            self._ship_velocity = (
                0.5 * self._ship_velocity[0] + 0.5 * velocity[0],
                0.5 * self._ship_velocity[1] + 0.5 * velocity[1],
            )
            self._ship_position = position
            self._ship_measured_at = now
        elif self._ship_position is None:
            self._ship_position = position
            self._ship_measured_at = now

    def should_fire(self, alien, ship) -> bool | None:
        """True = fire, False = hold, None = no opinion (caller uses its own fallback)."""
        self.last_fire = None
        if not self.enabled:
            return None

        now = self.now_ms
        last_fire = getattr(alien, "rl_last_fire", -10_000)
        if now - last_fire < FIRE_COOLDOWN_MS:
            return False

        state = features.fire_state(alien, ship, self._ship_velocity)
        if not self.fire.is_known(state) and not self.training:
            return None

        if self.fire.act(state, epsilon=self.play_epsilon) != features.FIRE_ACTION:
            return False

        alien.rl_last_fire = now
        self.last_fire = (state, features.FIRE_ACTION)
        return True
