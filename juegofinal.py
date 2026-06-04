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
        "enemy_speed":1.0
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
        "enemy_speed":1.3
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
        "enemy_speed":1.7
    }
}

# Definición de Colores (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY_BLUE = (125, 211, 252)
DIRT_BROWN = (180, 83, 9)
DIRT_DARK = (146, 64, 14)
MOUNTAIN_GRAY = (148, 163, 184)
RED = (239, 68, 68)
YELLOW = (253, 224, 71)
YELLOW_DARK = (245, 158, 11)
GREEN = (101, 163, 13)
GRAY_DARK = (55, 65, 81)
GRAY_LIGHT = (156, 163, 175)

# Fuentes
try:
    font_large = pygame.font.SysFont("courier", 60, bold=True)
    font_med = pygame.font.SysFont("courier", 30, bold=True)
    font_small = pygame.font.SysFont("courier", 18, bold=True)
except:
    font_large = pygame.font.Font(None, 74)
    font_med = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)

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
            color = random.choice([RED, YELLOW, YELLOW_DARK, GRAY_DARK])
        else:
            color = color_type
        life = 30 + random.random() * 20
        particles_list.append(Particle(x, y, color, 10, 8, life))

# --- PROYECTILES ---
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
            pygame.draw.rect(surface, color, rect)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

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
        # --- CARGA DE EFECTOS DE SONIDO ---
        if Player.jump_sound is None:
            try:
                Player.jump_sound = pygame.mixer.Sound("salto.wav")
                Player.jump_sound.set_volume(0.7) # Volumen al 30% para no aturdir
            except Exception as e:
                print(f"Aviso: No se encontró salto.wav - {e}")
                Player.jump_sound = False
                
        if Player.shoot_sound is None:
            try:
                Player.shoot_sound = pygame.mixer.Sound("kunai.wav")
                Player.shoot_sound.set_volume(0.9)
            except Exception as e:
                print(f"Aviso: No se encontró kunai.wav - {e}")
                Player.shoot_sound = False

        try:
            sheet = pygame.image.load("naruto_spritee.png").convert_alpha()
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
            create_explosion(self.x + self.width/2, self.y + self.height, GRAY_LIGHT, 5, particles_list)
            
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

