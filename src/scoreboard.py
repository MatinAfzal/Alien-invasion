import pygame.font

class Scoreboard:
    def __init__(self, ai_settings, screen, stats):
        """Initialize score keeping attributes."""
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self.ai_settings = ai_settings
        self.stats = stats

        # Font settings for scoring information.
        self.text_color = (0, 180, 0)
        self.font = pygame.font.Font("data/assets/fonts/sevenSegment.ttf", 48)
    
        # Background settings
        self.bg_color = (0, 0, 0, 128)  # Semi-transparent black
        self.bg_rect = pygame.Rect(0, 0, 250, 60)  # Adjust size as needed
        self.bg_rect.right = self.screen_rect.right - 10
        self.bg_rect.top = 10
    
        # Load the icon
        self.icon = pygame.image.load("data/assets/images/star_icon.png")  # Replace with your icon path
        self.icon = pygame.transform.scale(self.icon, (30, 30))  # Resize the icon
    
        # Prepare the initial score image.
        self.prep_score()

    def prep_score(self):
        """Turn the score into a rendered image."""
        score_str = str(self.stats.score).zfill(4)

        # Render the shadow
        shadow_color = (0, 0, 0)  # Black shadow
        shadow_offset = 2  # Shadow offset in pixels
        self.shadow_image = self.font.render(score_str, True, shadow_color)
        self.shadow_rect = self.shadow_image.get_rect()
        self.shadow_rect.right = self.screen_rect.right - 20 + shadow_offset
        self.shadow_rect.top = 20 + shadow_offset

        # Render the main score with animation
        self.score_image = self.font.render(score_str, True, self.text_color)
        self.score_rect = self.score_image.get_rect()
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.top = 20

        # Animation effect
        self.animation_timer = 10  # Duration of the animation


    def show_score(self):
        """Draw score to the screen."""
        # Draw the background
        bg_surface = pygame.Surface((self.bg_rect.width, self.bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill(self.bg_color)
        self.screen.blit(bg_surface, self.bg_rect)

        # Draw the shadow
        self.screen.blit(self.shadow_image, self.shadow_rect)

        # Draw the score with animation
        if self.animation_timer > 0:
            scale_factor = 1 + (self.animation_timer / 20)  # Scale up the score
            scaled_image = pygame.transform.scale(self.score_image, (int(self.score_rect.width * scale_factor), int(self.score_rect.height * scale_factor)))
            scaled_rect = scaled_image.get_rect(center=self.score_rect.center)
            self.screen.blit(scaled_image, scaled_rect)
            self.animation_timer -= 1
        else:
            self.screen.blit(self.score_image, self.score_rect)

        #     Draw the icon
        icon_rect = self.icon.get_rect(right=self.score_rect.left - 10, centery=self.score_rect.centery)
        self.screen.blit(self.icon, icon_rect)
