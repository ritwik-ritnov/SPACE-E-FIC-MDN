

# dino_game.py using Pygame



import pygame
import sys
import random
import json
import os

# Initialize Pygame
pygame.init()

# Game Window Setup
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
is_fullscreen = False 
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
pygame.display.set_caption("Cyber-Dino: Evolution")

# Vibrant Palette
COLOR_BG = (12, 10, 24)
COLOR_WHITE = (255, 255, 255)
COLOR_OBSTACLE = (255, 0, 128)
COLOR_GOLD = (255, 215, 0)
COLOR_SILVER = (192, 192, 192)
COLOR_BRONZE = (205, 127, 50)
COLOR_BAR_BG = (45, 45, 65)
COLOR_GROUND = (32, 28, 54)

# Game Economy & States
GAME_STATE = "LOGIN"  
SAVE_FILE = "cyber_dino_save.json"
all_users_data = {}
current_username = ""
username_input = ""
total_coins = 0
shop_data = {}
save_message_timer = 0

# Stamina System
MAX_STAMINA = 100
player_stamina = MAX_STAMINA
STAMINA_DRAIN = 2.0
STAMINA_REGEN = 0.3

# Default Shop Blueprint
DEFAULT_CHARACTERS = {
    "1": {"name": "CLASSIC (Standard)", "desc": "No special abilities. Pure skill.", "color": (0, 255, 200), "cost": 0, "unlocked": True, "ability": "NONE"},
    "2": {"name": "AUTO-BOT (The Machine)", "desc": "Auto-jumps 3s every 15s.", "color": (255, 255, 0), "cost": 50, "unlocked": False, "ability": "AUTO_PILOT"},
    "3": {"name": "PHANTOM (The Ghost)", "desc": "Can Double Jump mid-air.", "color": (150, 0, 255), "cost": 100, "unlocked": False, "ability": "DOUBLE_JUMP"},
    "4": {"name": "TITAN (The Tank)", "desc": "Armor survives 1 crash per run.", "color": (255, 100, 0), "cost": 150, "unlocked": False, "ability": "ARMOR"},
    "5": {"name": "GLIDER (The Wind)", "desc": "Hold Jump to glide slowly.", "color": (0, 190, 255), "cost": 200, "unlocked": False, "ability": "GLIDE"}
}

# --- ASCII SPRITE ART GENERATOR ---
DINO_STAND_ART = [
    "       XXXXX ",
    "       XXXXX ",
    "       XXXX  ",
    "X    XXXX    ",
    "XX  XXXXX    ",
    "XXXXXXXXX    ",
    " XXXXXXX     ",
    "  X   X      ",
    "  X   X      "
]

DINO_DUCK_ART = [
    "             ",
    "             ",
    "       XXXXX ",
    "       XXXXX ",
    "XX     XXXXX ",
    "XXXXXXXXX    ",
    " XXXXXXX     ",
    "  X   X      ",
    "  X   X      "
]

CACTUS_ART = [
    "    X    ",
    " X  X  X ",
    " X  X  X ",
    " XXXX  X ",
    "    XXXX ",
    "    X    ",
    "    X    "
]

BIRD_ART = [
    "  X       ",
    "   X      ",
    "XXXXX     ",
    "   XXXXXX ",
    "    X     ",
    "   X      "
]

def create_sprite(ascii_art, color, target_width, target_height):
    art_w = len(ascii_art[0])
    art_h = len(ascii_art)
    surf = pygame.Surface((art_w, art_h), pygame.SRCALPHA)
    for y, row in enumerate(ascii_art):
        for x, char in enumerate(row):
            if char != ' ':
                surf.set_at((x, y), color)
    return pygame.transform.scale(surf, (target_width, target_height))


# --- SAVE & LOAD SYSTEM ---
def load_all_data():
    global all_users_data
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as file:
                all_users_data = json.load(file)
        except:
            all_users_data = {}
    else:
        all_users_data = {}

def load_user_profile(username):
    global total_coins, shop_data, all_users_data
    shop_data = {k: v.copy() for k, v in DEFAULT_CHARACTERS.items()}
    
    if username in all_users_data:
        user_info = all_users_data[username]
        total_coins = user_info.get("coins", 0)
        saved_unlocks = user_info.get("unlocked_chars", {})
        for key in shop_data:
            if key in saved_unlocks:
                shop_data[key]["unlocked"] = saved_unlocks[key]
    else:
        total_coins = 0