# --- ENEMIGOS ---
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
        # Aplicamos el multiplicador de velocidad del nivel
        base_speed = -1.0 if e_type == 'tank' else (random.random() * -1.5 - 1.0)
        self.speed = base_speed * speed_multiplier 
        
        self.shoot_timer = random.randint(0, 100)
        self.anim_frame = 0

    @classmethod
    def cargar_sprites(cls, enemy_img_name, tank_img_name):
        cls.sprites_ninja.clear()
        cls.sprites_tank.clear()

        # Cargar Soldado
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
        
        # Cargar Tanque
        try:
            hoja_tank = pygame.image.load(tank_img_name).convert_alpha()
            frames_totales_tank = 6 
            ancho_frame = hoja_tank.get_width() // frames_totales_tank
            alto_frame = hoja_tank.get_height()
            for i in range(frames_totales_tank):
                surf = pygame.Surface((ancho_frame, alto_frame), pygame.SRCALPHA)
                surf.blit(hoja_tank, (0, 0), (i * ancho_frame, 0, ancho_frame, alto_frame))
                surf = pygame.transform.scale(surf, (120, 120))
                #surf = pygame.transform.flip(surf, True, False)
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
        self.level_distance = 5000
        
        self.current_background = None
        self.level_message_timer = 0
        self.level_message = ""
        self.floor_image = None

        # --- CARGAR IMAGEN DE INICIO ---
        try:
            img_inicio = pygame.image.load("poortada.png").convert()
            self.start_image = pygame.transform.scale(img_inicio, (WIDTH, HEIGHT))
        except Exception as e:
            print(f"Error cargando la imagen de portada: {e}")
            self.start_image = None


    def load_level(self, level_num):
        self.level = level_num
    
        if level_num not in LEVELS:
            return 
            
        data = LEVELS[level_num]
        print(f"=== CARGANDO NIVEL {self.level}: {data['name']} ===")

        # 1. Cargar fondo
        try:
            img = pygame.image.load(data["background"]).convert()
            self.current_background = pygame.transform.scale(img, (WIDTH, HEIGHT))
        except Exception as e:
            print(f"Error cargando fondo: {e}")
            self.current_background = None

        # 2. Cargar el suelo del nivel ---
        try:
            piso_img = pygame.image.load(data["floor"]).convert()
            self.floor_image = pygame.transform.scale(piso_img, (WIDTH, HEIGHT - GROUND_Y))
        except Exception as e:
            print(f"Error cargando el suelo {data['floor']}: {e}")
            self.floor_image = None

        # 2. Cargar Sprites Enemigos
        Enemy.cargar_sprites(data["enemy"], data["tank"])
        
        # 3. Limpiar enemigos viejos para evitar fallos de renderizado
        self.enemies.clear()

        # 4. Cargar y reproducir música
        try:
            pygame.mixer.music.load(data["music"])
            pygame.mixer.music.play(-1) # -1 para Loop
        except Exception as e:
            print(f"Aviso de música: {e}")

        # 5. Preparar mensaje en pantalla
        self.level_message = data["name"]
        self.level_message_timer = 180 # 3 segundos a 60FPS

    def reset(self):
        self.player = Player()
        self.bullets.clear()
        self.particles.clear()
        self.score = 0
        self.camera_x = 0
        self.frame_count = 0
        self.screen_shake = 0
        self.state = 'PLAYING'
        self.load_level(1) # Arrancamos en nivel 1

    def update(self):
        if self.state != 'PLAYING':
            return
            
        self.frame_count += 1
        keys = pygame.key.get_pressed()

        # Cámara
        target_cam_x = self.player.x - 200
        if target_cam_x > self.camera_x:
            self.camera_x = target_cam_x

        # Lógica de cambio de Nivel
        nuevo_nivel = min(
            max(LEVELS.keys()), # Máximo nivel disponible en el diccionario
            int(self.camera_x / self.level_distance) + 1
        )

        if nuevo_nivel != self.level:
            self.load_level(nuevo_nivel)

        # Spawn Enemigos (basado en el diccionario)
        current_level_data = LEVELS[self.level]
        if self.frame_count % current_level_data["spawn_rate"] == 0:
            # Evaluamos la probabilidad dinámica del tanque
            e_type = 'tank' if random.random() < current_level_data["tank_probability"] else 'soldier'
            # Instanciamos el enemigo pasándole la velocidad del nivel
            self.enemies.append(Enemy(
                self.camera_x + WIDTH + 50, 
                e_type, 
                current_level_data["enemy_speed"]
            ))

        # Actualizar Jugador
        self.player.update(keys, self.camera_x, self.bullets, self.particles)

        # Actualizar Proyectiles
        for b in self.bullets[:]:
            b.update(self.camera_x)
            b_rect = b.get_rect()

            hit = False
            if b.is_player:
                for e in self.enemies:
                    if b_rect.colliderect(e.get_rect()):
                        e.take_damage(b.damage)
                        create_explosion(b.x + b.width, b.y, YELLOW, 3, self.particles)
                        hit = True
                        break
            else:
                if b_rect.colliderect(self.player.get_rect()):
                    self.player.take_damage(b.damage)
                    self.screen_shake = 15
                    create_explosion(self.player.x, self.player.y, RED, 10, self.particles)
                    hit = True

            if hit or not b.active:
                if b in self.bullets:
                    self.bullets.remove(b)

        # Actualizar Enemigos
        for e in self.enemies[:]:
            e.update(self.player.x, self.bullets, self.particles)
            
            # Daño por contacto
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

        # Comprobar muerte del jugador
        if self.player.dead:
            self.state = 'GAMEOVER'

        # Actualizar Partículas
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        # Reducir Temblor
        if self.screen_shake > 0:
            self.screen_shake *= 0.9
            if self.screen_shake < 0.5: self.screen_shake = 0

    def draw_background(self, surface):
        # 1. Dibujar el fondo dinámico del nivel
        if self.current_background:
            surface.blit(self.current_background, (0, 0))
        else:
            surface.fill(SKY_BLUE)

        # 2. Dibujar el suelo con scroll infinito
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
            for e in self.enemies:
                e.draw(render_surface, self.camera_x, self.frame_count)
            for b in self.bullets:
                b.draw(render_surface, self.camera_x)
            for p in self.particles:
                p.draw(render_surface, self.camera_x)

            # --- DIBUJAR HUD (Interfaz) ---
            # Puntos
            shadow_score = font_med.render(f"PUNTOS: {self.score}", True, BLACK)
            score_surf = font_med.render(f"PUNTOS: {self.score}", True, YELLOW)
            offset = 2
            render_surface.blit(shadow_score, (20 + offset, 20 + offset))
            render_surface.blit(score_surf, (20, 20))
            
            # Barra de vida
            pygame.draw.rect(render_surface, WHITE, (20, 60, 204, 24), 2) 
            pygame.draw.rect(render_surface, (127, 29, 29), (22, 62, 200, 20)) 
            hp_width = int((self.player.hp / self.player.max_hp) * 200)
            if hp_width > 0:
                pygame.draw.rect(render_surface, RED, (22, 62, hp_width, 20)) 
                
            # Arma
            shadow_surf1 = font_small.render("ARMA", True, BLACK)
            shadow_surf2 = font_med.render("KUNAI ∞", True, BLACK)

            weapon_surf1 = font_small.render("ARMA", True, WHITE)
            weapon_surf2 = font_med.render("KUNAI ∞", True, YELLOW)
            #Dibujar las sombras con un desplazamiento (offset) de +2 píxeles
            offset = 2
            render_surface.blit(shadow_surf1, (WIDTH - 150 + offset, 20 + offset))
            render_surface.blit(shadow_surf2, (WIDTH - 180 + offset, 40 + offset))

            render_surface.blit(weapon_surf1, (WIDTH - 150, 20))
            render_surface.blit(weapon_surf2, (WIDTH - 180, 40))

            # --- MENSAJE DE CAMBIO DE NIVEL ---
            if self.level_message_timer > 0:
                # Sombra para mejor lectura
                shadow = font_large.render(f"NIVEL {self.level}: {self.level_message}", True, BLACK)
                msg = font_large.render(f"NIVEL {self.level}: {self.level_message}", True, YELLOW)
                
                pos_x = WIDTH//2 - msg.get_width()//2
                pos_y = 150
                
                render_surface.blit(shadow, (pos_x + 3, pos_y + 3))
                render_surface.blit(msg, (pos_x, pos_y))
                self.level_message_timer -= 1

        # --- PANTALLAS DE MENÚ ---
        if self.state == 'START':
            if self.start_image:
                render_surface.blit(self.start_image, (0, 0))
            else:
                # Fallback por si hay un error con la imagen (fondo negro)
                render_surface.fill(BLACK)
            
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

        # Aplicar Screen Shake final
        shake_x = (random.random() - 0.5) * self.screen_shake
        shake_y = (random.random() - 0.5) * self.screen_shake
        screen.blit(render_surface, (shake_x, shake_y))

# --- BUCLE PRINCIPAL DE LA APLICACIÓN ---
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