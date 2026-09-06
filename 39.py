
# target shooting game with procedural textures, enemies, and a particle system using NumPy and Pygame.


import pygame
import numpy as np
import math
import json
import os
import random

# ==========================================
# 1. ENGINE CONFIGURATION
# ==========================================
W, H = 640, 480
TEX_WIDTH, TEX_HEIGHT = 64, 64
MAX_PARTICLES = 300
SAVE_FILE = "cyber_doom_save.json"

pygame.init()
is_fullscreen = False
screen = pygame.display.set_mode((W, H), pygame.SCALED)
pygame.display.set_caption("NumPy 3D Shooter: Expanded Roster")
clock = pygame.time.Clock()

font_large = pygame.font.Font(None, 60)
font_medium = pygame.font.Font(None, 32) # Reduced slightly to fit more text
font_small = pygame.font.Font(None, 22)

# ==========================================
# 2. ECONOMY, LOGIN & SHOP DATA
# ==========================================
GAME_STATE = "LOGIN"
all_users_data = {}
current_username = ""
username_input = ""
total_coins = 0
shop_data = {}

DEFAULT_CHARACTERS = {
    "1": {"name": "CLASSIC (Grunt)", "desc": "Standard speed. Yellow Sparks.", "color": (200, 200, 0), "cost": 0, "unlocked": True, "speed": 0.05},
    "2": {"name": "PHANTOM (Ghost)", "desc": "High speed. Purple Sparks.", "color": (150, 0, 255), "cost": 50, "unlocked": False, "speed": 0.08},
    "3": {"name": "TITAN (Heavy)", "desc": "Slow speed. Red Sparks.", "color": (255, 50, 50), "cost": 100, "unlocked": False, "speed": 0.03},
    "4": {"name": "NINJA (Stealth)", "desc": "Extreme speed. Cyan Sparks.", "color": (0, 255, 255), "cost": 200, "unlocked": False, "speed": 0.10},
    "5": {"name": "JUGGERNAUT (Mech)", "desc": "Walking tank. Green Sparks.", "color": (0, 255, 50), "cost": 300, "unlocked": False, "speed": 0.02},
    "6": {"name": "VIPER (Sniper)", "desc": "Elite balance. White Sparks.", "color": (255, 255, 255), "cost": 500, "unlocked": False, "speed": 0.06},
}

selected_char = None
player_speed = 0.05
particle_color = (200, 200, 0)
score = 0
high_score = 0
perp_wall_dist = np.full(W, 1000.0)

def load_data():
    global all_users_data
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f: all_users_data = json.load(f)
        except: all_users_data = {}
    else: all_users_data = {}

def load_profile(username):
    global total_coins, shop_data, all_users_data, score, high_score
    shop_data = {k: v.copy() for k, v in DEFAULT_CHARACTERS.items()}
    score = 0
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

def save_game():
    global high_score
    if current_username != "":
        current_high = all_users_data.get(current_username, {}).get("high_score", 0)
        high_score = max(current_high, score, high_score)
        
        all_users_data[current_username] = {
            "coins": total_coins,
            "high_score": high_score,
            "unlocked": {key: char["unlocked"] for key, char in shop_data.items()}
        }
        try:
            with open(SAVE_FILE, "w") as f: json.dump(all_users_data, f)
        except: pass

# ==========================================
# 3. PROCEDURAL TEXTURES & MAP
# ==========================================
textures = np.zeros((4, TEX_WIDTH, TEX_HEIGHT, 3), dtype=np.uint8)

# Tex 1: Cyber-Grid
textures[1, ...] = [10, 15, 30]
textures[1, ::16, :] = [0, 255, 200]
textures[1, :, ::16] = [0, 255, 200]

# Tex 2: Warning Stripes
for y in range(TEX_HEIGHT):
    for x in range(TEX_WIDTH):
        if (x + y) % 32 < 16: textures[2, x, y] = [200, 200, 0]
        else: textures[2, x, y] = [20, 20, 20]

# Tex 3: Rusty Metal Box
noise = np.random.randint(50, 120, (TEX_WIDTH, TEX_HEIGHT, 1), dtype=np.uint8)
textures[3] = np.repeat(noise, 3, axis=2)
textures[3, 0:4, :] = [60, 40, 30]
textures[3, -4:, :] = [60, 40, 30]
textures[3, :, 0:4] = [60, 40, 30]
textures[3, :, -4:] = [60, 40, 30]

