import os
import pygame
import json
import base64
import hashlib
from datetime import date, timedelta
from config import *

# ---------------------------------------------------------------------------
# Pixel-art bird template (11 wide × 11 tall, scale=3 → 33×33 in 35×35 surf)
# B=body  W=wing  L=belly  E=eye-white  P=pupil  K=beak  T=beak-tip
# ---------------------------------------------------------------------------
_BIRD_ART = [
    "....BBBBB..",  # 0  head top
    "...BBBBBBB.",  # 1  head
    "..BBBBBBBBB",  # 2  body (widest)
    "..BBBBEEKK.",  # 3  eye-white + beak top
    "..BBBBPPKT.",  # 4  pupil + beak tip
    "..BBBBBLLLL",  # 5  belly (right side)
    ".BWWBBLLL..",  # 6  wing + belly
    ".BWWBB.....",  # 7  wing
    ".BWBBB.....",  # 8  wing tail
    "..BBBBB....",  # 9  lower body
    "...BBB.....",  # 10 tail
]

_SKIN_COLORS = {
    #          body              wing
    'default': ((255, 215,  30), (195, 130,   0)),  # golden yellow
    'red':     ((220,  55,  55), (145,  15,  15)),  # crimson
    'blue':    (( 55, 140, 255), ( 20,  75, 200)),  # sky blue
    'gold':    ((255, 190,  40), (170, 115,   0)),  # amber
    'green':   (( 55, 195,  65), ( 15, 125,  25)),  # emerald
    'purple':  ((185,  55, 255), (105,  15, 185)),  # violet
    'dark':    (( 80,  80, 125), ( 35,  35,  80)),  # slate
}


def _make_pixel_bird(body_col, wing_col=None):
    """Return a 35×35 SRCALPHA surface with a pixel-art bird."""
    r, g, b = body_col
    if wing_col is None:
        wing_col = (max(0, r - 60), max(0, g - 60), max(0, b - 60))
    belly_col = (min(255, r + 65), min(255, g + 65), min(255, b + 45))

    cmap = {
        'B': body_col,
        'W': wing_col,
        'L': belly_col,
        'E': (255, 255, 255),   # eye white
        'P': (20,  20,  20),    # pupil
        'K': (255, 160,   0),   # beak orange
        'T': (185, 100,   0),   # beak dark tip
    }

    scale = 3
    art_w, art_h = len(_BIRD_ART[0]), len(_BIRD_ART)
    ox = (35 - art_w * scale) // 2   # 1-px margin each side
    oy = (35 - art_h * scale) // 2

    surf = pygame.Surface((35, 35), pygame.SRCALPHA)
    for ry, row in enumerate(_BIRD_ART):
        for cx, ch in enumerate(row):
            col = cmap.get(ch)
            if col:
                pygame.draw.rect(surf, col,
                                 (ox + cx * scale, oy + ry * scale, scale, scale))
    return surf

