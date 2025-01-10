import pygame

class Debug:
    def __init__(self, screen, ai_settings):
        self.screen = screen
        self.ai_settings = ai_settings
        self.enabled = False
        self.font = pygame.font.SysFont(None, 24)
        self.text_color = (0, 255, 0)  # Green text
        self.bg_color = (0, 0, 0, 128)  # Semi-transparent black
        self.padding = 5
        self.line_height = 20
        self.fps_clock = pygame.time.Clock()
        
    def toggle(self):
        """Toggle debug display on/off."""
        self.enabled = not self.enabled
        
    def update(self, ship, aliens, bullets, cargoes, stats):
        """Update debug info."""
        if not self.enabled:
            return
            
        self.fps = int(self.fps_clock.get_fps())
        self.ship_pos = (int(ship.rect.centerx), int(ship.rect.centery))
        self.alien_count = len(aliens)
        self.bullet_count = len(bullets)
        self.cargo_count = len(cargoes)
        self.score = stats.score
        
    def draw(self):
        """Draw debug information."""
        if not self.enabled:
            return
            
        debug_info = [
            f"FPS: {self.fps}",
            f"Ship Position: {self.ship_pos}",
            f"Aliens: {self.alien_count}",
            f"Bullets: {self.bullet_count}",
            f"Cargo Ships: {self.cargo_count}",
            f"Score: {self.score}",
            f"Resolution: {self.screen.get_width()}x{self.screen.get_height()}",
            f"Fullscreen: {bool(self.screen.get_flags() & pygame.FULLSCREEN)}"
        ]
        
        # Create background surface
        max_width = max(self.font.size(text)[0] for text in debug_info)
        height = len(debug_info) * self.line_height
        bg_surface = pygame.Surface((max_width + 2*self.padding, height + 2*self.padding))
        bg_surface.set_alpha(128)
        bg_surface.fill(self.bg_color)
        
        # Draw background
        self.screen.blit(bg_surface, (0, 0))
        
        # Draw text
        for i, text in enumerate(debug_info):
            text_surface = self.font.render(text, True, self.text_color)
            text_rect = text_surface.get_rect()
            text_rect.topleft = (self.padding, self.padding + i * self.line_height)
            self.screen.blit(text_surface, text_rect)
            
    def tick(self):
        """Update FPS clock."""
        self.fps_clock.tick() 