map_layout = [
    "11111111111111111111",
    "10000000000000000001",
    "10022220000333000001",
    "10020020000303000001",
    "10020020000333000001",
    "10000000000000000001",
    "10000000000000000001",
    "11111000000111111111",
    "10000000000000000001",
    "11111111111111111111"
]
MAP_W, MAP_H = len(map_layout[0]), len(map_layout)
map_grid = np.zeros((MAP_W, MAP_H), dtype=int)
for y, row in enumerate(map_layout):
    for x, char in enumerate(row):
        map_grid[x, y] = int(char)

# ==========================================
# 4. GAME ENTITIES (ENEMIES & PARTICLES)
# ==========================================
def spawn_enemy():
    while True:
        ex = random.uniform(1.5, MAP_W - 1.5)
        ey = random.uniform(1.5, MAP_H - 1.5)
        if map_grid[int(ex), int(ey)] == 0:
            return [ex, ey, 1, 0]

NUM_ENEMIES = 5
enemies = np.array([spawn_enemy() for _ in range(NUM_ENEMIES)], dtype=np.float32)

# Particles: [X, Y, Z, VelX, VelY, VelZ, Life, R, G, B]
particles = np.zeros((MAX_PARTICLES, 10))

def spawn_particles(x, y, z, r, g, b, count):
    dead_idx = np.where(particles[:, 6] <= 0)[0]
    spawns = min(count, len(dead_idx))
    if spawns == 0: return
    idx = dead_idx[:spawns]
    particles[idx, 0] = x
    particles[idx, 1] = y
    particles[idx, 2] = z
    particles[idx, 3] = np.random.uniform(-0.1, 0.1, spawns)
    particles[idx, 4] = np.random.uniform(-0.1, 0.1, spawns)
    particles[idx, 5] = np.random.uniform(-10, 10, spawns)
    particles[idx, 6] = np.random.uniform(15, 30, spawns)
    particles[idx, 7] = r
    particles[idx, 8] = g
    particles[idx, 9] = b

def move_player(dx, dy):
    global pos_x, pos_y
    new_x = pos_x + dx
    new_y = pos_y + dy
    if 0 <= int(new_x) < MAP_W and map_grid[int(new_x), int(pos_y)] == 0:
        pos_x = new_x
    if 0 <= int(new_y) < MAP_H and map_grid[int(pos_x), int(new_y)] == 0:
        pos_y = new_y

# ==========================================
# 5. MAIN LOOP & RENDERING
# ==========================================
load_data()
pos_x, pos_y = 10.0, 5.0
dir_x, dir_y = -1.0, 0.0
plane_x, plane_y = 0.0, 0.66
camera_x_arr = np.linspace(-1, 1, W)
screen_buffer = np.zeros((W, H, 3), dtype=np.uint8)

