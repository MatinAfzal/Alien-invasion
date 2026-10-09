"""Discrete state (feature) encoders for the enemy Q-learning agents.

``train_rl.py`` and the in-game controller use the exact same encoders,
so the policy always sees the world the way it did while pre-training.
"""

from __future__ import annotations

import math

# --- Bins ------------------------------------------------------------------

DISTANCE_BINS = (120, 300, 550)  # close / mid / far / very far
EDGE_BINS = (60, 160)  # danger / close / safe
THREAT_BINS = (110, 240)  # imminent / close
STILL_SPEED = 4.0  # ship pixels per 100 ms considered "stationary"
SIDEWAYS_DOT = 0.4  # |cos| below this counts as lateral motion

# --- Action sets -----------------------------------------------------------

# Movement actions are RELATIVE to the direction of the ship: action i moves
# the alien along (ship_bearing + i) degrees. This rotation-invariant frame
# makes "dodge sideways when threatened" one crisp, easily learned rule
# instead of eight mirrored copies of it.
RELATIVE_MOVEMENT_ACTIONS = ("FWD", "+45", "+90", "+135", "BACK", "-135", "-90", "-45", "HOLD")
HOLD_ACTION = 8

# Absolute screen-space vectors used to actually move (index == bearing bin).
MOVEMENT_VECTORS: tuple[tuple[float, float], ...] = tuple(
    (math.cos(math.radians(index * 45)), math.sin(math.radians(index * 45))) for index in range(8)
) + ((0.0, 0.0),)

FIRE_ACTIONS = ("HOLD", "FIRE")
FIRE_ACTION = 1

# --- Ship auto-pilot bins ---------------------------------------------------

SHIP_ALIEN_BINS = (150, 350, 600)  # close / mid / far / very far
SHIP_THREAT_BINS = (110, 240)  # imminent / close
SHIP_EDGE_BINS = (120,)  # pinned near a wall / open space

# State-space fingerprints. A table trained for a different encoding is
# rejected on load instead of being misinterpreted at runtime.
ENEMY_STATE_SPACE = "enemy-v1"
SHIP_STATE_SPACE = "ship-v2"


# --- Helpers ----------------------------------------------------------------


