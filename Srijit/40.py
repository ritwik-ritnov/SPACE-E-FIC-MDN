import pygame
import math
import random
import sys
import os
import json

# --- Engine Setup ---
pygame.init()
WIDTH, HEIGHT = 1280, 720
is_fullscreen = False
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
pygame.display.set_caption("Shoot The Box: Gun Game Replica")
clock = pygame.time.Clock()

SAVE_FILE = "shoot_the_box_pc_save.json"

# --- Fonts & Colors ---
font_combo_huge = pygame.font.Font(None, 80)
font_combo_small = pygame.font.Font(None, 40)
font_large = pygame.font.Font(None, 60)
font_medium = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 30)

BG_COLOR = (23, 130, 140)     # Teal background
GRID_COLOR = (35, 150, 160)   # Lighter teal for grid lines
BULLET_COLOR = (255, 255, 255)
HEART_COLOR = (255, 50, 80)

# --- Economy & User Data ---
GAME_STATE = "LOGIN"
all_users_data = {}
current_username = ""
username_input = ""
total_coins = 0
high_score = 0

DEFAULT_SHOP = {
    "1": {"name": "PISTOL", "desc": "Semi-Auto", "auto": False, "cd": 0, "spread": 1, "speed": 35, "color": (210, 180, 140), "cost": 0, "unlocked": True},
    "2": {"name": "SHOTGUN", "desc": "Spread Shot", "auto": False, "cd": 0, "spread": 5, "speed": 30, "color": (255, 100, 0), "cost": 500, "unlocked": False},
    "3": {"name": "ASSAULT RIFLE", "desc": "Full-Auto", "auto": True, "cd": 120, "spread": 1, "speed": 40, "color": (0, 200, 100), "cost": 1500, "unlocked": False},
    "4": {"name": "MINIGUN", "desc": "Extreme Fire Rate", "auto": True, "cd": 40, "spread": 1, "speed": 45, "color": (255, 255, 0), "cost": 3000, "unlocked": False},
    "5": {"name": "LASER", "desc": "Perfect Accuracy", "auto": True, "cd": 80, "spread": 1, "speed": 60, "color": (0, 255, 255), "cost": 5000, "unlocked": False}
}

shop_data = {}
current_weapon = None

def load_data():
    global all_users_data
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f: all_users_data = json.load(f)
        except: all_users_data = {}
    else: all_users_data = {}

def load_profile(username):
    global total_coins, shop_data, all_users_data, high_score
    shop_data = {k: v.copy() for k, v in DEFAULT_SHOP.items()}
    if username in all_users_data:
        user_info = all_users_data[username]
        total_coins = user_info.get("coins", 0)
        high_score = user_info.get("high_score", 0)
        saved_unlocks = user_info.get("unlocked", {})
        for key in shop_data:
            if key in saved_unlocks: shop_data[key]["unlocked"] = saved_unlocks[key]
    else:
        total_coins = 0
        high_score = 0

def save_game(current_score=0):
    global high_score
    if current_username != "":
        current_high = all_users_data.get(current_username, {}).get("high_score", 0)
        high_score = max(current_high, current_score, high_score)
        
        all_users_data[current_username] = {
            "coins": total_coins,
            "high_score": high_score,
            "unlocked": {key: val["unlocked"] for key, val in shop_data.items()}
        }
        try:
            with open(SAVE_FILE, "w") as f: json.dump(all_users_data, f)
        except: pass

# --- Box Definitions ---
BOX_TYPES = [
    {"type": "WOOD", "color": (160, 82, 45), "weight": 50, "symbol": ""},
    {"type": "SCORE", "color": (50, 255, 50), "weight": 15, "symbol": "+10"},
    {"type": "GOLD", "color": (255, 215, 0), "weight": 10, "symbol": "$$$"},
    {"type": "AMMO", "color": (100, 150, 255), "weight": 10, "symbol": "AMMO"},
    {"type": "EXPLOSION", "color": (255, 100, 0), "weight": 5, "symbol": "BOOM"},
    {"type": "POWERUP", "color": (200, 0, 255), "weight": 5, "symbol": "BUFF"},
    {"type": "BLACK", "color": (30, 30, 30), "weight": 5, "symbol": "☠"}
]

# --- Game Entities ---
class Bullet:
    def __init__(self, x, y, angle, speed, color):
        self.x = x
        self.y = y
        self.radius = 5
        self.color = color
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)

