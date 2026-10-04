import pygame
import numpy as np
import math
import random
import sys

# ==========================================
# ENGINE CONFIGURATION
# ==========================================
pygame.init()
W, H = 1200, 900
CELL_SIZE = 3
GRID_W, GRID_H = W // CELL_SIZE, H // CELL_SIZE

screen = pygame.display.set_mode((W, H), pygame.SCALED)
pygame.display.set_caption("Cellular Decay: The Living Maze")
clock = pygame.time.Clock()

font_large = pygame.font.Font(None, 60)
font_small = pygame.font.Font(None, 30)

# Colors
COLOR_WALL = [50, 255, 120]
COLOR_VOID = [15, 20, 25]

# ==========================================
# NUMPY CELLULAR AUTOMATA ENGINE
# ==========================================
# Initialize with a stable-ish organic noise pattern
grid = np.random.choice([0, 1], size=(GRID_W, GRID_H), p=[0.85, 0.15]).astype(np.uint8)

def compute_life_generation(current_grid):
    # Vectorized 8-neighbor convolution using np.roll (torus wrap-around)
    N = (np.roll(current_grid, 1, axis=0) + np.roll(current_grid, -1, axis=0) +
         np.roll(current_grid, 1, axis=1) + np.roll(current_grid, -1, axis=1) +
         np.roll(np.roll(current_grid, 1, axis=0), 1, axis=1) +
         np.roll(np.roll(current_grid, -1, axis=0), -1, axis=1) +
         np.roll(np.roll(current_grid, 1, axis=0), -1, axis=1) +
         np.roll(np.roll(current_grid, -1, axis=0), 1, axis=1))
    
    # Conway's Rules applied matrix-wide
    # 1. Survive if 2 or 3 neighbors
    # 2. Born if exactly 3 neighbors
    return np.where((current_grid == 1) & ((N == 2) | (N == 3)), 1,
           np.where((current_grid == 0) & (N == 3), 1, 0)).astype(np.uint8)

def mutate_ecosystem(cx, cy, radius=15):
    # Inject heavy random noise in a radius to disrupt the Life rules
    x_min, x_max = max(0, cx - radius), min(GRID_W, cx + radius)
    y_min, y_max = max(0, cy - radius), min(GRID_H, cy + radius)
    
    noise = np.random.choice([0, 1], size=(x_max-x_min, y_max-y_min), p=[0.5, 0.5])
    grid[x_min:x_max, y_min:y_max] = noise

