import pygame
import random
from config import GRAY_LIGHT, YELLOW_DARK, RED

from entities.base import Entity, create_explosion


class Bullet:
    image_right = None
    image_left = None

    def __init__(self, x, y, dir_x, is_player):
        self.x = float(x)
        self.y = float(y)
        self.vx = dir_x * 15
        self.width = 42
        self.height = 10
        self.is_player = is_player
        self.damage = 25 if is_player else 10
        self.active = True
        self.dir_x = dir_x

        if Bullet.image_right is None:
            try:
                img = pygame.image.load("Textures/kunai.png").convert_alpha()
                Bullet.image_right = pygame.transform.scale(img, (self.width, self.height))
                Bullet.image_left = pygame.transform.flip(Bullet.image_right, True, False)
            except Exception as e:
                print(f"Error cargando kunai.png: {e}")
                Bullet.image_right = False

    def update(self, cam_x):
        self.x += self.vx
        if self.x < cam_x - 200 or self.x > cam_x + 800 + 200:
            self.active = False

    def draw(self, surface, cam_x):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)

        if Bullet.image_right:
            if self.dir_x > 0:
                surface.blit(Bullet.image_right, (render_x, render_y))
            else:
                surface.blit(Bullet.image_left, (render_x, render_y))
        else:
            color = (253, 224, 71) if self.is_player else (239, 68, 68)
            rect = pygame.Rect(render_x, render_y, self.width, self.height)
            pygame.draw.rect(color, rect)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


class Player(Entity):
    jump_sound = None
    shoot_sound = None

    def __init__(self):
        super().__init__(100, 100, 30, 50, 100)
        self.speed = 5
        self.jump_force = -12
        self.shoot_cooldown = 0
        self.invulnerable_timer = 0
        self.anim_frame = 0

        self.frames_right = []
        self.frames_left = []

        original_size = 204
        scale_size = 80

        if Player.jump_sound is None:
            try:
                Player.jump_sound = pygame.mixer.Sound("Music/Effects/salto.wav")
                Player.jump_sound.set_volume(0.7)
            except Exception as e:
                print(f"Aviso: No se encontró salto.wav - {e}")
                Player.jump_sound = False

        if Player.shoot_sound is None:
            try:
                Player.shoot_sound = pygame.mixer.Sound("Music/Effects/kunai.wav")
                Player.shoot_sound.set_volume(0.9)
            except Exception as e:
                print(f"Aviso: No se encontró kunai.wav - {e}")
                Player.shoot_sound = False

        try:
            sheet = pygame.image.load("Textures/naruto_spritee.png").convert_alpha()
            for i in range(6):
                frame_surf = pygame.Surface((original_size, original_size), pygame.SRCALPHA)
                area_recorte = (i * original_size, 0, original_size, original_size)
                frame_surf.blit(sheet, (0, 0), area_recorte)
                frame_scaled = pygame.transform.scale(frame_surf, (scale_size, scale_size))
                self.frames_right.append(frame_scaled)
                self.frames_left.append(pygame.transform.flip(frame_scaled, True, False))
        except Exception as e:
            print(f"Error cargando el sprite de Naruto: {e}")
            fallback = pygame.Surface((scale_size, scale_size), pygame.SRCALPHA)
            fallback.fill(RED)
            self.frames_right = [fallback] * 6
            self.frames_left = [fallback] * 6

    def update(self, keys, cam_x, bullets_list, particles_list):
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -self.speed
            self.facing_right = False
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = self.speed
            self.facing_right = True
        else:
            self.vx *= 0.8

        if (keys[pygame.K_w] or keys[pygame.K_UP]) and self.is_grounded:
            self.vy = self.jump_force
            create_explosion(self.x + self.width / 2, self.y + self.height, GRAY_LIGHT, 5, particles_list)
            if Player.jump_sound:
                Player.jump_sound.play()

        if keys[pygame.K_SPACE] and self.shoot_cooldown <= 0:
            self.shoot_cooldown = 8
            bx = self.x + self.width if self.facing_right else self.x - 12
            by = self.y + 15
            direction = 1 if self.facing_right else -1
            bullets_list.append(Bullet(bx, by, direction, True))
            self.x += -2 if self.facing_right else 2
            if Player.shoot_sound:
                Player.shoot_sound.play()

        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        if self.invulnerable_timer > 0: self.invulnerable_timer -= 1

        self.apply_physics()

        if self.x < cam_x: self.x = cam_x

        if abs(self.vx) > 1 and self.is_grounded:
            self.anim_frame += 0.3
        else:
            self.anim_frame = 0

    def draw(self, surface, cam_x, frame_count):
        if self.invulnerable_timer > 0 and (frame_count // 4) % 2 == 0:
            return

        render_x = int(self.x - cam_x)
        render_y = int(self.y)
        current_index = int(self.anim_frame) % 6

        if self.facing_right:
            current_image = self.frames_right[current_index]
        else:
            current_image = self.frames_left[current_index]

        offset_x = -15
        offset_y = -10
        surface.blit(current_image, (render_x + offset_x, render_y + offset_y))

        if self.shoot_cooldown > 4:
            radius = int(5 + random.random() * 5)
            f_x = render_x + 45 if self.facing_right else render_x - 15
            pygame.draw.circle(surface, YELLOW_DARK, (f_x, render_y + 25), radius)