import pygame
import random
import math
import sys

# Inicializar Pygame y el Mixer para la música
pygame.init()
pygame.mixer.init()

# Constantes de la pantalla y el motor
WIDTH, HEIGHT = 1000, 560
GRAVITY = 0.6
GROUND_Y = HEIGHT - 60

# Configuración de la ventana
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Camino Ninja")
clock = pygame.time.Clock()

# --- ARQUITECTURA DE NIVELES ---
LEVELS = {
    1:{
        "name":"Aldea de la Hoja",
        "background":"fondo1.png",
        "floor":"piso1.jpg",
        "music":"music1.mp3",
        "enemy":"enemigo1.png",
        "tank":"tank1.png",
        "spawn_rate":120,
        "tank_probability":0.15,
        "enemy_speed":1.0,
        "has_boss": True
    },
    2:{
        "name":"Valle Del Fin",
        "background":"fondo2.jpg",
        "floor":"piso2.jpg",
        "music":"music2.mp3",
        "enemy":"enemigo2.png",
        "tank":"tank2.png",
        "spawn_rate":90,
        "tank_probability":0.20,
        "enemy_speed":1.3,
        "has_boss": True 
    },
    3:{
        "name":"Aldea de la Arena",
        "background":"fondoo3.jpg",
        "floor":"piso3.jpg",
        "music":"music3.mp3",
        "enemy":"enemigo3.png",
        "tank":"tank3.png",
        "spawn_rate":70,
        "tank_probability":0.30,
        "enemy_speed":1.7,
        "has_boss": False
    }
}

ITEM_SPAWN_INTERVAL = 180 
PROB_RAMEN = 0.10      
PROB_CLON = 0.10       
PROB_PERGAMINO = 0.10  

# Definición de Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY_BLUE = (125, 211, 252)
DIRT_BROWN = (180, 83, 9)
DIRT_DARK = (146, 64, 14)
MOUNTAIN_GRAY = (148, 163, 184)
RED = (255, 0, 0)
RED_DARK = (115, 0, 0)
YELLOW = (253, 224, 71)
YELLOW_DARK = (245, 158, 11)
GREEN = (101, 163, 13)
GRAY_DARK = (55, 65, 81)
GRAY_LIGHT = (156, 163, 175)
PURPLE = (128, 0, 128)

# Fuentes
try:
    font_large = pygame.font.SysFont("courier", 60, bold=True)
    font_med = pygame.font.SysFont("courier", 30, bold=True)
    font_small = pygame.font.SysFont("courier", 18, bold=True)
except:
    font_large = pygame.font.Font(None, 74)
    font_med = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)

# --- FUNCIÓN AUXILIAR PARA SPRITESHEETS ---
def load_spritesheet(filename, width, height, frames_count):
    frames = []
    try:
        sheet = pygame.image.load(filename).convert_alpha()
        fw = sheet.get_width() // frames_count
        fh = sheet.get_height()
        for i in range(frames_count):
            surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
            surf.blit(sheet, (0, 0), (i * fw, 0, fw, fh))
            surf = pygame.transform.scale(surf, (width, height))
            frames.append(surf)
    except Exception as e:
        print(f"Aviso: No se pudo cargar {filename}: {e}")
    return frames

# --- SISTEMA DE PARTÍCULAS ---
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
            color = random.choice([RED, RED_DARK, RED, RED_DARK])
        else:
            color = color_type
        life = 30 + random.random() * 20
        particles_list.append(Particle(x, y, color, 10, 8, life))

