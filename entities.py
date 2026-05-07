import pygame
import random
import math
from config import *

# ---------------------------------------------------------------------------
# Pixel-art boss template  20 cols × 20 rows  scale=5  → 100×100 surface
# 0=transparent  1=body(dark metal)  2=shadow/armor  3=highlight/rivet
# 4=eye-red  5=eye-glow  6=fang(gold)  7=wing  8=thruster  9=flame
# ---------------------------------------------------------------------------
_BOSS_GRID = [
    [0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0],  #  0  crown
    [0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0],  #  1
    [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],  #  2
    [0,0,0,1,1,3,3,1,1,1,1,1,1,3,3,1,1,0,0,0],  #  3  rivets
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],  #  4
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],  #  5
    [0,0,1,1,4,4,4,1,1,1,1,1,1,4,4,4,1,1,0,0],  #  6  eyes
    [0,0,1,1,4,5,4,1,1,1,1,1,1,4,5,4,1,1,0,0],  #  7  eye-glow center
    [0,0,1,1,4,4,4,1,1,1,1,1,1,4,4,4,1,1,0,0],  #  8
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0],  #  9
    [0,0,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,1,0,0],  # 10  armor crease
    [0,0,1,1,6,6,6,1,1,1,1,1,1,6,6,6,1,1,0,0],  # 11  fangs top
    [0,0,1,6,6,6,6,1,1,1,1,1,1,6,6,6,6,1,0,0],  # 12  fangs mid (widest)
    [0,0,1,1,6,6,6,1,1,1,1,1,1,6,6,6,1,1,0,0],  # 13  fangs bottom
    [0,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,0,0],  # 14  shoulder armor
    [0,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,0,0],  # 15
    [7,7,7,7,7,1,1,1,1,1,1,1,1,1,1,7,7,7,7,7],  # 16  wings spread (5+10+5)
    [7,7,7,7,7,7,1,1,1,1,1,1,1,1,7,7,7,7,7,7],  # 17  widest wings (6+8+6)
    [0,7,7,7,7,7,1,1,1,1,1,1,1,7,7,7,7,7,0,0],  # 18  tapered wings
    [0,0,0,8,8,8,9,9,9,9,9,9,8,8,8,0,0,0,0,0],  # 19  thrusters + flame
]

_BOSS_PALETTE = {
    1: ( 52,  52,  78),   # dark metal body
    2: ( 28,  28,  48),   # deep shadow / armor plate
    3: (108, 108, 152),   # highlight / rivet
    4: (220,  28,  28),   # eye red
    5: (255, 175,  55),   # eye inner glow
    6: (205, 162,   0),   # golden fang
    7: ( 32,  32,  58),   # wing (darker metal)
    8: (225,  95,   0),   # thruster casing
    9: (255, 220,  35),   # thruster flame
}


def _make_boss_image():
    """Return a fresh 100×100 SRCALPHA pixel-art boss surface."""
    scale = 5
    surf  = pygame.Surface((100, 100), pygame.SRCALPHA)
    for ry, row in enumerate(_BOSS_GRID):
        for cx, idx in enumerate(row):
            col = _BOSS_PALETTE.get(idx)
            if col:
                pygame.draw.rect(surf, col, (cx * scale, ry * scale, scale, scale))
    return surf