class Box:
    def __init__(self):
        self.size = random.randint(50, 70)
        total_weight = sum(b["weight"] for b in BOX_TYPES)
        rand_val = random.uniform(0, total_weight)
        current = 0
        for b in BOX_TYPES:
            current += b["weight"]
            if rand_val <= current:
                self.b_type = b["type"]
                self.color = b["color"]
                self.symbol = b["symbol"]
                break

        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-4, 4)
        
        self.x = WIDTH + self.size
        self.vx = random.uniform(-10, -5)
        self.y = random.randint(HEIGHT // 2, HEIGHT - 100)
        self.vy = random.uniform(-18, -12)

    def update(self):
        self.vy += 0.35  # Gravity
        self.x += self.vx
        self.y += self.vy
        self.angle += self.rot_speed

    def draw(self, surf, offset_x, offset_y):
        box_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, self.color, (0, 0, self.size, self.size), border_radius=6)
        
        border_col = (255, 0, 0) if self.b_type == "BLACK" else (255, 255, 255)
        pygame.draw.rect(box_surf, border_col, (0, 0, self.size, self.size), width=3, border_radius=6)
        
        if self.symbol:
            txt = font_small.render(self.symbol, True, (255, 255, 255))
            box_surf.blit(txt, (self.size//2 - txt.get_width()//2, self.size//2 - txt.get_height()//2))

        rotated_surf = pygame.transform.rotate(box_surf, self.angle)
        rect = rotated_surf.get_rect(center=(int(self.x) + offset_x, int(self.y) + offset_y))
        surf.blit(rotated_surf, rect)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(4, 12)
        self.vx = random.uniform(-8, 8)
        self.vy = random.uniform(-8, 8)
        self.life = 255
        self.decay = random.randint(8, 15)

    def update(self):
        self.vy += 0.2
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay

    def draw(self, surf, offset_x, offset_y):
        if self.life > 0:
            temp_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.rect(temp_surf, (*self.color, max(0, self.life)), (0, 0, self.size, self.size))
            surf.blit(temp_surf, (int(self.x) + offset_x, int(self.y) + offset_y))

def main():
    global is_fullscreen, screen, current_weapon, GAME_STATE, current_username, username_input, total_coins
    
    score = 0
    combo = 0
    lives = 3
    bullets = []
    boxes = []
    particles = []
    
    gun_x, gun_y = 120, HEIGHT // 2
    last_shot = 0
    spawn_timer = 0
    shake_timer = 0

    def create_explosion(x, y, color, scale=1.0):
        for _ in range(int(15 * scale)):
            particles.append(Particle(x, y, color))

    load_data()

    while True:
        dt = clock.tick(60)
        current_time = pygame.time.get_ticks()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(score)
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)

                if event.key == pygame.K_ESCAPE:
                    if GAME_STATE == "PLAYING":
                        save_game(score)
                        GAME_STATE = "MENU"
                    elif GAME_STATE == "LEADERBOARD":
                        GAME_STATE = "MENU"
                    else:
                        save_game(score)
                        pygame.quit()
                        sys.exit()

                # Login Input
                if GAME_STATE == "LOGIN":
                    if event.key == pygame.K_RETURN and len(username_input) > 0:
                        current_username = username_input
                        load_profile(current_username)
                        GAME_STATE = "MENU"
                    elif event.key == pygame.K_BACKSPACE: 
                        username_input = username_input[:-1]
                    elif event.unicode.isalnum() and len(username_input) < 15: 
                        username_input += event.unicode

                # Menu Input
                elif GAME_STATE == "MENU":
                    for k in ["1", "2", "3", "4", "5"]:
                        if event.unicode == k:
                            item = shop_data[k]
                            if item["unlocked"]:
                                current_weapon = item
                                score = 0
                                combo = 0
                                lives = 3
                                bullets.clear()
                                boxes.clear()
                                particles.clear()
                                GAME_STATE = "PLAYING"
                            else:
                                if total_coins >= item["cost"]:
                                    total_coins -= item["cost"]
                                    item["unlocked"] = True
                                    save_game()
                                    
                    if event.key == pygame.K_l:
                        load_data()
                        GAME_STATE = "LEADERBOARD"

            # Single Shot Logic
            if GAME_STATE == "PLAYING":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not current_weapon["auto"]:
                    dx, dy = mouse_x - gun_x, mouse_y - gun_y
                    angle = math.atan2(dy, dx)
                    spread = current_weapon["spread"]
                    speed = current_weapon["speed"]
                    
                    if spread == 1:
                        bullets.append(Bullet(gun_x, gun_y, angle, speed, current_weapon["color"]))
                    elif spread == 5:
                        for offset in [-0.15, -0.075, 0, 0.075, 0.15]:
                            bullets.append(Bullet(gun_x, gun_y, angle+offset, speed, current_weapon["color"]))

        # --- RENDERING STATES ---
        screen.fill(BG_COLOR)

        if GAME_STATE == "LOGIN":
            title = font_large.render("SYSTEM LOGIN", True, (255, 255, 255))
            prompt = font_medium.render("Enter Username:", True, (200, 200, 200))
            user_txt = font_combo_huge.render(username_input + "_", True, (255, 215, 0))
            
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 150))
            screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 20))
            screen.blit(user_txt, (WIDTH//2 - user_txt.get_width()//2, HEIGHT//2 + 40))

        elif GAME_STATE == "LEADERBOARD":
            title = font_large.render("GLOBAL HIGHSCORES", True, (255, 215, 0))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
            
            sorted_users = sorted(all_users_data.items(), key=lambda x: x[1].get('high_score', 0), reverse=True)
            
            y_pos = 200
            for i, (usr, data) in enumerate(sorted_users[:5]):
                if i == 0: color = (255, 215, 0)
                elif i == 1: color = (192, 192, 192)
                elif i == 2: color = (205, 127, 50)
                else: color = (255, 255, 255)
                
                rank_txt = font_medium.render(f"#{i+1}  {usr}", True, color)
                score_txt = font_medium.render(f"{data.get('high_score', 0)} Pts", True, color)
                
                screen.blit(rank_txt, (WIDTH//2 - 300, y_pos))
                screen.blit(score_txt, (WIDTH//2 + 150, y_pos))
                y_pos += 60
                
            esc = font_small.render("[ESC] Return to Menu", True, (150, 150, 150))
            screen.blit(esc, (WIDTH//2 - esc.get_width()//2, HEIGHT - 100))

        elif GAME_STATE == "MENU":
            info = font_medium.render(f"User: {current_username}  |  HI: {high_score}", True, (255, 255, 255))
            coins_txt = font_large.render(f"COINS: {total_coins}", True, (255, 215, 0))
            screen.blit(info, (WIDTH//2 - info.get_width()//2, 40))
            screen.blit(coins_txt, (WIDTH//2 - coins_txt.get_width()//2, 90))
            
            fs_hint = font_small.render("[F11] Fullscreen | [L] Leaderboard | [1-5] Equip/Buy", True, (200, 200, 200))
            screen.blit(fs_hint, (WIDTH//2 - fs_hint.get_width()//2, 160))

            y = 250
            for k, v in shop_data.items():
                status = "UNLOCKED (Press to Equip)" if v["unlocked"] else f"COST {v['cost']} (Press to Buy)"
                c = v["color"] if v["unlocked"] else (100, 100, 100)
                txt = font_medium.render(f"[{k}] {v['name']} - {status}", True, c)
                desc = font_small.render(v["desc"], True, (220, 220, 220))
                
                pygame.draw.rect(screen, c, (WIDTH//2 - 250, y, 30, 30), border_radius=5)
                screen.blit(txt, (WIDTH//2 - 190, y))
                screen.blit(desc, (WIDTH//2 - 190, y + 30))
                y += 80 

        elif GAME_STATE == "PLAYING":
            # Auto Fire Logic
            if mouse_pressed and current_weapon["auto"] and current_time - last_shot > current_weapon["cd"]:
                last_shot = current_time
                dx, dy = mouse_x - gun_x, mouse_y - gun_y
                angle = math.atan2(dy, dx)
                bullets.append(Bullet(gun_x, gun_y, angle, current_weapon["speed"], current_weapon["color"]))

            # --- Gameplay Logic ---
            spawn_timer += dt
            current_delay = max(400, 1200 - (score * 5))
            if spawn_timer >= current_delay:
                spawn_timer = 0
                boxes.append(Box())

            for b in bullets[:]:
                b.update()
                if b.y < 0 or b.y > HEIGHT or b.x < 0 or b.x > WIDTH:
                    bullets.remove(b)

            for p in particles[:]:
                p.update()
                if p.life <= 0:
                    particles.remove(p)

            for box in boxes[:]:
                box.update()
                
                if box.y > HEIGHT + box.size or box.x < -box.size:
                    if box.b_type != "BLACK":
                        lives -= 1
                        combo = 0 
                        shake_timer = 15
                    boxes.remove(box)
                    if lives <= 0:
                        save_game(score)
                        GAME_STATE = "MENU"
                    continue
                
                hit = False
                for b in bullets[:]:
                    if math.hypot(b.x - box.x, b.y - box.y) < (box.size / 2) + b.radius + 5:
                        try: bullets.remove(b)
                        except: pass
                        hit = True
                        break
                
                if hit:
                    # EARN 10 COINS PER BOX SHOT
                    total_coins += 10
                    create_explosion(box.x, box.y, box.color)
                    
                    if box.b_type == "BLACK":
                        lives -= 1
                        combo = 0
                        shake_timer = 20
                        create_explosion(box.x, box.y, (255, 0, 0), 2.0)
                        if lives <= 0:
                            save_game(score)
                            GAME_STATE = "MENU"
                    else:
                        combo += 1
                        multiplier = 1 + (combo // 10)
                        score += (10 if box.b_type == "SCORE" else 1) * multiplier
                        
                        if box.b_type == "EXPLOSION":
                            create_explosion(box.x, box.y, (255, 100, 0), 3.0)
                            for ob in boxes[:]:
                                if ob != box and ob.b_type != "BLACK":
                                    total_coins += 10 # Chain reaction coins
                                    create_explosion(ob.x, ob.y, ob.color)
                                    score += 1 * multiplier
                                    try: boxes.remove(ob)
                                    except: pass

                    try: boxes.remove(box)
                    except: pass

            # --- Screen Shake Math ---
            sx, sy = 0, 0
            if shake_timer > 0:
                sx = random.randint(-shake_timer, shake_timer)
                sy = random.randint(-shake_timer, shake_timer)
                shake_timer -= 1

            # --- Blueprint Grid Pattern ---
            for x in range(0, WIDTH, 60):
                pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
            for y in range(0, HEIGHT, 60):
                pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))

            # --- Trajectory Dotted Line ---
            dx, dy = mouse_x - gun_x, mouse_y - gun_y
            angle = math.atan2(dy, dx)
            for i in range(50, 1200, 40):
                px = gun_x + math.cos(angle) * i
                py = gun_y + math.sin(angle) * i
                pygame.draw.circle(screen, (255, 255, 255), (int(px) + sx, int(py) + sy), 3)

            # --- Draw Entities ---
            for p in particles: p.draw(screen, sx, sy)
            for box in boxes: box.draw(screen, sx, sy)
            for b in bullets: b.draw(screen)

            # --- Draw Gun Base ---
            barrel_length = 60
            end_x = gun_x + math.cos(angle) * barrel_length + sx
            end_y = gun_y + math.sin(angle) * barrel_length + sy
            pygame.draw.line(screen, (100, 100, 100), (gun_x + sx, gun_y + sy), (end_x, end_y), 20)
            pygame.draw.line(screen, current_weapon["color"], (gun_x + sx, gun_y + sy), (end_x, end_y), 12)
            pygame.draw.circle(screen, (40, 50, 60), (gun_x + sx, gun_y + sy), 35)
            pygame.draw.circle(screen, current_weapon["color"], (gun_x + sx, gun_y + sy), 25, 4)

            # --- Draw UI Overlays ---
            if combo > 0:
                combo_lbl = font_combo_small.render("COMBO", True, (150, 220, 220))
                combo_val = font_combo_huge.render(f"x{combo}", True, (255, 255, 255))
                screen.blit(combo_lbl, (WIDTH - 180, 30))
                screen.blit(combo_val, (WIDTH - 120, 20))

            score_txt = font_large.render(f"SCORE: {score}", True, (255, 255, 255))
            coin_txt = font_medium.render(f"COINS: {total_coins}", True, (255, 215, 0))
            screen.blit(score_txt, (20, 20))
            screen.blit(coin_txt, (20, 80))
            
            for i in range(3):
                color = HEART_COLOR if i < lives else (50, 50, 60)
                pygame.draw.rect(screen, color, (20 + (i * 35), HEIGHT - 50, 25, 25), border_radius=5)

        pygame.display.flip()

if __name__ == "__main__":
    main()