# --- OBJETOS (POWER-UPS) ---
class Item:
    images = {}
    def __init__(self, x, item_type):
        self.x = float(x)
        self.width = 90
        self.height = 90
        self.y = GROUND_Y - self.height - 1 
        self.type = item_type
        self.active = True
        self.anim_float = random.random() * 10 

        if not Item.images:
            for t, img_name in [('pergamino', 'pergamino.png'), ('ramen', 'ramen.png'), ('clon', 'clon.png')]:
                try:
                    img = pygame.image.load(img_name).convert_alpha()
                    Item.images[t] = pygame.transform.scale(img, (self.width, self.height))
                except Exception as e:
                    Item.images[t] = None

    def update(self):
        self.anim_float += 0.1

    def draw(self, surface, cam_x):
        render_x = int(self.x - cam_x)
        render_y = int(self.y + math.sin(self.anim_float) * 5)
        if Item.images.get(self.type):
            surface.blit(Item.images[self.type], (render_x, render_y))
        else:
            color = GREEN if self.type == 'ramen' else (SKY_BLUE if self.type == 'clon' else YELLOW_DARK)
            pygame.draw.rect(surface, color, (render_x, render_y, self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# --- PROYECTILES DEL JUGADOR ---
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
                img = pygame.image.load("kunai.png").convert_alpha()
                Bullet.image_right = pygame.transform.scale(img, (self.width, self.height))
                Bullet.image_left = pygame.transform.flip(Bullet.image_right, True, False)
            except Exception as e:
                Bullet.image_right = False 

    def update(self, cam_x):
        self.x += self.vx
        if self.x < cam_x - 200 or self.x > cam_x + 800 + 200:
            self.active = False

    def draw(self, surface, cam_x):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)

        if Bullet.image_right: 
            if self.dir_x > 0: surface.blit(Bullet.image_right, (render_x, render_y))
            else: surface.blit(Bullet.image_left, (render_x, render_y))
        else:
            color = (253, 224, 71) if self.is_player else (239, 68, 68)
            rect = pygame.Rect(render_x, render_y, self.width, self.height)
            pygame.draw.rect(surface, color, rect)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Rasengan:
    image = None
    frames = []
    def __init__(self, x, y, dir_x):
        self.x = float(x)
        self.y = float(y)
        self.vx = dir_x * 12
        self.width = 60
        self.height = 60
        self.damage = 300
        self.active = True
        self.anim_frame = 0

        if not Rasengan.frames:
            try:
                sheet = pygame.image.load("rasengan.png").convert_alpha()
                fw = sheet.get_width() // 6
                fh = sheet.get_height()
                for i in range(6):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.blit(sheet, (0, 0), (i * fw, 0, fw, fh))
                    surf = pygame.transform.scale(surf, (self.width, self.height))
                    Rasengan.frames.append(surf)
                Rasengan.image = True
            except Exception as e:
                Rasengan.image = False

    def update(self, cam_x):
        self.x += self.vx
        self.anim_frame += 0.2
        if self.x < cam_x - 200 or self.x > cam_x + WIDTH + 200:
            self.active = False

    def draw(self, surface, cam_x):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)
        if Rasengan.image:
            idx = int(self.anim_frame) % len(Rasengan.frames)
            surface.blit(Rasengan.frames[idx], (render_x, render_y))
        else:
            pygame.draw.circle(surface, (56, 189, 248), (render_x + 30, render_y + 30), 30)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# --- ATAQUES DE LOS JEFES (PROYECTILES Y TRAMPAS) ---
class Bijudama:
    frames = []
    def __init__(self, x, y, dir_x):
        self.x = float(x)
        self.y = float(y)
        self.vx = dir_x * 8 
        self.width = 160
        self.height = 160
        self.damage = 20
        self.active = True
        self.anim_frame = 0

        if not Bijudama.frames:
            Bijudama.frames = load_spritesheet("bijudama.png", self.width, self.height, 6)

    def update(self, cam_x):
        self.x += self.vx
        self.anim_frame += 0.2
        if self.x < cam_x - 200 or self.x > cam_x + WIDTH + 200: self.active = False

    def draw(self, surface, cam_x):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)
        if Bijudama.frames:
            idx = int(self.anim_frame) % len(Bijudama.frames)
            surface.blit(Bijudama.frames[idx], (render_x, render_y))
        else:
            pygame.draw.circle(surface, PURPLE, (render_x + 70, render_y + 70), 70)

    def get_rect(self):
        return pygame.Rect(self.x + 20, self.y + 20, self.width - 40, self.height - 40)