class Bird(pygame.sprite.Sprite):
    def __init__(self, x, y, image, skin_color=None):
        super().__init__()
        self.original_image = image
        if skin_color:
            self.original_image = pygame.Surface((35, 35), pygame.SRCALPHA)
            pygame.draw.circle(self.original_image, skin_color, (17, 17), 17)
            pygame.draw.circle(self.original_image, WHITE, (25, 12), 4)
            pygame.draw.circle(self.original_image, BLACK, (26, 12), 2)
            
        self.image = self.original_image
        self.base_image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity = 0
        self.mask = pygame.mask.from_surface(self.image)
        self.ghost_mode = False
        self.alpha = 255
        self.is_giant = False

    def update(self, state, current_gravity, is_ghost, is_any_warning, is_giant):
        if state == PLAYING:
            self.velocity += current_gravity
            self.rect.y += self.velocity

            center = self.rect.center

            if is_giant:
                if not self.is_giant:
                    self.is_giant = True
                    self.base_image = pygame.transform.scale(self.original_image, (70, 70))
            else:
                if self.is_giant:
                    self.is_giant = False
                    self.base_image = self.original_image.copy()

            angle = max(-70, min(25, -self.velocity * 3))
            self.image = pygame.transform.rotate(self.base_image, angle)
            self.rect = self.image.get_rect(center=center)
            self.mask = pygame.mask.from_surface(self.image)

            if self.rect.top < 0:
                self.rect.top = 0
                self.velocity = 0
            if self.rect.bottom > HEIGHT - 25:
                return True 

            self.ghost_mode = is_ghost
            base_alpha = 150 if self.ghost_mode else 255

            if is_any_warning:
                if (pygame.time.get_ticks() // 100) % 2 == 0:
                    self.alpha = 50
                else:
                    self.alpha = base_alpha
            else:
                self.alpha = base_alpha

            self.image.set_alpha(self.alpha)

        return False

    def jump(self, current_jump_strength):
        self.velocity = current_jump_strength

class Tube(pygame.sprite.Sprite):
    def __init__(self, x, height, is_top, moving=False):
        super().__init__()
        self.is_top   = is_top
        self.is_moving = moving
        self.base_y   = 0 if is_top else height + TUBE_GAP
        self.offset   = random.uniform(0, math.pi * 2)

        self.image = self._draw_tube(TUBE_WIDTH, height, is_top, moving)
        if is_top:
            self.rect = self.image.get_rect(topleft=(x, 0))
        else:
            self.rect = self.image.get_rect(topleft=(x, self.base_y))
        self.mask = pygame.mask.from_surface(self.image)

    @staticmethod
    def _draw_tube(w, h, is_top, moving):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Color scheme: green for static, blue-teal for moving
        if moving:
            body  = (55,  160, 215)
            dark  = (25,  100, 155)
            light = (110, 210, 255)
            rim   = (40,  130, 185)
        else:
            body  = (65,  185, 65)
            dark  = (30,  115, 30)
            light = (130, 235, 130)
            rim   = (45,  155, 45)

        # --- Body ---
        surf.fill(body)
        pygame.draw.rect(surf, dark,  (0,     0, 8, h))       # left shadow
        pygame.draw.rect(surf, light, (w - 6, 0, 6, h))       # right highlight
        # center crease
        cr = tuple(max(0, c - 30) for c in body)
        pygame.draw.rect(surf, cr, (w // 2 - 2, 0, 3, h))

        # --- Cap / rim at the open end (20 px) ---
        CAP = 20
        if is_top:
            cy = h - CAP                                       # cap at bottom edge
            pygame.draw.rect(surf, rim,   (0, cy,      w,   CAP))
            pygame.draw.rect(surf, light, (0, cy,      w,   4  ))   # top highlight
            pygame.draw.rect(surf, dark,  (0, h - 3,   w,   3  ))   # bottom shadow
            pygame.draw.rect(surf, dark,  (0, cy,      3,   CAP))   # left shadow on cap
            pygame.draw.rect(surf, light, (w - 4, cy,  4,   CAP))   # right highlight on cap
        else:
            cy = 0
            pygame.draw.rect(surf, rim,   (0, cy,      w,   CAP))
            pygame.draw.rect(surf, dark,  (0, cy,      w,   3  ))   # top shadow
            pygame.draw.rect(surf, light, (0, CAP - 4, w,   4  ))   # bottom highlight
            pygame.draw.rect(surf, dark,  (0, cy,      3,   CAP))
            pygame.draw.rect(surf, light, (w - 4, cy,  4,   CAP))

        # --- Outer border ---
        pygame.draw.rect(surf, dark, surf.get_rect(), 2)
        return surf

    def update(self, velocity):
        self.rect.x -= velocity
        if self.is_moving:
            self.rect.y = int(self.base_y + math.sin(
                pygame.time.get_ticks() * 0.003 + self.offset) * 50)
        if self.rect.right < 0:
            self.kill()

class Cloud(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        w = random.randint(60, 120)
        h = w // 2
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        color = (255, 255, 255, random.randint(50, 150)) 
        pygame.draw.ellipse(self.image, color, (0, 0, w, h))
        
        self.rect = self.image.get_rect(topleft=(WIDTH + random.randint(0, 100), random.randint(20, 200)))
        self.speed = random.uniform(0.5, 1.5)

    def update(self, current_vel):
        self.rect.x -= self.speed * (current_vel / INITIAL_TUBE_VELOCITY)
        if self.rect.right < 0:
            self.kill()

class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        self.type = type
        self._base_image = self._draw_icon(type)
        self.image = self._base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self._bob_timer = 0
        self._glow_timer = 0

    def _draw_icon(self, type):
        S = ITEM_SIZE + 10  # 40px canvas
        surf = pygame.Surface((S, S), pygame.SRCALPHA)
        c = S // 2

        if type == 'LASER':
            # Red hexagon background
            self._draw_hexagon(surf, c, c, 18, (200, 30, 30))
            self._draw_hexagon(surf, c, c, 18, (255, 80, 80), border=2)
            # Lightning bolt
            pts = [(c-3, c-10), (c+4, c-10), (c, c-1), (c+6, c-1), (c-4, c+10), (c+1, c+10), (c+3, c+1), (c-3, c+1)]
            pygame.draw.polygon(surf, YELLOW, pts)
            pygame.draw.polygon(surf, WHITE, pts, 1)

        elif type == 'GHOST':
            # Dark blue-purple background
            self._draw_hexagon(surf, c, c, 18, (50, 30, 100))
            self._draw_hexagon(surf, c, c, 18, (150, 100, 255), border=2)
            # Ghost body: rounded top + wavy bottom
            ghost_color = (200, 200, 255)
            pygame.draw.ellipse(surf, ghost_color, (c-8, c-11, 16, 14))
            pygame.draw.rect(surf, ghost_color, (c-8, c-4, 16, 12))
            # Wavy bottom (3 bumps)
            for i in range(3):
                pygame.draw.circle(surf, ghost_color, (c-7+i*7, c+9), 4)
            # Gaps between bumps
            pygame.draw.circle(surf, (0, 0, 0, 0), (c-3, c+9), 3)
            pygame.draw.circle(surf, (0, 0, 0, 0), (c+3, c+9), 3)
            # Eyes
            pygame.draw.circle(surf, (80, 40, 180), (c-4, c-3), 3)
            pygame.draw.circle(surf, (80, 40, 180), (c+4, c-3), 3)
            pygame.draw.circle(surf, WHITE, (c-3, c-4), 1)
            pygame.draw.circle(surf, WHITE, (c+5, c-4), 1)

        elif type == 'SLOW':
            # Purple hexagon background
            self._draw_hexagon(surf, c, c, 18, (80, 20, 120))
            self._draw_hexagon(surf, c, c, 18, (200, 80, 255), border=2)
            # Hourglass shape
            hg_color = (230, 200, 255)
            pts_top = [(c-8, c-11), (c+8, c-11), (c+2, c-2), (c-2, c-2)]
            pts_bot = [(c-2, c+2), (c+2, c+2), (c+8, c+11), (c-8, c+11)]
            pygame.draw.polygon(surf, hg_color, pts_top)
            pygame.draw.polygon(surf, hg_color, pts_bot)
            # Border lines
            pygame.draw.line(surf, WHITE, (c-8, c-11), (c+8, c-11), 2)
            pygame.draw.line(surf, WHITE, (c-8, c+11), (c+8, c+11), 2)
            # Sand dots
            for dx, dy in [(-1, 4), (1, 4), (0, 6), (-1, -5), (1, -5)]:
                pygame.draw.circle(surf, (255, 220, 100), (c+dx, c+dy), 1)

        elif type == 'GIANT':
            # Orange hexagon background
            self._draw_hexagon(surf, c, c, 18, (160, 70, 0))
            self._draw_hexagon(surf, c, c, 18, (255, 160, 30), border=2)
            # Up-arrow (growth symbol)
            arr_color = (255, 240, 100)
            arrow_pts = [(c, c-11), (c+8, c-2), (c+4, c-2), (c+4, c+10), (c-4, c+10), (c-4, c-2), (c-8, c-2)]
            pygame.draw.polygon(surf, arr_color, arrow_pts)
            pygame.draw.polygon(surf, WHITE, arrow_pts, 1)

        return surf

    def _draw_hexagon(self, surf, cx, cy, r, color, border=0):
        pts = []
        for i in range(6):
            angle = math.pi / 180 * (60 * i - 30)
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        if border:
            pygame.draw.polygon(surf, color, pts, border)
        else:
            pygame.draw.polygon(surf, color, pts)

    def update(self, velocity):
        self.rect.x -= velocity
        if self.rect.right < 0:
            self.kill()
            return
        # Bob animation
        self._bob_timer += 0.08
        self._glow_timer += 1
        bob_y = int(math.sin(self._bob_timer) * 3)
        self.image = pygame.transform.rotate(self._base_image, math.sin(self._bob_timer * 0.5) * 8)
        new_rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery + bob_y))
        self.rect = new_rect

class Laser(pygame.sprite.Sprite):
    def __init__(self, start_pos):
        super().__init__()
        self.image = pygame.Surface((40, 6), pygame.SRCALPHA)
        pygame.draw.rect(self.image, RED, (0, 0, 40, 6))
        pygame.draw.rect(self.image, WHITE, (0, 2, 40, 2))
        self.rect = self.image.get_rect(midleft=start_pos)
        self.speed = 15

    def update(self, bird_rect):
        self.rect.x += self.speed
        if self.rect.left > WIDTH:
            self.kill()

class TrailEffect(pygame.sprite.Sprite):
    def __init__(self, x, y, image):
        super().__init__()
        self.image = image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.alpha = 150

    def update(self):
        self.alpha -= 10
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.alpha)

class FloatingText(pygame.sprite.Sprite):
    def __init__(self, x, y, text, color, font):
        super().__init__()
        self.font = font
        self.image = self.font.render(text, True, color)
        self.rect = self.image.get_rect(center=(x, y))
        self.velocity = -2
        self.alpha = 255

    def update(self):
        self.rect.y += self.velocity
        self.alpha -= 5
        if self.alpha <= 0:
            self.kill()
        else:
            temp_image = self.image.copy()
            temp_image.set_alpha(self.alpha)
            self.image = temp_image

class Missile(pygame.sprite.Sprite):
    def __init__(self, y):
        super().__init__()
        self.missile_image = pygame.Surface((40, 20), pygame.SRCALPHA)
        pygame.draw.rect(self.missile_image, (150, 150, 150), (10, 5, 25, 10))
        pygame.draw.polygon(self.missile_image, RED, [(35, 5), (40, 10), (35, 15)])
        pygame.draw.polygon(self.missile_image, ORANGE, [(0, 5), (10, 5), (10, 15), (0, 15)])
        
        self.warning_image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.warning_image, RED, [(20, 0), (40, 40), (0, 40)])
        pygame.draw.polygon(self.warning_image, YELLOW, [(20, 5), (35, 35), (5, 35)])
        pygame.draw.rect(self.warning_image, RED, (18, 15, 4, 12))
        pygame.draw.rect(self.warning_image, RED, (18, 30, 4, 4))
        
        self.image = self.warning_image
        self.rect = self.image.get_rect(midright=(WIDTH - 10, y))
        self.y_pos = y
        self.speed = 8
        self.warning_timer = 90 # 1.5s warning

    def update(self, current_vel=0):
        if self.warning_timer > 0:
            self.warning_timer -= 1
            if self.warning_timer % 10 < 5:
                self.image.set_alpha(255)
            else:
                self.image.set_alpha(0)
                
            if self.warning_timer == 0:
                self.image = self.missile_image
                self.image.set_alpha(255)
                self.rect = self.image.get_rect(midleft=(WIDTH, self.y_pos))
        else:
            self.rect.x -= self.speed + current_vel
            if self.rect.right < 0:
                self.kill()

