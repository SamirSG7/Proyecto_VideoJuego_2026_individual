import pygame
import random
import sys
from firebase_admin import firestore


from config import screen, clock, WIDTH, HEIGHT, GROUND_Y, LEVELS, db, \
    BLACK, WHITE, SKY_BLUE, DIRT_BROWN, RED, YELLOW, YELLOW_DARK, GREEN, GRAY_DARK, GRAY_LIGHT, \
    font_large, font_med, font_small


from entities.player import Player
from entities.enemy import Enemy
from entities.base import create_explosion



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
        self.top_scores = []
        self.player_name = ""

        try:
            img_inicio = pygame.image.load("Textures/poortada.png").convert()
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

        try:
            img = pygame.image.load(data["background"]).convert()
            self.current_background = pygame.transform.scale(img, (WIDTH, HEIGHT))
        except Exception as e:
            print(f"Error cargando fondo: {e}")
            self.current_background = None

        try:
            piso_img = pygame.image.load(data["floor"]).convert()
            self.floor_image = pygame.transform.scale(piso_img, (WIDTH, HEIGHT - GROUND_Y))
        except Exception as e:
            print(f"Error cargando el suelo {data['floor']}: {e}")
            self.floor_image = None

        Enemy.cargar_sprites(data["enemy"], data["tank"])
        self.enemies.clear()

        try:
            pygame.mixer.music.load(data["music"])
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Aviso de música: {e}")

        self.level_message = data["name"]
        self.level_message_timer = 180

    def reset(self):
        self.player = Player()
        self.bullets.clear()
        self.particles.clear()
        self.score = 0
        self.camera_x = 0
        self.frame_count = 0
        self.screen_shake = 0
        self.state = 'PLAYING'
        self.load_level(1)

    def update(self):
        if self.state != 'PLAYING':
            return

        self.frame_count += 1
        keys = pygame.key.get_pressed()

        target_cam_x = self.player.x - 200
        if target_cam_x > self.camera_x:
            self.camera_x = target_cam_x

        nuevo_nivel = min(
            max(LEVELS.keys()),
            int(self.camera_x / self.level_distance) + 1
        )

        if nuevo_nivel != self.level:
            self.load_level(nuevo_nivel)

        current_level_data = LEVELS[self.level]
        if self.frame_count % current_level_data["spawn_rate"] == 0:
            e_type = 'tank' if random.random() < current_level_data["tank_probability"] else 'soldier'
            self.enemies.append(Enemy(
                self.camera_x + WIDTH + 50,
                e_type,
                current_level_data["enemy_speed"]
            ))

        self.player.update(keys, self.camera_x, self.bullets, self.particles)

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
                create_explosion(e.x + e.width / 2, e.y + e.height / 2, 'explosion', 30 if e.type == 'tank' else 15,
                                 self.particles)
                if e.type == 'tank': self.screen_shake = 10
                self.enemies.remove(e)
            elif e.x < self.camera_x - 200:
                self.enemies.remove(e)

        if self.player.dead:
            if self.state == 'PLAYING':
                self.state = 'INPUT_NAME'

        if self.particles[:]:
            for p in self.particles[:]:
                p.update()
                if p.life <= 0:
                    self.particles.remove(p)

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
            for e in self.enemies:
                e.draw(render_surface, self.camera_x, self.frame_count)
            for b in self.bullets:
                b.draw(render_surface, self.camera_x)
            for p in self.particles:
                p.draw(render_surface, self.camera_x)

            # --- HUD ---
            shadow_score = font_med.render(f"PUNTOS: {self.score}", True, BLACK)
            score_surf = font_med.render(f"PUNTOS: {self.score}", True, YELLOW)
            render_surface.blit(shadow_score, (22, 22))
            render_surface.blit(score_surf, (20, 20))

            pygame.draw.rect(render_surface, WHITE, (20, 60, 204, 24), 2)
            pygame.draw.rect(render_surface, (127, 29, 29), (22, 62, 200, 20))
            hp_width = int((self.player.hp / self.player.max_hp) * 200)
            if hp_width > 0:
                pygame.draw.rect(render_surface, RED, (22, 62, hp_width, 20))

            shadow_surf1 = font_small.render("ARMA", True, BLACK)
            shadow_surf2 = font_med.render("KUNAI ∞", True, BLACK)
            weapon_surf1 = font_small.render("ARMA", True, WHITE)
            weapon_surf2 = font_med.render("KUNAI ∞", True, YELLOW)

            render_surface.blit(shadow_surf1, (WIDTH - 148, 22))
            render_surface.blit(shadow_surf2, (WIDTH - 178, 42))
            render_surface.blit(weapon_surf1, (WIDTH - 150, 20))
            render_surface.blit(weapon_surf2, (WIDTH - 180, 40))

            if self.level_message_timer > 0:
                shadow = font_large.render(f"NIVEL {self.level}: {self.level_message}", True, BLACK)
                msg = font_large.render(f"NIVEL {self.level}: {self.level_message}", True, YELLOW)
                pos_x = WIDTH // 2 - msg.get_width() // 2
                render_surface.blit(shadow, (pos_x + 3, 153))
                render_surface.blit(msg, (pos_x, 150))
                self.level_message_timer -= 1

        if self.state == 'INPUT_NAME':
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 240))
            render_surface.blit(overlay, (0, 0))
            msg_title = font_large.render("¡NUEVA MARCA!", True, YELLOW)
            render_surface.blit(msg_title, (WIDTH // 2 - msg_title.get_width() // 2, 100))

            msg_sub = font_med.render("INGRESA TU NOMBRE DE NINJA:", True, WHITE)
            render_surface.blit(msg_sub, (WIDTH // 2 - msg_sub.get_width() // 2, 200))

            input_box = pygame.Rect(WIDTH // 2 - 200, 260, 400, 50)
            pygame.draw.rect(render_surface, GRAY_DARK, input_box, border_radius=8)
            pygame.draw.rect(render_surface, YELLOW if len(self.player_name) > 0 else WHITE, input_box, width=2,
                             border_radius=8)

            text_surf = font_med.render(self.player_name + ("|" if (pygame.time.get_ticks() // 400) % 2 == 0 else ""),
                                        True, YELLOW)
            render_surface.blit(text_surf, (input_box.x + 15, input_box.y + 10))

            if len(self.player_name) >= 3:
                info_txt = font_small.render("PRESIONA ENTER PARA GUARDAR TU RÉCORD", True, GREEN)
            else:
                info_txt = font_small.render("(Escribe al menos 3 caracteres)", True, GRAY_LIGHT)
            render_surface.blit(info_txt, (WIDTH // 2 - info_txt.get_width() // 2, 350))

        if self.state == 'START':
            if self.start_image:
                render_surface.blit(self.start_image, (0, 0))
            else:
                render_surface.fill(BLACK)

            if (pygame.time.get_ticks() // 500) % 2 == 0:
                start_txt = font_med.render("PRESIONA ESPACIO PARA INICIAR", True, YELLOW)
                shadow_start = font_med.render("PRESIONA ESPACIO PARA INICIAR", True, BLACK)
                pos_x = WIDTH // 2 - start_txt.get_width() // 2
                render_surface.blit(shadow_start, (pos_x + 2, HEIGHT - 198))
                render_surface.blit(start_txt, (pos_x, HEIGHT - 200))

        elif self.state == 'GAMEOVER':
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            render_surface.blit(overlay, (0, 0))

            title = font_large.render("MISIÓN FALLIDA", True, RED)
            render_surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))

            score_txt = font_med.render(f"PUNTUACIÓN FINAL: {self.score}", True, YELLOW)
            render_surface.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, 130))

            leaderboards_title = font_med.render("top 5 ninjas", True, YELLOW)
            render_surface.blit(leaderboards_title, (WIDTH // 2 - leaderboards_title.get_width() // 2, 200))

            pygame.draw.line(render_surface, YELLOW_DARK, (WIDTH // 2 - 200, 235), (WIDTH // 2 + 200, 235), 2)
            start_y = 260
            if len(self.top_scores) == 0:
                no_data_txt = font_small.render("cargando posiciones", True, GRAY_LIGHT)
                render_surface.blit(no_data_txt, (WIDTH // 2 - no_data_txt.get_width() // 2, start_y + 30))
            else:
                for i, jugador in enumerate(self.top_scores):
                    pos_text = f"{i + 1}. {jugador.get('nombre', 'Anónimo')}"
                    pts_text = f"{jugador.get('puntos', 0)} pts"
                    render_pos = font_small.render(pos_text, True, WHITE if i > 0 else YELLOW)
                    render_pts = font_small.render(pts_text, True, WHITE if i > 0 else YELLOW)
                    render_surface.blit(render_pos, (WIDTH // 2 - 180, start_y + (i * 30)))
                    render_surface.blit(render_pts, (WIDTH // 2 + 80, start_y + (i * 30)))
            restart_txt = font_small.render("PRESIONA ESPACIO PARA REINICIAR", True, WHITE)
            render_surface.blit(restart_txt, (WIDTH // 2 - restart_txt.get_width() // 2, 420))

        screen.blit(render_surface, (0, 0))


def save_record(nombre_jugador, puntos):
    if db is None:
        print("firebase no esta disponible. no se guardo el record")
        return
    try:
        doc_ref = db.collection("leaderboard").document(nombre_jugador)
        doc = doc_ref.get()
        if doc.exists:
            record_actual = doc.to_dict().get("puntos", 0)
            if puntos <= record_actual:
                print("el puntaje actual no supera el record existente")
                return

        doc_ref.set({
            "nombre": nombre_jugador,
            "puntos": puntos,
            "fecha": firestore.SERVER_TIMESTAMP
        })
        print(f"¡Récord de {nombre_jugador} ({puntos} pts) guardado en Firebase!")
    except Exception as e:
        print(f"Error al subir datos: {e}")


def obtener_top():
    if db is None: return []
    try:
        top_jugadores = db.collection("leaderboard") \
            .order_by("puntos", direction=firestore.Query.DESCENDING) \
            .limit(5) \
            .stream()
        return [jugador.to_dict() for jugador in top_jugadores]
    except Exception as e:
        print(f"Error al bajar top scores: {e}")
        return []


# --- BUCLE PRINCIPAL ---
def main():
    game = Game()
    running = True

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if game.state in ['START', 'GAMEOVER']:
                    if event.key == pygame.K_SPACE:
                        game.player_name = ""
                        game.reset()

                elif game.state == 'INPUT_NAME':
                    if event.key == pygame.K_RETURN:
                        if len(game.player_name) >= 3:
                            save_record(game.player_name, game.score)
                            print("Descargando tabla de clasificación...")
                            game.top_scores = obtener_top()
                            game.state = 'GAMEOVER'
                    elif event.key == pygame.K_BACKSPACE:
                        game.player_name = game.player_name[:-1]
                    else:
                        if len(game.player_name) < 12 and event.unicode:
                            if event.unicode.isalnum() or event.unicode == " ":
                                game.player_name += event.unicode

        game.update()
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()