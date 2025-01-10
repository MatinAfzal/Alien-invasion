import pygame

class Menu:
    def __init__(self, screen, title):
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.width, self.height = 500, 600
        self.button_height = 50
        self.button_width = 400
        self.button_spacing = 20
        
        # Set colors
        self.bg_color = (0, 0, 0)
        self.text_color = (255, 255, 255)
        self.button_color = (0, 100, 200)
        self.button_hover_color = (0, 150, 255)
        
        # Create menu surface
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = self.screen_rect.center
        
        # Set up font
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 64)
        
        # Prepare title
        self.title = title
        self.title_image = self.title_font.render(title, True, self.text_color)
        self.title_rect = self.title_image.get_rect()
        self.title_rect.centerx = self.width // 2
        self.title_rect.top = 20
        
        self.buttons = []
        self.separators = []  # Track separator positions
        self.active_button = None
        self.waiting_for_key = False

    def add_button(self, text, callback):
        button_y = self.title_rect.bottom + 20 + (self.button_height + self.button_spacing) * len(self.buttons)
        button = {
            'rect': pygame.Rect((self.width - self.button_width) // 2, button_y, 
                              self.button_width, self.button_height),
            'text': text,
            'text_image': self.font.render(text, True, self.text_color),
            'callback': callback,
            'hover': False,
            'is_separator': False
        }
        button['text_rect'] = button['text_image'].get_rect()
        button['text_rect'].center = button['rect'].center
        self.buttons.append(button)

    def add_separator(self):
        """Add a visual separator between buttons"""
        separator = {
            'rect': pygame.Rect((self.width - self.button_width) // 2, 
                              self.title_rect.bottom + 20 + (self.button_height + self.button_spacing) * len(self.buttons), 
                              self.button_width, self.button_spacing),
            'is_separator': True,
            'hover': False
        }
        self.buttons.append(separator)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.handle_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_click(event.pos)

    def handle_hover(self, pos):
        # Adjust position for menu location
        adjusted_pos = (pos[0] - (self.screen_rect.width - self.width) // 2,
                       pos[1] - (self.screen_rect.height - self.height) // 2)
        
        for button in self.buttons:
            if not button['is_separator']:
                button['hover'] = button['rect'].collidepoint(adjusted_pos)

    def handle_click(self, pos):
        # Adjust position for menu location
        adjusted_pos = (pos[0] - (self.screen_rect.width - self.width) // 2,
                       pos[1] - (self.screen_rect.height - self.height) // 2)
        
        for button in self.buttons:
            if not button['is_separator'] and button['rect'].collidepoint(adjusted_pos):
                button['callback']()
                break

    def draw(self):
        # Create menu surface
        menu_surface = pygame.Surface((self.width, self.height))
        menu_surface.fill(self.bg_color)
        
        # Draw title
        menu_surface.blit(self.title_image, self.title_rect)
        
        # Draw buttons and separators
        for button in self.buttons:
            if button['is_separator']:
                # Draw separator line
                pygame.draw.line(menu_surface, (100, 100, 100),
                               (button['rect'].left, button['rect'].centery),
                               (button['rect'].right, button['rect'].centery), 2)
            else:
                # Draw button
                color = self.button_hover_color if button['hover'] else self.button_color
                if button['text'].startswith("Back"):  # Special style for back button
                    color = (100, 100, 100) if button['hover'] else (50, 50, 50)
                pygame.draw.rect(menu_surface, color, button['rect'])
                menu_surface.blit(button['text_image'], button['text_rect'])
        
        # Draw menu on screen
        menu_rect = menu_surface.get_rect()
        menu_rect.center = self.screen_rect.center
        self.screen.blit(menu_surface, menu_rect)


class MainMenu(Menu):
    def __init__(self, screen, start_game, show_settings, quit_game):
        super().__init__(screen, "Alien Invasion")
        self.add_button("Play", start_game)
        self.add_button("Settings", show_settings)
        self.add_button("Quit", quit_game)


class SettingsMenu(Menu):
    def __init__(self, screen, ai_settings, back_to_main):
        super().__init__(screen, "Settings")
        self.ai_settings = ai_settings
        self.back_to_main = back_to_main
        
        # Game Settings
        self.add_button("Music: " + ("On" if ai_settings.music_on else "Off"), 
                       self.toggle_music)
        self.add_button("Sound FX: " + ("On" if ai_settings.sound_fx_on else "Off"), 
                       self.toggle_sound_fx)
        self.add_button("Difficulty: " + ai_settings.difficulty, 
                       self.cycle_difficulty)
        
        # Display Settings
        current_res = f"{ai_settings.screen_width}x{ai_settings.screen_height}"
        self.add_button(f"Resolution: {current_res}",
                       self.cycle_resolution)
        self.add_button("Fullscreen: " + ("On" if ai_settings.fullscreen else "Off"),
                       self.toggle_fullscreen)
        
        # Controls submenu button
        self.add_button("Controls...", self.show_controls_menu)
        
        # Back button
        self.add_button("Back", self.save_and_back)
        
        self.controls_menu = None

    def save_and_back(self):
        """Save settings before going back to main menu."""
        self.ai_settings.save_settings()
        self.back_to_main()

    def toggle_music(self):
        self.ai_settings.music_on = not self.ai_settings.music_on
        self.buttons[0]['text'] = "Music: " + ("On" if self.ai_settings.music_on else "Off")
        self.buttons[0]['text_image'] = self.font.render(self.buttons[0]['text'], True, self.text_color)

    def toggle_sound_fx(self):
        self.ai_settings.sound_fx_on = not self.ai_settings.sound_fx_on
        self.buttons[1]['text'] = "Sound FX: " + ("On" if self.ai_settings.sound_fx_on else "Off")
        self.buttons[1]['text_image'] = self.font.render(self.buttons[1]['text'], True, self.text_color)

    def cycle_difficulty(self):
        difficulties = ["Easy", "Medium", "Hard"]
        current_index = difficulties.index(self.ai_settings.difficulty)
        next_index = (current_index + 1) % len(difficulties)
        self.ai_settings.difficulty = difficulties[next_index]
        self.ai_settings.apply_difficulty_settings()
        self.buttons[2]['text'] = "Difficulty: " + self.ai_settings.difficulty
        self.buttons[2]['text_image'] = self.font.render(self.buttons[2]['text'], True, self.text_color)

    def show_controls_menu(self):
        self.controls_menu = ControlsMenu(self.screen, self.ai_settings, self.hide_controls_menu)

    def hide_controls_menu(self):
        self.controls_menu = None

    def handle_event(self, event):
        if self.controls_menu:
            self.controls_menu.handle_event(event)
        else:
            super().handle_event(event)

    def draw(self):
        if self.controls_menu:
            self.controls_menu.draw()
        else:
            super().draw()

    def cycle_resolution(self):
        new_res = self.ai_settings.cycle_resolution()
        self.buttons[3]['text'] = f"Resolution: {new_res[0]}x{new_res[1]}"
        self.buttons[3]['text_image'] = self.font.render(self.buttons[3]['text'], True, self.text_color)

    def toggle_fullscreen(self):
        is_fullscreen = self.ai_settings.toggle_fullscreen()
        self.buttons[4]['text'] = "Fullscreen: " + ("On" if is_fullscreen else "Off")
        self.buttons[4]['text_image'] = self.font.render(self.buttons[4]['text'], True, self.text_color)


class ControlsMenu(Menu):
    def __init__(self, screen, ai_settings, back_callback):
        super().__init__(screen, "Controls")
        self.ai_settings = ai_settings
        self.waiting_for_key = False
        self.current_action = None
        
        # Add buttons for each control
        self.action_buttons = {}  # Keep track of buttons by action
        
        # Define the order and display names of controls
        control_order = [
            ('move_up', 'Move Up'),
            ('move_down', 'Move Down'),
            ('move_left', 'Move Left'),
            ('move_right', 'Move Right'),
            ('fire', 'Fire')
        ]
        
        # Add buttons in specific order
        for action, display_name in control_order:
            key = self.ai_settings.input_handler.get_current_binding(action)
            if key is not None:  # If the action has a key binding
                key_name = self.ai_settings.input_handler.get_key_name(key)
                button_text = f"{display_name}: {key_name}"
                self.add_button(button_text, lambda a=action: self.start_rebind(a))
                self.action_buttons[action] = len(self.buttons) - 1
        
        # Add a separator line
        self.add_separator()
        
        # Add back button with different style
        self.add_button("Back to Settings", back_callback)

    def start_rebind(self, action):
        if not self.waiting_for_key:
            self.waiting_for_key = True
            self.current_action = action
            
            # Update button text to show waiting state
            button_index = self.action_buttons[action]
            action_display = action.replace('_', ' ').title()
            self.buttons[button_index]['text'] = f"Press any key for {action_display}..."
            self.buttons[button_index]['text_image'] = self.font.render(
                self.buttons[button_index]['text'], True, (255, 255, 0)  # Yellow text for waiting state
            )
            # Update text rect position
            self.buttons[button_index]['text_rect'] = self.buttons[button_index]['text_image'].get_rect()
            self.buttons[button_index]['text_rect'].center = self.buttons[button_index]['rect'].center

    def handle_event(self, event):
        if self.waiting_for_key:
            if event.type == pygame.KEYDOWN:
                if event.key != pygame.K_ESCAPE:  # Don't allow binding Escape key
                    # Try to update the key binding
                    if self.ai_settings.input_handler.set_key_binding(self.current_action, event.key):
                        # Update all button texts since keys might have been swapped
                        for action, button_index in self.action_buttons.items():
                            key = self.ai_settings.input_handler.get_current_binding(action)
                            key_name = self.ai_settings.input_handler.get_key_name(key)
                            action_display = action.replace('_', ' ').title()
                            self.buttons[button_index]['text'] = f"{action_display}: {key_name}"
                            self.buttons[button_index]['text_image'] = self.font.render(
                                self.buttons[button_index]['text'], True, self.text_color
                            )
                            self.buttons[button_index]['text_rect'] = self.buttons[button_index]['text_image'].get_rect()
                            self.buttons[button_index]['text_rect'].center = self.buttons[button_index]['rect'].center
                self.waiting_for_key = False
                self.current_action = None
        else:
            super().handle_event(event)

    def draw(self):
        # Create menu surface
        menu_surface = pygame.Surface((self.width, self.height))
        menu_surface.fill(self.bg_color)
        
        # Draw title
        menu_surface.blit(self.title_image, self.title_rect)
        
        # Draw buttons and separators
        for button in self.buttons:
            if button['is_separator']:
                # Draw separator line
                pygame.draw.line(menu_surface, (100, 100, 100),
                               (button['rect'].left, button['rect'].centery),
                               (button['rect'].right, button['rect'].centery), 2)
            else:
                # Draw button
                color = self.button_hover_color if button['hover'] else self.button_color
                if button['text'].startswith("Back"):  # Special style for back button
                    color = (100, 100, 100) if button['hover'] else (50, 50, 50)
                pygame.draw.rect(menu_surface, color, button['rect'])
                menu_surface.blit(button['text_image'], button['text_rect'])
                
                # Draw key binding status if waiting
                if self.waiting_for_key and button.get('text', '').startswith(self.current_action.replace('_', ' ').title()):
                    pygame.draw.rect(menu_surface, (255, 255, 0), button['rect'], 2)  # Yellow border
        
        # Draw menu on screen
        menu_rect = menu_surface.get_rect()
        menu_rect.center = self.screen_rect.center
        self.screen.blit(menu_surface, menu_rect) 