from dataclasses import dataclass

import pygame


@dataclass
class SpritesManager:
    sprites = pygame.sprite.Group()
