# Librerías necesarias — "Camino Ninja"

## 1. Pygame (externa)
Motor gráfico, de audio y de eventos. Debe instalarse con pip.

```
pip install pygame
```

**Uso en el proyecto:**
- `pygame.init()` / `pygame.mixer.init()` — Inicialización del motor y audio.
- `pygame.display.set_mode()` — Creación de la ventana.
- `pygame.image.load()` — Carga de sprites, fondos y suelos.
- `pygame.transform.scale()` / `flip()` — Redimensionado y volteo de imágenes.
- `pygame.Surface` / `pygame.Rect` — Superficies de dibujo y cajas de colisión.
- `pygame.draw.rect()` / `pygame.draw.circle()` — Primitivas gráficas.
- `pygame.font.SysFont()` / `pygame.font.Font()` — Renderizado de texto.
- `pygame.mixer.Sound()` / `pygame.mixer.music()` — Efectos de sonido y música.
- `pygame.key.get_pressed()` / `pygame.event.get()` — Entrada de teclado y eventos.
- `pygame.time.Clock()` / `pygame.time.get_ticks()` — Control de FPS y temporización.
- `pygame.SRCALPHA` — Transparencia en superficies.

---

## 2. random (estándar)
Generación de números aleatorios.

```
import random
```

**Uso en el proyecto:**
- `random.random()` — Probabilidades (spawn de enemigos, salto del soldado).
- `random.randint()` — Temporizadores de disparo.
- `random.choice()` — Colores aleatorios en explosiones.
- `random.random()` — Velocidad y dirección de partículas.

---

## 3. math (estándar)
Operaciones matemáticas.

```
import math
```

**Uso en el proyecto:**
- `math.sin()` — Efecto de ondulación en el fallback del enemigo.

---

## 4. sys (estándar)
Interacción con el intérprete de Python.

```
import sys
```

**Uso en el proyecto:**
- `sys.exit()` — Cierre controlado del juego al salir del bucle principal.

---

## Instalación rápida

```bash
pip install pygame
```

Los módulos `random`, `math` y `sys` vienen incluidos con Python y no requieren instalación adicional.