class Cuervos:
    frames = []
    def __init__(self, x, y, dir_x):
        self.x = float(x)
        self.y = float(y)
        self.vx = dir_x * 12 
        self.width = 170
        self.height = 170
        self.damage = 20
        self.active = True
        self.anim_frame = 0

        if not Cuervos.frames:
            Cuervos.frames = load_spritesheet("cuervos.png", self.width, self.height, 6)

    def update(self, cam_x):
        self.x += self.vx
        self.anim_frame += 0.25
        if self.x < cam_x - 200 or self.x > cam_x + WIDTH + 200: self.active = False

    def draw(self, surface, cam_x):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)
        if Cuervos.frames:
            idx = int(self.anim_frame) % len(Cuervos.frames)
            surface.blit(Cuervos.frames[idx], (render_x, render_y))
        else:
            pygame.draw.rect(surface, BLACK, (render_x, render_y, self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x + 10, self.y + 10, self.width - 20, self.height - 20)

class BossTrapBase:
    """Clase base para ataques de suelo que persiguen a Naruto"""
    def __init__(self, x, y, width, height, damage, frames_attack):
        self.width = width
        self.height = height
        self.x = float(x) - self.width / 2
        self.y = float(y) - self.height
        self.state = 'warning'
        self.timer = 60 # 1 segundo de aviso
        self.active = True
        self.anim_frame = 0
        self.damage = damage
        self.has_hit = False
        self.frames_attack = frames_attack

    def update(self):
        self.timer -= 1
        if self.state == 'warning' and self.timer <= 0:
            self.state = 'attacking'
            self.timer = 25 
            self.anim_frame = 0
        elif self.state == 'attacking':
            self.anim_frame += 0.2
            if self.timer <= 0:
                self.active = False

    def check_collision(self, player):
        if self.state == 'attacking' and not self.has_hit:
            hitbox = self.get_rect()
            if hitbox.colliderect(player.get_rect()) and player.invulnerable_timer <= 0:
                self.has_hit = True
                return True
        return False

    def draw(self, surface, cam_x, warning_color, default_atk_color):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)
        if self.state == 'warning':
            if (self.timer // 5) % 2 == 0:
                pygame.draw.rect(surface, warning_color, (render_x, render_y + self.height - 10, self.width, 10))
        elif self.state == 'attacking':
            if self.frames_attack:
                idx = int(self.anim_frame) % len(self.frames_attack)
                surface.blit(self.frames_attack[idx], (render_x, render_y))
            else:
                pygame.draw.rect(surface, default_atk_color, (render_x, render_y, self.width, self.height))

    def get_rect(self):
        return pygame.Rect(self.x + 20, self.y, self.width - 40, self.height)

class ArenaAttack(BossTrapBase):
    frames_attack = []
    def __init__(self, x, y):
        if not ArenaAttack.frames_attack:
            ArenaAttack.frames_attack = load_spritesheet("arena.png", 170, 170, 6)
        super().__init__(x, y, 170, 170, 50, ArenaAttack.frames_attack)

    def draw(self, surface, cam_x):
        super().draw(surface, cam_x, (200, 50, 50), (150, 100, 30))

class AmaterasuAttack(BossTrapBase):
    frames_attack = []
    def __init__(self, x, y):
        if not AmaterasuAttack.frames_attack:
            AmaterasuAttack.frames_attack = load_spritesheet("amaterasu.png", 170, 170, 6)
        super().__init__(x, y, 170, 170, 55, AmaterasuAttack.frames_attack)

    def draw(self, surface, cam_x):
        super().draw(surface, cam_x, (255, 0, 0), (0, 0, 0))

# --- ENTIDADES BASE ---
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

# --- JUGADOR ---
class Player(Entity):
    jump_sound = None
    shoot_sound = None
    rasengan_sound = None 

    def __init__(self):
        super().__init__(100, 100, 30, 50, 100)
        self.speed = 5
        self.jump_force = -12
        self.shoot_cooldown = 0
        self.invulnerable_timer = 0
        self.anim_frame = 0
        
        self.chakra = 100
        self.max_chakra = 100
        self.rasengan_cooldown = 0
        self.rasengan_anim_timer = 0
        self.frame_count = 0

        self.frames_right = []
        self.frames_left = []
        
        original_size = 204
        scale_size = 80 

        if Player.jump_sound is None:
            try: Player.jump_sound = pygame.mixer.Sound("salto.wav"); Player.jump_sound.set_volume(0.7) 
            except: Player.jump_sound = False
        if Player.shoot_sound is None:
            try: Player.shoot_sound = pygame.mixer.Sound("kunai.wav"); Player.shoot_sound.set_volume(0.9)
            except: Player.shoot_sound = False
        if Player.rasengan_sound is None:
            try: Player.rasengan_sound = pygame.mixer.Sound("rasengan.wav"); Player.rasengan_sound.set_volume(1.0)
            except: Player.rasengan_sound = False

        try:
            sheet = pygame.image.load("naruto_spritee.png").convert_alpha()
            for i in range(6):
                frame_surf = pygame.Surface((original_size, original_size), pygame.SRCALPHA)
                frame_surf.blit(sheet, (0, 0), (i * original_size, 0, original_size, original_size))
                frame_scaled = pygame.transform.scale(frame_surf, (scale_size, scale_size))
                self.frames_right.append(frame_scaled)
                self.frames_left.append(pygame.transform.flip(frame_scaled, True, False))
        except:
            fallback = pygame.Surface((scale_size, scale_size), pygame.SRCALPHA)
            fallback.fill(RED)
            self.frames_right = [fallback] * 6
            self.frames_left = [fallback] * 6

        self.rasengan_frames_right = []
        self.rasengan_frames_left = []
        try:
            sheet_r = load_spritesheet("naruto_rasengan.png", 100, 100, 6)
            self.rasengan_frames_right = sheet_r
            self.rasengan_frames_left = [pygame.transform.flip(f, True, False) for f in sheet_r]
        except:
            pass

    def update(self, keys, cam_x, bullets_list, particles_list, rasengan_list, cam_locked):
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
            create_explosion(self.x + self.width/2, self.y + self.height, GRAY_LIGHT, 5, particles_list)
            if Player.jump_sound: Player.jump_sound.play()

        if keys[pygame.K_SPACE] and self.shoot_cooldown <= 0:
            self.shoot_cooldown = 8
            bx = self.x + self.width if self.facing_right else self.x - 12
            bullets_list.append(Bullet(bx, self.y + 15, 1 if self.facing_right else -1, True))
            self.x += -2 if self.facing_right else 2
            if Player.shoot_sound: Player.shoot_sound.play()

        if keys[pygame.K_r] and self.rasengan_cooldown <= 0 and self.chakra >= 30:
            self.chakra -= 30
            self.rasengan_cooldown = 60
            self.rasengan_anim_timer = 20
            bx = self.x + self.width if self.facing_right else self.x - 60
            rasengan_list.append(Rasengan(bx, self.y - 5, 1 if self.facing_right else -1))
            if Player.rasengan_sound: Player.rasengan_sound.play()

        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        if self.invulnerable_timer > 0: self.invulnerable_timer -= 1
        if self.rasengan_cooldown > 0: self.rasengan_cooldown -= 1
        if self.rasengan_anim_timer > 0: self.rasengan_anim_timer -= 1

        if self.chakra < self.max_chakra and self.frame_count % 30 == 0:
            self.chakra = min(self.max_chakra, self.chakra + 1)

        self.apply_physics()

        if cam_locked:
            if self.x < cam_x: self.x = cam_x
            if self.x + self.width > cam_x + WIDTH: self.x = cam_x + WIDTH - self.width
        else:
            if self.x < cam_x: self.x = cam_x

        if abs(self.vx) > 1 and self.is_grounded: self.anim_frame += 0.3
        else: self.anim_frame = 0

    def draw(self, surface, cam_x, frame_count):
        if self.invulnerable_timer > 0 and (frame_count // 4) % 2 == 0: return 

        render_x = int(self.x - cam_x)
        render_y = int(self.y)
        current_index = int(self.anim_frame) % 6

        if self.rasengan_anim_timer > 0 and self.rasengan_frames_right:
            rasengan_idx = int((20 - self.rasengan_anim_timer) * 0.3) % 6
            r_img = self.rasengan_frames_right[rasengan_idx] if self.facing_right else self.rasengan_frames_left[rasengan_idx]
            surface.blit(r_img, (render_x + 15 if self.facing_right else render_x - 45, render_y - 25))
        else:
            current_image = self.frames_right[current_index] if self.facing_right else self.frames_left[current_index]
            surface.blit(current_image, (render_x - 15, render_y - 10))

# --- ENEMIGOS REGULARES ---
class Enemy(Entity):
    sprites_ninja = []
    sprites_tank = []

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
        cls.sprites_ninja = load_spritesheet(enemy_img_name, 100, 90, 6)
        cls.sprites_tank = load_spritesheet(tank_img_name, 120, 120, 6)

    def update(self, player_x, bullets_list, particles_list):
        self.apply_physics()
        self.facing_right = False
        self.vx = self.speed
        self.anim_frame += 0.15 
        
        if self.type == 'soldier' and random.random() < 0.01 and self.is_grounded: self.vy = -8

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
                surface.blit(self.sprites_ninja[int(self.anim_frame) % len(self.sprites_ninja)], (render_x - 10, render_y - 20))
            else:
                pygame.draw.rect(surface, GRAY_LIGHT, (render_x, render_y + 15, self.width, 20))
        elif self.type == 'tank':
            if self.sprites_tank:
                surface.blit(self.sprites_tank[int(self.anim_frame) % len(self.sprites_tank)], (render_x - 5, render_y - 35))
            else:
                pygame.draw.rect(surface, GRAY_DARK, (render_x, render_y + 20, self.width, 25))


# --- CLASES DE JEFES ---
class BossShukaku(Entity):
    frames_idle = []
    frames_charge_b = []
    frames_charge_a = []
    snd_bijudama = None
    snd_arena = None

    def __init__(self, x, y):
        super().__init__(x, y - 200, 180, 200, hp=1000)
        self.state = 'idle'  
        self.action_timer = 120 
        self.anim_frame = 0
        self.name = "SHUKAKU (UNA COLA)"

        if not BossShukaku.frames_idle:
            BossShukaku.frames_idle = load_spritesheet("boss1.png", 250, 250, 6)
            BossShukaku.frames_charge_b = load_spritesheet("cargabijudama.png", 250, 250, 6)
            BossShukaku.frames_charge_a = load_spritesheet("cargaarena.png", 250, 250, 6)
            
        if BossShukaku.snd_bijudama is None:
            try: BossShukaku.snd_bijudama = pygame.mixer.Sound("bijudama.wav"); BossShukaku.snd_bijudama.set_volume(1.8)
            except: BossShukaku.snd_bijudama = False
        if BossShukaku.snd_arena is None:
            try: BossShukaku.snd_arena = pygame.mixer.Sound("arena.wav"); BossShukaku.snd_arena.set_volume(20.0)
            except: BossShukaku.snd_arena = False

    def update(self, player, proj_list, trap_list):
        self.apply_physics()
        self.anim_frame += 0.15

        if self.state == 'idle':
            self.action_timer -= 1
            if self.action_timer <= 0:
                attack = random.choice(['bijudama', 'arena'])
                if attack == 'bijudama':
                    self.state = 'charge_bijudama'
                    self.action_timer = 90
                    self.anim_frame = 0
                    if BossShukaku.snd_bijudama: BossShukaku.snd_bijudama.play()
                elif attack == 'arena':
                    self.state = 'charge_arena'
                    self.action_timer = 60 
                    self.anim_frame = 0
                    trap_list.append(ArenaAttack(player.x + player.width/2, GROUND_Y))
                    if BossShukaku.snd_arena: BossShukaku.snd_arena.play()

        elif self.state == 'charge_bijudama':
            self.action_timer -= 1
            if self.action_timer <= 0:
                proj_list.append(Bijudama(self.x, self.y + 40, -1))
                self.state = 'idle'
                self.action_timer = 150

        elif self.state == 'charge_arena':
            self.action_timer -= 1
            if self.action_timer <= 0:
                self.state = 'idle'
                self.action_timer = 120

    def draw(self, surface, cam_x):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)
        offset_x, offset_y = -80, -10

        if self.state == 'charge_bijudama' and BossShukaku.frames_charge_b:
            surface.blit(BossShukaku.frames_charge_b[int(self.anim_frame) % 6], (render_x + offset_x, render_y + offset_y))
        elif self.state == 'charge_arena' and BossShukaku.frames_charge_a:
            surface.blit(BossShukaku.frames_charge_a[int(self.anim_frame) % 6], (render_x + offset_x, render_y + offset_y))
        else:
            if BossShukaku.frames_idle: surface.blit(BossShukaku.frames_idle[int(self.anim_frame) % 6], (render_x + offset_x, render_y + offset_y))


class BossItachi(Entity):
    frames_idle = []
    frames_charge_c = []
    frames_charge_a = []
    snd_cuervos = None
    snd_amaterasu = None

    def __init__(self, x, y):
        # Tamaño adaptado para un personaje humanoide 
        super().__init__(x, y - 100, 60, 100, hp=1500)
        self.state = 'idle'
        self.action_timer = 100
        self.anim_frame = 0
        self.name = "ITACHI UCHIHA"

        if not BossItachi.frames_idle:
            BossItachi.frames_idle = load_spritesheet("boss2.png", 180, 180, 6)
            BossItachi.frames_charge_c = load_spritesheet("cargacuervos.png", 180, 180, 6)
            BossItachi.frames_charge_a = load_spritesheet("cargaamaterasu.png", 180, 180, 6)
        
        if BossItachi.snd_cuervos is None:
            try: BossItachi.snd_cuervos = pygame.mixer.Sound("cuervos.wav"); BossItachi.snd_cuervos.set_volume(3.0)
            except: BossItachi.snd_cuervos = False
        if BossItachi.snd_amaterasu is None:
            try: BossItachi.snd_amaterasu = pygame.mixer.Sound("amaterasu.wav"); BossItachi.snd_amaterasu.set_volume(20.0)
            except: BossItachi.snd_amaterasu = False

    def update(self, player, proj_list, trap_list):
        self.apply_physics()
        self.anim_frame += 0.2

        if self.state == 'idle':
            self.action_timer -= 1
            if self.action_timer <= 0:
                attack = random.choice(['cuervos', 'amaterasu'])
                if attack == 'cuervos':
                    self.state = 'charge_cuervos'
                    self.action_timer = 60
                    self.anim_frame = 0
                    if BossItachi.snd_cuervos: BossItachi.snd_cuervos.play()
                elif attack == 'amaterasu':
                    self.state = 'charge_amaterasu'
                    self.action_timer = 60 
                    self.anim_frame = 0
                    trap_list.append(AmaterasuAttack(player.x + player.width/2, GROUND_Y))
                    if BossItachi.snd_amaterasu: BossItachi.snd_amaterasu.play()

        elif self.state == 'charge_cuervos':
            self.action_timer -= 1
            if self.action_timer <= 0:
                proj_list.append(Cuervos(self.x, self.y + 20, -1))
                self.state = 'idle'
                self.action_timer = 100 

        elif self.state == 'charge_amaterasu':
            self.action_timer -= 1
            if self.action_timer <= 0:
                self.state = 'idle'
                self.action_timer = 120

    def draw(self, surface, cam_x):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)
        offset_x, offset_y = -70, -50

        if self.state == 'charge_cuervos' and BossItachi.frames_charge_c:
            surface.blit(BossItachi.frames_charge_c[int(self.anim_frame) % 6], (render_x + offset_x, render_y + offset_y))
        elif self.state == 'charge_amaterasu' and BossItachi.frames_charge_a:
            surface.blit(BossItachi.frames_charge_a[int(self.anim_frame) % 6], (render_x + offset_x, render_y + offset_y))
        else:
            if BossItachi.frames_idle: 
                surface.blit(BossItachi.frames_idle[int(self.anim_frame) % 6], (render_x + offset_x, render_y + offset_y))
            else:
                pygame.draw.rect(surface, GRAY_DARK, (render_x, render_y, self.width, self.height))


