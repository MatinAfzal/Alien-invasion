"""Window fitting for Alien Invasion.

The whole game is authored for a fixed *logical* resolution (1200x800) and
every entity's position, the scrolling background and the pre-trained RL
Q-tables assume it. To keep that intact while making sure the window actually
fits on the monitor, the game renders to an off-screen logical surface and this
module scales that surface onto the real window at the end of every frame.

To avoid touching dozens of classes, ``pygame.display.get_surface`` is
redirected to the logical surface, so anything that grabs "the screen" (sprite,
UI button, the health/heart bar, ...) keeps drawing in logical coordinates.
``pygame.mouse.get_pos`` is redirected the other way (window -> logical) so
hit-testing and the crosshair line up with what the player sees.
"""

from __future__ import annotations

import pygame

_logical: pygame.Surface | None = None
_window: pygame.Surface | None = None
_scale_x: float = 1.0
_scale_y: float = 1.0

# Captured before any monkey-patching so we can still read the real cursor.
_raw_mouse_pos = pygame.mouse.get_pos


def _desktop_size() -> tuple[int, int]:
    """Return the primary monitor size, falling back to the display info."""
    try:
        sizes = pygame.display.get_desktop_sizes()
        if sizes:
            return sizes[0]
    except pygame.error:
        pass
    info = pygame.display.Info()
    return info.current_w, info.current_h


def fit_window_size(logical_size: tuple[int, int], reserve_y: int = 90) -> tuple[int, int]:
    """Largest window with the logical aspect ratio that fits the monitor.

    Never grows past the logical size, so on monitors that already fit the
    window the game behaves exactly as before. ``reserve_y`` leaves room for the
    title bar and the taskbar so the window never slips off the screen.
    """
    width, height = logical_size
    desktop_w, desktop_h = _desktop_size()
    avail_w = max(1, desktop_w)
    avail_h = max(1, desktop_h - reserve_y)

    scale = min(1.0, avail_w / width, avail_h / height)
    return max(1, int(width * scale)), max(1, int(height * scale))


def init(window_size: tuple[int, int], logical_size: tuple[int, int]) -> pygame.Surface:
    """Create the window and the logical surface, then patch pygame accessors."""
    global _logical, _window, _scale_x, _scale_y

    _window = pygame.display.set_mode(window_size)

    if window_size == logical_size:
        # Nothing to scale - draw straight to the display as before.
        _logical = _window
    else:
        _logical = pygame.Surface(logical_size).convert()

    _scale_x = logical_size[0] / window_size[0]
    _scale_y = logical_size[1] / window_size[1]

    # Anything that asks pygame for "the screen" must draw in logical
    # coordinates, because that is what present() scales against.
    pygame.display.get_surface = get_logical

    if window_size != logical_size:
        pygame.mouse.get_pos = get_mouse_pos

    return _logical


def get_logical() -> pygame.Surface:
    """Return the surface the game actually draws on."""
    return _logical


def is_scaled() -> bool:
    """True when the logical surface differs from the real window."""
    return _logical is not None and _window is not None and _logical is not _window


def to_logical(pos: tuple[float, float]) -> tuple[int, int]:
    """Convert a window-space position into logical-surface coordinates."""
    return int(pos[0] * _scale_x), int(pos[1] * _scale_y)


def get_mouse_pos() -> tuple[int, int]:
    """Replacement for ``pygame.mouse.get_pos`` that reports logical coords."""
    return to_logical(_raw_mouse_pos())


def present() -> None:
    """Scale the logical surface onto the window and flip it."""
    if _window is None or _logical is None:
        return

    if is_scaled():
        pygame.transform.scale(_logical, _window.get_size(), _window)

    pygame.display.flip()
