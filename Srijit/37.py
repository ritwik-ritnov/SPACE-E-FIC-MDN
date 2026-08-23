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
pygame.display.set_caption("Cyber-Pong: Evolution")

# Vibrant Palette
COLOR_BG = (12, 10, 24)
COLOR_WHITE = (255, 255, 255)
COLOR_AI = (255, 0, 128)
COLOR_P2 = (0, 150, 255) 
COLOR_GOLD = (255, 215, 0)
COLOR_SILVER = (192, 192, 192)
COLOR_BRONZE = (205, 127, 50)
COLOR_BAR_BG = (45, 45, 65)

BALL_COLORS = [(255, 230, 0), (255, 90, 0), (0, 255, 0), (180, 0, 255), (0, 190, 255)]
current_ball_color = random.choice(BALL_COLORS)

# Game Economy & States
GAME_STATE = "LOGIN"  
game_mode = "1vBOT"   # "1vBOT", "1v1", "GHOST"
SAVE_FILE = "cyber_pong_save.json"

# Profile variables
all_users_data = {}

# Player 1 Data
current_username = ""
username_input = ""
total_coins = 0
shop_data = {}

# Player 2 / Ghost Data
p2_username = ""
p2_username_input = ""
p2_total_coins = 0
ghost_search_msg = "Enter opponent's username:"

# Visual feedback timer for saving
save_message_timer = 0

# Default Shop Blueprint
DEFAULT_CHARACTERS = {
    "1": {"name": "CLASSIC (Standard)", "desc": "No special abilities. Pure skill.", "color": (0, 255, 200), "cost": 0, "unlocked": True, "ability": "NONE"},
    "2": {"name": "AUTO-BOT (The Machine)", "desc": "Automates movement for 2s every 5s.", "color": (255, 255, 0), "cost": 30, "unlocked": False, "ability": "AUTO_PILOT"},
    "3": {"name": "PHANTOM (The Ghost)", "desc": "Moves incredibly fast.", "color": (150, 0, 255), "cost": 80, "unlocked": False, "ability": "SPEED"}
}

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
    global total_coins, shop_data, all_users_data, player_score, opponent_score
    shop_data = {k: v.copy() for k, v in DEFAULT_CHARACTERS.items()}
    
    player_score = 0
    opponent_score = 0
    
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
        all_users_data[current_username] = {
            "coins": total_coins,
            "unlocked_chars": {key: char["unlocked"] for key, char in shop_data.items()}
        }
        
    if game_mode == "1v1" and p2_username != "":
        if p2_username not in all_users_data:
            all_users_data[p2_username] = {
                "coins": p2_total_coins,
                "unlocked_chars": {k: v["unlocked"] for k, v in DEFAULT_CHARACTERS.items()}
            }
        else:
            all_users_data[p2_username]["coins"] = p2_total_coins

    try:
        with open(SAVE_FILE, "w") as file:
            json.dump(all_users_data, file)
    except Exception as e:
        print(f"Error saving game: {e}")

def reset_profile():
    global total_coins, shop_data, player_score, opponent_score
    total_coins = 0
    player_score = 0
    opponent_score = 0
    shop_data = {k: v.copy() for k, v in DEFAULT_CHARACTERS.items()}
    save_game()

load_all_data()

selected_char = None
color_player = (0, 255, 200)
active_ability = "NONE"

# Automation Timers
auto_ability_timer = 0
is_auto_active = False
auto_end_time = 0

# Game Objects Layout
PADDLE_WIDTH = 15
PADDLE_BASE_HEIGHT = 100
BALL_SIZE = 15