def save_game():
    if current_username != "": 
        current_high = all_users_data.get(current_username, {}).get("high_score", 0)
        new_high = max(current_high, high_score)
        
        all_users_data[current_username] = {
            "coins": total_coins,
            "high_score": new_high,
            "unlocked_chars": {key: char["unlocked"] for key, char in shop_data.items()}
        }
    try:
        with open(SAVE_FILE, "w") as file:
            json.dump(all_users_data, file)
    except Exception as e:
        pass

def reset_profile():
    global total_coins, shop_data, high_score
    total_coins = 0
    high_score = 0
    shop_data = {k: v.copy() for k, v in DEFAULT_CHARACTERS.items()}
    save_game()

# Fonts
game_font = pygame.font.Font(None, 65)
menu_font = pygame.font.Font(None, 35)
title_font = pygame.font.Font(None, 65)
small_font = pygame.font.Font(None, 26)

# --- GAMEPLAY VARIABLES ---
GROUND_Y = 450
PLAYER_START_X = 100
PLAYER_WIDTH = 44
PLAYER_HEIGHT_STAND = 60
PLAYER_HEIGHT_DUCK = 40

player_y = GROUND_Y - PLAYER_HEIGHT_STAND
player_vel_y = 0
gravity = 0.6
jump_power = -12

selected_char = None
color_player = (0, 255, 200)
active_ability = "NONE"

# Dynamic Player Sprites
dino_stand_surf = None
dino_duck_surf = None
dino_dash_stand_surf = None
dino_dash_duck_surf = None

is_jumping = False
is_ducking = False
can_double_jump = False
extra_life = False
is_dashing = False
auto_active = False
auto_timer = 0

score = 0
high_score = 0
game_speed = 7
obstacles = []
particles = []

def spawn_obstacle():
    obs_type = random.choice(["GROUND", "AIR"])
    if obs_type == "GROUND":
        width = random.choice([30, 45, 60])
        height = random.choice([45, 65, 80])
        y = GROUND_Y - height
        surf = create_sprite(CACTUS_ART, COLOR_OBSTACLE, width, height)
    else:
        width = 50
        height = 35
        y = GROUND_Y - random.choice([70, 105])
        surf = create_sprite(BIRD_ART, COLOR_OBSTACLE, width, height)
        
    # Added "passed": False to track if we jumped it successfully
    obstacles.append({"rect": pygame.Rect(SCREEN_WIDTH, y, width, height), "type": obs_type, "surf": surf, "passed": False})

def reset_game(full_reset=False):
    global player_y, player_vel_y, is_jumping, is_ducking, obstacles, score, game_speed, player_stamina, extra_life, auto_timer
    player_y = GROUND_Y - PLAYER_HEIGHT_STAND
    player_vel_y = 0
    is_jumping = False
    is_ducking = False
    obstacles = []
    
    if full_reset:
        score = 0
    game_speed = 7
    player_stamina = MAX_STAMINA
    
    if active_ability == "ARMOR": extra_life = True
    else: extra_life = False
    
    auto_timer = pygame.time.get_ticks()

def draw_stamina_bar(surface, x, y, stamina):
    bar_width = 150
    bar_height = 15
    fill_width = int((stamina / MAX_STAMINA) * bar_width)
    
    if stamina > 50: color = (0, 255, 100)
    elif stamina > 20: color = (255, 200, 0)
    else: color = (255, 50, 50)
        
    pygame.draw.rect(surface, COLOR_BAR_BG, (x, y, bar_width, bar_height), border_radius=4)
    if fill_width > 0:
        pygame.draw.rect(surface, color, (x, y, fill_width, bar_height), border_radius=4)
    pygame.draw.rect(surface, COLOR_WHITE, (x, y, bar_width, bar_height), 2, border_radius=4)

load_all_data()

# Game Clock
clock = pygame.time.Clock()
FPS = 60
running = True

# Obstacle Spawner Timer
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 1500)