def bearing_bin(dx: float, dy: float) -> int:
    """Quantise a direction into one of 8 compass bins."""
    angle = math.degrees(math.atan2(dy, dx))
    return int(((angle + 22.5) % 360.0) // 45.0)


def distance_to(alien, ship) -> float:
    """Euclidean distance between alien and ship centres."""
    return math.hypot(ship.rect.centerx - alien.rect.centerx, ship.rect.centery - alien.rect.centery)


def distance_bin(distance: float) -> int:
    for index, threshold in enumerate(DISTANCE_BINS):
        if distance <= threshold:
            return index
    return len(DISTANCE_BINS)


def edge_bin(alien, screen_width: int, screen_height: int) -> int:
    """How trapped the alien is against the screen border."""
    rect = alien.rect
    margin = min(rect.left, screen_width - rect.right, rect.top, screen_height - rect.bottom)
    if margin <= EDGE_BINS[0]:
        return 0
    if margin <= EDGE_BINS[1]:
        return 1
    return 2


def ship_bearing_bin(alien, ship) -> int:
    """8-bin bearing FROM the alien TO the ship (screen space)."""
    return bearing_bin(ship.rect.centerx - alien.rect.centerx, ship.rect.centery - alien.rect.centery)


def _nearest_threat(alien, ship_bullets) -> tuple[int, int]:
    """Nearest incoming bullet as (urgency, bearing bin of the bullet).

    urgency: 0 = nothing threatens the alien, 1 = bullet within 240 px,
    2 = bullet within 110 px. Only bullets actually travelling towards the
    alien count.
    """
    if not ship_bullets:
        return 0, 0

    ax, ay = alien.rect.centerx, alien.rect.centery
    best_key = None
    best = (0, 0)

    for bullet in ship_bullets:
        dx = ax - bullet.rect.centerx
        dy = ay - bullet.rect.centery
        distance = math.hypot(dx, dy)
        if distance > THREAT_BINS[1]:
            continue

        # Bullet velocity direction (mirrors Bullet.update motion).
        velocity_x = -math.sin(bullet.angle)
        velocity_y = -math.cos(bullet.angle)
        if velocity_x * dx + velocity_y * dy <= 0:
            continue  # travelling away, no threat

        urgency = 2 if distance <= THREAT_BINS[0] else 1
        key = (urgency, -distance)
        if best_key is None or key > best_key:
            best_key = key
            best = (urgency, bearing_bin(bullet.rect.centerx - ax, bullet.rect.centery - ay))

    return best


def movement_state(alien, ship, ship_bullets) -> tuple[int, int, int, int]:
    """Discrete state consumed by the movement policy (rotation invariant).

    Components: distance band, threat urgency, threat direction as a
    quadrant relative to the alien->ship axis, and screen-edge pressure.
    """
    settings = alien.ai_settings
    distance = math.hypot(ship.rect.centerx - alien.rect.centerx, ship.rect.centery - alien.rect.centery)
    urgency, bullet_bearing = _nearest_threat(alien, ship_bullets)
    relative = (bullet_bearing - ship_bearing_bin(alien, ship)) % 8 if urgency else 0

    return (
        distance_bin(distance),
        urgency,
        relative // 2,  # 0..3 quadrant
        edge_bin(alien, settings.screen_width, settings.screen_height),
    )


def ship_motion_bin(alien, ship, ship_velocity: tuple[float, float]) -> int:
    """0 = still, 1 = closing on the alien, 2 = escaping, 3 = crossing."""
    velocity_x, velocity_y = ship_velocity
    speed = math.hypot(velocity_x, velocity_y)
    if speed < STILL_SPEED:
        return 0

    to_alien_x = alien.rect.centerx - ship.rect.centerx
    to_alien_y = alien.rect.centery - ship.rect.centery
    span = math.hypot(to_alien_x, to_alien_y)
    if span < 1.0:
        return 0

    alignment = (velocity_x * to_alien_x + velocity_y * to_alien_y) / (speed * span)
    if alignment > SIDEWAYS_DOT:
        return 1
    if alignment < -SIDEWAYS_DOT:
        return 2
    return 3


def fire_state(alien, ship, ship_velocity: tuple[float, float]) -> tuple[int, int]:
    """Full discrete state consumed by the fire policy."""
    return (distance_bin(distance_to(alien, ship)), ship_motion_bin(alien, ship, ship_velocity))


# --- Ship (auto-pilot) states ------------------------------------------------


def aim_bearing_bin(angle: float) -> int:
    """8-bin compass bearing the ship's facing points at.

    ``Ship.angle`` follows the ``(-sin, -cos)`` velocity convention used by
    ``ShipBullet``.
    """
    return bearing_bin(-math.sin(angle), -math.cos(angle))


def ship_alien_bin(ship, aliens) -> int:
    """0 = no alien alive, otherwise 1..4 = distance band of nearest alien."""
    if not aliens:
        return 0
    nearest = min(
        math.hypot(alien.rect.centerx - ship.rect.centerx, alien.rect.centery - ship.rect.centery) for alien in aliens
    )
    for index, threshold in enumerate(SHIP_ALIEN_BINS):
        if nearest <= threshold:
            return index + 1
    return len(SHIP_ALIEN_BINS) + 1


def ship_threat_bin(ship, alien_bullets, aim_bin: int) -> int:
    """Nearest incoming alien bullet relative to where the ship is aiming.

    Returns 0 when nothing threatens the ship, otherwise
    ``1 + urgency * 4 + quadrant`` with quadrant measured against the
    aim direction (0 = ahead, 1/2/3 = clockwise quadrants).
    """
    if not alien_bullets:
        return 0

    sx, sy = ship.rect.centerx, ship.rect.centery
    best_key = None
    best_value = 0

    for bullet in alien_bullets:
        dx = sx - bullet.rect.centerx
        dy = sy - bullet.rect.centery
        distance = math.hypot(dx, dy)
        if distance > SHIP_THREAT_BINS[1]:
            continue

        velocity_x = -math.sin(bullet.angle)
        velocity_y = -math.cos(bullet.angle)
        if velocity_x * dx + velocity_y * dy <= 0:
            continue  # travelling away, no threat

        urgency = 1 if distance <= SHIP_THREAT_BINS[0] else 0
        quadrant = (bearing_bin(bullet.rect.centerx - sx, bullet.rect.centery - sy) - aim_bin) % 8 // 2
        key = (urgency, -distance)
        if best_key is None or key > best_key:
            best_key = key
            best_value = 1 + urgency * 4 + quadrant

    return best_value


def ship_edge_bin(ship, screen_width: int, screen_height: int) -> int:
    """1 when the ship is pinned close to a wall, 0 in open space."""
    rect = ship.rect
    margin = min(rect.left, screen_width - rect.right, rect.top, screen_height - rect.bottom)
    return 1 if margin <= SHIP_EDGE_BINS[0] else 0


def nearest_alien(ship, aliens):
    """Closest alien to the ship, or None."""
    if not aliens:
        return None
    return min(
        aliens,
        key=lambda alien: math.hypot(alien.rect.centerx - ship.rect.centerx, alien.rect.centery - ship.rect.centery),
    )


def ship_alien_side(ship, aliens, aim_bin: int) -> int:
    """Where the nearest alien sits relative to the aim direction (0..3, 0 if none).

    Without this the ship cannot learn to dodge a diving alien, because
    the distance band alone does not say which way to move.
    """
    nearest = nearest_alien(ship, aliens)
    if nearest is None:
        return 0
    bearing = bearing_bin(nearest.rect.centerx - ship.rect.centerx, nearest.rect.centery - ship.rect.centery)
    return ((bearing - aim_bin) % 8) // 2


def ship_movement_state(ship, aliens, alien_bullets, aim_bin: int, screen_width: int, screen_height: int) -> tuple:
    """Discrete state consumed by the ship's movement policy.

    Components: nearest-alien distance band, nearest-alien direction
    relative to the aim axis, incoming-bullet threat, wall proximity.
    """
    return (
        ship_alien_bin(ship, aliens),
        ship_alien_side(ship, aliens, aim_bin),
        ship_threat_bin(ship, alien_bullets, aim_bin),
        ship_edge_bin(ship, screen_width, screen_height),
    )


def ship_fire_state(ship, aliens) -> tuple[int]:
    """Discrete state consumed by the ship's fire policy."""
    return (ship_alien_bin(ship, aliens),)
