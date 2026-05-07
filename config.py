import os

# --- Font helper ---
_font_cache: dict = {}

def make_font(size: int, bold: bool = False):
    """Cached font with Vietnamese/Unicode support. Prefers Segoe UI > Tahoma > Verdana > Arial."""
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    import pygame
    available = set(pygame.font.get_fonts())
    for name in ('segoeui', 'tahoma', 'verdana', 'arial'):
        if name in available:
            _font_cache[key] = pygame.font.SysFont(name, size, bold=bold)
            return _font_cache[key]
    _font_cache[key] = pygame.font.SysFont(None, size, bold=bold)
    return _font_cache[key]

# --- Cấu hình & Hằng số ---
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 0.4
JUMP_STRENGTH = -7
INITIAL_TUBE_VELOCITY = 3
TUBE_WIDTH = 60
TUBE_GAP = 180
ITEM_SIZE = 30
ITEM_CHANCE = 0.15  # 15% tỷ lệ xuất hiện vật phẩm
POWERUP_DURATION = 5000  # 5 giây (ms)
WARNING_TIME = 1500  # 1.5 giây (ms) cảnh báo hết giờ

# Thư mục tài nguyên
ASSETS_DIR = "assets"
IMG_DIR = os.path.join(ASSETS_DIR, "images")
SND_DIR = os.path.join(ASSETS_DIR, "sounds")

# Đường dẫn settings.json: dùng thư mục writable của app trên Android
if 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_ROOT' in os.environ:
    try:
        from android.storage import app_storage_path
        _DATA_DIR = app_storage_path()
    except Exception:
        _DATA_DIR = os.path.expanduser('~')
else:
    _DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(_DATA_DIR, 'settings.json')

# Màu sắc
WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0  )
RED     = (255, 50,  50 )
BLUE    = (50,  150, 255)
YELLOW  = (255, 220, 0  )
GRAY    = (150, 150, 150)
PURPLE  = (180, 50,  255)
ORANGE  = (255, 120, 0  )
CYAN    = (0,   255, 255)
GREEN   = (50,  200, 50 )
GOLD    = (255, 195, 30 )
DARK    = (70,  70,  95 )

# Trạng thái Game
LOBBY        = "LOBBY"
PLAYING      = "PLAYING"
GAME_OVER    = "GAME_OVER"
SETTINGS     = "SETTINGS"
SHOP         = "SHOP"
ACHIEVEMENTS = "ACHIEVEMENTS"
PAUSED       = "PAUSED"
TUTORIAL     = "TUTORIAL"

# Danh mục skin (key, tên, giá, màu nút)
SKIN_CATALOG = [
    {'key': 'default', 'name': 'DEFAULT BIRD', 'price': 0,   'btn_color': (50, 100, 180),  'target': None},
    {'key': 'red',     'name': 'RED BIRD',      'price': 50,  'btn_color': (180, 50,  50),  'target': (255, 50,  50) },
    {'key': 'blue',    'name': 'BLUE BIRD',      'price': 75,  'btn_color': (30,  100, 220), 'target': (50,  150, 255)},
    {'key': 'gold',    'name': 'GOLD BIRD',      'price': 150, 'btn_color': (170, 130, 0),   'target': (255, 195, 30) },
    {'key': 'green',   'name': 'GREEN BIRD',     'price': 175, 'btn_color': (30,  140, 30),  'target': (50,  200, 50) },
    {'key': 'purple',  'name': 'PURPLE BIRD',    'price': 200, 'btn_color': (130, 30,  200), 'target': (180, 50,  255)},
    {'key': 'dark',    'name': 'DARK BIRD',      'price': 250, 'btn_color': (50,  50,  80),  'target': (70,  70,  95) },
]

# Danh mục upgrade (section=True là tiêu đề phân cách)
UPGRADE_CATALOG = [
    {'section': 'POWERUP UPGRADES'},
    {'id': 'longer_ghost',  'name': 'Ghost +50% Duration', 'price': 80,  'btn_color': (100,100,160)},
    {'id': 'longer_laser',  'name': 'Laser +50% Duration', 'price': 80,  'btn_color': (160, 30, 30)},
    {'id': 'longer_slow',   'name': 'Slow  +50% Duration', 'price': 80,  'btn_color': (120, 30,180)},
    {'id': 'longer_giant',  'name': 'Giant +50% Duration', 'price': 100, 'btn_color': (160, 80,  0)},
    {'section': 'SPECIAL UPGRADES'},
    {'id': 'fire_aura',     'name': 'Fire Aura',           'price': 200, 'btn_color': (180, 60,  0)},
    {'id': 'item_magnet',   'name': 'Item Magnet',         'price': 150, 'btn_color': (0,  160, 180)},
]

class Config:
    def __init__(self):
        self.master_volume = 1.0  # 0% - 100% (0.0 - 1.0)
        self.bgm_enabled = True

config = Config()
