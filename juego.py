import pygame
import random
import math
import sys

# Inicializar Pygame
pygame.init()

# Constantes de la pantalla y el motor
WIDTH, HEIGHT = 1000, 560
GRAVITY = 0.6
GROUND_Y = HEIGHT - 60

# Configuración de la ventana
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Camino Ninja")
clock = pygame.time.Clock()

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
            # Opacidad simulada no es tan directa en Pygame básico sin superficies, 
            # pero reducimos el tamaño para dar un efecto similar de desaparición
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
    # Usamos variables de clase para cargar la imagen UNA sola vez y evitar lag al disparar
    image_right = None
    image_left = None

    def __init__(self, x, y, dir_x, is_player):
        self.x = float(x)
        self.y = float(y)
        self.vx = dir_x * 15
        
        # Dimensiones escaladas del kunai (423x100 original -> escalado a 42x10)
        self.width = 42
        self.height = 10
        
        self.is_player = is_player
        self.damage = 25 if is_player else 10
        self.active = True
        self.dir_x = dir_x

        # Cargar y escalar la imagen la primera vez que disparamos
        if Bullet.image_right is None:
            try:
                img = pygame.image.load("Textures/kunai.png").convert_alpha()
                # Escalar la imagen al tamaño del hitbox
                Bullet.image_right = pygame.transform.scale(img, (self.width, self.height))
                # Crear una copia invertida para cuando disparemos hacia la izquierda
                Bullet.image_left = pygame.transform.flip(Bullet.image_right, True, False)
            except Exception as e:
                print(f"Error cargando kunai.png: {e}")
                # Señal de fallback por si la imagen no se encuentra
                Bullet.image_right = False 

    def update(self, cam_x):
        self.x += self.vx
        # Eliminar el proyectil si sale de la pantalla (WIDTH es aprox 800)
        if self.x < cam_x - 200 or self.x > cam_x + 800 + 200:
            self.active = False

    def draw(self, surface, cam_x):
        render_x = int(self.x - cam_x)
        render_y = int(self.y)

        # Si la imagen se cargó correctamente, dibujarla
        if Bullet.image_right: 
            if self.dir_x > 0:
                surface.blit(Bullet.image_right, (render_x, render_y))
            else:
                surface.blit(Bullet.image_left, (render_x, render_y))
        else:
            # Fallback: Si no hay imagen, dibuja un rectángulo amarillo/rojo como antes
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
    def __init__(self):
        # Mantenemos el hitbox (caja de colisión) original de 30x50 para no alterar la física
        super().__init__(100, 100, 30, 50, 100)
        self.speed = 5
        self.jump_force = -12
        self.shoot_cooldown = 0
        self.invulnerable_timer = 0
        self.anim_frame = 0

        # --- SISTEMA DE SPRITES ---
        self.frames_right = []
        self.frames_left = []
        
        # Tamaño de tu sprite original y el tamaño al que lo vamos a reducir
        original_size = 204
        scale_size = 80 # Reducimos el personaje a 60x60 píxeles

        try:
            # 1. Cargar la hoja de Textures completa
            sheet = pygame.image.load("Textures/naruto_spritee.png").convert_alpha()
            
            # 2. Recortar los 6 fotogramas
            for i in range(6):
                # Crear una superficie transparente vacía del tamaño de un fotograma
                frame_surf = pygame.Surface((original_size, original_size), pygame.SRCALPHA)
                
                # Copiar solo el cuadradito correspondiente de la hoja grande
                area_recorte = (i * original_size, 0, original_size, original_size)
                frame_surf.blit(sheet, (0, 0), area_recorte)
                
                # 3. Escalar el fotograma al tamaño del juego
                frame_scaled = pygame.transform.scale(frame_surf, (scale_size, scale_size))
                
                # 4. Guardar la versión mirando a la derecha y la invertida (izquierda)
                self.frames_right.append(frame_scaled)
                self.frames_left.append(pygame.transform.flip(frame_scaled, True, False))
                
        except Exception as e:
            print(f"Error cargando el sprite de Naruto: {e}")
            # Fallback de seguridad por si la imagen no está: crea un cuadrado rojo
            fallback = pygame.Surface((scale_size, scale_size), pygame.SRCALPHA)
            fallback.fill(RED)
            self.frames_right = [fallback] * 6
            self.frames_left = [fallback] * 6

    def update(self, keys, cam_x, bullets_list, particles_list):
        # Movimiento
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vx = -self.speed
            self.facing_right = False
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vx = self.speed
            self.facing_right = True
        else:
            self.vx *= 0.8 # Fricción

        # Salto
        if (keys[pygame.K_w] or keys[pygame.K_UP]) and self.is_grounded:
            self.vy = self.jump_force
            create_explosion(self.x + self.width/2, self.y + self.height, GRAY_LIGHT, 5, particles_list)

        # Disparo
        if keys[pygame.K_SPACE] and self.shoot_cooldown <= 0:
            self.shoot_cooldown = 8
            bx = self.x + self.width if self.facing_right else self.x - 12
            by = self.y + 15
            direction = 1 if self.facing_right else -1
            bullets_list.append(Bullet(bx, by, direction, True))
            # Retroceso visual
            self.x += -2 if self.facing_right else 2

        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        if self.invulnerable_timer > 0: self.invulnerable_timer -= 1

        self.apply_physics()

        # Límite de cámara izquierda
        if self.x < cam_x: self.x = cam_x

        # Animación de caminar (ajustada a los 6 fotogramas)
        if abs(self.vx) > 1 and self.is_grounded:
            self.anim_frame += 0.3
        else:
            self.anim_frame = 0

    def draw(self, surface, cam_x, frame_count):
        # Parpadeo de invulnerabilidad
        if self.invulnerable_timer > 0 and (frame_count // 4) % 2 == 0:
            return

        render_x = int(self.x - cam_x)
        render_y = int(self.y)

        # Determinar qué fotograma toca (usamos el módulo % 6 porque hay 6 frames)
        current_index = int(self.anim_frame) % 6

        # Elegir la lista de imágenes correcta dependiendo de a dónde mira
        if self.facing_right:
            current_image = self.frames_right[current_index]
        else:
            current_image = self.frames_left[current_index]

        # Como el sprite es de 60x60 pero nuestra caja de colisiones es de 30x50,
        # necesitamos desplazar un poco el dibujo para que quede centrado
        offset_x = -15
        offset_y = -10

        # Dibujar a Naruto en pantalla
        surface.blit(current_image, (render_x + offset_x, render_y + offset_y))

        # Fogonazo del arma adaptado a la nueva posición
        if self.shoot_cooldown > 4:
            radius = int(5 + random.random() * 5)
            f_x = render_x + 45 if self.facing_right else render_x - 15
            pygame.draw.circle(surface, YELLOW_DARK, (f_x, render_y + 25), radius)


# --- ENEMIGOS ---
class Enemy(Entity):
    # Caché de Textures (variables de clase) para no causar lag al crear muchos enemigos
    sprites_ninja = []
    sprites_tank = []
    sprites_cargados = False

    def __init__(self, x, e_type):
        hp = 150 if e_type == 'tank' else 30
        w = 80 if e_type == 'tank' else 30
        h = 60 if e_type == 'tank' else 50
        super().__init__(x, GROUND_Y - h, w, h, hp)
        
        self.type = e_type
        self.speed = -1.0 if e_type == 'tank' else (random.random() * -1.5 - 1.0)
        self.shoot_timer = random.randint(0, 100)
        self.anim_frame = 0
        
        # Cargar imágenes solo para el primer enemigo que aparezca en el juego
        if not Enemy.sprites_cargados:
            Enemy.cargar_sprites()

    @classmethod
    def cargar_sprites(cls):
        # --- CONFIGURACIÓN NINJA DE LA ARENA (Soldier) ---
        try:
            # Reemplaza 'ninja_arena.png' con el nombre de tu archivo real
            hoja_ninja = pygame.image.load("Textures/enemigo2.png").convert_alpha()
            
            # ¡IMPORTANTE! Cambia este '4' por la cantidad de frames que tenga tu spritesheet
            frames_totales_ninja = 6 
            
            ancho_frame = hoja_ninja.get_width() // frames_totales_ninja
            alto_frame = hoja_ninja.get_height()
            
            for i in range(frames_totales_ninja):
                surf = pygame.Surface((ancho_frame, alto_frame), pygame.SRCALPHA)
                surf.blit(hoja_ninja, (0, 0), (i * ancho_frame, 0, ancho_frame, alto_frame))
                # Hitbox original es 30x50, escalamos la imagen un poco más grande por estética
                surf = pygame.transform.scale(surf, (90, 80))
                # Invertimos porque los enemigos caminan hacia la izquierda hacia Naruto
                #surf = pygame.transform.flip(surf, True, False) 
                cls.sprites_ninja.append(surf)
        except Exception as e:
            print(f"Aviso ninja: Falta imagen ninja_arena.png - {e}")
        
        # --- CONFIGURACIÓN ENEMIGO PESADO (Tank) ---
        try:
            # Reemplaza 'enemigo_pesado.png' con el nombre de tu archivo
            hoja_tank = pygame.image.load("Textures/tank2.png").convert_alpha()
            
            # Cambia este '4' por los frames de tu enemigo grande
            frames_totales_tank = 6 
            
            ancho_frame = hoja_tank.get_width() // frames_totales_tank
            alto_frame = hoja_tank.get_height()
            
            for i in range(frames_totales_tank):
                surf = pygame.Surface((ancho_frame, alto_frame), pygame.SRCALPHA)
                surf.blit(hoja_tank, (0, 0), (i * ancho_frame, 0, ancho_frame, alto_frame))
                # Hitbox original es 80x60, escalamos acorde
                surf = pygame.transform.scale(surf, (100, 90))
                #surf = pygame.transform.flip(surf, True, False)
                cls.sprites_tank.append(surf)
        except Exception as e:
            print(f"Aviso tank: Falta imagen enemigo_pesado.png - {e}")
            
        cls.sprites_cargados = True

    def update(self, player_x, bullets_list, particles_list):
        self.apply_physics()
        self.facing_right = False
        
        # Movimiento y animación
        self.vx = self.speed
        self.anim_frame += 0.15 # Velocidad de la animación
        
        if self.type == 'soldier' and random.random() < 0.01 and self.is_grounded:
            self.vy = -8

        # Disparo (Usarán los mismos kunais que Naruto pero rojos si no cargaste una imagen de kunai enemigo)
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
                # Compensamos la posición porque la imagen es ligeramente más grande que el hitbox
                surface.blit(imagen_actual, (render_x - 10, render_y - 5))
            else:
                # Fallback: Soldado base si falta la imagen
                render_y += int(math.sin(frame_count * 0.2) * 2)
                pygame.draw.rect(surface, GRAY_LIGHT, (render_x, render_y + 15, self.width, 20))
                pygame.draw.rect(surface, (252, 165, 165), (render_x + 6, render_y, 18, 15))

        elif self.type == 'tank':
            if self.sprites_tank:
                indice = int(self.anim_frame) % len(self.sprites_tank)
                imagen_actual = self.sprites_tank[indice]
                surface.blit(imagen_actual, (render_x - 5, render_y - 10))
            else:
                # Fallback: Tanque base si falta la imagen
                pygame.draw.rect(surface, (55, 65, 81), (render_x, render_y + 20, self.width, 25))
                pygame.draw.circle(surface, (31, 41, 55), (render_x + 50, render_y + 20), 20)

# --- MOTOR PRINCIPAL ---
class Game:
    def __init__(self):
        self.state = 'START' # START, PLAYING, GAMEOVER
        self.score = 0
        self.camera_x = 0
        self.frame_count = 0
        self.screen_shake = 0
        self.player = None
        self.enemies = []
        self.bullets = []
        self.particles = []

        # --- NUEVO: CARGAR FONDO ---
        try:
            # .convert() acelera drásticamente el rendimiento al dibujar fondos grandes
            img = pygame.image.load("fondo1.jpg").convert()
            # Escalamos la imagen para que cubra exactamente toda la ventana
            self.bg_image = pygame.transform.scale(img, (WIDTH, HEIGHT))
        except Exception as e:
            print(f"Aviso: No se pudo cargar fondo1.jpg: {e}")
            self.bg_image = None
        
        # --- CARGAR PISO ---
        try:
            piso_img = pygame.image.load("piso2.jpeg").convert_alpha()
            # Lo escalamos: ancho de pantalla (800) y altura del suelo (60)
            self.floor_image = pygame.transform.scale(piso_img, (WIDTH, HEIGHT - GROUND_Y))
        except Exception as e:
            print(f"Error cargando piso.jpeg: {e}")
            self.floor_image = None

    def reset(self):
        self.player = Player()
        self.enemies.clear()
        self.bullets.clear()
        self.particles.clear()
        self.score = 0
        self.camera_x = 0
        self.frame_count = 0
        self.screen_shake = 0
        self.state = 'PLAYING'

    def update(self):
        if self.state != 'PLAYING':
            return
            
        self.frame_count += 1
        keys = pygame.key.get_pressed()

        # Cámara
        target_cam_x = self.player.x - 200
        if target_cam_x > self.camera_x:
            self.camera_x = target_cam_x

        # Spawn Enemigos
        spawn_rate = max(30, 120 - int(self.camera_x / 100))
        if self.frame_count % spawn_rate == 0:
            e_type = 'tank' if random.random() < 0.15 else 'soldier'
            self.enemies.append(Enemy(self.camera_x + WIDTH + 50, e_type))

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
            # 1. Dibujar el fondo estático (cielo/montañas)
            if self.bg_image:
                surface.blit(self.bg_image, (0, 0))
            else:
                surface.fill(SKY_BLUE)

            # 2. Dibujar el suelo con scroll infinito
            if self.floor_image:
                # Calculamos el desplazamiento basado en la cámara
                # El suelo se mueve 1:1 con la cámara
                rel_x = self.camera_x % WIDTH
                
                # Dibujamos dos veces la imagen para cubrir el hueco al moverse
                surface.blit(self.floor_image, (-rel_x, GROUND_Y))
                surface.blit(self.floor_image, (-rel_x + WIDTH, GROUND_Y))
            else:
                # Fallback si no hay imagen (rectángulo marrón)
                pygame.draw.rect(surface, DIRT_BROWN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    def draw(self, screen):
        # Superficie intermedia para aplicar el Screen Shake
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
            score_surf = font_med.render(f"PUNTOS: {self.score}", True, YELLOW)
            render_surface.blit(score_surf, (20, 20))
            
            # Barra de vida
            pygame.draw.rect(render_surface, WHITE, (20, 60, 204, 24), 2) # Borde
            pygame.draw.rect(render_surface, (127, 29, 29), (22, 62, 200, 20)) # Fondo rojo oscuro
            hp_width = int((self.player.hp / self.player.max_hp) * 200)
            if hp_width > 0:
                pygame.draw.rect(render_surface, RED, (22, 62, hp_width, 20)) # Vida actual
                
            # Arma
            weapon_surf1 = font_small.render("ARMA", True, WHITE)
            weapon_surf2 = font_med.render("MTRL. PESADA ∞", True, YELLOW)
            render_surface.blit(weapon_surf1, (WIDTH - 150, 20))
            render_surface.blit(weapon_surf2, (WIDTH - 250, 40))

        # --- PANTALLAS DE MENÚ ---
        if self.state == 'START':
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            render_surface.blit(overlay, (0,0))
            
            title = font_large.render("Camino Ninja", True, YELLOW)
            render_surface.blit(title, (WIDTH//2 - title.get_width()//2, 100))
            
            subtitle = font_med.render("MISIÓN: SOBREVIVIR", True, WHITE)
            render_surface.blit(subtitle, (WIDTH//2 - subtitle.get_width()//2, 180))
            
            controls = font_small.render("W A S D: Mover | ESPACIO: Disparar", True, GRAY_LIGHT)
            render_surface.blit(controls, (WIDTH//2 - controls.get_width()//2, 250))
            
            # Botón parpadeante
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                start_txt = font_med.render("PRESIONA ESPACIO PARA INICIAR", True, YELLOW)
                render_surface.blit(start_txt, (WIDTH//2 - start_txt.get_width()//2, 350))

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
        # Controlar FPS (60 cuadros por segundo)
        clock.tick(60)
        
        # Procesar Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Controles de Menú
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game.state == 'START' or game.state == 'GAMEOVER':
                        game.reset()

        # Lógica del juego
        game.update()
        
        # Dibujar en pantalla
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()