running = True
while running:
    current_time = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            running = False
            
        # --- RIGHT CLICK MOUSE-LOOK LOGIC ---
        if event.type == pygame.MOUSEMOTION and GAME_STATE == "PLAYING":
            if event.buttons[2]: 
                rot_amt = -event.rel[0] * 0.003  
                old_dir_x, old_plane_x = dir_x, plane_x
                dir_x = dir_x * math.cos(rot_amt) - dir_y * math.sin(rot_amt)
                dir_y = old_dir_x * math.sin(rot_amt) + dir_y * math.cos(rot_amt)
                plane_x = plane_x * math.cos(rot_amt) - plane_y * math.sin(rot_amt)
                plane_y = old_plane_x * math.sin(rot_amt) + plane_y * math.cos(rot_amt)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if GAME_STATE == "PLAYING": 
                    GAME_STATE = "MENU"
                    save_game()
                elif GAME_STATE == "LEADERBOARD":
                    GAME_STATE = "MENU"
                else:
                    save_game()
                    running = False
            
            elif event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.SCALED)
                else:
                    screen = pygame.display.set_mode((W, H), pygame.SCALED)
            
            # --- LOGIN STATE ---
            if GAME_STATE == "LOGIN":
                if event.key == pygame.K_RETURN and len(username_input) > 0:
                    current_username = username_input
                    load_profile(current_username)
                    GAME_STATE = "MENU"
                elif event.key == pygame.K_BACKSPACE: username_input = username_input[:-1]
                elif event.unicode.isalnum() and len(username_input) < 15: username_input += event.unicode
            
            # --- MENU STATE ---
            elif GAME_STATE == "MENU":
                # Check for keys 1 through 6
                for k in ["1", "2", "3", "4", "5", "6"]:
                    if event.unicode == k:
                        char = shop_data[k]
                        if char["unlocked"]:
                            player_speed = char["speed"]
                            particle_color = char["color"]
                            
                            score = 0
                            pos_x, pos_y = 10.0, 5.0
                            for i in range(NUM_ENEMIES):
                                new_pos = spawn_enemy()
                                enemies[i, 0] = new_pos[0]
                                enemies[i, 1] = new_pos[1]
                                enemies[i, 2] = 1
                            GAME_STATE = "PLAYING"
                        else:
                            if total_coins >= char["cost"]:
                                total_coins -= char["cost"]
                                char["unlocked"] = True
                                save_game()
                
                if event.key == pygame.K_l:
                    load_data()  # Refresh data before showing leaderboard
                    GAME_STATE = "LEADERBOARD"

        # --- PLAYING STATE (SHOOTING) ---
        if event.type == pygame.MOUSEBUTTONDOWN and GAME_STATE == "PLAYING":
            if event.button == 1: # Left click
                spawn_particles(pos_x, pos_y, 0, particle_color[0], particle_color[1], particle_color[2], 30)
                
                for i in range(len(enemies)):
                    if enemies[i, 2] == 1:
                        dx = enemies[i, 0] - pos_x
                        dy = enemies[i, 1] - pos_y
                        inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y)
                        trans_x = inv_det * (dir_y * dx - dir_x * dy)
                        trans_y = inv_det * (-plane_y * dx + plane_x * dy)
                        
                        if trans_y > 0:
                            sx = int((W / 2) * (1 + trans_x / trans_y))
                            size = max(1, abs(int(H / trans_y)))
                            
                            if (sx - size//2 < W//2 < sx + size//2) and (trans_y < perp_wall_dist[W//2]):
                                enemies[i, 2] = 0 # Kill
                                enemies[i, 3] = 120 # Respawn timer frames
                                total_coins += 10
                                score += 100
                                if score > high_score:
                                    high_score = score
                                save_game()
                                spawn_particles(enemies[i, 0], enemies[i, 1], 0, 255, 0, 0, 100)

    if not running: break

    # ==========================================
    # --- UI RENDERING BLOCKS ---
    # ==========================================
    if GAME_STATE == "LOGIN":
        screen.fill((12, 10, 24))
        title = font_large.render("SYSTEM LOGIN", True, (0, 255, 200))
        prompt = font_medium.render("Enter Username:", True, (200, 200, 200))
        user_txt = font_large.render(username_input + "_", True, (255, 215, 0))
        screen.blit(title, (W//2 - title.get_width()//2, 100))
        screen.blit(prompt, (W//2 - prompt.get_width()//2, 220))
        screen.blit(user_txt, (W//2 - user_txt.get_width()//2, 270))
        pygame.display.flip()
        clock.tick(60)
        continue

    elif GAME_STATE == "LEADERBOARD":
        screen.fill((12, 10, 24))
        title = font_large.render("GLOBAL HIGHSCORES", True, (255, 215, 0))
        screen.blit(title, (W//2 - title.get_width()//2, 50))
        
        sorted_users = sorted(all_users_data.items(), key=lambda x: x[1].get('high_score', 0), reverse=True)
        
        y_pos = 150
        for i, (usr, data) in enumerate(sorted_users[:5]):
            if i == 0: color = (255, 215, 0) # Gold
            elif i == 1: color = (192, 192, 192) # Silver
            elif i == 2: color = (205, 127, 50) # Bronze
            else: color = (255, 255, 255)
            
            rank_txt = font_medium.render(f"#{i+1}  {usr}", True, color)
            score_txt = font_medium.render(f"{data.get('high_score', 0)} Pts", True, color)
            
            screen.blit(rank_txt, (150, y_pos))
            screen.blit(score_txt, (W - 150 - score_txt.get_width(), y_pos))
            y_pos += 60
            
        esc = font_small.render("[ESC] Return to Menu", True, (150, 150, 150))
        screen.blit(esc, (W//2 - esc.get_width()//2, 420))
        
        pygame.display.flip()
        clock.tick(60)
        continue

    elif GAME_STATE == "MENU":
        screen.fill((12, 10, 24))
        info = font_medium.render(f"User: {current_username} | High Score: {high_score} | Coins: {total_coins}", True, (255, 215, 0))
        screen.blit(info, (W//2 - info.get_width()//2, 15))
        
        fs_hint = font_small.render("[F11] Fullscreen | [L] Leaderboard | [Right-Click Drag] Look Around", True, (150, 150, 150))
        screen.blit(fs_hint, (W//2 - fs_hint.get_width()//2, 50))

        y = 90
        for k, v in shop_data.items():
            status = "UNLOCKED (Press to Play)" if v["unlocked"] else f"COST {v['cost']} (Press to Buy)"
            c = v["color"] if v["unlocked"] else (100, 100, 100)
            txt = font_medium.render(f"[{k}] {v['name']} - {status}", True, c)
            desc = font_small.render(v["desc"], True, (180, 180, 180))
            screen.blit(txt, (40, y))
            screen.blit(desc, (80, y + 25))
            y += 60 # Reduced spacing to fit 6 characters
            
        pygame.display.flip()
        clock.tick(60)
        continue

    # ==========================================
    # --- RENDER: PLAYING (NumPy Pseudo-3D) ---
    # ==========================================
    keys = pygame.key.get_pressed()
    rot_speed = 0.04

    # Safe Movement Physics
    if keys[pygame.K_w]: move_player(dir_x * player_speed, dir_y * player_speed)
    if keys[pygame.K_s]: move_player(-dir_x * player_speed, -dir_y * player_speed)
    if keys[pygame.K_a]: move_player(dir_y * player_speed, -dir_x * player_speed)
    if keys[pygame.K_d]: move_player(-dir_y * player_speed, dir_x * player_speed)

    # Keyboard Camera rotation
    if keys[pygame.K_LEFT]:
        old_dir_x, old_plane_x = dir_x, plane_x
        dir_x = dir_x * math.cos(rot_speed) - dir_y * math.sin(rot_speed)
        dir_y = old_dir_x * math.sin(rot_speed) + dir_y * math.cos(rot_speed)
        plane_x = plane_x * math.cos(rot_speed) - plane_y * math.sin(rot_speed)
        plane_y = old_plane_x * math.sin(rot_speed) + plane_y * math.cos(rot_speed)
    if keys[pygame.K_RIGHT]:
        old_dir_x, old_plane_x = dir_x, plane_x
        dir_x = dir_x * math.cos(-rot_speed) - dir_y * math.sin(-rot_speed)
        dir_y = old_dir_x * math.sin(-rot_speed) + dir_y * math.cos(-rot_speed)
        plane_x = plane_x * math.cos(-rot_speed) - plane_y * math.sin(-rot_speed)
        plane_y = old_plane_x * math.sin(-rot_speed) + plane_y * math.cos(-rot_speed)

    # --- Vectorized Raycasting ---
    ray_dir_x = dir_x + plane_x * camera_x_arr
    ray_dir_y = dir_y + plane_y * camera_x_arr

    map_x = np.full(W, int(pos_x))
    map_y = np.full(W, int(pos_y))

    delta_dist_x = np.abs(1 / (ray_dir_x + 1e-10))
    delta_dist_y = np.abs(1 / (ray_dir_y + 1e-10))

    step_x = np.where(ray_dir_x < 0, -1, 1)
    step_y = np.where(ray_dir_y < 0, -1, 1)

    side_dist_x = np.where(ray_dir_x < 0, (pos_x - map_x) * delta_dist_x, (map_x + 1.0 - pos_x) * delta_dist_x)
    side_dist_y = np.where(ray_dir_y < 0, (pos_y - map_y) * delta_dist_y, (map_y + 1.0 - pos_y) * delta_dist_y)

    hit = np.zeros(W, dtype=bool)
    side = np.zeros(W, dtype=int)
    active = ~hit

    while np.any(active):
        jump_x = active & (side_dist_x < side_dist_y)
        jump_y = active & ~jump_x

        map_x = np.where(jump_x, map_x + step_x, map_x)
        side_dist_x = np.where(jump_x, side_dist_x + delta_dist_x, side_dist_x)
        side = np.where(jump_x, 0, side)

        map_y = np.where(jump_y, map_y + step_y, map_y)
        side_dist_y = np.where(jump_y, side_dist_y + delta_dist_y, side_dist_y)
        side = np.where(jump_y, 1, side)

        valid = (map_x >= 0) & (map_x < MAP_W) & (map_y >= 0) & (map_y < MAP_H)
        oob = active & ~valid
        hit[oob] = True
        active[oob] = False

        hits_now = np.zeros(W, dtype=bool)
        active_valid = active & valid
        
        safe_x = np.clip(map_x[active_valid], 0, MAP_W - 1)
        safe_y = np.clip(map_y[active_valid], 0, MAP_H - 1)
        hits_now[active_valid] = map_grid[safe_x, safe_y] > 0

        new_hits = active & hits_now
        hit[new_hits] = True
        active[new_hits] = False

    # --- Wall Shading & Texture Map ---
    perp_wall_dist = np.where(side == 0, side_dist_x - delta_dist_x, side_dist_y - delta_dist_y)
    line_height = np.clip((H / (perp_wall_dist + 1e-10)), 1, 10000).astype(int)
    
    draw_start = np.clip(-line_height // 2 + H // 2, 0, H - 1)
    draw_end = np.clip(line_height // 2 + H // 2, 0, H - 1)

    safe_map_x = np.clip(map_x, 0, MAP_W - 1)
    safe_map_y = np.clip(map_y, 0, MAP_H - 1)
    tex_num = np.clip(map_grid[safe_map_x, safe_map_y], 1, 3)

    wall_x = np.where(side == 0, pos_y + perp_wall_dist * ray_dir_y, pos_x + perp_wall_dist * ray_dir_x)
    wall_x -= np.floor(wall_x)
    tex_x = (wall_x * TEX_WIDTH).astype(int)
    
    flip_x = ((side == 0) & (ray_dir_x > 0)) | ((side == 1) & (ray_dir_y < 0))
    tex_x = np.where(flip_x, TEX_WIDTH - tex_x - 1, tex_x)
    tex_x = np.clip(tex_x, 0, TEX_WIDTH - 1)

    y_coords = np.arange(H).reshape(1, H)
    wall_mask = (y_coords >= draw_start.reshape(W, 1)) & (y_coords <= draw_end.reshape(W, 1))
    
    tex_step = TEX_HEIGHT / line_height
    tex_pos = (y_coords - (-line_height.reshape(W, 1) / 2 + H / 2)) * tex_step.reshape(W, 1)
    tex_y = np.clip(tex_pos, 0, TEX_HEIGHT - 1).astype(int)

    tex_num_b = np.broadcast_to(tex_num[:, None], (W, H))
    tex_x_b = np.broadcast_to(tex_x[:, None], (W, H))

    wall_colors = textures[tex_num_b, tex_x_b, tex_y]
    shade = np.clip(1.0 / (1.0 + perp_wall_dist * 0.15), 0, 1)
    shade[side == 1] *= 0.75 
    wall_colors = (wall_colors * shade[:, None, None]).astype(np.uint8)

    # Base Backgrounds
    screen_buffer[:, :H//2] = [20, 20, 25]  # Ceiling
    screen_buffer[:, H//2:] = [40, 40, 45]  # Floor
    screen_buffer[wall_mask] = wall_colors[wall_mask]

    # --- PROCEDURAL ALIEN DRONE BILLBOARDING ---
    for i in range(len(enemies)):
        if enemies[i, 2] == 0:
            enemies[i, 3] -= 1
            if enemies[i, 3] <= 0:
                new_pos = spawn_enemy()
                enemies[i, 0] = new_pos[0]
                enemies[i, 1] = new_pos[1]
                enemies[i, 2] = 1 # Respawn
            continue
            
        dx = enemies[i, 0] - pos_x
        dy = enemies[i, 1] - pos_y
        
        inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y)
        trans_x = inv_det * (dir_y * dx - dir_x * dy)
        trans_y = inv_det * (-plane_y * dx + plane_x * dy)
        
        if trans_y > 0.1: 
            size = max(1, abs(int(H / trans_y)))
            sx = int((W / 2) * (1 + trans_x / trans_y))
            
            sx_start = sx - size//2
            sy_start = H//2 - size//2
            
            x1 = max(0, sx_start)
            x2 = min(W, sx_start + size)
            y1 = max(0, sy_start)
            y2 = min(H, sy_start + size)
            
            if x1 < x2 and y1 < y2:
                u1 = (x1 - sx_start) / size * 2 - 1
                u2 = (x2 - sx_start) / size * 2 - 1
                v1 = (y1 - sy_start) / size * 2 - 1
                v2 = (y2 - sy_start) / size * 2 - 1
                
                x_idx = np.linspace(u1, u2, x2-x1)[:, None]
                y_idx = np.linspace(v1, v2, y2-y1)[None, :]
                
                dist = np.sqrt(x_idx**2 + y_idx**2)
                diamond = (np.abs(x_idx) + np.abs(y_idx)) < 0.9
                eye = dist < 0.3
                core = dist < 0.1
                
                box_buffer = np.zeros((x2-x1, y2-y1, 3), dtype=np.uint8)
                box_buffer[diamond] = [40, 40, 50]
                box_buffer[eye] = [200, 0, 0]     
                box_buffer[core] = [255, 255, 0]  
                
                visible_mask = trans_y < perp_wall_dist[x1:x2]
                mask_3d = visible_mask[:, None, None]
                alpha_mask = diamond[:, :, None]
                
                final_mask = mask_3d & alpha_mask
                screen_slice = screen_buffer[x1:x2, y1:y2]
                screen_buffer[x1:x2, y1:y2] = np.where(final_mask, box_buffer, screen_slice)

    # --- VECTORIZED PARTICLE ENGINE ---
    active_parts = particles[:, 6] > 0
    if np.any(active_parts):
        particles[active_parts, 0] += particles[active_parts, 3]
        particles[active_parts, 1] += particles[active_parts, 4]
        particles[active_parts, 2] += particles[active_parts, 5]
        particles[active_parts, 5] += 1.5  # Gravity
        particles[active_parts, 6] -= 1    # Decay
        
        bounce = active_parts & (particles[:, 2] > H//4)
        particles[bounce, 2] = H//4
        particles[bounce, 5] *= -0.6
        particles[bounce, 3] *= 0.8
        particles[bounce, 4] *= 0.8
        
        dx = particles[:, 0] - pos_x
        dy = particles[:, 1] - pos_y
        inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y)
        trans_x = inv_det * (dir_y * dx - dir_x * dy)
        trans_y = inv_det * (-plane_y * dx + plane_x * dy)

        visible = active_parts & (trans_y > 0.1)
        for i in np.where(visible)[0]:
            sx = int((W / 2) * (1 + trans_x[i] / trans_y[i]))
            sy = int((H / 2) + particles[i, 2] / trans_y[i])
            size = max(1, int(15 / trans_y[i]))

            if 0 <= sx < W and trans_y[i] < perp_wall_dist[sx]:
                x1, x2 = max(0, sx - size//2), min(W, sx + size//2)
                y1, y2 = max(0, sy - size//2), min(H, sy + size//2)
                if x1 < x2 and y1 < y2:
                    screen_buffer[x1:x2, y1:y2] = particles[i, 7:10]

    # Crosshair
    screen_buffer[W//2-4:W//2+4, H//2] = [0, 255, 0]
    screen_buffer[W//2, H//2-4:H//2+4] = [0, 255, 0]

    # --- LOCK, FLUSH, & UI OVERLAY ---
    surf = pygame.surfarray.pixels3d(screen)
    surf[...] = screen_buffer
    del surf 
    
    hud_c = font_medium.render(f"Coins: {total_coins}", True, (255, 215, 0))
    hud_s = font_medium.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(hud_c, (20, 20))
    screen.blit(hud_s, (W - hud_s.get_width() - 20, 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