# --- MOTOR PRINCIPAL ---
class Game:
    def __init__(self):
        self.state = 'START' 
        self.score = 0
        self.camera_x = 0
        self.level = 1
        self.frame_count = 0
        self.screen_shake = 0
        self.player = None
        self.enemies = []
        self.bullets = []
        self.particles = []
        self.rasengan_list = []
        self.items = [] 
        self.level_distance = 5000
        
        # Variables de Jefe Final Generalizadas
        self.boss_active = False
        self.boss_defeated = False
        self.boss = None
        self.boss_projectiles = []
        self.boss_traps = []       
        
        self.current_background = None
        self.level_message_timer = 0
        self.level_message = ""
        self.floor_image = None

        try:
            self.start_image = pygame.transform.scale(pygame.image.load("poortada.png").convert(), (WIDTH, HEIGHT))
        except:
            self.start_image = None

    def load_level(self, level_num):
        self.level = level_num
        if level_num not in LEVELS: return 
            
        data = LEVELS[level_num]
        print(f"=== CARGANDO NIVEL {self.level}: {data['name']} ===")
        
        self.boss_active = False
        self.boss_defeated = False
        self.boss = None
        self.boss_projectiles.clear()
        self.boss_traps.clear()

        try:
            self.current_background = pygame.transform.scale(pygame.image.load(data["background"]).convert(), (WIDTH, HEIGHT))
            self.floor_image = pygame.transform.scale(pygame.image.load(data["floor"]).convert(), (WIDTH, HEIGHT - GROUND_Y))
        except: pass

        Enemy.cargar_sprites(data["enemy"], data["tank"])
        self.enemies.clear()

        try:
            pygame.mixer.music.load(data["music"])
            pygame.mixer.music.play(-1)
        except: pass

        self.level_message = data["name"]
        self.level_message_timer = 180 

    def reset(self):
        self.player = Player()
        self.bullets.clear()
        self.particles.clear()
        self.rasengan_list.clear()
        self.items.clear()
        self.score = 0
        self.camera_x = 0
        self.frame_count = 0
        self.screen_shake = 0
        self.state = 'PLAYING'
        self.load_level(1)

    def update(self):
        if self.state != 'PLAYING': return
            
        self.frame_count += 1
        keys = pygame.key.get_pressed()
        current_level_data = LEVELS[self.level]

        # --- LÓGICA DE CÁMARA Y JEFE FINAL ---
        target_boss_cam = self.level * self.level_distance - WIDTH

        if self.camera_x >= target_boss_cam and current_level_data.get("has_boss") and not self.boss_defeated:
            if not self.boss_active:
                self.boss_active = True
                self.camera_x = target_boss_cam 
                
                # Instanciador dinámico de Jefes por Nivel
                if self.level == 1:
                    self.boss = BossShukaku(self.camera_x + WIDTH - 200, GROUND_Y)
                elif self.level == 2:
                    self.boss = BossItachi(self.camera_x + WIDTH - 150, GROUND_Y)

        if not self.boss_active:
            target_cam_x = self.player.x - 200
            if target_cam_x > self.camera_x:
                self.camera_x = target_cam_x

            nuevo_nivel = min(max(LEVELS.keys()), int(self.camera_x / self.level_distance) + 1)
            if nuevo_nivel != self.level:
                self.load_level(nuevo_nivel)

        # Spawns regulares
        if not self.boss_active and self.frame_count % current_level_data["spawn_rate"] == 0:
            e_type = 'tank' if random.random() < current_level_data["tank_probability"] else 'soldier'
            self.enemies.append(Enemy(self.camera_x + WIDTH + 50, e_type, current_level_data["enemy_speed"]))

        if not self.boss_active and self.frame_count % ITEM_SPAWN_INTERVAL == 0:
            rand_val = random.random() 
            if rand_val < PROB_PERGAMINO: self.items.append(Item(self.camera_x + WIDTH + 100, 'pergamino'))
            elif rand_val < (PROB_PERGAMINO + PROB_RAMEN): self.items.append(Item(self.camera_x + WIDTH + 100, 'ramen'))
            elif rand_val < (PROB_PERGAMINO + PROB_RAMEN + PROB_CLON): self.items.append(Item(self.camera_x + WIDTH + 100, 'clon'))

        # Actualizar Jugador
        self.player.frame_count = self.frame_count
        self.player.update(keys, self.camera_x, self.bullets, self.particles, self.rasengan_list, self.boss_active)

        # Actualizar Boss y sus ataques
        if self.boss_active and self.boss:
            self.boss.update(self.player, self.boss_projectiles, self.boss_traps)
            
            if self.boss.get_rect().colliderect(self.player.get_rect()) and self.player.invulnerable_timer <= 0:
                self.player.take_damage(20)
                self.player.invulnerable_timer = 40
                self.screen_shake = 15
                create_explosion(self.player.x, self.player.y, RED, 10, self.particles)

            if self.boss.dead:
                self.boss_active = False
                self.boss_defeated = True
                self.score += 5000 * self.level
                create_explosion(self.boss.x + self.boss.width/2, self.boss.y + self.boss.height/2, 'explosion', 100, self.particles)
                self.screen_shake = 30
                self.boss = None

        # Gestionar Proyectiles de los Jefes
        for p in self.boss_projectiles[:]:
            p.update(self.camera_x)
            if p.get_rect().colliderect(self.player.get_rect()):
                if self.player.invulnerable_timer <= 0:
                    self.player.take_damage(p.damage)
                    self.screen_shake = 20
                    self.player.invulnerable_timer = 40
                    create_explosion(self.player.x, self.player.y, PURPLE if self.level == 1 else BLACK, 15, self.particles)
                if p in self.boss_projectiles: self.boss_projectiles.remove(p)
            elif not p.active:
                self.boss_projectiles.remove(p)

        # Gestionar Trampas de los Jefes
        for t in self.boss_traps[:]:
            t.update()
            if t.check_collision(self.player):
                self.player.take_damage(t.damage)
                self.screen_shake = 15
                self.player.invulnerable_timer = 40
                create_explosion(self.player.x, self.player.y, YELLOW if self.level == 1 else BLACK, 10, self.particles)
            if not t.active:
                self.boss_traps.remove(t)

        # Actualizar Items y Colisiones
        for item in self.items[:]:
            item.update()
            if item.get_rect().colliderect(self.player.get_rect()):
                if item.type == 'ramen': self.player.hp = self.player.max_hp
                elif item.type == 'clon': self.player.chakra = self.player.max_chakra
                elif item.type == 'pergamino': self.player.invulnerable_timer = 240 
                create_explosion(item.x + 20, item.y + 20, WHITE, 8, self.particles)
                self.items.remove(item)
            elif item.x < self.camera_x - 100:
                self.items.remove(item)

        # Actualizar Kunais
        for b in self.bullets[:]:
            b.update(self.camera_x)
            b_rect = b.get_rect()
            hit = False
            if b.is_player:
                for e in self.enemies:
                    if b_rect.colliderect(e.get_rect()):
                        e.take_damage(b.damage)
                        create_explosion(b.x + b.width, b.y, YELLOW, 3, self.particles)
                        hit = True; break
                
                if not hit and self.boss_active and self.boss:
                    if b_rect.colliderect(self.boss.get_rect()):
                        self.boss.take_damage(b.damage)
                        create_explosion(b.x + b.width, b.y, YELLOW, 5, self.particles)
                        hit = True
            else:
                if b_rect.colliderect(self.player.get_rect()):
                    if self.player.invulnerable_timer <= 0:
                        self.player.take_damage(b.damage)
                        self.screen_shake = 15
                        create_explosion(self.player.x, self.player.y, RED, 10, self.particles)
                    hit = True

            if hit or not b.active:
                if b in self.bullets: self.bullets.remove(b)

        # Actualizar Rasengan
        for r in self.rasengan_list[:]:
            r.update(self.camera_x)
            r_rect = r.get_rect()
            hit = False
            for e in self.enemies:
                if r_rect.colliderect(e.get_rect()):
                    e.take_damage(r.damage)
                    create_explosion(e.x + e.width/2, e.y + e.height/2, 'explosion', 40, self.particles)
                    self.screen_shake = 20
                    hit = True; break
            
            if not hit and self.boss_active and self.boss:
                if r_rect.colliderect(self.boss.get_rect()):
                    self.boss.take_damage(r.damage)
                    create_explosion(r.x + r.width, r.y, 'explosion', 50, self.particles)
                    self.screen_shake = 30
                    hit = True

            if hit or not r.active:
                if r in self.rasengan_list: self.rasengan_list.remove(r)

        # Actualizar Enemigos
        for e in self.enemies[:]:
            e.update(self.player.x, self.bullets, self.particles)
            if e.get_rect().colliderect(self.player.get_rect()):
                if self.player.invulnerable_timer <= 0:
                    self.player.take_damage(10)
                    self.player.invulnerable_timer = 40
                    self.screen_shake = 15
                    create_explosion(self.player.x, self.player.y, RED, 10, self.particles)

            if e.dead:
                self.score += 500 if e.type == 'tank' else 100
                create_explosion(e.x + e.width/2, e.y + e.height/2, 'explosion', 30 if e.type == 'tank' else 15, self.particles)
                if e.type == 'tank': self.screen_shake = 10
                self.enemies.remove(e)
            elif e.x < self.camera_x - 200:
                self.enemies.remove(e)

        if self.player.dead:
            self.state = 'GAMEOVER'

        for p in self.particles[:]:
            p.update()
            if p.life <= 0: self.particles.remove(p)

        if self.screen_shake > 0:
            self.screen_shake *= 0.9
            if self.screen_shake < 0.5: self.screen_shake = 0

    def draw_background(self, surface):
        if self.current_background:
            surface.blit(self.current_background, (0, 0))
        else:
            surface.fill(SKY_BLUE)

        if self.floor_image:
            rel_x = self.camera_x % WIDTH
            surface.blit(self.floor_image, (-rel_x, GROUND_Y))
            surface.blit(self.floor_image, (-rel_x + WIDTH, GROUND_Y))
        else:
            pygame.draw.rect(surface, DIRT_BROWN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    def draw(self, screen):
        render_surface = pygame.Surface((WIDTH, HEIGHT))
        self.draw_background(render_surface)

        if self.state in ['PLAYING', 'GAMEOVER']:
            if not self.player.dead:
                self.player.draw(render_surface, self.camera_x, self.frame_count)
            for e in self.enemies: e.draw(render_surface, self.camera_x, self.frame_count)
            if self.boss_active and self.boss: self.boss.draw(render_surface, self.camera_x)
            
            for t in self.boss_traps: t.draw(render_surface, self.camera_x)
            for p in self.boss_projectiles: p.draw(render_surface, self.camera_x)
            
            for b in self.bullets: b.draw(render_surface, self.camera_x)
            for r in self.rasengan_list: r.draw(render_surface, self.camera_x)
            for item in self.items: item.draw(render_surface, self.camera_x)
            for p in self.particles: p.draw(render_surface, self.camera_x)

            # --- DIBUJAR HUD (Interfaz) ---
            shadow_score = font_med.render(f"PUNTOS: {self.score}", True, BLACK)
            score_surf = font_med.render(f"PUNTOS: {self.score}", True, YELLOW)
            offset = 2
            render_surface.blit(shadow_score, (20 + offset, 20 + offset))
            render_surface.blit(score_surf, (20, 20))
            
            pygame.draw.rect(render_surface, WHITE, (20, 60, 204, 24), 2) 
            pygame.draw.rect(render_surface, (127, 29, 29), (22, 62, 200, 20)) 
            hp_width = int((self.player.hp / self.player.max_hp) * 200)
            if hp_width > 0: pygame.draw.rect(render_surface, RED, (22, 62, hp_width, 20)) 
                
            pygame.draw.rect(render_surface, WHITE, (20, 90, 204, 24), 2)
            pygame.draw.rect(render_surface, (15, 23, 42), (22, 92, 200, 20)) 
            ch_width = int((self.player.chakra / self.player.max_chakra) * 200)
            if ch_width > 0: pygame.draw.rect(render_surface, (14, 165, 233), (22, 92, ch_width, 20))
                
            # HUD Jefe Final
            if self.boss_active and self.boss:
                pygame.draw.rect(render_surface, WHITE, (WIDTH//2 - 250, 30, 500, 24), 2)
                pygame.draw.rect(render_surface, (60, 10, 10), (WIDTH//2 - 248, 32, 496, 20))
                boss_hp_w = int((self.boss.hp / self.boss.max_hp) * 496)
                if boss_hp_w > 0: pygame.draw.rect(render_surface, RED_DARK, (WIDTH//2 - 248, 32, boss_hp_w, 20))
                
                boss_name = font_small.render(self.boss.name, True, WHITE)
                render_surface.blit(boss_name, (WIDTH//2 - boss_name.get_width()//2, 60))

            if self.boss_defeated and not self.boss_active:
                msg_win = font_med.render("¡JEFE DERROTADO! AVANZA", True, GREEN)
                render_surface.blit(msg_win, (WIDTH//2 - msg_win.get_width()//2, 100))

            shadow_surf1 = font_small.render("ARMA", True, BLACK)
            shadow_surf2 = font_med.render("KUNAI ∞", True, BLACK)
            weapon_surf1 = font_small.render("ARMA", True, WHITE)
            weapon_surf2 = font_med.render("KUNAI ∞", True, YELLOW)
            render_surface.blit(shadow_surf1, (WIDTH - 150 + offset, 20 + offset))
            render_surface.blit(shadow_surf2, (WIDTH - 180 + offset, 40 + offset))
            render_surface.blit(weapon_surf1, (WIDTH - 150, 20))
            render_surface.blit(weapon_surf2, (WIDTH - 180, 40))

            rasengan_label = font_small.render("RASENGAN (R)", True, WHITE)
            render_surface.blit(rasengan_label, (WIDTH - 180, 70))
            if self.player.chakra >= 30: rasengan_ready = font_small.render("30 CHAKRA", True, (56, 189, 248))
            else: rasengan_ready = font_small.render("SIN CHAKRA", True, RED)
            render_surface.blit(rasengan_ready, (WIDTH - 130, 88))

            if self.level_message_timer > 0:
                shadow = font_large.render(f"NIVEL {self.level}: {self.level_message}", True, BLACK)
                msg = font_large.render(f"NIVEL {self.level}: {self.level_message}", True, YELLOW)
                pos_x = WIDTH//2 - msg.get_width()//2
                pos_y = 150
                render_surface.blit(shadow, (pos_x + 3, pos_y + 3))
                render_surface.blit(msg, (pos_x, pos_y))
                self.level_message_timer -= 1

        if self.state == 'START':
            if self.start_image: render_surface.blit(self.start_image, (0, 0))
            else: render_surface.fill(BLACK)
            
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                start_txt = font_med.render("PRESIONA ESPACIO PARA INICIAR", True, YELLOW)
                shadow_start = font_med.render("PRESIONA ESPACIO PARA INICIAR", True, BLACK)
                pos_x = WIDTH//2 - start_txt.get_width()//2
                pos_y = HEIGHT - 200 
                render_surface.blit(shadow_start, (pos_x + 2, pos_y + 2))
                render_surface.blit(start_txt, (pos_x, pos_y))

        elif self.state == 'GAMEOVER':
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            render_surface.blit(overlay, (0,0))
            title = font_large.render("MISIÓN FALLIDA", True, RED)
            render_surface.blit(title, (WIDTH//2 - title.get_width()//2, 150))
            score_txt = font_med.render(f"PUNTUACIÓN FINAL: {self.score}", True, YELLOW)
            render_surface.blit(score_txt, (WIDTH//2 - score_txt.get_width()//2, 230))
            restart_txt = font_small.render("PRESIONA ESPACIO PARA REINICIAR", True, WHITE)
            render_surface.blit(restart_txt, (WIDTH//2 - restart_txt.get_width()//2, 320))

        shake_x = (random.random() - 0.5) * self.screen_shake
        shake_y = (random.random() - 0.5) * self.screen_shake
        screen.blit(render_surface, (shake_x, shake_y))

def main():
    game = Game()
    running = True
    
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game.state == 'START' or game.state == 'GAMEOVER':
                        game.reset()
        game.update()
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()