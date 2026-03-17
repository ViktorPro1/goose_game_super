import random
import os
import sys

import pygame
from pygame.constants import QUIT, K_DOWN, K_UP, K_LEFT, K_RIGHT

def resource_path(relative_path):
    """Отримати абсолютний шлях до ресурсу, працює і в .exe від PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

pygame.init()

# 🎵 Ініціалізація та запуск музики
try:
    pygame.mixer.init()
    music_path = resource_path('music.mp3')
    if os.path.exists(music_path):
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)
    else:
        print("⚠️ Файл music.mp3 не знайдено, гра працює без музики")
except Exception as e:
    print(f"⚠️ Помилка завантаження музики: {e}")

FPS = pygame.time.Clock()

HEIGHT = 700
WIDTH = 1200

FONT = pygame.font.SysFont('Verdana', 20)

COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)

main_display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🦆 Goose Game - Гра Гуска")

# Завантаження та масштабування фону
try:
    bg = pygame.transform.scale(pygame.image.load(resource_path('background.png')), (WIDTH, HEIGHT))
    print("✅ Фон успішно завантажено")
except Exception as e:
    print(f"⚠️ Помилка завантаження фону: {e}")
    print("📝 Створюємо градієнтний фон...")
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        color_value = 135 + int((206 - 135) * (y / HEIGHT))
        pygame.draw.line(bg, (color_value, 206, 235), (0, y), (WIDTH, y))

bg_X1 = 0
bg_X2 = bg.get_width()
bg_move = 3

# Завантаження зображень гравця
IMAGE_PATH = resource_path("Goose")
player = None
PLAYER_IMAGES = []

try:
    if os.path.exists(IMAGE_PATH) and os.path.isdir(IMAGE_PATH):
        PLAYER_IMAGES = [f for f in os.listdir(IMAGE_PATH) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if PLAYER_IMAGES:
            player = pygame.image.load(os.path.join(IMAGE_PATH, PLAYER_IMAGES[0])).convert_alpha()
            print(f"✅ Завантажено {len(PLAYER_IMAGES)} зображень гуски")
        else:
            raise FileNotFoundError("Папка Goose не містить зображень")
    else:
        raise FileNotFoundError("Папка Goose не знайдена")
except Exception as e:
    print(f"⚠️ Помилка завантаження зображень гуски: {e}")
    print("📝 Створюємо базовий спрайт гравця...")
    PLAYER_IMAGES = ['default']
    player = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.ellipse(player, (255, 215, 0), (0, 0, 50, 50))
    pygame.draw.ellipse(player, (255, 140, 0), (5, 5, 40, 40))
    pygame.draw.circle(player, COLOR_BLACK, (20, 20), 5)
    pygame.draw.circle(player, COLOR_BLACK, (30, 20), 5)

player_rect = player.get_rect(center=(WIDTH // 2, HEIGHT // 2))

player_move_up = [0, -5]
player_move_down = [0, 5]
player_move_left = [-5, 0]
player_move_right = [5, 0]

def create_enemy():
    """Створення ворога"""
    try:
        enemy_path = resource_path('enemy.png')
        if os.path.exists(enemy_path):
            enemy_original = pygame.image.load(enemy_path).convert_alpha()
            enemy = pygame.transform.scale(enemy_original, (45, 45))
        else:
            raise FileNotFoundError
    except Exception:
        enemy = pygame.Surface((45, 45), pygame.SRCALPHA)
        pygame.draw.polygon(enemy, COLOR_RED, [(22, 0), (45, 45), (0, 45)])
        pygame.draw.circle(enemy, (139, 0, 0), (22, 30), 8)
    
    enemy_rect = enemy.get_rect(topleft=(WIDTH, random.randint(50, HEIGHT - 75)))
    enemy_move = [random.randint(-8, -4), 0]
    return [enemy, enemy_rect, enemy_move]

def create_bonus():
    """Створення бонусу"""
    try:
        bonus_path = resource_path('bonus.png')
        if os.path.exists(bonus_path):
            bonus_original = pygame.image.load(bonus_path).convert_alpha()
            bonus = pygame.transform.scale(bonus_original, (65, 65))
        else:
            raise FileNotFoundError
    except Exception:
        bonus = pygame.Surface((65, 65), pygame.SRCALPHA)
        pygame.draw.circle(bonus, COLOR_GREEN, (32, 32), 32)
        pygame.draw.circle(bonus, (0, 200, 0), (32, 32), 25)
        pygame.draw.circle(bonus, (0, 255, 100), (32, 32), 15)
        pygame.draw.polygon(bonus, (255, 215, 0), [(32, 10), (28, 25), (36, 25)])
    
    bonus_rect = bonus.get_rect(topleft=(random.randint(50, WIDTH - 65), 0))
    bonus_move = [0, random.randint(4, 8)]
    return [bonus, bonus_rect, bonus_move]

# Таймери подій
CREATE_ENEMY = pygame.USEREVENT + 1
pygame.time.set_timer(CREATE_ENEMY, 1500)
CREATE_BONUS = pygame.USEREVENT + 2
pygame.time.set_timer(CREATE_BONUS, 3000)
CHANGE_IMAGES = pygame.USEREVENT + 3
pygame.time.set_timer(CHANGE_IMAGES, 200)

# Ігрові змінні
enemies = []
bonuses = []
score = 0
level = 1
level_thresholds = [10, 30, 50, 80, 120]
image_index = 0
paused = False
playing = True

def show_game_over():
    """Екран завершення гри"""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((30, 30, 30))
    main_display.blit(overlay, (0, 0))
    
    game_over_text = pygame.font.SysFont('Verdana', 50).render("💀 GAME OVER 💀", True, COLOR_RED)
    score_text = pygame.font.SysFont('Verdana', 30).render(f"Ваш рахунок: {score}", True, COLOR_WHITE)
    level_text = pygame.font.SysFont('Verdana', 25).render(f"Досягнутий рівень: {level}", True, (255, 215, 0))
    restart_text = FONT.render("Натисніть ENTER для рестарту або ESC для виходу", True, (100, 255, 100))
    
    main_display.blit(game_over_text, game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))
    main_display.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
    main_display.blit(level_text, level_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
    main_display.blit(restart_text, restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

def show_level_up(current_level):
    """Екран підвищення рівня"""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 100, 0))
    main_display.blit(overlay, (0, 0))
    
    level_text = pygame.font.SysFont('Verdana', 50).render(f"🎉 РІВЕНЬ {current_level} 🎉", True, (255, 215, 0))
    congrats_text = pygame.font.SysFont('Verdana', 25).render("Вітаємо з підвищенням рівня!", True, COLOR_WHITE)
    continue_text = FONT.render("Натисніть ENTER, щоб продовжити...", True, (200, 255, 200))
    
    main_display.blit(level_text, level_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))
    main_display.blit(congrats_text, congrats_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10)))
    main_display.blit(continue_text, continue_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                waiting = False

print("🎮 Гра запущена! Керування: стрілки, ПРОБІЛ - пауза, ESC - вихід")

# 🎮 ГОЛОВНИЙ ІГРОВИЙ ЦИКЛ
while playing:
    FPS.tick(120)

    for event in pygame.event.get():
        if event.type == QUIT:
            playing = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
                print("⏸️ Пауза" if paused else "▶️ Продовжити")
            if event.key == pygame.K_ESCAPE:
                print("👋 Вихід з гри...")
                playing = False
        
        if not paused:
            if event.type == CREATE_ENEMY:
                enemies.append(create_enemy())
            
            if event.type == CREATE_BONUS:
                bonuses.append(create_bonus())
            
            if event.type == CHANGE_IMAGES:
                if len(PLAYER_IMAGES) > 1 and PLAYER_IMAGES[0] != 'default':
                    try:
                        player = pygame.image.load(os.path.join(IMAGE_PATH, PLAYER_IMAGES[image_index])).convert_alpha()
                        image_index = (image_index + 1) % len(PLAYER_IMAGES)
                    except Exception:
                        pass

    if paused:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 50))
        main_display.blit(overlay, (0, 0))
        
        pause_text = pygame.font.SysFont('Verdana', 40).render("⏸️ ПАУЗА", True, (100, 200, 255))
        continue_text = FONT.render("Натисніть ПРОБІЛ щоб продовжити", True, COLOR_WHITE)
        
        main_display.blit(pause_text, pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
        main_display.blit(continue_text, continue_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))
        
        pygame.display.flip()
        continue

    # Рух фону (ефект скролінгу)
    bg_X1 -= bg_move
    bg_X2 -= bg_move
    if bg_X1 < -bg.get_width():
        bg_X1 = bg.get_width()
    if bg_X2 < -bg.get_width():
        bg_X2 = bg.get_width()
    
    main_display.blit(bg, (bg_X1, 0))
    main_display.blit(bg, (bg_X2, 0))

    # Керування гравцем
    keys = pygame.key.get_pressed()
    if keys[K_DOWN] and player_rect.bottom < HEIGHT:
        player_rect = player_rect.move(player_move_down)
    if keys[K_UP] and player_rect.top > 0:
        player_rect = player_rect.move(player_move_up)
    if keys[K_RIGHT] and player_rect.right < WIDTH:
        player_rect = player_rect.move(player_move_right)
    if keys[K_LEFT] and player_rect.left > 0:
        player_rect = player_rect.move(player_move_left)

    # Обробка ворогів
    for enemy in enemies[:]:
        enemy[1] = enemy[1].move(enemy[2])
        main_display.blit(enemy[0], enemy[1])
        
        if player_rect.colliderect(enemy[1]):
            print(f"💀 Game Over! Рахунок: {score}, Рівень: {level}")
            show_game_over()
            enemies.clear()
            bonuses.clear()
            score = 0
            level = 1
            player_rect.center = (WIDTH // 2, HEIGHT // 2)
            print("🔄 Гра перезапущена!")

    # Обробка бонусів
    for bonus in bonuses[:]:
        bonus[1] = bonus[1].move(bonus[2])
        main_display.blit(bonus[0], bonus[1])
        
        if player_rect.colliderect(bonus[1]):
            score += 1
            bonuses.remove(bonus)
            print(f"⭐ Бонус! Рахунок: {score}")
            
            # Перевірка підвищення рівня
            if level <= len(level_thresholds) and score >= level_thresholds[level - 1]:
                level += 1
                print(f"🎉 Новий рівень: {level}!")
                show_level_up(level)
                
                # Збільшення складності
                bg_move += 0.5
                if level > 2:
                    pygame.time.set_timer(CREATE_ENEMY, max(800, 1500 - (level * 100)))

    # Відображення HUD (інтерфейс)
    hud_bg = pygame.Surface((200, 100))
    hud_bg.set_alpha(180)
    hud_bg.fill((0, 0, 0))
    main_display.blit(hud_bg, (WIDTH - 210, 10))
    
    score_text = pygame.font.SysFont('Verdana', 22).render(f"⭐ Очки: {score}", True, (255, 215, 0))
    level_text = pygame.font.SysFont('Verdana', 22).render(f"📊 Рівень: {level}", True, (100, 200, 255))
    
    main_display.blit(score_text, (WIDTH - 200, 20))
    main_display.blit(level_text, (WIDTH - 200, 50))
    
    # Прогрес до наступного рівня
    if level <= len(level_thresholds):
        next_threshold = level_thresholds[level - 1]
        progress = min(score / next_threshold, 1.0)
        pygame.draw.rect(main_display, (50, 50, 50), (WIDTH - 200, 80, 180, 15))
        pygame.draw.rect(main_display, COLOR_GREEN, (WIDTH - 200, 80, int(180 * progress), 15))

    # Відображення гравця
    main_display.blit(player, player_rect)

    pygame.display.flip()

    # Видалення об'єктів за межами екрану
    enemies = [enemy for enemy in enemies if enemy[1].left > -50]
    bonuses = [bonus for bonus in bonuses if bonus[1].top < HEIGHT + 50]

print("👋 Дякуємо за гру!")
pygame.quit()
sys.exit()