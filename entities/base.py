import pygame
import random

from config import GRAVITY, GROUND_Y, RED, YELLOW, YELLOW_DARK, GRAY_DARK

class Particle:
    def __init__(self, x, y, color, speed, size, life):
        self.x = x
        self.y = y
        self.vx = (random.random() - 0.5) * speed
        self.vy = (random.random() - 0.5) * speed
        self.color = color
        self.size = random.random() * size + 2
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += GRAVITY * 0.2
        self.life -= 1
        self.size = max(0, self.size - 0.1)

    def draw(self, surface, cam_x):
        if self.life > 0:
            rect = pygame.Rect(int(self.x - cam_x), int(self.y), int(self.size), int(self.size))
            pygame.draw.rect(surface, self.color, rect)

def create_explosion(x, y, color_type, count, particles_list):
    for _ in range(count):
        if color_type == 'explosion':
            color = random.choice([RED, YELLOW, YELLOW_DARK, GRAY_DARK])
        else:
            color = color_type
        life = 30 + random.random() * 20
        particles_list.append(Particle(x, y, color, 10, 8, life))

class Entity:
    def __init__(self, x, y, w, h, hp):
        self.x = float(x)
        self.y = float(y)
        self.width = w
        self.height = h
        self.vx = 0.0
        self.vy = 0.0
        self.hp = hp
        self.max_hp = hp
        self.facing_right = True
        self.is_grounded = False
        self.dead = False

    def apply_physics(self):
        self.vy += GRAVITY
        self.y += self.vy
        self.x += self.vx

        if self.y + self.height >= GROUND_Y:
            self.y = GROUND_Y - self.height
            self.vy = 0
            self.is_grounded = True
        else:
            self.is_grounded = False

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.dead = True

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)