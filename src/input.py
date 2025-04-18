import pygame


class Input:
    """Handle Pygame input more easily, including key/mouse press, release and double-press."""

    def __init__(self):
        self.double_press_timeout = 30  # milliseconds

        # set current and previous states
        self.current_key_states = pygame.key.get_pressed()
        self.previous_key_states = pygame.key.get_pressed()
        self.current_mouse_button_states = pygame.mouse.get_pressed()
        self.previous_mouse_button_states = pygame.mouse.get_pressed()

        # store previous mouse position
        self.current_mouse_position = pygame.mouse.get_pos()
        self.previous_mouse_position = pygame.mouse.get_pos()

        # set long press durations
        self.__key_press_durations = [
            0 for _ in range(len(self.current_key_states))
        ]
        self.__mouse_button_durations = [
            0 for _ in range(len(self.current_mouse_button_states))
        ]

        # store info to determine button double-press
        self.__key_time_since_last_pressed = [
            0 for _ in range(len(self.current_key_states))
        ]
        self.__mouse_time_since_last_pressed = [
            0 for _ in range(len(self.current_mouse_button_states))
        ]

        # stores the press state of each button
        # 'none' -> 'single' -> 'double'
        self.__key_press_states = [
            "none" for _ in range(len(self.current_key_states))
        ]
        self.__mouse_press_states = [
            "none" for _ in range(len(self.current_mouse_button_states))
        ]

    def update(self):
        # update key press info
        # update key presses
        self.previous_key_states = self.current_key_states
        self.current_key_states = pygame.key.get_pressed()

        # update key press durations
        for i in range(len(self.__key_press_durations)):
            if self.current_key_states[i]:
                self.__key_press_durations[i] += 1
            else:
                self.__key_press_durations[i] = 0

        # update mouse button time since last pressed
        for i in range(len(self.__key_time_since_last_pressed)):
            if self.is_key_pressed(i):
                self.__key_time_since_last_pressed[i] = 0
            else:
                self.__key_time_since_last_pressed[i] += 1

        # update mouse button press state between
        # 'none', 'single' and 'double'
        for i in range(len(self.__key_press_states)):
            # none -> single
            if self.__key_press_states[i] == "none" and self.is_key_pressed(i):
                self.__key_press_states[i] = "single"
            # single -> double
            elif self.__key_press_states[i] == "single" and self.is_key_pressed(
                i
            ):
                self.__key_press_states[i] = "double"
            # single -> none
            elif (
                self.__key_press_states[i] == "single"
                and self.__key_time_since_last_pressed[i]
                > self.double_press_timeout
            ):
                self.__key_press_states[i] = "none"
            # double -> none
            elif self.__key_press_states[i] == "double":
                self.__key_press_states[i] = "none"

        #
        # update mouse button info
        #

        # update mouse presses
        self.previous_mouse_button_states = self.current_mouse_button_states
        self.current_mouse_button_states = pygame.mouse.get_pressed()

        # update mouse position
        self.previous_mouse_position = self.current_mouse_position
        self.current_mouse_position = pygame.mouse.get_pos()

        # update mouse button press durations
        for i in range(len(self.__mouse_button_durations)):
            if self.current_mouse_button_states[i]:
                self.__mouse_button_durations[i] += 1
            else:
                self.__mouse_button_durations[i] = 0

        # update mouse button time since last pressed
        for i in range(len(self.__mouse_time_since_last_pressed)):
            if self.is_mouse_button_pressed(i):
                self.__mouse_time_since_last_pressed[i] = 0
            else:
                self.__mouse_time_since_last_pressed[i] += 1

        # update mouse button press state between
        # 'none', 'single' and 'double'
        for i in range(len(self.__mouse_press_states)):
            # none -> single
            if self.__mouse_press_states[
                i
            ] == "none" and self.is_mouse_button_pressed(i):
                self.__mouse_press_states[i] = "single"
            # single -> double
            elif self.__mouse_press_states[
                i
            ] == "single" and self.is_mouse_button_pressed(i):
                self.__mouse_press_states[i] = "double"
            # single -> none
            elif (
                self.__mouse_press_states[i] == "single"
                and self.__mouse_time_since_last_pressed[i]
                > self.double_press_timeout
            ):
                self.__mouse_press_states[i] = "none"
            # double -> none
            elif self.__mouse_press_states[i] == "double":
                self.__mouse_press_states[i] = "none"

    #
    # key methods
    #

    def is_key_down(self, key_code):
        """
        Returns true if the key denoted by keyCode is held down during the current frame.

        :param pygame.Key key_code: The key to check.
        """

        if self.current_key_states is None or self.previous_key_states is None:
            return False
        return self.current_key_states[key_code]

    def is_key_pressed(self, key_code):
        """
        Returns true if the key denoted by keyCode has been pressed down during the current frame.

        :param pygame.Key key_code: The key to check.
        """

        if self.current_key_states is None or self.previous_key_states is None:
            return False
        return (
            self.current_key_states[key_code]
            and not self.previous_key_states[key_code]
        )

    def is_key_double_pressed(self, key_code):
        """
        Returns true if the key denoted by keyCode has been double-pressed during the current frame.

        :param pygame.Key key_code: The key to check.
        """

        return self.__key_press_states[key_code] == "double"

    def is_key_released(self, key_code):
        """
        Returns true if the key denoted by keyCode has been released during the current frame.

        :param pygame.Key key_code: The key to check.
        """

        if self.current_key_states is None or self.previous_key_states is None:
            return False
        return (
            not self.current_key_states[key_code]
            and self.previous_key_states[key_code]
        )

    def get_key_down_duration(self, key_code):
        """
        Returns the number of frames a keyCode has been held down.

        :param pygame.Key key_code: The key to check.
        """

        return self.__key_press_durations[key_code]

    #
    # mouse methods
    #

    def get_mouse_cursor_position(self):
        """
        Returns the pygame mouse pointer position.
        """

        return self.current_mouse_position

    def is_mouse_button_down(self, mouse_button):
        """
        Returns true if the mouse button specified is held down during the current frame.

        :param int mouse_button: The mouse button to check.
        """

        if (
            self.current_mouse_button_states is None
            or self.previous_mouse_button_states is None
        ):
            return False
        return self.current_mouse_button_states[mouse_button]

    def is_mouse_button_pressed(self, mouse_button):
        """
        Returns true if the mouse button specified has been pressed in the current frame.

        :param int mouse_button: The mouse button to check.
        """

        if (
            self.current_mouse_button_states is None
            or self.previous_mouse_button_states is None
        ):
            return False
        return (
            self.current_mouse_button_states[mouse_button]
            and not self.previous_mouse_button_states[mouse_button]
        )

    def is_mouse_button_double_pressed(self, mouse_button):
        """
        Returns true if the mouse button specified has been double-pressed in the current frame.

        :param int mouse_button: The mouse button to check.
        """

        return self.__mouse_press_states[mouse_button] == "double"

    def is_mouse_button_released(self, mouse_button):
        """
        Returns true if the mouse button specified has been released in the current frame.

        :param int mouse_button: The mouse button to check.
        """

        if (
            self.current_mouse_button_states is None
            or self.previous_mouse_button_states is None
        ):
            return False
        return (
            not self.current_mouse_button_states[mouse_button]
            and self.previous_mouse_button_states[mouse_button]
        )

    def get_mouse_button_down_duration(self, mouse_button):
        """
        Returns the number of frames a mouse button has been held down.

        :param int mouse_button: The mouse button to check.
        """

        return self.__mouse_button_durations[mouse_button]
