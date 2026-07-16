# Documentación Técnica — Camino Ninja

## Estructura del Proyecto

```
Proyecto_VideoJuego_2026_individual/
├── juegofinal.py          # Código fuente completo
├── sprite/                # Assets del HUD
│   ├── pergamino.png
│   ├── naruto.png
│   ├── emblema.png
│   └── granjefe.png
├── *.png / *.jpg          # Fondos, sprites, íconos de ítems
├── *.wav / *.mp3          # Efectos de sonido y música
├── README.md
└── tecnico.md
```

## Dependencias

- Python 3.x
- Pygame (`pip install pygame`)

## Arquitectura General

El juego se estructura en un solo archivo (`juegofinal.py`) siguiendo el paradigma POO. El bucle principal (`main()`) corre a 60 FPS y ejecuta el ciclo: **entrada → actualización → renderizado**.

### Constantes Globales

| Constante   | Valor | Descripción |
|-------------|-------|-------------|
| `WIDTH`     | 1000  | Ancho de pantalla |
| `HEIGHT`    | 560   | Alto de pantalla |
| `GRAVITY`   | 0.6   | Aceleración gravitacional por frame |
| `GROUND_Y`  | 500   | Coordenada Y del suelo |

### Sistema de Niveles (`LEVELS`)

Diccionario anidado con configuración por nivel:

```python
LEVELS = {
    1: {
        "name": "Aldea de la Hoja",
        "background": "fondo1.png",
        "floor": "piso1.jpg",
        "music": "music1.mp3",
        "enemy": "enemigo1.png",
        "tank": "tank1.png",
        "spawn_rate": 120,        # Frames entre spawns
        "tank_probability": 0.15, # Probabilidad de tanque vs soldado
        "enemy_speed": 1.0,       # Multiplicador de velocidad
        "has_boss": True
    },
    # ... niveles 2 y 3
}
```

La cámara determina el nivel actual mediante `int(camera_x / 5000) + 1`.

## Diagrama de Clases

```
Entity (base)
├── atributos: x, y, vx, vy, width, height, hp, max_hp, facing_right, is_grounded, dead
├── apply_physics()  → gravedad + colisión con suelo
├── take_damage(amount)
└── get_rect()       → pygame.Rect para colisiones

Player(Entity)
├── speed, jump_force, shoot_cooldown, invulnerable_timer
├── chakra, max_chakra, rasengan_cooldown
├── spritesheet animado (6 frames左右)
├── update(keys, cam_x, bullets, particles, rasengan_list, cam_locked)
└── draw(surface, cam_x, frame_count)

Enemy(Entity)
├── type: 'soldier' | 'tank'
├── speed (negativa = izquierda), shoot_timer
├── cargar_sprites(cls, enemy_img, tank_img)  → método de clase
├── update(player_x, bullets, particles)
└── draw(surface, cam_x, frame_count)

BossShukaku(Entity)
├── state: 'idle' | 'charge_bijudama' | 'charge_arena'
├── action_timer, anim_frame
├── update(player, proj_list, trap_list)
└── draw(surface, cam_x)

BossItachi(Entity)
├── state: 'idle' | 'charge_cuervos' | 'charge_amaterasu'
├── action_timer, anim_frame
├── update(player, proj_list, trap_list)
└── draw(surface, cam_x)

Bullet
├── x, y, vx, width, height, is_player, damage, active, dir_x
├── update(cam_x)
├── draw(surface, cam_x)
└── get_rect()

Rasengan
├── x, y, vx, damage=300, anim_frame (6 frames)
├── update(cam_x)
├── draw(surface, cam_x)
└── get_rect()

Bijudama / Cuervos (proyectiles de jefes)
├── similar a Rasengan, con spritesheet propio
└── daño fijo de 20

BossTrapBase (ataques de suelo)
├── ArenaAttack( BossTrapBase)
├── AmaterasuAttack( BossTrapBase)
├── state: 'warning' → 'attacking'
├── update(), check_collision(player), draw()
└── daño: 50 (Arena), 55 (Amaterasu)

Item
├── type: 'pergamino' | 'ramen' | 'clon'
├── anim_float (flotación sinusoidal)
├── update(), draw(surface, cam_x), get_rect()
└── imágenes estáticas compartidas (class attribute)

Particle
├── x, y, vx, vy, color, size, life, max_life
├── update()  → movimiento + gravedad reducida + decaimiento
└── draw(surface, cam_x)

Game (motor)
├── state: 'START' | 'PLAYING' | 'GAMEOVER'
├── camera_x (scroll), score, level
├── screen_shake (efecto temblor)
├── player, enemies[], bullets[], particles[], rasengan_list[], items[]
├── boss_active, boss_defeated, boss, boss_projectiles[], boss_traps[]
├── current_background, floor_image
├── load_level(level_num)
├── reset()
├── update()  → toda la lógica del juego
└── draw(screen)  → renderizado completo
```

