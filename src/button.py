import pygame
import pygame.font
from pygame import Color
pygame.mixer.init()


class Button:
    """A class to create button.

    Args:
        screen (pygame.Surface): Game screen
        input (src.input.Input): Game input handler
        position (tuple[int, int]): Button position on screen
        size (tuple[int, int]): Button height and width
        text (str): Button text
        font (pygame.font.Font): Button text font
        foreground_color (tuple[int, int, int]): Button text color
        background_color (tuple[int, int, int]): Button background color
        hover_color (tuple[int, int, int]): Button background color when hovered
        border_width (int): Button border width. Set to zero for no border
        border_color (tuple[int, int, int]): Button border color
        display_condition (() -> bool): Button display condition. Leave empty to be always displayed
        on_clicked (() -> Any): A function to run when button is clicked
        icon (pygame.Surface): An optional icon to display next to the text
    """

    def __init__(
            self,
            screen,
            input,
            position=(0, 0),
            size=(200, 50),
            text="",
            font=None,
            foreground_color=(255, 255, 255),
            background_color=(0, 0, 0),
            hover_color=None,
            border_width=1,
            border_color=(255, 255, 255),
            display_condition=None,
            on_clicked=None,
            icon=None):

        self.screen = screen
        self.input = input
        self.position = list(position)
        self.original_size = list(size)
        self.size = list(size)
        self.text = text
        self.font = font if font else pygame.font.Font(None, 48)
        self.foreground_color = foreground_color
        self.background_color = background_color
        self.hover_color = hover_color if hover_color else self.__lighten_color(background_color)
        self.border_width = border_width
        self.border_color = border_color
        self.display_condition = display_condition
        self.on_clicked = on_clicked
        self.icon = icon

        self.__sound = pygame.mixer.Sound("data/assets/sounds/button_clicked.mp3")
        self.__sound.set_volume(0.35)
        self.__hovered = False
        self.__clicked = False
        self.__scale = 1.0
        self.__target_scale = 1.0

    def update(self):
        """Must be called every frame."""
        if self.input is None:
            return

        if self.__should_display():
            self.__set_hovered()
            self.__set_clicked()
            self.__animate()
            self.__draw()

    #
    #  Update helper methods
    #

    def __set_hovered(self):
        cursor = self.input.get_mouse_cursor_position()
        self.__hovered = self.__is_within_bounds(cursor, (self.position[0], self.position[1], self.size[0], self.size[1]))

        # Set target scale for hover effect
        self.__target_scale = 1.1 if self.__hovered else 1.0

    def __set_clicked(self):
        if self.__hovered and self.input.is_mouse_button_pressed(0):
            self.__sound.play()
            self.__clicked = True
            self.__target_scale = 0.95  # Click effect
            if self.on_clicked is not None:
                self.on_clicked()
        else:
            self.__clicked = False

    def __animate(self):
        """Smoothly animate the button scale."""
        self.__scale += (self.__target_scale - self.__scale) * 0.2
        self.size[0] = int(self.original_size[0] * self.__scale)
        self.size[1] = int(self.original_size[1] * self.__scale)

    @staticmethod
    def __is_within_bounds(position, rect):
        return ((position[0] >= rect[0]) and (position[0] <= rect[0] + rect[2]) and (position[1] >= rect[1])
                and (position[1] <= rect[1] + rect[3]))

    def __draw(self):
        self.__draw_shadow()
        self.__draw_background()
        self.__draw_text()
        self.__draw_border()

    #
    #  Draw helper methods
    #

    def __draw_shadow(self):
        """Draws a shadow under the button."""
        shadow_offset = 5
        shadow_rect = pygame.Rect(
            self.position[0] + shadow_offset,
            self.position[1] + shadow_offset,
            self.size[0],
            self.size[1]
        )
        pygame.draw.rect(self.screen, (0, 0, 0, 100), shadow_rect, border_radius=10)

    def __draw_background(self):
        """Draws the button background with hover effect."""
        bg_color = self.hover_color if self.__hovered else self.background_color
        button_rect = pygame.Rect(self.position[0], self.position[1], self.size[0], self.size[1])
        pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=10)

    def __draw_text(self):
        """Draws the button text with icon (if any)."""
        text_image = self.font.render(self.text, True, self.foreground_color, None)
        text_rect = text_image.get_rect(center=(
            self.position[0] + self.size[0] // 2,
            self.position[1] + self.size[1] // 2
        ))

        if self.icon:
            icon_rect = self.icon.get_rect(center=(text_rect.left - 30, text_rect.centery))
            self.screen.blit(self.icon, icon_rect)

        self.screen.blit(text_image, text_rect)

    def __draw_border(self):
        """Draws the button border with rounded corners."""
        if self.border_width > 0:
            border_rect = pygame.Rect(self.position[0], self.position[1], self.size[0], self.size[1])
            pygame.draw.rect(self.screen, self.border_color, border_rect, self.border_width, border_radius=10)

    def __should_display(self):
        if self.display_condition is not None:
            if isinstance(self.display_condition, bool):
                return self.display_condition
            else:
                return self.display_condition()
        return True

    @staticmethod
    def __lighten_color(color, factor=1.5):
        """Lighten the given color by a factor."""
        return tuple(min(int(c * factor), 255) for c in color)