class AssetManager:
    def __init__(self):
        self.stats = {
            'high_score': 0,
            'total_credits': 0,
            'total_destroyed': 0,
            'total_ghost_passes': 0,
            'total_giant_uses': 0,
            'total_laser_uses': 0,
            'total_slow_uses': 0,
            'total_games_played': 0,
            'total_boss_kills': 0,
            'total_near_misses': 0,
            'total_combos': 0,
            'max_combo': 0,
            'current_skin': 'default',
            'unlocked_skins': ['default'],
            'unlocked_upgrades': [],
            'unlocked_achievements': [],
            # daily reward
            'last_daily_date': '',
            'streak_count': 0,
            'max_streak': 0,
            # tutorial
            'tutorial_done': False,
            # settings
            'master_volume': 1.0,
            'bgm_enabled': True,
        }
        self.sounds = {}
        self.bg_img = None
        self.bird_img = None
        self.music_file = None
        self.skin_cache = {}

        self.load_stats()

    # ------------------------------------------------------------------ assets
    def load_assets(self):
        self.bg_img   = self.load_image("BG2.png",  (WIDTH, HEIGHT))
        self.bird_img = self.load_image("FB2.png",  (35, 35))

        self.sounds['wing']      = self.load_sound('wing.wav')
        self.sounds['laser']     = self.load_sound('laser_shot.wav')
        self.sounds['collect']   = self.load_sound('powerup_collect.wav')
        self.sounds['explosion'] = self.load_sound('explosion.wav')
        self.sounds['game_over'] = self.load_sound('game_over.wav')

        music_paths = [
            os.path.join(SND_DIR, 'music.ogg'),
            os.path.join(APP_DIR, 'music.ogg'),
            os.path.join(SND_DIR, 'music.mp3'),
            os.path.join(APP_DIR, 'music.mp3'),
        ]
        self.music_file = next((p for p in music_paths if os.path.exists(p)), None)

        self.pre_render_skins()

    def load_image(self, filename, scale=None):
        paths = [os.path.join(IMG_DIR, filename), os.path.join(APP_DIR, filename)]
        for p in paths:
            if os.path.exists(p):
                try:
                    img = pygame.image.load(p).convert_alpha()
                    if scale:
                        img = pygame.transform.scale(img, scale)
                    return img
                except:
                    pass
        fallback = pygame.Surface(scale if scale else (35, 35))
        fallback.fill(RED)
        return fallback

    def load_sound(self, filename):
        paths = [os.path.join(SND_DIR, filename), os.path.join(APP_DIR, filename)]
        for p in paths:
            if os.path.exists(p):
                try:
                    return pygame.mixer.Sound(p)
                except:
                    pass
        return None

    def play_sound(self, key, combo_count=0):
        if key in self.sounds and self.sounds[key]:
            vol_mult = 1.2 if combo_count > 3 else 1.0
            self.sounds[key].set_volume(config.master_volume * vol_mult)
            self.sounds[key].play()

    def update_volumes(self, is_powerup_active=False):
        base_vol = 0.6 if is_powerup_active else 0.5
        pygame.mixer.music.set_volume(base_vol * config.master_volume if config.bgm_enabled else 0)

    # ------------------------------------------------------------------ skins
    def pre_render_skins(self):
        for skin in SKIN_CATALOG:
            key = skin['key']
            colors = _SKIN_COLORS.get(key)
            if colors:
                body_col, wing_col = colors
                self.skin_cache[key] = _make_pixel_bird(body_col, wing_col)
            else:
                self.skin_cache[key] = _make_pixel_bird((255, 215, 30))

    def get_skin_image(self, skin_key):
        return self.skin_cache.get(skin_key, self.bird_img)

    # -------------------------------------------------------- daily reward
    def get_daily_reward_info(self):
        """Returns (should_show: bool, reward: int, new_streak: int)."""
        today     = str(date.today())
        yesterday = str(date.today() - timedelta(days=1))
        last      = self.stats.get('last_daily_date', '')
        streak    = self.stats.get('streak_count', 0)

        if last == today:
            return False, 0, streak          # already claimed today

        streak = (streak + 1) if last == yesterday else 1
        rewards = [30, 50, 75, 100, 150, 200, 300]
        reward  = rewards[min(streak - 1, 6)]
        return True, reward, streak

    def claim_daily_reward(self):
        """Claim today's reward. Returns (reward, streak) actually given."""
        can, reward, streak = self.get_daily_reward_info()
        if not can:
            return 0, self.stats.get('streak_count', 0)
        self.stats['last_daily_date'] = str(date.today())
        self.stats['streak_count']    = streak
        self.stats['max_streak']      = max(self.stats.get('max_streak', 0), streak)
        self.stats['total_credits']  += reward
        self.save_stats()
        return reward, streak

    # --------------------------------------------------------- save / load
    def get_save_hash(self, data_str):
        salt = "ActionBird_Hardcore_Secret_Key_2026"
        return hashlib.sha256((data_str + salt).encode('utf-8')).hexdigest()

    def load_stats(self):
        if not os.path.exists(SETTINGS_FILE):
            return
        try:
            with open(SETTINGS_FILE, 'r') as f:
                raw = f.read()
            parsed = json.loads(raw)
            if "payload" in parsed and "hash" in parsed:
                payload = parsed["payload"]
                if self.get_save_hash(payload) == parsed["hash"]:
                    data = json.loads(base64.b64decode(payload).decode('utf-8'))
                    self.stats.update(data)
                else:
                    print("[Anti-Cheat] File save đã bị chỉnh sửa!")
            else:
                self.stats.update(parsed)
            config.master_volume = self.stats.get('master_volume', 1.0)
            config.bgm_enabled   = self.stats.get('bgm_enabled',   True)
        except Exception as e:
            print(f"Lỗi load save: {e}")

    def save_stats(self):
        try:
            self.stats['master_volume'] = config.master_volume
            self.stats['bgm_enabled']   = config.bgm_enabled
            json_str = json.dumps(self.stats)
            encoded  = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            save_data = {
                "_warning": "DO NOT EDIT THIS FILE. TAMPERING WILL CORRUPT YOUR SAVE.",
                "payload": encoded,
                "hash":    self.get_save_hash(encoded),
            }
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(save_data, f, indent=4)
        except Exception as e:
            print(f"Lỗi save: {e}")