while running:
    current_time = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            running = False
            
        if event.type == SPAWN_EVENT and GAME_STATE == "PLAYING":
            spawn_obstacle()
            next_spawn = random.randint(int(800 - (game_speed*20)), int(1800 - (game_speed*20)))
            pygame.time.set_timer(SPAWN_EVENT, max(500, next_spawn))
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if GAME_STATE == "PLAYING":
                    save_game()
                    GAME_STATE = "MENU"
                elif GAME_STATE == "LEADERBOARD":
                    GAME_STATE = "MENU"
                else:
                    save_game()
                    running = False
                    
            elif event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                if is_fullscreen: screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                else: screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
            
            # LOGIN
            if GAME_STATE == "LOGIN":
                if event.key == pygame.K_RETURN and len(username_input) > 0:
                    current_username = username_input
                    load_user_profile(current_username)
                    high_score = all_users_data.get(current_username, {}).get("high_score", 0)
                    GAME_STATE = "MENU"
                elif event.key == pygame.K_BACKSPACE:
                    username_input = username_input[:-1]
                elif event.key != pygame.K_ESCAPE and event.key != pygame.K_F11:
                    if event.unicode.isalnum() and len(username_input) < 15:
                        username_input += event.unicode

            # MENU
            elif GAME_STATE == "MENU":
                for k in ["1", "2", "3", "4", "5"]:
                    if event.unicode == k:
                        char = shop_data[k]
                        if char["unlocked"]:
                            selected_char = char["name"]
                            color_player = char["color"]
                            active_ability = char["ability"]
                            
                            dino_stand_surf = create_sprite(DINO_STAND_ART, color_player, PLAYER_WIDTH, PLAYER_HEIGHT_STAND)
                            dino_duck_surf = create_sprite(DINO_DUCK_ART, color_player, PLAYER_WIDTH, PLAYER_HEIGHT_DUCK)
                            
                            dino_dash_stand_surf = create_sprite(DINO_STAND_ART, COLOR_WHITE, PLAYER_WIDTH, PLAYER_HEIGHT_STAND)
                            dino_dash_duck_surf = create_sprite(DINO_DUCK_ART, COLOR_WHITE, PLAYER_WIDTH, PLAYER_HEIGHT_DUCK)
                            
                            GAME_STATE = "PLAYING"
                            reset_game(full_reset=True)
                        else:
                            if total_coins >= char["cost"]:
                                total_coins -= char["cost"]
                                char["unlocked"] = True
                                save_game()
                
                if event.key == pygame.K_l:
                    load_all_data()
                    GAME_STATE = "LEADERBOARD"
                elif event.key == pygame.K_r:
                    reset_profile()
                elif event.key == pygame.K_s:
                    save_game()
                    save_message_timer = current_time

            # PLAYING Controls
            elif GAME_STATE == "PLAYING":
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    if not is_jumping:
                        player_vel_y = jump_power
                        is_jumping = True
                        if active_ability == "DOUBLE_JUMP": can_double_jump = True
                    elif can_double_jump and active_ability == "DOUBLE_JUMP":
                        player_vel_y = jump_power
                        can_double_jump = False
                        
                if event.key == pygame.K_r:
                    save_game()
                    reset_game(full_reset=True)

        # KEY UP
        if event.type == pygame.KEYUP:
            if GAME_STATE == "PLAYING":
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP) and player_vel_y < 0:
                    player_vel_y = player_vel_y * 0.5 

    if not running: break

    # --- LOGIN SCREEN ---
    if GAME_STATE == "LOGIN":
        screen.fill(COLOR_BG)
        title = title_font.render("CYBER-DINO LOGIN", True, COLOR_WHITE)
        prompt = menu_font.render("Enter Username and press ENTER:", True, (200, 200, 200))
        user_txt = game_font.render(username_input + "_", True, (0, 255, 200))
        
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 250))
        screen.blit(user_txt, (SCREEN_WIDTH//2 - user_txt.get_width()//2, 320))
        pygame.display.flip()
        clock.tick(FPS)
        continue

    # --- LEADERBOARD SCREEN ---
    if GAME_STATE == "LEADERBOARD":
        screen.fill(COLOR_BG)
        title = title_font.render("GLOBAL HIGHSCORES", True, COLOR_GOLD)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        sorted_users = sorted(all_users_data.items(), key=lambda x: x[1].get('high_score', 0), reverse=True)
        
        y_pos = 150
        for i, (usr, data) in enumerate(sorted_users[:5]):
            if i == 0: color = COLOR_GOLD
            elif i == 1: color = COLOR_SILVER
            elif i == 2: color = COLOR_BRONZE
            else: color = COLOR_WHITE
            
            rank = menu_font.render(f"#{i+1}  {usr}", True, color)
            sc = menu_font.render(f"{data.get('high_score', 0)} Pts", True, color)
            
            screen.blit(rank, (150, y_pos))
            screen.blit(sc, (SCREEN_WIDTH - 150 - sc.get_width(), y_pos))
            y_pos += 60
            
        esc = small_font.render("[ESC] Return to Menu", True, (150, 150, 150))
        screen.blit(esc, (SCREEN_WIDTH//2 - esc.get_width()//2, 500))
        pygame.display.flip()
        clock.tick(FPS)
        continue

    # --- MENU SCREEN ---
    if GAME_STATE == "MENU":
        screen.fill(COLOR_BG)
        
        info_str = f"Player: {current_username}  |  High Score: {high_score}  |  Coins: {total_coins}"
        info_txt = small_font.render(info_str, True, COLOR_GOLD)
        screen.blit(info_txt, (SCREEN_WIDTH//2 - info_txt.get_width()//2, 15))
        
        controls = small_font.render("[L] Leaderboard  |  [R] Reset Stats  |  [S] Save | [F11] Fullscreen | [ESC] Quit", True, (150, 150, 150))
        screen.blit(controls, (SCREEN_WIDTH//2 - controls.get_width()//2, 50))

        title = title_font.render("SELECT DINO", True, COLOR_WHITE)
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        
        y_offset = 180
        for key, char in shop_data.items():
            status = "UNLOCKED (Press to Play)" if char["unlocked"] else f"COST: {char['cost']} Coins (Press to Buy)"
            color = char["color"] if char["unlocked"] else (100, 100, 100)
            
            c_title = menu_font.render(f"[{key}] {char['name']} - {status}", True, color)
            c_desc = small_font.render(char['desc'], True, (180, 180, 180))
            
            screen.blit(c_title, (70, y_offset))
            screen.blit(c_desc, (100, y_offset + 30))
            y_offset += 75

        if save_message_timer > 0 and (current_time - save_message_timer) < 2000:
            saved = menu_font.render("PROFILE SAVED!", True, (0, 255, 0))
            screen.blit(saved, (SCREEN_WIDTH//2 - saved.get_width()//2, SCREEN_HEIGHT - 35))

        pygame.display.flip()
        clock.tick(FPS)
        continue

    # --- PLAYING LOGIC ---
    if GAME_STATE == "PLAYING":
        
        keys = pygame.key.get_pressed()
        
        # Stamina Dash Logic
        is_dashing = False
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if player_stamina > 0:
                is_dashing = True
                player_stamina = max(0, player_stamina - STAMINA_DRAIN)
        else:
            player_stamina = min(MAX_STAMINA, player_stamina + STAMINA_REGEN)

        # Ducking Logic
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            is_ducking = True
            if is_jumping: player_vel_y += 1.5 
        else:
            is_ducking = False

        # Glider Ability
        current_grav = gravity
        if active_ability == "GLIDE" and is_jumping and player_vel_y > 0:
            if keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]:
                current_grav = 0.15

        # Auto-Bot Ability
        if active_ability == "AUTO_PILOT":
            if not auto_active and current_time - auto_timer > 15000:
                auto_active = True
                auto_timer = current_time
            if auto_active and current_time - auto_timer > 3000:
                auto_active = False
                auto_timer = current_time
                
            if auto_active and not is_jumping:
                for obs in obstacles:
                    if obs["rect"].x > PLAYER_START_X and obs["rect"].x < PLAYER_START_X + 150:
                        if obs["type"] == "GROUND":
                            player_vel_y = jump_power
                            is_jumping = True
                        elif obs["type"] == "AIR":
                            is_ducking = True

        # Physics
        player_vel_y += current_grav
        player_y += player_vel_y
        
        current_height = PLAYER_HEIGHT_DUCK if is_ducking else PLAYER_HEIGHT_STAND
        
        # Ground Collision
        if player_y + current_height >= GROUND_Y:
            player_y = GROUND_Y - current_height
            is_jumping = False
            can_double_jump = False
            player_vel_y = 0

        player_rect = pygame.Rect(PLAYER_START_X, player_y, PLAYER_WIDTH, current_height)

        # Move Obstacles & Score
        score += game_speed * 0.1
        game_speed = 7 + (score / 1000)

        for obs in obstacles[:]:
            obs["rect"].x -= (game_speed + (3 if is_dashing else 0))
            
            # --- NEW: Give 10 coins for safely passing the obstacle ---
            if not obs["passed"] and obs["rect"].right < player_rect.left:
                obs["passed"] = True
                total_coins += 10
            
            if obs["rect"].right < 0:
                obstacles.remove(obs)
            
            # Collision
            if player_rect.colliderect(obs["rect"]):
                if is_dashing:
                    obstacles.remove(obs)
                    for _ in range(10): particles.append([[obs["rect"].centerx, obs["rect"].centery], [random.uniform(-4, 4), random.uniform(-4, 4)], 4, COLOR_WHITE, 255])
                elif extra_life and active_ability == "ARMOR":
                    extra_life = False
                    obstacles.remove(obs)
                    for _ in range(15): particles.append([[player_rect.centerx, player_rect.centery], [random.uniform(-3, 3), random.uniform(-3, 3)], 5, (255,100,0), 255])
                else:
                    if score > high_score: high_score = int(score)
                    save_game()
                    reset_game(full_reset=True)

        # Particles (Trail)
        if not is_jumping or is_dashing:
            particles.append([
                [player_rect.centerx - 10, player_rect.bottom - 5], 
                [random.uniform(-2, 0), random.uniform(-1, 0)], 
                random.randint(3, 6), 
                color_player if not is_dashing else (255, 255, 255), 
                255
            ])

        for p in particles[:]:
            p[0][0] += p[1][0]
            p[0][1] += p[1][1]
            p[4] -= 10
            p[2] -= 0.1
            if p[4] <= 0 or p[2] <= 0:
                particles.remove(p)

        # --- DRAWING ---
        screen.fill(COLOR_BG)
        
        # Draw Ground Line
        pygame.draw.rect(screen, COLOR_GROUND, (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
        pygame.draw.line(screen, color_player, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)

        # Draw Particles
        for p in particles:
            if p[2] > 0:
                surf = pygame.Surface((int(p[2])*2, int(p[2])*2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (p[3][0], p[3][1], p[3][2], p[4]), (int(p[2]), int(p[2])), int(p[2]))
                screen.blit(surf, (int(p[0][0] - p[2]), int(p[0][1] - p[2])))

        # Draw Player Sprite
        if is_ducking:
            screen.blit(dino_dash_duck_surf if is_dashing else dino_duck_surf, player_rect)
        else:
            screen.blit(dino_dash_stand_surf if is_dashing else dino_stand_surf, player_rect)
            
        # Draw Shield Auras behind player
        if is_dashing:
            aura = player_rect.inflate(15, 15)
            pygame.draw.rect(screen, (0, 255, 255), aura, 2, border_radius=4)
        elif active_ability == "ARMOR" and extra_life:
            aura = player_rect.inflate(8, 8)
            pygame.draw.rect(screen, (255, 100, 0), aura, 2, border_radius=4)
        elif active_ability == "AUTO_PILOT" and auto_active:
            aura = player_rect.inflate(8, 8)
            pygame.draw.rect(screen, (255, 255, 0), aura, 2, border_radius=4)

        # Draw Obstacle Sprites
        for obs in obstacles:
            screen.blit(obs["surf"], obs["rect"])

        # HUD
        score_txt = game_font.render(f"{int(score)}", True, color_player)
        hi_txt = menu_font.render(f"HI: {int(high_score)}", True, (150, 150, 150))
        coin_txt = menu_font.render(f"Coins: {total_coins}", True, COLOR_GOLD)
        esc_txt = small_font.render("[ESC] Menu  |  [R] Restart  |  [SHIFT] Cyber-Dash", True, (150, 150, 150))
        
        screen.blit(score_txt, (SCREEN_WIDTH // 2 - score_txt.get_width() // 2, 20))
        screen.blit(hi_txt, (SCREEN_WIDTH - hi_txt.get_width() - 20, 20))
        screen.blit(coin_txt, (20, 20))
        draw_stamina_bar(screen, 20, 60, player_stamina)
        screen.blit(esc_txt, (SCREEN_WIDTH // 2 - esc_txt.get_width() // 2, 80))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
