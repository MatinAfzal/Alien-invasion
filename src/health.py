import pygame
from src.button import Button

class Health:
    """A class for manging and show user lives."""
    def __init__(self, ai_settings, screen):
        """Initialize class properties."""
        self.ai_settings = ai_settings
        self.screen = screen
        self.current_hearts = 0


    def initHealth(self):
        #todo: method description
        if self.ai_settings.init_hearts > self.ai_settings.max_hearts:
            return 
        self.current_hearts = self.ai_settings.init_hearts

    def fullHealth(self):
        #todo: method description
        self.current_hearts = self.ai_settings.max_hearts

    def addHealth(self):
        #todo: method description
        if self.current_hearts + 1 > self.ai_settings.max_hearts:
            return
        self.current_hearts += 1

    def decreaseHealth(self, damage):
        #todo: method description        

        self.current_hearts -= damage

    def show_health(self):
        HEART_SIZE = 20
        heart_full = pygame.image.load('data/assets/hearts/full_heart.png')
        heart_empty = pygame.image.load('data/assets/hearts/empty_heart.png') 
        
        heart_full = pygame.transform.scale(heart_full, (HEART_SIZE, HEART_SIZE))
        heart_empty = pygame.transform.scale(heart_empty, (HEART_SIZE, HEART_SIZE))
        health_rect = self.screen.get_rect()
        health_rect.top = 20
        health_rect.left = health_rect.left + 20
        for i in range(1, self.ai_settings.max_hearts + 1):
            if i <= self.current_hearts:
                self.screen.blit(heart_full, health_rect)
            else:
                self.screen.blit(heart_empty, health_rect)
            health_rect.left = health_rect.left + 25

