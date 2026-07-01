# Camino Ninja: Presentación del Proyecto

## Introducción al Proyecto
**¿De qué trata "Camino Ninja"?**
* Es un videojuego de plataformas y acción en 2D (Side-scroller).
* Desarrollado completamente en Python utilizando la librería Pygame.
* Inspirado en el universo anime (Naruto), donde el jugador debe evadir y derrotar enemigos mientras avanza por diferentes escenarios.
* **Objetivo técnico:** Demostrar el dominio de la Programación Orientada a Objetos (POO), manejo de eventos, colisiones y físicas básicas.

---

## Archivos del Proyecto

| Archivo | Descripción |
|---|---|
| `juegofinal.py` | Versión completa: 3 niveles, portada, música por nivel, volumen, rasengan |
| `juego.py` | Versión simple: 1 nivel infinito, volumen, rasengan |
| `LIBRERIAS.md` | Documentación de librerías |
| `requirements.txt` | Dependencias para `pip` |

---

## Instalación y Ejecución

```bash
pip install -r requirements.txt
python3 juegofinal.py   # Versión completa
python3 juego.py        # Versión simple
```

**En WSL:** Si no hay audio, el juego lo detecta automáticamente y funciona sin sonido.

---

## Controles

| Tecla | Acción |
|---|---|
| `W` / `↑` | Saltar |
| `A` / `←` | Mover izquierda |
| `D` / `→` | Mover derecha |
| `ESPACIO` | Disparar Kunai |
| `R` | Lanzar Rasengan (cuesta 30 de chakra) |

En la pantalla de inicio:
| `W` / `↑` | Subir volumen música |
| `S` / `↓` | Bajar volumen música |
| `A` / `←` | Bajar volumen efectos |
| `D` / `→` | Subir volumen efectos |

---

## Arquitectura y Herramientas
**Tecnologías utilizadas:**
* **Python:** Lenguaje principal.
* **Pygame:** Motor gráfico y de audio.
* **Módulos estándar:** `os`, `random`, `math`, `sys`.

**Estructura del Código (POO):**
* Clases base y derivadas para organizar el comportamiento.
* Separación de responsabilidades: Entidades, Partículas, Proyectiles, Habilidades y el Motor Principal (`Game`).

---

## Diseño de Niveles Escalable (juegofinal.py)
**Uso de Diccionarios para Configuración:**
* En lugar de "quemar" (hardcodear) los datos de cada nivel, se utilizó un diccionario global `LEVELS`.
* **Atributos por nivel:** Fondo, suelo, música, sprites de enemigos, velocidad y tasa de aparición (spawn rate).
* **Ventaja:** Permite agregar nuevos niveles fácilmente sin modificar la lógica principal del juego.
* **Progresión dinámica:** La cámara determina en qué nivel estamos según la distancia recorrida.

---

## Físicas y Herencia (Clase Entity)
**La Clase Base Entity:**
* Define propiedades comunes: posición (x, y), dimensiones, velocidad (vx, vy), puntos de vida (HP).
* Implementa el método `apply_physics()`:
    * Aplica una constante de gravedad.
    * Maneja la colisión con el suelo (`is_grounded`).
* Implementa la lógica de recibir daño (`take_damage`).

**Herencia:**
* Las clases `Player` y `Enemy` heredan de `Entity`, reutilizando todo el código de físicas y vida.

---

## El Jugador (Clase Player)
**Mecánicas Principales:**
* **Movimiento y Salto:** Controlado por eventos de teclado (W, A, S, D / Flechas).
* **Ataque básico:** Disparo de proyectiles (Kunais) con la tecla ESPACIO y un sistema de cooldown.
* **Habilidad especial - Rasengan (R):** Lanza una esfera de energía que requiere 30 de chakra. Hace 300 de daño (mata cualquier enemigo de un golpe). Animación de carga con spritesheet propio (`naruto_rasengan.png`).
* **Chakra:** Sistema de energía con regeneración pasiva (+1 cada 0.5s). Se muestra en una barra estilo acero en el HUD.
* **Animación:** Carga un spritesheet, lo recorta y actualiza los frames según la dirección y velocidad del jugador.
* **Sonidos:** Integración del módulo `pygame.mixer` para efectos de salto, disparo y rasengan.

---

## Inteligencia de Enemigos (Clase Enemy)
**Tipos de Enemigos:**
* **Soldado Ninja:** Rápido, salta aleatoriamente, menor vida.
* **Tanque:** Lento, dispara proyectiles más grandes, mucha vida.

**Lógica de Spawn y Comportamiento:**
* Generación dinámica fuera de la pantalla (a la derecha).
* Calculan la distancia con el jugador para decidir cuándo disparar (`shoot_timer`).
* Su velocidad y probabilidad de aparición se adaptan según la dificultad del nivel actual.

---

## Habilidades Especiales (Clase Rasengan)
**Rasengan:**
* Proyectil grande (60x60px) con animación de 2 frames (`rasengan.png`).
* Daño 300 — elimina cualquier enemigo al impacto.
* Genera una explosión de partículas masiva al colisionar.
* Cooldown de 60 frames (~1 segundo) entre usos.

---

## Colisiones y Efectos Visuales
**Proyectiles (Clase Bullet):**
* Diferencia entre proyectiles del jugador y del enemigo (dirección y daño).
* Uso de `pygame.Rect.colliderect()` para detectar impactos (Hitboxes).

**Sistema de Partículas (Clase Particle):**
* Creado desde cero para simular explosiones, chispas y polvo al saltar.
* Cada partícula tiene posición, velocidad aleatoria, color, tamaño y "tiempo de vida".

---

## El Motor del Juego (Clase Game)
**El Controlador Principal:**
* **Máquina de Estados:** Maneja las transiciones entre pantallas (START, PLAYING, GAMEOVER).
* **Cámara de Desplazamiento (Scrolling):** La cámara sigue al jugador (`target_cam_x`). El suelo y el fondo se renderizan de manera relativa a la cámara, creando la ilusión de un mundo infinito.
* **HUD (Interfaz):** Muestra puntaje, barra de vida, barra de chakra (estilo acero con remaches), armas (Kunai ∞, Rasengan) y nivel actual.
* **Control de Volumen:** En la pantalla de inicio se pueden ajustar volumen de música y efectos con barras visuales estilo acero.
* **Screen Shake:** Efecto de temblor de pantalla al recibir daño o destruir tanques.

---

## Compatibilidad con WSL
El juego detecta automáticamente si el sistema de audio está disponible:
* Si `pygame.mixer.init()` falla (ej. en WSL sin PulseAudio), establece `audio_disponible = False` y el juego funciona sin sonido.
* Fuerza el driver `pulse` mediante variables de entorno para compatibilidad con WSLg.

---

## Conclusiones y Mejoras Futuras
**Aprendizajes clave:**
* Aplicación práctica de Álgebra y Física en código (vectores, gravedad).
* Entendimiento del Game Loop (Bucle de juego: Entrada -> Actualización -> Renderizado).

**Mejoras a futuro:**
* Añadir un jefe final (Boss).
* Implementar un sistema de guardado de puntaje máximo (High Score) usando archivos de texto o bases de datos.
* Agregar más habilidades especiales.
