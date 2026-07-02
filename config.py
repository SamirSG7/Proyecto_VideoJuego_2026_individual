import pygame
import json
import firebase_admin
from firebase_admin import credentials, firestore
import sys


pygame.init()
pygame.mixer.init()


WIDTH, HEIGHT = 1000, 560
GRAVITY = 0.6
GROUND_Y = HEIGHT - 60


screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Camino Ninja")
clock = pygame.time.Clock()


try:
    with open("levels.json", "r", encoding="utf-8") as f:
        LEVELS = {int(k): v for k, v in json.load(f).items()}
except Exception as e:
    print(f"Error crítico: No se pudo cargar levels.json. Detalle: {e}")
    sys.exit()


try:
    cred = credentials.Certificate("firebasekey.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("conexion exitosa a firebase")
except Exception as e:
    print(f"error al conectar con firebase: {e}")
    db = None


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY_BLUE = (125, 211, 252)
DIRT_BROWN = (180, 83, 9)
RED = (239, 68, 68)
YELLOW = (253, 224, 71)
YELLOW_DARK = (245, 158, 11)
GREEN = (101, 163, 13)
GRAY_DARK = (55, 65, 81)
GRAY_LIGHT = (156, 163, 1)
gray_light = (156, 163, 175)


try:
    font_large = pygame.font.SysFont("courier", 60, bold=True)
    font_med = pygame.font.SysFont("courier", 30, bold=True)
    font_small = pygame.font.SysFont("courier", 18, bold=True)
except:
    font_large = pygame.font.Font(None, 74)
    font_med = pygame.font.Font(None, 36)
    font_small = pygame.font.Font(None, 24)