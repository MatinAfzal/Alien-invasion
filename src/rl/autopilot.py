"""Auto-pilot for the player's ship, backed by pre-trained Q-tables.

Enabled from the main menu (the "Auto" toggle). The auto-pilot always
handles aiming (intercept lead on the nearest alien) and firing; the
learned Q-tables add movement (dodging and positioning). Without tables
it degrades to plain aim-and-fire, and without the menu toggle the ship
plays exactly like before.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path

from .. import settings
from .agents import QLearningAgent
from . import state as features

logger = logging.getLogger(__name__)

SHIP_MOVEMENT_FILE = "ship_movement.json"
SHIP_FIRE_FILE = "ship_fire.json"

SHIP_DECISION_INTERVAL = 6  # frames between movement decisions
SHIP_FIRE_COOLDOWN_MS = 150  # ms between auto-fired shots
SHIP_PLAY_EPSILON = 0.05
SHIP_SEEK_DEADZONE = 4  # px: close enough on an axis, stop nudging that way


class ShipAutopilot:
    """Selects movement, aim and fire for the player's ship.

    Read-only inside the game: like the enemy controller, it never updates
    Q-values. ``train_ship.py`` is the only place that learns.
    """

    def __init__(self, movement: QLearningAgent | None = None, fire: QLearningAgent | None = None):
        self.movement = movement
        self.fire = fire
        self.active = True  # gates the learned movement only
        self.training = False  # True only inside train_ship.py
        self.play_epsilon = SHIP_PLAY_EPSILON

        # Simulated clock (ms): wall-clock in the game, frame-based headless.
        self.now_ms = 0.0

        # Decision markers consumed by train_ship.py for reward bookkeeping.
        self.last_movement_decision: tuple[tuple[int, ...], int] | None = None
        self.last_fire: tuple[tuple[int, ...], int] | None = None

        self._held_action: int | None = None
        self._cooldown = 0
        self._last_fire_ms = -10_000
        self._aim_angle = 0.0
        self._aim_bin = 0
        self._alien_track: dict[int, tuple[int, int]] = {}
        self._alien_velocities: dict[int, tuple[int, int]] = {}

    @property
    def movement_enabled(self) -> bool:
        return self.active and self.movement is not None

    @property
    def fire_enabled(self) -> bool:
        return self.fire is not None

    @classmethod
    def load(cls, directory: str | Path) -> "ShipAutopilot":
        """Load ship Q-tables; missing files leave aim-and-fire intact."""
        directory = Path(directory)
        autopilot = cls()

        for filename, attribute, expected, expected_space in (
            (SHIP_MOVEMENT_FILE, "movement", features.RELATIVE_MOVEMENT_ACTIONS, features.SHIP_STATE_SPACE),
            (SHIP_FIRE_FILE, "fire", features.FIRE_ACTIONS, features.SHIP_STATE_SPACE),
        ):
            path = directory / filename
            if not path.exists():
                logger.warning("Ship RL table %s not found - auto-pilot aims and fires only", path)
                continue
            try:
                agent = QLearningAgent.load(path)
            except Exception:  # noqa: BLE001 - a corrupt table must never break the game
                logger.exception("Failed to load ship RL table %s", path)
                continue
            if list(agent.actions) != list(expected):
                logger.warning("Ship RL table %s uses an obsolete action set - re-run train_ship.py", path)
                continue
            if agent.space_id != expected_space:
                logger.warning(
                    "Ship RL table %s was trained for state space %r, current is %r - re-run train_ship.py",
                    path,
                    agent.space_id,
                    expected_space,
                )
                continue
            setattr(autopilot, attribute, agent)
            logger.info("Loaded ship RL %s table: %d states", attribute, len(agent))

        return autopilot

    # --- Aiming -------------------------------------------------------------

    def _update_tracking(self, aliens) -> None:
        """Per-frame alien positions used to estimate velocity for lead aim."""
        current = {id(alien): (alien.rect.centerx, alien.rect.centery) for alien in aliens}
        velocities = {
            key: (position[0] - previous[0], position[1] - previous[1])
            for key, position in current.items()
            if (previous := self._alien_track.get(key)) is not None
        }
        self._alien_track = current
        self._alien_velocities = velocities

    def _compute_aim(self, ship, aliens) -> None:
        """Pick the nearest alien and aim at an intercept point."""
        self._update_tracking(aliens)
        if not aliens:
            self._aim_angle = ship.angle
            self._aim_bin = features.aim_bearing_bin(ship.angle)
            return

        nearest = min(
            aliens,
            key=lambda alien: math.hypot(
                alien.rect.centerx - ship.rect.centerx, alien.rect.centery - ship.rect.centery
            ),
        )
        flight = math.hypot(
            nearest.rect.centerx - ship.rect.centerx, nearest.rect.centery - ship.rect.centery
        ) / max(settings.BULLET_SPEED_FACTOR * settings.DELTA_TIME, 0.001)
        velocity = self._alien_velocities.get(id(nearest), (0,0))

        aim_x = nearest.rect.centerx + velocity[0] * flight
        aim_y = nearest.rect.centery + velocity[1] * flight
        dx = aim_x - ship.rect.centerx
        dy = aim_y - ship.rect.centery

        self._aim_angle = math.atan2(-dx, -dy)  # Ship/ShipBullet angle convention
        self._aim_bin = features.bearing_bin(dx, dy)

    def apply_aim(self, ship) -> None:
        """Overwrite the mouse-derived angle with the auto-pilot aim."""
        ship.angle = self._aim_angle

    # --- Movement -----------------------------------------------------------

    @staticmethod
    def _apply_action(ship, action: int | None) -> None:
        """Drive the ship's movement flags from an absolute direction index."""
        if action is None or action == features.HOLD_ACTION:
            ship.moving_right = ship.moving_left = ship.moving_up = ship.moving_down = False
            return
        direction_x, direction_y = features.MOVEMENT_VECTORS[action]
        ship.moving_right = direction_x > 0.05
        ship.moving_left = direction_x < -0.05
        ship.moving_up = direction_y < -0.05
        ship.moving_down = direction_y > 0.05

    # --- Pickups ------------------------------------------------------------

    def _seek_pickups(self, ship, pickups) -> bool:
        """Steer straight at the nearest heart/shield currently on screen.

        Returns True when a pickup is being chased, which overrides the
        learned dodge for this frame. Hearts and shields fall from the top,
        so this is a greedy intercept - immediate and clear, no retraining
        required.
        """
        nearest = None
        nearest_distance = None
        for pickup in pickups:
            distance = math.hypot(
                pickup.rect.centerx - ship.rect.centerx,
                pickup.rect.centery - ship.rect.centery,
            )
            if nearest_distance is None or distance < nearest_distance:
                nearest, nearest_distance = pickup, distance

        if nearest is None:
            return False

        dx = nearest.rect.centerx - ship.rect.centerx
        dy = nearest.rect.centery - ship.rect.centery
        ship.moving_right = dx > SHIP_SEEK_DEADZONE
        ship.moving_left = dx < -SHIP_SEEK_DEADZONE
        ship.moving_up = dy < -SHIP_SEEK_DEADZONE
        ship.moving_down = dy > SHIP_SEEK_DEADZONE
        return True

    def plan(self, ship, aliens, alien_bullets, pickups=None) -> None:
        """Called BEFORE Ship.update: choose aim and movement for this frame.

        ``pickups`` is an optional iterable of hearts/shields on screen; when
        given, collecting the nearest one wins over the learned movement.
        """
        self.last_movement_decision = None
        self._compute_aim(ship, aliens)

        # Hearts and shields always win: go grab the nearest one.
        if pickups and self._seek_pickups(ship, pickups):
            return

        if not self.movement_enabled:
            # Auto mode without learned tables: stand still (aim/fire still work).
            self._apply_action(ship, features.HOLD_ACTION)
            return

        self._cooldown -= 1
        if self._cooldown > 0:
            self._apply_action(ship, self._held_action)
            return

        state = features.ship_movement_state(
            ship,
            aliens,
            alien_bullets,
            self._aim_bin,
            settings.SCREEN_WIDTH,
            settings.SCREEN_HEIGHT,
        )
        if not self.movement.is_known(state) and not self.training:
            self._held_action = None  # unseen: no movement (aim/fire still active)
        else:
            relative = self.movement.act(state, epsilon=self.play_epsilon)
            self._held_action = (
                features.HOLD_ACTION
                if relative == features.HOLD_ACTION
                else (self._aim_bin + relative) % 8
            )
            self.last_movement_decision = (state, relative)

        self._cooldown = SHIP_DECISION_INTERVAL - 1
        self._apply_action(ship, self._held_action)

    # --- Firing -------------------------------------------------------------

    def should_fire(self, ship, aliens, ship_bullets) -> bool:
        """True = fire this frame. Cooldown and magazine slots are respected."""
        self.last_fire = None
        if self.now_ms - self._last_fire_ms < SHIP_FIRE_COOLDOWN_MS:
            return False
        if len(ship_bullets) >= settings.BULLETS_ALLOWED:
            return False

        state = features.ship_fire_state(ship, aliens)

        if not self.fire_enabled or (not self.fire.is_known(state) and not self.training):
            fire = state[0] > 0  # deterministic fallback: shoot when an alien exists
        else:
            fire = self.fire.act(state, epsilon=self.play_epsilon) == features.FIRE_ACTION

        if not fire:
            return False
        self._last_fire_ms = self.now_ms
        self.last_fire = (state, features.FIRE_ACTION)
        return True