player = pygame.Rect(30, (SCREEN_HEIGHT // 2) - (PADDLE_BASE_HEIGHT // 2), PADDLE_WIDTH, PADDLE_BASE_HEIGHT)
opponent = pygame.Rect(SCREEN_WIDTH - 30 - PADDLE_WIDTH, (SCREEN_HEIGHT // 2) - (PADDLE_BASE_HEIGHT // 2), PADDLE_WIDTH, PADDLE_BASE_HEIGHT)
ball = pygame.Rect((SCREEN_WIDTH // 2) - (BALL_SIZE // 2), (SCREEN_HEIGHT // 2) - (BALL_SIZE // 2), BALL_SIZE, BALL_SIZE)

# Speeds
p1_direction = 0
p2_direction = 0
BASE_SPEED = 7
SPRINT_SPEED = 13
AI_BASE_SPEED = 4.8

ball_speed_x = 6
ball_speed_y = 6

player_score = 0
opponent_score = 0

# Fonts
game_font = pygame.font.Font(None, 65)
menu_font = pygame.font.Font(None, 35)
title_font = pygame.font.Font(None, 70)
coin_font = pygame.font.Font(None, 45)
small_font = pygame.font.Font(None, 28)

def reset_ball():
    global ball_speed_x, ball_speed_y, current_ball_color
    ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    ball_speed_x = 6 if ball_speed_x > 0 else -6
    ball_speed_y = random.choice([6, -6]) 
    ball_speed_x *= -1
    current_ball_color = random.choice(BALL_COLORS)

def attempt_select_or_buy(char_key):
    global total_coins, GAME_STATE, selected_char, color_player, active_ability, auto_ability_timer
    char = shop_data[char_key]
    
    if char["unlocked"]:
        selected_char = char["name"]
        color_player = char["color"]
        active_ability = char["ability"]
        auto_ability_timer = pygame.time.get_ticks() 
        GAME_STATE = "PLAYING"
        
        player.y = (SCREEN_HEIGHT // 2) - (PADDLE_BASE_HEIGHT // 2)
        opponent.y = (SCREEN_HEIGHT // 2) - (PADDLE_BASE_HEIGHT // 2)
    else:
        if total_coins >= char["cost"]:
            total_coins -= char["cost"]
            char["unlocked"] = True
            save_game() 

# Game Clock
clock = pygame.time.Clock()
FPS = 60
running = True

while running:
    current_time = pygame.time.get_ticks()
    
    # --- 1. Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            running = False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if GAME_STATE == "PLAYING":
                    GAME_STATE = "MENU"
                elif GAME_STATE in ["LOGIN_P2", "LOGIN_GHOST", "LEADERBOARD"]:
                    game_mode = "1vBOT"
                    GAME_STATE = "MENU"
                else:
                    save_game()
                    running = False
                
            elif event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                else:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED)
            
            # P1 LOGIN
            if GAME_STATE == "LOGIN":
                if event.key == pygame.K_RETURN and len(username_input) > 0:
                    current_username = username_input
                    load_user_profile(current_username)
                    GAME_STATE = "MENU"
                elif event.key == pygame.K_BACKSPACE:
                    username_input = username_input[:-1]
                elif event.key != pygame.K_ESCAPE and event.key != pygame.K_F11:
                    if event.unicode.isalnum() and len(username_input) < 15:
                        username_input += event.unicode
                        
            # P2 1v1 LOGIN
            elif GAME_STATE == "LOGIN_P2":
                if event.key == pygame.K_RETURN and len(p2_username_input) > 0:
                    if p2_username_input == current_username:
                        p2_username_input += "_2" 
                    p2_username = p2_username_input
                    if p2_username not in all_users_data:
                        all_users_data[p2_username] = {"coins": 0, "unlocked_chars": {k: v["unlocked"] for k, v in DEFAULT_CHARACTERS.items()}}
                    p2_total_coins = all_users_data[p2_username].get("coins", 0)
                    GAME_STATE = "MENU"
                elif event.key == pygame.K_BACKSPACE:
                    p2_username_input = p2_username_input[:-1]
                elif event.key != pygame.K_ESCAPE and event.key != pygame.K_F11:
                    if event.unicode.isalnum() and len(p2_username_input) < 15:
                        p2_username_input += event.unicode

            # GHOST / ONLINE SEARCH
            elif GAME_STATE == "LOGIN_GHOST":
                if event.key == pygame.K_RETURN and len(p2_username_input) > 0:
                    if p2_username_input in all_users_data and p2_username_input != current_username:
                        p2_username = p2_username_input
                        game_mode = "GHOST"
                        ghost_search_msg = "Enter opponent's username:"
                        GAME_STATE = "MENU"
                    else:
                        ghost_search_msg = "User not found! Try again:"
                        p2_username_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    p2_username_input = p2_username_input[:-1]
                elif event.key != pygame.K_ESCAPE and event.key != pygame.K_F11:
                    if event.unicode.isalnum() and len(p2_username_input) < 15:
                        p2_username_input += event.unicode

            # MENU
            elif GAME_STATE == "MENU":
                if event.key == pygame.K_1: attempt_select_or_buy("1")
                elif event.key == pygame.K_2: attempt_select_or_buy("2")
                elif event.key == pygame.K_3: attempt_select_or_buy("3")
                elif event.key == pygame.K_m: 
                    if game_mode in ["1vBOT", "GHOST"]:
                        game_mode = "1v1"
                        p2_username_input = ""
                        GAME_STATE = "LOGIN_P2"
                    else:
                        game_mode = "1vBOT"
                        p2_username = ""
                elif event.key == pygame.K_o:
                    game_mode = "GHOST"
                    p2_username_input = ""
                    ghost_search_msg = "Enter opponent's username:"
                    GAME_STATE = "LOGIN_GHOST"
                elif event.key == pygame.K_l:
                    load_all_data() # Refresh data before showing leaderboard
                    GAME_STATE = "LEADERBOARD"
                elif event.key == pygame.K_r:
                    reset_profile()
                elif event.key == pygame.K_s:
                    save_game()
                    save_message_timer = current_time

            # PLAYING
            elif GAME_STATE == "PLAYING":
                if event.key == pygame.K_w: p1_direction = -1
                if event.key == pygame.K_s: p1_direction = 1
                
                if game_mode in ["1vBOT", "GHOST"]:
                    if event.key == pygame.K_UP: p1_direction = -1
                    if event.key == pygame.K_DOWN: p1_direction = 1
                elif game_mode == "1v1":
                    if event.key == pygame.K_UP: p2_direction = -1
                    if event.key == pygame.K_DOWN: p2_direction = 1

        if event.type == pygame.KEYUP:
            if GAME_STATE == "PLAYING":
                if event.key in (pygame.K_w, pygame.K_s): p1_direction = 0
                if game_mode in ["1vBOT", "GHOST"] and event.key in (pygame.K_UP, pygame.K_DOWN): p1_direction = 0
                if game_mode == "1v1" and event.key in (pygame.K_UP, pygame.K_DOWN): p2_direction = 0

    if not running:
        break

    # --- 2. LOGIN & MENU SCREENS ---
    if GAME_STATE == "LOGIN":
        screen.fill(COLOR_BG)
        title_text = title_font.render("CYBER-PONG LOGIN", True, COLOR_WHITE)
        prompt_text = menu_font.render("Enter Username and press ENTER:", True, (200, 200, 200))
        user_text = game_font.render(username_input + "_", True, (0, 255, 200))
        
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
        screen.blit(prompt_text, (SCREEN_WIDTH//2 - prompt_text.get_width()//2, 250))
        screen.blit(user_text, (SCREEN_WIDTH//2 - user_text.get_width()//2, 320))
        pygame.display.flip()
        clock.tick(FPS)
        continue
        
    if GAME_STATE == "LOGIN_P2":
        screen.fill(COLOR_BG)
        title_text = title_font.render("PLAYER 2 LOGIN", True, COLOR_P2)
        prompt_text = menu_font.render("Enter Username and press ENTER:", True, (200, 200, 200))
        user_text = game_font.render(p2_username_input + "_", True, COLOR_P2)
        esc_text = small_font.render("[ESC] Cancel", True, (150, 150, 150))
        
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
        screen.blit(prompt_text, (SCREEN_WIDTH//2 - prompt_text.get_width()//2, 250))
        screen.blit(user_text, (SCREEN_WIDTH//2 - user_text.get_width()//2, 320))
        screen.blit(esc_text, (SCREEN_WIDTH//2 - esc_text.get_width()//2, 400))
        pygame.display.flip()
        clock.tick(FPS)
        continue

    if GAME_STATE == "LOGIN_GHOST":
        screen.fill(COLOR_BG)
        title_text = title_font.render("FIND GHOST MATCH", True, COLOR_AI)
        prompt_text = menu_font.render(ghost_search_msg, True, (200, 200, 200))
        user_text = game_font.render(p2_username_input + "_", True, COLOR_AI)
        esc_text = small_font.render("[ESC] Cancel", True, (150, 150, 150))
        
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 100))
        screen.blit(prompt_text, (SCREEN_WIDTH//2 - prompt_text.get_width()//2, 250))
        screen.blit(user_text, (SCREEN_WIDTH//2 - user_text.get_width()//2, 320))
        screen.blit(esc_text, (SCREEN_WIDTH//2 - esc_text.get_width()//2, 400))
        pygame.display.flip()
        clock.tick(FPS)
        continue

    if GAME_STATE == "LEADERBOARD":
        screen.fill(COLOR_BG)
        title_text = title_font.render("GLOBAL LEADERBOARD", True, COLOR_GOLD)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 50))
        
        # Sort users by coins descending
        sorted_users = sorted(all_users_data.items(), key=lambda x: x[1].get('coins', 0), reverse=True)
        
        y_pos = 150
        for i, (usr, data) in enumerate(sorted_users[:5]):
            if i == 0: color = COLOR_GOLD
            elif i == 1: color = COLOR_SILVER
            elif i == 2: color = COLOR_BRONZE
            else: color = COLOR_WHITE
            
            rank_text = menu_font.render(f"#{i+1}  {usr}", True, color)
            score_text = menu_font.render(f"{data.get('coins', 0)} Coins", True, color)
            
            screen.blit(rank_text, (150, y_pos))
            screen.blit(score_text, (SCREEN_WIDTH - 150 - score_text.get_width(), y_pos))
            y_pos += 60
            
        esc_text = small_font.render("[ESC] Return to Menu", True, (150, 150, 150))
        screen.blit(esc_text, (SCREEN_WIDTH//2 - esc_text.get_width()//2, 500))
        
        pygame.display.flip()
        clock.tick(FPS)
        continue

    # MENU SCREEN
    if GAME_STATE == "MENU":
        screen.fill(COLOR_BG)
        
        if game_mode == "1v1":
            info_str = f"P1: {current_username}  |  P2: {p2_username}  |  Mode: 1v1"
        elif game_mode == "GHOST":
            info_str = f"Player: {current_username}  |  Ghost: {p2_username}  |  Mode: Ghost Match"
        else:
            info_str = f"Player: {current_username}  |  Mode: 1vBOT  |  Coins: {total_coins}"
            
        info_text = menu_font.render(info_str, True, COLOR_GOLD)
        screen.blit(info_text, (SCREEN_WIDTH//2 - info_text.get_width()//2, 30))
        
        controls_text = small_font.render("[M] 1v1 Mode | [O] Ghost Mode | [L] Leaderboard | [S] Save | [ESC] Quit", True, (150, 150, 150))
        screen.blit(controls_text, (SCREEN_WIDTH//2 - controls_text.get_width()//2, 80))

        title_text = title_font.render("SELECT CHARACTER", True, COLOR_WHITE)
        screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, 140))
        
        y_offset = 230
        for key, char in shop_data.items():
            status = "UNLOCKED (Press to Play)" if char["unlocked"] else f"COST: {char['cost']} Coins (Press to Buy)"
            color = char["color"] if char["unlocked"] else (100, 100, 100)
            
            char_title = menu_font.render(f"[{key}] {char['name']} - {status}", True, color)
            char_desc = menu_font.render(char['desc'], True, (180, 180, 180))
            
            screen.blit(char_title, (100, y_offset))
            screen.blit(char_desc, (120, y_offset + 30))
            y_offset += 90

        if save_message_timer > 0 and (current_time - save_message_timer) < 2000:
            saved_text = menu_font.render("PROFILE SAVED!", True, (0, 255, 0))
            screen.blit(saved_text, (SCREEN_WIDTH//2 - saved_text.get_width()//2, SCREEN_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)
        continue

    # --- 4. PLAYING LOGIC ---
    if active_ability == "AUTO_PILOT":
        if not is_auto_active and current_time - auto_ability_timer > 5000:
            is_auto_active = True
            auto_end_time = current_time + 2000
            auto_ability_timer = current_time
            
        if is_auto_active and current_time > auto_end_time:
            is_auto_active = False
            auto_ability_timer = current_time

    current_player_speed = SPRINT_SPEED if active_ability == "SPEED" else BASE_SPEED
    
    if is_auto_active:
        if player.centery < ball.centery: player.y += current_player_speed
        if player.centery > ball.centery: player.y -= current_player_speed
    else:
        player.y += p1_direction * current_player_speed
    player.clamp_ip(screen.get_rect())

    if game_mode in ["1vBOT", "GHOST"]:
        if ball_speed_x > 0:
            if opponent.centery < ball.centery - 15: 
                opponent.y += AI_BASE_SPEED
            elif opponent.centery > ball.centery + 15: 
                opponent.y -= AI_BASE_SPEED
        else:
            target_y = SCREEN_HEIGHT // 2
            if opponent.centery < target_y - 10: opponent.y += AI_BASE_SPEED - 2 
            elif opponent.centery > target_y + 10: opponent.y -= AI_BASE_SPEED - 2
    else:
        opponent.y += p2_direction * BASE_SPEED
    opponent.clamp_ip(screen.get_rect())

    ball.x += ball_speed_x
    ball.y += ball_speed_y

    if ball.top <= 0 or ball.bottom >= SCREEN_HEIGHT:
        ball_speed_y *= -1
        current_ball_color = random.choice(BALL_COLORS)

    # Scoring Rules
    if ball.left <= 0:
        opponent_score += 1
        if game_mode == "1v1":
            p2_total_coins += 10
            save_game()
        reset_ball()
        
    if ball.right >= SCREEN_WIDTH:
        player_score += 1
        total_coins += 10 
        save_game() 
        reset_ball()

    if ball.colliderect(player):
        ball_speed_x *= -1.05
        ball_speed_y += random.uniform(-1, 1) 
        ball.left = player.right
        
    if ball.colliderect(opponent):
        ball_speed_x *= -1.05
        ball_speed_y += random.uniform(-1, 1)
        ball.right = opponent.left

    # --- 5. Rendering Assets ---
    screen.fill(COLOR_BG)
    pygame.draw.line(screen, (32, 28, 54), (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 4)

    pygame.draw.rect(screen, color_player, player, border_radius=4)
    p2_draw_color = COLOR_P2 if game_mode == "1v1" else COLOR_AI
    pygame.draw.rect(screen, p2_draw_color, opponent, border_radius=4)
    pygame.draw.ellipse(screen, current_ball_color, ball)

    if is_auto_active:
        aura_rect = player.inflate(10, 10)
        pygame.draw.rect(screen, (255, 255, 0), aura_rect, 2, border_radius=4)

    # In-game HUD
    player_text = game_font.render(f"{player_score}", True, color_player)
    opponent_text = game_font.render(f"{opponent_score}", True, p2_draw_color)
    ingame_coin_text = menu_font.render(f"P1 Coins: {total_coins}", True, (255, 215, 0))
    
    # Determine who you are playing against for HUD
    if game_mode == "1v1": vs_string = f"P2 (Arrows): {p2_username}"
    elif game_mode == "GHOST": vs_string = f"GHOST: {p2_username}"
    else: vs_string = "BOT"
    
    mode_text = small_font.render(f"{current_username} vs {vs_string}", True, (150, 150, 150))
    esc_hint_text = small_font.render("[ESC] Return to Menu", True, (150, 150, 150))
    
    screen.blit(player_text, (SCREEN_WIDTH // 4, 25))
    screen.blit(opponent_text, (3 * SCREEN_WIDTH // 4, 25))
    screen.blit(ingame_coin_text, (20, 20))
    
    if game_mode == "1v1":
        p2_coin_text = menu_font.render(f"P2 Coins: {p2_total_coins}", True, (255, 215, 0))
        screen.blit(p2_coin_text, (SCREEN_WIDTH - p2_coin_text.get_width() - 20, 20))
        screen.blit(esc_hint_text, (SCREEN_WIDTH - esc_hint_text.get_width() - 20, 50))
    else:
        screen.blit(esc_hint_text, (SCREEN_WIDTH - esc_hint_text.get_width() - 20, 20))

    screen.blit(mode_text, (SCREEN_WIDTH//2 - mode_text.get_width()//2, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
