import math

import inject
import pygame

from src import settings
from src.entities.sprites.bullet import Bullet
from src.sprite_manager import SpritesManager
from src.utils.timer import Timer


class Player(pygame.sprite.Sprite):
    PLAYER_SPEED = 300
    sprite_manager: SpritesManager = inject.attr(SpritesManager)

    def __init__(self, pos: tuple[int, int], offset: pygame.math.Vector2 = pygame.math.Vector2(0, 0)) -> None:
        super().__init__()
        self.screen: pygame.Surface = pygame.display.get_surface()
        self.original_image: pygame.Surface = pygame.transform.scale(
            pygame.image.load(settings.ASSETS_DIR / "sprites" / "ship.png"),
            (200, 200),
        )
        self.image: pygame.Surface = self.original_image.copy()
        self.rect: pygame.Rect = self.image.get_rect()
        self.rect.centerx = pos[0]
        self.rect.centery = pos[1]
        self.rect.bottom = self.screen.get_rect().bottom - self.rect.height + 64
        self.angle = 0
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.center)
        self.fire_timer = Timer(700)
        # دریافت offset از بیرون (با مقدار دیفالت)
        self.offset = offset

    def input(self, dt: float) -> None:
        keys: pygame.key.ScancodeWrapper = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction.y = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction.y = 1
        else:
            self.direction.y = 0

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
        else:
            self.direction.x = 0

        if pygame.mouse.get_pressed()[0] and not self.fire_timer.active:
            self.fire_timer.activate()
            self.fire()

        # دریافت موقعیت موس (screen coordinates)
        mouse_screen: tuple[int, int] = pygame.mouse.get_pos()
        # تبدیل به world coordinates با در نظر گرفتن offset
        mouse_world = pygame.math.Vector2(mouse_screen) + self.offset

        x_dist: float = mouse_world.x - self.pos.x
        y_dist: float = -(mouse_world.y - self.pos.y)
        target_angle = math.degrees(math.atan2(y_dist, x_dist))
        diff = (target_angle - self.angle + 180) % 360 - 180
        self.angle += diff * 20 * dt

    def move(self, dt: float) -> None:
        if self.direction.magnitude():
            self.direction = self.direction.normalize()
        self.pos.x += self.direction.x * self.PLAYER_SPEED * dt
        self.pos.y += self.direction.y * self.PLAYER_SPEED * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.image = pygame.transform.rotate(self.original_image, self.angle - 90)
        self.rect = self.image.get_rect(center=self.rect.center)

        # self.rect.center -= self.offset

    def update(self, dt: float) -> None:
        print(self.offset)
        print(self.rect.center)
        self.fire_timer.update()
        self.input(dt)
        self.move(dt)

    def draw(self) -> None:
        self.screen.blit(self.image, self.rect)

    def center_ship(self) -> None:
        self.pos.x = self.screen.get_rect().centerx
        self.pos.y = self.screen.get_rect().bottom - self.rect.height

    def fire(self) -> None:
        self.sprite_manager.sprites.add(Bullet(self.pos.x, self.pos.y, self.angle))
