import pygame
import random
import math
from config import GROUND_Y, GRAY_LIGHT

from entities.base import Entity, create_explosion
from entities.player import Bullet


class Enemy(Entity):
    sprites_ninja = []
    sprites_tank = []
    sprites_cargados = False

    def __init__(self, x, e_type, speed_multiplier=1.0):
        hp = 150 if e_type == 'tank' else 30
        w = 80 if e_type == 'tank' else 30
        h = 60 if e_type == 'tank' else 50
        super().__init__(x, GROUND_Y - h, w, h, hp)

        self.type = e_type
        base_speed = -1.0 if e_type == 'tank' else (random.random() * -1.5 - 1.0)
        self.speed = base_speed * speed_multiplier
        self.shoot_timer = random.randint(0, 100)
        self.anim_frame = 0

    @classmethod
    def cargar_sprites(cls, enemy_img_name, tank_img_name):
        cls.sprites_ninja.clear()
        cls.sprites_tank.clear()

        try:
            hoja_ninja = pygame.image.load(enemy_img_name).convert_alpha()
            frames_totales_ninja = 6
            ancho_frame = hoja_ninja.get_width() // frames_totales_ninja
            alto_frame = hoja_ninja.get_height()
            for i in range(frames_totales_ninja):
                surf = pygame.Surface((ancho_frame, alto_frame), pygame.SRCALPHA)
                surf.blit(hoja_ninja, (0, 0), (i * ancho_frame, 0, ancho_frame, alto_frame))
                surf = pygame.transform.scale(surf, (100, 90))
                cls.sprites_ninja.append(surf)
        except Exception as e:
            print(f"Aviso: Falta imagen {enemy_img_name} - {e}")

        try:
            hoja_tank = pygame.image.load(tank_img_name).convert_alpha()
            frames_totales_tank = 6
            ancho_frame = hoja_tank.get_width() // frames_totales_tank
            alto_frame = hoja_tank.get_height()
            for i in range(frames_totales_tank):
                surf = pygame.Surface((ancho_frame, alto_frame), pygame.SRCALPHA)
                surf.blit(hoja_tank, (0, 0), (i * ancho_frame, 0, ancho_frame, alto_frame))
                surf = pygame.transform.scale(surf, (120, 120))
                cls.sprites_tank.append(surf)
        except Exception as e:
            print(f"Aviso: Falta imagen {tank_img_name} - {e}")

        cls.sprites_cargados = True

    def update(self, player_x, bullets_list, particles_list):
        self.apply_physics()
        self.facing_right = False
        self.vx = self.speed
        self.anim_frame += 0.15

        if self.type == 'soldier' and random.random() < 0.01 and self.is_grounded:
            self.vy = -8

        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            if self.type == 'soldier' and abs(self.x - player_x) < 400:
                bullets_list.append(Bullet(self.x, self.y + 15, -1, False))
                self.shoot_timer = random.randint(100, 200)
            elif self.type == 'tank' and abs(self.x - player_x) < 600:
                bullets_list.append(Bullet(self.x, self.y + 10, -1.5, False))
                self.shoot_timer = 80
                create_explosion(self.x, self.y + 10, GRAY_LIGHT, 5, particles_list)

    def draw(self, surface, cam_x, frame_count):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)

        if self.type == 'soldier':
            if self.sprites_ninja:
                indice = int(self.anim_frame) % len(self.sprites_ninja)
                imagen_actual = self.sprites_ninja[indice]
                surface.blit(imagen_actual, (render_x - 10, render_y - 20))
            else:
                render_y += int(math.sin(frame_count * 0.2) * 2)
                pygame.draw.rect(surface, GRAY_LIGHT, (render_x, render_y + 15, self.width, 20))
                pygame.draw.rect(surface, (252, 165, 165), (render_x + 6, render_y, 18, 15))

        elif self.type == 'tank':
            if self.sprites_tank:
                indice = int(self.anim_frame) % len(self.sprites_tank)
                imagen_actual = self.sprites_tank[indice]
                surface.blit(imagen_actual, (render_x - 5, render_y - 35))
            else:
                pygame.draw.rect(surface, (55, 65, 81), (render_x, render_y + 20, self.width, 25))
                pygame.draw.circle(surface, (31, 41, 55), (render_x + 50, render_y + 20), 20)