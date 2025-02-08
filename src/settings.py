class Settings:
    """A class to store all settings for Alien Invasion"""
     
    def __init__(self):
        # Debug mode
        self.debug_mode = True  # Set to False to show the loading screen
        """Initialize the game's static settings."""
        # Clock
        self.fps = 120.0
        self.delta_time = (1000.0 / self.fps) / 10
        self.default_animation_latency = self.delta_time / 500

        # Screen settings
        self.screen_width = 1200
        self.screen_height = 800
        self.bg_color = (225, 225, 255)

        # Ship settings
        self.ship_speed_factor_x = 3
        self.ship_speed_factor_y = 3
        self.ship_limit = 2

        # Bullets settings
        self.bullet_speed_factor = 10
        self.bullet_width = 3
        self.bullet_height = 15
        self.bullet_color = 60, 60, 60
        self.bullets_allowed = 5
        self.alien_bullet_speed_factor = 5

        # Alien settings
        self.alien_speed_factor = 5
        self.cargo_speed_factor = 0.5
        self.fleet_drop_speed = 2
        self.cargo_drop_chance = 0  # TODO: There is an interesting bug in hereش
        self.alien_fire_chance = 100  # from 1000
        self.alien_l2_fire_chance = 200  # from 1000
        self.alien_l2_health = 2
        self.alien_l1_health = 1
        self.alien_l2_spawn_chance = 5

        # Drop down items setting
        self.generate_heart_chance = 10  # from 1000
        self.generate_shield_chance = 10  # from 1000
        self.shield_time = 10  # in seconds

        # How quickly the game speeds up
        self.speedup_scale = 1.1

        # How quickly the alien point values increase
        self.score_scale = 1.5

        self.alien_points = 50
        self.cargo_points = 100

        self.initialize_dynamic_settings()

        # screen background settings.
        self.bg_screen_x = 0
        self.bg_screen_y = 0
        self.bg_screen_2_x = 0
        self.bg_screen_2_y = -self.screen_height
        self.bg_screen_scroll_speed = 0.2

        # lives settings.
        self.init_hearts = 5
        self.max_hearts = 5

    def initialize_dynamic_settings(self):
        """Increase speed settings and alien point values."""
        # self.ship_speed_factor_x = 2.5
        # self.ship_speed_factor_y = 1.5
        # self.bullet_speed_factor = 3
        self.heart_speed_factor = 4
        self.alien_speed_factor = 2
        self.cargo_speed_factor = 0.5
        self.cargo_drop_chance = 0

        # Scoring
        self.alien_points = 10

    def increase_speed(self):
        """Increase speed settings."""
        self.ship_speed_factor_x *= self.speedup_scale
        self.ship_speed_factor_y *= self.speedup_scale
        self.bullet_speed_factor *= self.speedup_scale
        self.alien_speed_factor *= self.speedup_scale
        self.cargo_speed_factor *= self.speedup_scale
        self.cargo_drop_chance *= self.speedup_scale
        self.alien_l2_spawn_chance *= self.speedup_scale
        self.alien_points = int(self.alien_points * self.score_scale)
        # self.bullet_width += 4