# ==========================================
# GAME ENTITIES
# ==========================================
class Player:
    def __init__(self):
        self.x, self.y = W // 2, H // 2
        self.speed = 4
        self.health = 100
        self.radius = 8

    def update(self, keys):
        px, py = self.x, self.y
        if keys[pygame.K_w]: py -= self.speed
        if keys[pygame.K_s]: py += self.speed
        if keys[pygame.K_a]: px -= self.speed
        if keys[pygame.K_d]: px += self.speed

        # Safe boundaries
        px = max(self.radius, min(W - self.radius, px))
        py = max(self.radius, min(H - self.radius, py))

        # Check Cellular Collision
        gx, gy = int(px // CELL_SIZE), int(py // CELL_SIZE)
        if grid[gx, gy] == 1:
            self.health -= 1  # The walls burn you
            # Automatically carve a tiny safe zone to prevent getting permastuck
            mutate_ecosystem(gx, gy, radius=3)
        else:
            self.x, self.y = px, py

    def draw(self, surf):
        pygame.draw.circle(surf, (255, 100, 100), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 1)

class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.speed = 15
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        self.active = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        
        if self.x < 0 or self.x >= W or self.y < 0 or self.y >= H:
            self.active = False
            return

        gx, gy = int(self.x // CELL_SIZE), int(self.y // CELL_SIZE)
        
        # If bullet hits a living cell, trigger systemic disruption
        if grid[gx, gy] == 1:
            mutate_ecosystem(gx, gy, radius=20)
            self.active = False

    def draw(self, surf):
        pygame.draw.circle(surf, (0, 255, 255), (int(self.x), int(self.y)), 4)

class GlitchEnemy:
    def __init__(self):
        # Spawn in a random dead cell near the edges
        while True:
            gx = random.choice([random.randint(1, 10), random.randint(GRID_W-11, GRID_W-2)])
            gy = random.choice([random.randint(1, 10), random.randint(GRID_H-11, GRID_H-2)])
            if grid[gx, gy] == 0:
                self.x = gx * CELL_SIZE
                self.y = gy * CELL_SIZE
                break
        self.speed = 2
        self.active = True

    def update(self, px, py):
        dx, dy = px - self.x, py - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        # If enemy touches a living cell, it gets absorbed and mutates the wall
        gx, gy = int(self.x // CELL_SIZE), int(self.y // CELL_SIZE)
        if grid[gx, gy] == 1:
            mutate_ecosystem(gx, gy, radius=8)
            self.active = False
            
        # Player collision
        if dist < 12:
            self.active = False
            return True # Hit player
        return False

    def draw(self, surf):
        pygame.draw.rect(surf, (255, 0, 255), (int(self.x)-6, int(self.y)-6, 12, 12))

# ==========================================
# MAIN LOOP
# ==========================================
def main():
    global grid
    player = Player()
    bullets = []
    enemies = []
    
    score = 0
    gol_timer = 0
    GOL_UPDATE_RATE = 4  # Frames between Game of Life calculations (determines ecosystem speed)
    
    running = True
    while running:
        clock.tick(60)
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if player.health > 0:
                    dx, dy = mouse_x - player.x, mouse_y - player.y
                    angle = math.atan2(dy, dx)
                    bullets.append(Bullet(player.x, player.y, angle))

        if player.health > 0:
            # --- Ecosystem Simulation ---
            gol_timer += 1
            if gol_timer >= GOL_UPDATE_RATE:
                grid = compute_life_generation(grid)
                gol_timer = 0
                score += 1 # Survive to earn points

            # --- Entity Updates ---
            player.update(keys)

            for b in bullets[:]:
                b.update()
                if not b.active:
                    bullets.remove(b)
                    
            if random.random() < 0.05 + (score / 100000):
                enemies.append(GlitchEnemy())
                
            for e in enemies[:]:
                hit = e.update(player.x, player.y)
                if hit:
                    player.health -= 15
                    enemies.remove(e)
                elif not e.active:
                    enemies.remove(e)
                    
            # --- Rendering ---
            # Fast NumPy to Pygame Surface rendering
            color_array = np.zeros((GRID_W, GRID_H, 3), dtype=np.uint8)
            color_array[grid == 1] = COLOR_WALL
            color_array[grid == 0] = COLOR_VOID
            
            # Convert array to surface and scale up
            bg_surf = pygame.surfarray.make_surface(color_array)
            bg_surf = pygame.transform.scale(bg_surf, (W, H))
            screen.blit(bg_surf, (0, 0))

            # Draw Entities
            for e in enemies: e.draw(screen)
            for b in bullets: b.draw(screen)
            player.draw(screen)

            # UI Overlay
            health_txt = font_small.render(f"CELL INTEGRITY: {max(0, player.health)}%", True, (255, 255, 255))
            score_txt = font_small.render(f"SURVIVAL: {score}", True, (50, 255, 120))
            
            screen.blit(health_txt, (20, 20))
            screen.blit(score_txt, (20, 50))
            
            # Crosshair
            pygame.draw.circle(screen, (0, 255, 255), (mouse_x, mouse_y), 5, 1)

        else:
            # Game Over Screen
            screen.fill((15, 20, 25))
            go_txt = font_large.render("SYSTEM COLLAPSE", True, (255, 50, 50))
            screen.blit(go_txt, (W//2 - go_txt.get_width()//2, H//2 - 30))
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