## Físicas

### Gravedad y Suelo

```python
def apply_physics(self):
    self.vy += GRAVITY        # 0.6 px/frame²
    self.y += self.vy
    self.x += self.vx
    if self.y + self.height >= GROUND_Y:
        self.y = GROUND_Y - self.height
        self.vy = 0
        self.is_grounded = True
    else:
        self.is_grounded = False
```

Las partículas usan una gravedad reducida (`GRAVITY * 0.2`).

### Colisiones

Todas las colisiones usan `pygame.Rect.colliderect()`:

1. **Jugador ↔ Enemigos**: daño 10, invulnerabilidad 40 frames (~0.67s).
2. **Jugador ↔ Jefe**: daño 20, invulnerabilidad 40 frames.
3. **Jugador ↔ Proyectiles enemigos**: daño 10.
4. **Jugador ↔ Proyectiles de jefe**: daño 20.
5. **Jugador ↔ Trampas de jefe**: daño 50–55.
6. **Proyectil del jugador ↔ Enemigo**: daño 25, explosión.
7. **Proyectil del jugador ↔ Jefe**: daño 25.
8. **Rasengan ↔ Enemigo/Jefe**: daño 300, explosión grande + screen shake.
9. **Jugador ↔ Item**: según tipo (vida/chakra/invulnerabilidad).

## Cámara

- La cámara sigue al jugador con un offset de 200px (`target_cam_x = player.x - 200`).
- Durante la pelea contra el jefe, la cámara se bloquea en la posición del jefe.
- La distancia para cambio de nivel es `level * 5000 - WIDTH`.

## Máquina de Estados del Juego

```
START  ──(ESPACIO)──→  PLAYING  ──(muerte)──→  GAMEOVER
                       ↑                          │
                       └────(ESPACIO)──────────────┘
```

## HUD

- **Barra de vida (HP)**: degradado de rojo/verde según porcentaje.
- **Barra de chakra**: degradado azul.
- **Cuadro central**: puntuación y nivel actual.
- **Cuadro derecho**: arma (Kunai ∞) y estado del Rasengan (30 CHAKRA / SIN CHAKRA).
- **Mensaje de nivel**: "NIVEL X: Nombre" con sombra.
- **Pantalla de inicio**: portada + "PRESIONA ESPACIO PARA INICIAR" parpadeante.
- **Game Over**: overlay negro + puntuación final + opción de reinicio.

## Jefes — Máquina de Estados

Cada jefe alterna entre `idle` y carga de ataque:

```
idle ──(timer)──→ charge_* ──(timer)──→ idle
```

**Shukaku** (Nv.1, 1000 HP):
- Bijudama: proyectil grande púrpura.
- Arena: tramza de suelo que daña al pisarla.

**Itachi** (Nv.2, 1500 HP):
- Cuervos: proyectil negro con spritesheet.
- Amaterasu: trampa de suelo negra.

## Sprites y Recursos

- `load_spritesheet(filename, width, height, frames_count)`: carga una hoja de sprites y la divide en frames individuales.
- Las imágenes se cargan con `convert_alpha()` para transparencia.
- El spritesheet del jugador tiene 6 frames para animación de movimiento.
- Cada jefe tiene 3 spritesheets: idle, carga de ataque 1, carga de ataque 2.

## Sonido

- `pygame.mixer.Sound` para efectos (salto, kunai, rasengan, ataques de jefe).
- `pygame.mixer.music` para música de fondo por nivel.
- Cada sonido se carga una sola vez (patrón singleton con variables de clase).

## Sistema de Partículas

Las explosiones se crean con `create_explosion(x, y, color_type, count, particles_list)`:
- Genera `count` partículas con velocidad aleatoria radial.
- Cada partícula tiene `life` (frames antes de desaparecer) y `size` que se reduce gradualmente.
- Colores predefinidos: `'explosion'` (rojos), o cualquier color RGB.

## Items — Probabilidades de Spawn

| Item       | Probabilidad | Efecto |
|------------|-------------|--------|
| Pergamino  | 10%         | Invulnerabilidad 240 frames (4s) |
| Ramen      | 10%         | Vida al máximo |
| Clon       | 10%         | Chakra al máximo |
| (nada)     | 70%         | — |

Intervalo de spawn: cada 180 frames (~3s a 60 FPS).

## Posibles Mejoras Técnicas

- Separar el código en múltiples módulos (uno por clase).
- Implementar un sistema de físicas más robusto (vs. colisión simple con el suelo).
- Asset loading con caché y manejo de errores más granular.
- Sistema de partículas con pooling para rendimiento.
- Guardado de high score en archivo.
