# Camino Ninja: Presentación del Proyecto

## Introducción al Proyecto
**¿De qué trata "Camino Ninja"?**
* Es un videojuego de plataformas y acción en 2D (Side-scroller).
* Desarrollado completamente en Python utilizando la librería Pygame.
* Inspirado en el universo anime (Naruto), donde el jugador debe evadir y derrotar enemigos mientras avanza por diferentes escenarios.
* **Objetivo técnico:** Demostrar el dominio de la Programación Orientada a Objetos (POO), manejo de eventos, colisiones y físicas básicas.

---

## Arquitectura y Herramientas
**Tecnologías utilizadas:**
* **Python:** Lenguaje principal.
* **Pygame:** Motor gráfico y de audio.
* **Módulos estándar:** `random`, `math`, `sys`.

**Estructura del Código (POO):**
* Clases base y derivadas para organizar el comportamiento.
* Separación de responsabilidades: Entidades, Partículas, Proyectiles y el Motor Principal (`Game`).

---

## Diseño de Niveles Escalable
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
* **Ataque:** Disparo de proyectiles (Kunais) con la tecla ESPACIO y un sistema de cooldown (enfriamiento) para no disparar infinitamente.
* **Animación:** Carga un spritesheet (hoja de sprites), lo recorta y actualiza los frames según la dirección y velocidad del jugador.
* **Sonidos:** Integración del módulo `pygame.mixer` para efectos de salto y disparo.
* **Recolección de Ítems (Power-Ups):** El jugador puede recoger diversos ítems con efectos estratégicos:
    * **Pergamino:** Otorga invulnerabilidad temporal por 5 segundos.
    * **Ramen:** Restaura completamente la vida del jugador.
    * **Clon Naruto:** Rellena por completo la barra de Chakra del jugador.

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
* **Cámara de Desplazamiento (Scrolling):** * La cámara sigue al jugador (`target_cam_x`).
    * El suelo y el fondo se renderizan de manera relativa a la cámara, creando la ilusión de un mundo infinito.
* **HUD (Interfaz):** Presenta un diseño completamente renovado estilo pergamino para el jugador. Incluye:
    * Retrato de Naruto y emblema de Konoha.
    * Barras de vida (HP) y Chakra con degradado de color y valores numéricos.
    * Un cuadro central estilo pergamino para el puntaje y el nivel actual.
    * Cuadros estilo pergamino para el tipo de arma (Kunai) y el estado del Rasengan.
* **Screen Shake:** Efecto de temblor de pantalla al recibir daño o destruir tanques.

---

## El Gran Jefe (Boss)
**Implementación:**
*   **Jefes por Nivel:** Se instancian dinámicamente según el nivel (Shukaku para Nivel 1, Itachi para Nivel 2).
*   **Ataques Especiales:** Cada jefe tiene un conjunto de ataques y proyectiles únicos, incluyendo poderosas técnicas como el Bijudama (Shukaku) y el Amaterasu (Itachi).
*   **Barra de Vida Estética:** Se integra una barra de vida dedicada en el HUD para cada jefe, mostrando su retrato, emblema y el indicador "VS Nivel".

---

## Conclusiones y Mejoras Futuras
**Aprendizajes clave:**
* Aplicación práctica de Álgebra y Física en código (vectores, gravedad).
* Entendimiento del Game Loop (Bucle de juego: Entrada -> Actualización -> Renderizado).

**Mejoras a futuro:**
* Implementar un sistema de guardado de puntaje máximo (High Score) usando archivos de texto o bases de datos.
* Agregar menús de configuración de volumen.
