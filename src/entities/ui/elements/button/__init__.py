"""
Implement a button class for a Pygame-based UI.

Provides a simple button with elevation, hover effect, and click handling.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

import pygame

from src import settings


class BtnColors(StrEnum):
    """Enumeration for button colors used in the UI."""

    TOP_COLOR = "#b5e48c"
    BOTTOM_COLOR = "#52b69a"
    TEXT_COLOR = "#184e77"
    HOVER_COLOR = "#99d98c"


# Initial elevation value for button
ELEVATION_INIT_VALUE = 6


@dataclass
class ButtonState:
    """Manage the state of the button including press and elevation."""

    elevation: int = field(default=ELEVATION_INIT_VALUE, init=False)
    pressed: bool = field(default=False, init=False)

    def set_pressed(self, value: bool) -> None:
        """Set the button press state and adjust the elevation accordingly.

        Args:
            value (bool): True if the button is pressed, False otherwise.
        """
        self.pressed = value
        self.elevation = 0 if value else ELEVATION_INIT_VALUE


@dataclass
class Button:
    """Create a UI button with elevation effect, hover state, and click handling.

    Attributes:
        text (str): The label displayed on the button.
        size (tuple[int, int]): The dimensions (width, height) of the button.
        pos (tuple[int, int]): The top-left position (x, y) of the button.
        on_click (Callable[[], None]): Callback function to be invoked when the button is clicked.
        show_fn (Callable[[], bool]): Function that returns True if the button should be visible.
    """

    text: str  # Button label text
    size: tuple[int, int]  # Button width and height
    pos: tuple[int, int]  # Button position (x, y)
    on_click: Callable[[], None]  # Function to call when button is clicked
    show_fn: Callable[[], bool]  # Function that determines button visibility

    state: ButtonState = field(default_factory=ButtonState, init=False)  # Button state manager

    def __post_init__(self) -> None:
        """Initialize button attributes and prepare UI elements after instantiation."""
        self.screen: pygame.Surface = pygame.display.get_surface()
        self.original_y_pos: int = self.pos[1]

        # Define the top rectangle (button face)
        self.top_rect = pygame.Rect(self.pos, self.size)
        self.top_color: pygame.Color = pygame.Color(BtnColors.TOP_COLOR)

        # Define the bottom rectangle (shadow/elevation effect)
        self.bottom_rect = pygame.Rect(self.pos, (self.size[0], self.state.elevation))
        self.bottom_color: pygame.Color = pygame.Color(BtnColors.BOTTOM_COLOR)

        # Render the button text
        self.text_surf: pygame.Surface = settings.FONT.render(self.text, True, BtnColors.TEXT_COLOR)
        self.text_rect: pygame.Rect = self.text_surf.get_rect(center=self.top_rect.center)

    def draw(self) -> None:
        """Draw the button on the screen with its current state.

        Adjusts the button's position based on its elevation and renders both the shadow and button face.
        """
        # Adjust the top rectangle's vertical position based on elevation
        self.top_rect.y = self.original_y_pos - self.state.elevation
        # Center the text on the top rectangle
        self.text_rect.center = self.top_rect.center

        # Adjust text vertical alignment to fix spacing issues
        self.text_rect.y -= (self.text_surf.get_height() - settings.FONT_ACCENT) // 2

        # Update the bottom rectangle (shadow) to align with the top rectangle
        self.bottom_rect.midtop = self.top_rect.midtop
        self.bottom_rect.height = self.top_rect.height + self.state.elevation

        # Draw the shadow (bottom rectangle) and the button face (top rectangle)
        pygame.draw.rect(self.screen, self.bottom_color, self.bottom_rect, border_radius=8)
        pygame.draw.rect(self.screen, self.top_color, self.top_rect, border_radius=8)

        # Render the button text on top of the button face
        self.screen.blit(self.text_surf, self.text_rect)

    def check_click(self) -> None:
        """Handle mouse hover and click interactions for the button.

        If the mouse is over the button and the left button is pressed, update the button state.
        When the mouse button is released after being pressed, trigger the on_click callback.
        """
        mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
        if self.top_rect.collidepoint(mouse_pos):
            # Change button face color to indicate hover state
            self.top_color = pygame.Color(BtnColors.HOVER_COLOR)
            if pygame.mouse.get_pressed()[0]:
                # If mouse button is pressed and button is not already in pressed state,
                # update the state to indicate a press.
                if not self.state.pressed:
                    self.state.set_pressed(True)
            else:
                # If mouse button is released and button was previously pressed,
                # trigger the click action.
                if self.state.pressed:
                    self.on_click()
                self.state.set_pressed(False)
        else:
            # Reset button color and state if mouse is not over the button
            self.top_color = pygame.Color(BtnColors.TOP_COLOR)
            self.state.set_pressed(False)

    def update(self) -> None:
        """Update the button state and render it if it should be visible.

        Checks for user interaction and redraws the button accordingly.
        """
        if self.show_fn():
            self.check_click()
            self.draw()