class EnergyBall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, PURPLE, (10, 10), 10)
        pygame.draw.circle(self.image, WHITE, (10, 10), 5)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5
        self.angle = random.uniform(-0.2, 0.2)

    def update(self, current_vel=0):
        self.rect.x -= self.speed + current_vel
        self.rect.y += self.angle * self.speed
        if self.rect.right < 0 or self.rect.top > HEIGHT or self.rect.bottom < 0:
            self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self._base_surf = _make_boss_image()
        self.image      = self._base_surf.copy()
        self.rect       = self.image.get_rect(center=(WIDTH + 100, HEIGHT // 2))
        self.target_x   = WIDTH - 80
        self.hp         = 10
        self.max_hp     = 10
        self.move_speed = 2
        self.direction  = 1
        self.shoot_timer= 0
        self.hit_timer  = 0

    def update(self, current_vel=0):
        if self.rect.centerx > self.target_x:
            self.rect.x -= 2
        else:
            self.rect.y += self.move_speed * self.direction
            if self.rect.top < 50:
                self.direction = 1
            elif self.rect.bottom > HEIGHT - 50:
                self.direction = -1

        if self.hit_timer > 0:
            self.hit_timer -= 1
            self.image = self._base_surf.copy()
            if self.hit_timer % 4 < 2:
                self.image.fill((255, 255, 255, 150), special_flags=pygame.BLEND_RGBA_ADD)
        else:
            self.image = self._base_surf

    def take_damage(self):
        self.hp -= 1
        self.hit_timer = 20
        return self.hp <= 0

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        size = random.randint(3, 8)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-3, -1)
        self.vy = random.uniform(-1, 1)
        self.life = 255

    def update(self, current_vel=0):
        self.rect.x += self.vx - current_vel
        self.rect.y += self.vy
        self.life -= 15
        if self.life <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.life)
