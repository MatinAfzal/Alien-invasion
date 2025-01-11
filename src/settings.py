import pygame
import json
import os
from src.input_handler import InputHandler

class Settings:
    """A class to store all settings for Alien Invasion."""

    def __init__(self):
        """Initialize the game's settings."""
        # Screen settings
        self.min_width = 800
        self.min_height = 600
        self.screen_width = 1280
        self.screen_height = 720
        self.fullscreen = False
        self.bg_color = (0, 0, 0)
        self.fps = 60

        # Background scrolling
        self.bg_screen_x = 0
        self.bg_screen_y = 0
        self.bg_screen_2_x = 0
        self.bg_screen_2_y = -self.screen_height
        self.bg_scroll_speed = 1

        # Input handler
        self.input_handler = InputHandler()

        # Ship settings
        self.ship_limit = 3
        self.ship_speed_factor_x = 2.5
        self.ship_speed_factor_y = 1.5

        # Bullet settings
        self.bullet_speed_factor = 3
        self.bullet_width = 3
        self.bullet_height = 15
        self.bullet_color = 60, 60, 60
        self.bullets_allowed = 3

        # Alien settings
        self.alien_speed_factor = 2
        self.cargo_speed_factor = 0.5
        self.fleet_drop_speed = 10
        self.cargo_drop_chance = 10
        self.alien_bullet_speed_factor = 1.5
        self.alien_fire_chance = 3  # Chance out of 1000 for alien to fire

        # Menu settings
        self.music_on = True
        self.sound_fx_on = True
        self.difficulty = "Medium"

        # How quickly the game speeds up
        self.speedup_scale = 1.1
        # How quickly the alien point values increase
        self.score_scale = 1.5

        # Scoring
        self.alien_points = 50
        self.cargo_points = 100

        # Debug settings
        self.debug_key = pygame.K_F3  # F3 key for debug toggle

        # Load saved settings if they exist
        self.load_settings()
        
        # Initialize dynamic settings
        self.initialize_dynamic_settings()

    def save_settings(self):
        """Save settings to a JSON file."""
        settings_data = {
            'resolution_index': self.resolution_index,
            'fullscreen': self.fullscreen,
            'music_on': self.music_on,
            'sound_fx_on': self.sound_fx_on,
            'difficulty': self.difficulty,
            'key_bindings': {
                action: self.input_handler.get_key_name(key)
                for action, key in self.input_handler.key_bindings.items()
                if action not in ['quit', 'pause']  # Don't save system keys
            }
        }
        
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            with open('data/game_settings.json', 'w') as f:
                json.dump(settings_data, f, indent=4)
            print("Settings saved successfully")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        """Load settings from JSON file."""
        try:
            if os.path.exists('data/game_settings.json'):
                with open('data/game_settings.json', 'r') as f:
                    settings_data = json.load(f)
                
                # Apply loaded settings
                self.resolution_index = settings_data.get('resolution_index', self.resolution_index)
                self.screen_width, self.screen_height = self.available_resolutions[self.resolution_index]
                self.fullscreen = settings_data.get('fullscreen', self.fullscreen)
                self.music_on = settings_data.get('music_on', self.music_on)
                self.sound_fx_on = settings_data.get('sound_fx_on', self.sound_fx_on)
                self.difficulty = settings_data.get('difficulty', self.difficulty)
                
                # Load key bindings
                key_bindings = settings_data.get('key_bindings', {})
                for action, key_name in key_bindings.items():
                    try:
                        # Convert key name to key code
                        key = getattr(pygame, f'K_{key_name}')
                        self.input_handler.set_key_binding(action, key)
                    except AttributeError:
                        print(f"Error loading key binding for {action}: {key_name}")
                
                print("Settings loaded successfully")
        except Exception as e:
            print(f"Error loading settings: {e}")
            # If there's an error, we'll use default settings

    def get_resolution(self):
        """Get current resolution."""
        return self.available_resolutions[self.resolution_index]

    def cycle_resolution(self):
        """Cycle to next available resolution."""
        old_resolution = self.get_resolution()
        self.resolution_index = (self.resolution_index + 1) % len(self.available_resolutions)
        new_resolution = self.get_resolution()
        
        # Update screen dimensions
        if not self.fullscreen:  # Only update dimensions if not in fullscreen
            self.screen_width, self.screen_height = new_resolution
        
        return new_resolution

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.fullscreen = not self.fullscreen
        return self.fullscreen

    def set_resolution(self, width, height):
        """Set custom resolution (used for fullscreen)."""
        self.screen_width = width
        self.screen_height = height

    def get_key_name(self, key_code):
        """Get the name of a key."""
        return self.input_handler.get_key_name(key_code)

    def update_key_binding(self, action, new_key):
        """Update a key binding."""
        if new_key != pygame.K_ESCAPE:  # Don't allow binding Escape key
            return self.input_handler.set_key_binding(action, new_key)
        return False

    def is_key_for_action(self, key, action):
        """Check if a key is bound to an action."""
        return self.input_handler.get_current_binding(action) == key

    def initialize_dynamic_settings(self):
        """Initialize settings that change throughout the game."""
        self.apply_difficulty_settings()
        self.fleet_direction = 1
        self.alien_points = 50
        self.cargo_points = 100
        self.cargo_drop_chance = 0  # Start with no cargo ships
        self.ship_speed_factor_x = 2.5
        self.ship_speed_factor_y = 1.5
        self.bullet_speed_factor = 3
        self.alien_speed_factor = 2
        self.cargo_speed_factor = 0.5
        self.alien_bullet_speed_factor = 1.5

    def apply_difficulty_settings(self):
        """Apply settings based on difficulty level."""
        if self.difficulty == "Easy":
            self.ship_speed_factor_x = 1.0
            self.ship_speed_factor_y = 0.7
            self.bullet_speed_factor = 2
            self.alien_speed_factor = 0.5
            self.cargo_speed_factor = 1
            self.speedup_scale = 1.1
            self.cargo_drop_chance = 2  # 2% chance per update
        elif self.difficulty == "Medium":
            self.ship_speed_factor_x = 1.5
            self.ship_speed_factor_y = 1.0
            self.bullet_speed_factor = 3
            self.alien_speed_factor = 1.0
            self.cargo_speed_factor = 1.5
            self.speedup_scale = 1.2
            self.cargo_drop_chance = 3  # 3% chance per update
        else:  # Hard
            self.ship_speed_factor_x = 2.0
            self.ship_speed_factor_y = 1.5
            self.bullet_speed_factor = 4
            self.alien_speed_factor = 1.5
            self.cargo_speed_factor = 2
            self.speedup_scale = 1.3
            self.cargo_drop_chance = 5  # 5% chance per update

    def increase_speed(self):
        """Increase speed settings."""
        self.ship_speed_factor_x *= self.speedup_scale
        self.ship_speed_factor_y *= self.speedup_scale
        self.bullet_speed_factor *= self.speedup_scale
        self.alien_speed_factor *= self.speedup_scale
        self.cargo_speed_factor *= self.speedup_scale
        self.alien_bullet_speed_factor *= self.speedup_scale
        self.cargo_drop_chance *= self.speedup_scale
        self.alien_points = int(self.alien_points * self.score_scale)

    def handle_resize(self, width, height):
        """Handle window resize event, enforcing minimum size."""
        self.screen_width = max(width, self.min_width)
        self.screen_height = max(height, self.min_height)
        return self.screen_width, self.screen_height
