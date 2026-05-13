import pygame
import math
from config import *

# Pre-built font sizes used across all UI functions (cached via make_font)
def _f(size, bold=False):
    return make_font(size, bold=bold)

def _render_fit(font, text, color, max_w):
    """Render text and scale down proportionally if wider than max_w."""
    surf = font.render(text, True, color)
    if surf.get_width() > max_w:
        ratio = max_w / surf.get_width()
        surf = pygame.transform.smoothscale(surf, (max_w, max(1, int(surf.get_height() * ratio))))
    return surf

# ============================================================= helpers
def draw_button(game, text, x, y, w, h, base_color, hover_color, font=None):
    mouse = pygame.mouse.get_pos()
    rect  = pygame.Rect(x, y, w, h)
    color = hover_color if rect.collidepoint(mouse) else base_color

    shadow = rect.copy(); shadow.y += 4
    pygame.draw.rect(game.screen, (20, 20, 20), shadow, border_radius=12)
    pygame.draw.rect(game.screen, color,         rect,   border_radius=12)

    hl = pygame.Surface((w - 4, h // 2), pygame.SRCALPHA)
    hl.fill((255, 255, 255, 40))
    game.screen.blit(hl, (x + 2, y + 2))

    pygame.draw.rect(game.screen, BLACK, rect, 2, border_radius=12)

    f = font or game.font
    ts  = f.render(text, True, WHITE)
    tsh = f.render(text, True, (0, 0, 0))
    max_tw = w - 12
    if ts.get_width() > max_tw:
        ratio = max_tw / ts.get_width()
        nh = max(1, int(ts.get_height() * ratio))
        ts  = pygame.transform.smoothscale(ts,  (max_tw, nh))
        tsh = pygame.transform.smoothscale(tsh, (max_tw, nh))
    tr  = ts.get_rect(center=rect.center)
    game.screen.blit(tsh, (tr.x + 1, tr.y + 1))
    game.screen.blit(ts,  tr)
    return rect.collidepoint(mouse)


def draw_panel(game, x, y, w, h, title=""):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((0, 0, 0, 180))
    game.screen.blit(s, (x, y))
    pygame.draw.rect(game.screen, CYAN, (x, y, w, h), 2, border_radius=5)
    if title:
        ts = game.font.render(title, True, CYAN)
        game.screen.blit(ts, (x + 10, y - 25))


def draw_settings_btn(game, x=None, y=10):
    """Draw a small hamburger-menu settings button. Default: top-right corner."""
    if x is None:
        x = WIDTH - 45
    r = pygame.Rect(x, y, 35, 35)
    mouse = pygame.mouse.get_pos()
    s = pygame.Surface((35, 35), pygame.SRCALPHA)
    s.fill((0, 0, 0, 160) if r.collidepoint(mouse) else (0, 0, 0, 100))
    game.screen.blit(s, (x, y))
    pygame.draw.rect(game.screen, (180, 180, 210), r, 2, border_radius=8)
    for i in range(3):
        pygame.draw.rect(game.screen, WHITE, (x + 7, y + 10 + i * 7, 21, 3), border_radius=1)


def draw_god_input_overlay(game):
    """Password input dialog for god mode toggle."""
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    game.screen.blit(ov, (0, 0))

    pw, ph = 300, 160
    px, py = WIDTH // 2 - pw // 2, HEIGHT // 2 - ph // 2
    ps = pygame.Surface((pw, ph), pygame.SRCALPHA)
    ps.fill((10, 10, 20, 240))
    game.screen.blit(ps, (px, py))
    pygame.draw.rect(game.screen, CYAN, (px, py, pw, ph), 2, border_radius=10)

    tf = _f(18, bold=True)
    lbl = tf.render("ENTER PASSWORD:", True, CYAN)
    game.screen.blit(lbl, lbl.get_rect(center=(WIDTH // 2, py + 30)))

    masked = "*" * len(game._god_input)
    inp_s = _f(22, bold=True).render(masked or "_", True, YELLOW)
    game.screen.blit(inp_s, inp_s.get_rect(center=(WIDTH // 2, py + 72)))

    hint_f = _f(13)
    game.screen.blit(hint_f.render("Enter: confirm  |  Esc: cancel", True, GRAY),
                     _f(13).render("Enter: confirm  |  Esc: cancel", True, GRAY).get_rect(center=(WIDTH // 2, py + 115)))

    if getattr(game, 'god_mode', False):
        gf = _f(14, bold=True)
        gs = gf.render("GOD MODE: ON", True, GREEN)
        game.screen.blit(gs, gs.get_rect(center=(WIDTH // 2, py + 140)))


def draw_transition(game):
    if hasattr(game, 'fade_alpha') and game.fade_alpha > 0:
        s = pygame.Surface((WIDTH, HEIGHT))
        s.fill(BLACK); s.set_alpha(game.fade_alpha)
        game.screen.blit(s, (0, 0))

# ============================================================= HUD (in-game)
def draw_ui(game):
    if game.state != PLAYING:
        return

    # Score pop
    if game.score != game.last_score:
        game.score_scale = 2.0
        game.last_score  = game.score
    game.score_scale += (1.0 - game.score_scale) * 0.15
    col  = YELLOW if game.score_scale > 1.1 else WHITE
    sf   = _f(int(24 * game.score_scale), bold=True)
    game.screen.blit(sf.render(f"Score: {game.score}", True, col), (20, 20))

    # Power-up bars
    y_off = 60
    now   = pygame.time.get_ticks()
    bar_font = _f(16, bold=True)
    for ptype, end_t in list(game.active_powerups.items()):
        tl = end_t - now
        if tl <= 0:
            continue
        upgrades = game.asset_manager.stats.get('unlocked_upgrades', [])
        is_longer = f'longer_{ptype.lower()}' in upgrades
        total_dur = POWERUP_DURATION * 1.5 if is_longer else POWERUP_DURATION
        if ptype == 'GIANT' and end_t > now + 999990:
            continue  # boss laser — infinite, skip bar
        ratio = max(0, min(1, tl / total_dur))

        pcolors = {'LASER': RED, 'GHOST': (160, 160, 255), 'SLOW': PURPLE, 'GIANT': ORANGE}
        bar_col = pcolors.get(ptype, WHITE)

        pygame.draw.rect(game.screen, (40, 40, 40), (20, y_off, 120, 12), border_radius=6)
        if tl < 1500:  # flash warning
            bar_col = WHITE if (now // 150) % 2 == 0 else bar_col
        pygame.draw.rect(game.screen, bar_col, (22, y_off + 2, int(116 * ratio), 8), border_radius=4)
        game.screen.blit(bar_font.render(ptype, True, WHITE), (148, y_off - 2))
        y_off += 28

    # Boss HP bar
    if game.boss_fight and game.boss_entity:
        boss  = game.boss_entity
        bw    = 200
        bx    = WIDTH // 2 - bw // 2
        by    = 15
        pygame.draw.rect(game.screen, (60, 0, 0), (bx - 2, by - 2, bw + 4, 16), border_radius=6)
        ratio = boss.hp / boss.max_hp
        hc    = RED if ratio > 0.4 else (YELLOW if ratio > 0.2 else (255, 80, 80))
        if ratio <= 0.2 and (now // 150) % 2 == 0:
            hc = WHITE
        pygame.draw.rect(game.screen, hc, (bx, by, int(bw * ratio), 12), border_radius=5)
        pygame.draw.rect(game.screen, (255, 80, 80), (bx - 2, by - 2, bw + 4, 16), 2, border_radius=6)
        bf = _f(14, bold=True)
        lbl = bf.render(f"BOSS  {boss.hp}/{boss.max_hp}", True, WHITE)
        game.screen.blit(lbl, lbl.get_rect(center=(WIDTH // 2, by + 6)))

    # Boss prep phase overlay
    if game.boss_fight and getattr(game, 'boss_prep_active', False):
        ms_left   = max(0, getattr(game, 'boss_prep_end', now) - now)
        secs_left = max(0, (ms_left + 999) // 1000)

        # Pulsing shield ring around boss
        if game.boss_entity:
            bpos = game.boss_entity.rect.center
            sa   = 80 + int(60 * math.sin(now * 0.006))
            ss   = pygame.Surface((140, 140), pygame.SRCALPHA)
            pygame.draw.circle(ss, (80, 200, 255, sa), (70, 70), 65, 5)
            game.screen.blit(ss, (bpos[0] - 70, bpos[1] - 70))

        # Bottom info panel
        ov_w, ov_h = WIDTH - 40, 108
        ov_x, ov_y = 20, HEIGHT - ov_h - 35
        ov = pygame.Surface((ov_w, ov_h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        game.screen.blit(ov, (ov_x, ov_y))
        pygame.draw.rect(game.screen, RED, (ov_x, ov_y, ov_w, ov_h), 2, border_radius=8)

        # Countdown
        cf     = _f(26, bold=True)
        ct_col = YELLOW if (now // 300) % 2 == 0 else (255, 100, 0)
        cstr   = f"BOSS INCOMING: {secs_left}s"
        cs     = cf.render(cstr, True, ct_col)
        csh    = cf.render(cstr, True, (50, 30, 0))
        game.screen.blit(csh, csh.get_rect(center=(WIDTH // 2 + 2, ov_y + 18)))
        game.screen.blit(cs,  cs.get_rect(center=(WIDTH // 2, ov_y + 16)))

        # Tips
        tf   = _f(13)
        tips = [
            "Shoot LASER at the boss to deal damage!",
            "Dodge the boss's purple projectiles!",
            "At 50% HP: boss fires extra missiles!",
        ]
        for i, tip in enumerate(tips):
            ts2 = tf.render(f"• {tip}", True, WHITE)
            game.screen.blit(ts2, ts2.get_rect(center=(WIDTH // 2, ov_y + 44 + i * 22)))

    # Boss Hearts HUD  (♥♥♥)
    upgrades = game.asset_manager.stats.get('unlocked_upgrades', [])
    if game.boss_fight and 'boss_hearts' in upgrades:
        lives = getattr(game, 'boss_lives', 3)
        inv   = getattr(game, 'boss_invincible_timer', 0)
        hx    = 20
        hy_h  = y_off + 6
        hf    = _f(22, bold=True)
        for i in range(3):
            if i < lives:
                # nhip nhanh khi con 1 mang
                if lives == 1 and (now // 200) % 2 == 0:
                    col = (255, 80, 80)
                else:
                    col = (230, 30, 30)
            else:
                col = (60, 60, 60)
            hs2 = hf.render("♥", True, col)
            game.screen.blit(hs2, (hx + i * 26, hy_h))
        # flash trang khi bi thuong
        if inv > 0 and (now // 80) % 2 == 0:
            fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fl.fill((255, 0, 0, 45))
            game.screen.blit(fl, (0, 0))

    # Settings button (top-right)
    draw_settings_btn(game)

    # God mode indicator
    if getattr(game, 'god_mode', False):
        gf = _f(15, bold=True)
        now_ms = pygame.time.get_ticks()
        gc = YELLOW if (now_ms // 400) % 2 == 0 else GREEN
        gs = gf.render("GOD MODE", True, gc)
        gsh = gf.render("GOD MODE", True, (30, 80, 0))
        game.screen.blit(gsh, (WIDTH // 2 - gs.get_width() // 2 + 1, HEIGHT - 58))
        game.screen.blit(gs,  (WIDTH // 2 - gs.get_width() // 2, HEIGHT - 59))


# ============================================================= LOBBY
def draw_lobby(game):
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 100))
    game.screen.blit(ov, (0, 0))

    # Title
    ts = game.large_font.render("ACTION BIRD", True, YELLOW)
    sh = game.large_font.render("ACTION BIRD", True, (50, 50, 0))
    game.screen.blit(sh, sh.get_rect(center=(WIDTH // 2 + 4, 104)))
    game.screen.blit(ts, ts.get_rect(center=(WIDTH // 2, 100)))

    # High score (blink on new record)
    hc = WHITE
    if game.new_record_flag:
        hc = YELLOW if (pygame.time.get_ticks() // 200) % 2 == 0 else WHITE
    hs = game.medium_font.render(f"BEST: {game.asset_manager.stats['high_score']}", True, hc)
    game.screen.blit(hs, hs.get_rect(center=(WIDTH // 2, 170)))

    draw_button(game, "START GAME", WIDTH//2-100, 260, 200, 50, BLUE,   (100,180,255))
    draw_button(game, "SHOP",       WIDTH//2-100, 330, 200, 50, PURPLE, (200,100,255))
    draw_button(game, "AWARDS",     WIDTH//2-100, 400, 200, 50, ORANGE, (255,180,50))
    draw_button(game, "SETTINGS",   WIDTH//2-100, 470, 200, 50, GRAY,   (200,200,200))
    draw_button(game, "QUIT GAME",  WIDTH//2-100, 535, 200, 45,
                (140, 25, 25), (220, 60, 60))
    draw_settings_btn(game)

    # Daily reward overlay on top
    if getattr(game, 'daily_reward_pending', False):
        draw_daily_reward_overlay(game)

    # Quit confirmation overlay
    if getattr(game, '_quit_confirm', False):
        _draw_quit_confirm(game)


def _draw_quit_confirm(game):
    """Overlay xác nhận thoát game."""
    # Tối phông
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    game.screen.blit(ov, (0, 0))

    # Panel
    pw, ph = 280, 180
    px, py = WIDTH // 2 - pw // 2, HEIGHT // 2 - ph // 2
    panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel.fill((15, 8, 8, 240))
    game.screen.blit(panel, (px, py))
    pygame.draw.rect(game.screen, (200, 40, 40), (px, py, pw, ph), 2, border_radius=12)

    # Icon cảnh báo
    now = pygame.time.get_ticks()
    pulse = 0.8 + 0.2 * math.sin(now * 0.006)
    icon_f = _f(32, bold=True)
    icon_s = icon_f.render("!", True, (int(255 * pulse), int(60 * pulse), 0))
    game.screen.blit(icon_s, icon_s.get_rect(center=(WIDTH // 2, py + 36)))

    # Text
    tf = _f(17, bold=True)
    t1 = tf.render("Leave Game?", True, WHITE)
    game.screen.blit(t1, t1.get_rect(center=(WIDTH // 2, py + 72)))
    sf = _f(13)
    t2 = sf.render("Progress will be saved.", True, GRAY)
    game.screen.blit(t2, t2.get_rect(center=(WIDTH // 2, py + 96)))

    # Nút YES / NO
    draw_button(game, "YES, QUIT", WIDTH // 2 - 105, py + ph - 58, 90, 40,
                (160, 25, 25), (220, 60, 60))
    draw_button(game, "STAY",     WIDTH // 2 + 15,  py + ph - 58, 90, 40,
                (30, 100, 30),  (60, 190, 60))

# ============================================================= DAILY REWARD
def draw_daily_reward_overlay(game):
    # Dark backdrop
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 200))
    game.screen.blit(ov, (0, 0))

    pw, ph = 320, 370
    px, py = WIDTH // 2 - pw // 2, HEIGHT // 2 - ph // 2

    draw_panel(game, px, py, pw, ph, "TODAY'S REWARD!")

    streak  = game.daily_reward_streak
    reward  = game.daily_reward_amount
    rewards = [30, 50, 75, 100, 150, 200, 300]

    # Title
    tf = _f(20, bold=True)
    ts = tf.render("LOGIN STREAK", True, YELLOW)
    game.screen.blit(ts, ts.get_rect(center=(WIDTH // 2, py + 28)))

    # 7-day streak bar
    box_w, box_h = 36, 44
    gap   = 6
    total_w = 7 * box_w + 6 * gap
    sx    = WIDTH // 2 - total_w // 2
    sy    = py + 58
    df    = _f(11, bold=True)
    rf    = _f(12, bold=True)
    day_labels = ['MON','TUE','WED','THU','FRI','SAT','SUN']

    for i in range(7):
        bx   = sx + i * (box_w + gap)
        done = i < streak
        active = i == streak - 1
        col  = GOLD if done else (60, 60, 80)
        pygame.draw.rect(game.screen, col, (bx, sy, box_w, box_h), border_radius=6)
        if active:
            pygame.draw.rect(game.screen, WHITE, (bx, sy, box_w, box_h), 2, border_radius=6)
        # day label
        dl = df.render(day_labels[i], True, WHITE if done else GRAY)
        game.screen.blit(dl, dl.get_rect(center=(bx + box_w // 2, sy + 10)))
        # reward amount
        rv = rf.render(f"+{rewards[i]}", True, WHITE if done else (100,100,100))
        game.screen.blit(rv, rv.get_rect(center=(bx + box_w // 2, sy + 30)))

    # Big reward display
    now   = pygame.time.get_ticks()
    scale = 1.0 + 0.05 * math.sin(now * 0.003)
    coin_r = int(28 * scale)
    cx, cy_coin = WIDTH // 2, py + 155
    pygame.draw.circle(game.screen, GOLD,   (cx, cy_coin), coin_r)
    pygame.draw.circle(game.screen, YELLOW, (cx, cy_coin), coin_r - 4)
    pygame.draw.circle(game.screen, GOLD,   (cx, cy_coin), coin_r - 8)
    hf = _f(36, bold=True)
    hs = hf.render(f"+{reward}", True, GOLD)
    game.screen.blit(hs, hs.get_rect(center=(cx, cy_coin + 48)))
    sf2 = _f(16)
    game.screen.blit(sf2.render("CREDITS", True, YELLOW),
                     sf2.render("CREDITS", True, YELLOW).get_rect(center=(cx, cy_coin + 78)))

    # Streak info
    stk_f = _f(15)
    stk_s = stk_f.render(f"Day Streak: {streak}  -  Max: {game.asset_manager.stats.get('max_streak',0)}", True, CYAN)
    game.screen.blit(stk_s, stk_s.get_rect(center=(cx, py + 215)))

    draw_button(game, "CLAIM REWARD!", cx - 90, py + 240, 180, 48, (0, 160, 80), (0, 210, 110))

# ============================================================= TUTORIAL
def draw_tutorial(game):
    step   = getattr(game, 'tutorial_step', 0)
    total  = 5

    # Full-screen dark overlay on background
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 210))
    game.screen.blit(ov, (0, 0))

    titles = [
        "WELCOME!",
        "SPECIAL POWER-UPS",
        "LASER BEAM",
        "BOSS FIGHT",
        "READY?",
    ]
    title_surf = _render_fit(game.large_font, titles[step], YELLOW,        WIDTH - 24)
    title_sh   = _render_fit(game.large_font, titles[step], (60, 50, 0),   WIDTH - 24)
    game.screen.blit(title_sh,   title_sh.get_rect(center=(WIDTH // 2 + 2, 82)))
    game.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2,   80)))

    # Dot progress indicator
    for i in range(total):
        col = WHITE if i == step else GRAY
        pygame.draw.circle(game.screen, col, (WIDTH // 2 - (total - 1) * 12 + i * 24, 125), 6 if i == step else 4)

    now = pygame.time.get_ticks()
    sf  = _f(16)

    if step == 0:  # Controls
        # Animated bird
        bob = int(math.sin(now * 0.004) * 10)
        bird_img = game.asset_manager.get_skin_image(game.asset_manager.stats['current_skin'])
        if bird_img:
            bi = pygame.transform.scale(bird_img, (55, 55))
            game.screen.blit(bi, bi.get_rect(center=(WIDTH // 2, 220 + bob)))

        # Tap indicators
        left_s  = pygame.Surface((WIDTH // 2 - 10, HEIGHT // 2 - 20), pygame.SRCALPHA)
        right_s = pygame.Surface((WIDTH // 2 - 10, HEIGHT // 2 - 20), pygame.SRCALPHA)
        left_s.fill((0, 200, 255, 30)); right_s.fill((255, 120, 0, 30))
        game.screen.blit(left_s,  (5,  300))
        game.screen.blit(right_s, (WIDTH // 2 + 5, 300))

        lines = [
            "Tap LEFT half of screen to JUMP",
            "Tap RIGHT half to SHOOT LASER",
            "Avoid hitting pipes to survive!",
            "Each pipe passed = +1 point",
        ]
        y = 305
        for ln in lines:
            s = sf.render(ln, True, WHITE)
            game.screen.blit(s, s.get_rect(center=(WIDTH // 2, y)))
            y += 28

    elif step == 1:  # Power-ups
        from entities import Item
        icons_y = 210
        spacing = 80
        x_start = WIDTH // 2 - spacing * 1.5
        for i, itype in enumerate(['LASER', 'GHOST', 'SLOW', 'GIANT']):
            tmp = Item(0, 0, itype)
            ix  = int(x_start + i * spacing)
            bob = int(math.sin(now * 0.004 + i * 1.2) * 5)
            game.screen.blit(tmp.image, tmp.image.get_rect(center=(ix, icons_y + bob)))

        descs = {
            'LASER': ("LASER", "Shoot beam\nbreak pipes"),
            'GHOST': ("GHOST", "Phase\nthrough pipes"),
            'SLOW':  ("SLOW",  "Slow down\neverything"),
            'GIANT': ("GIANT", "Grow huge\nsmash pipes"),
        }
        df  = _f(13, bold=True)
        df2 = _f(12)
        for i, (k, (nm, desc)) in enumerate(descs.items()):
            ix = int(x_start + i * spacing)
            ns = df.render(nm, True, YELLOW)
            game.screen.blit(ns, ns.get_rect(center=(ix, icons_y + 38)))
            for j, dl in enumerate(desc.split('\n')):
                ds = df2.render(dl, True, WHITE)
                game.screen.blit(ds, ds.get_rect(center=(ix, icons_y + 56 + j * 16)))

        hint = sf.render("Collect power-ups as you fly through!", True, CYAN)
        game.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 365)))
        hint2 = sf.render("Each power-up lasts 5 seconds.", True, GRAY)
        game.screen.blit(hint2, hint2.get_rect(center=(WIDTH // 2, 395)))

    elif step == 2:  # Laser
        # Mini animation: bird → laser → pipe exploding
        t = (now % 2000) / 2000
        # Bird
        bird_img = game.asset_manager.get_skin_image(game.asset_manager.stats['current_skin'])
        if bird_img:
            bi = pygame.transform.scale(bird_img, (45, 45))
            game.screen.blit(bi, bi.get_rect(midleft=(30, 270)))
        # Laser beam
        beam_len = int(220 * min(1, t * 3))
        if beam_len > 0:
            pygame.draw.rect(game.screen, RED,   (75, 268, beam_len, 6))
            pygame.draw.rect(game.screen, WHITE, (75, 270, beam_len, 2))
        # Pipe fragment (explosion)
        if t > 0.4:
            ex = 75 + beam_len
            for _ in range(6):
                import random
                seed = int(t * 1000)
                rx = ex + (seed * 7  + _ * 13) % 30 - 15
                ry = 260 + (seed * 11 + _ * 17) % 30 - 15
                pygame.draw.rect(game.screen, (70,185,70), (rx, ry, 8, 8))
        lines = [
            "Collect the LASER power-up first",
            "Tap the RIGHT half of the screen to shoot",
            "Laser destroys the pipe it hits and scores points",
            "Chain hits quickly for a COMBO multiplier!",
        ]
        y = 330
        for ln in lines:
            s = sf.render(ln, True, WHITE)
            game.screen.blit(s, s.get_rect(center=(WIDTH // 2, y)))
            y += 28

    elif step == 3:  # Boss
        from entities import _make_boss_image
        if not hasattr(game, '_tutorial_boss_surf'):
            game._tutorial_boss_surf = pygame.transform.scale(_make_boss_image(), (72, 72))
        bx, by = WIDTH // 2, 230
        bob = int(math.sin(now * 0.003) * 8)
        bs_surf = game._tutorial_boss_surf
        game.screen.blit(bs_surf, bs_surf.get_rect(center=(bx, by + bob)))
        # HP bar above boss
        pygame.draw.rect(game.screen, (60, 0, 0), (bx - 40, by - 52 + bob, 80, 10), border_radius=4)
        pygame.draw.rect(game.screen, RED,         (bx - 40, by - 52 + bob, 50, 10), border_radius=4)
        bf2 = _f(12, bold=True)
        bs  = bf2.render("BOSS  6/10", True, WHITE)
        game.screen.blit(bs, bs.get_rect(center=(bx, by - 58 + bob)))

        lines = [
            "Every 50 points, a BOSS appears!",
            "Use LASER to shoot the boss down",
            "Defeat boss: +5 points and +50 credits",
            "Watch out: the boss shoots projectiles!",
        ]
        y = 330
        for ln in lines:
            s = sf.render(ln, True, WHITE)
            game.screen.blit(s, s.get_rect(center=(WIDTH // 2, y)))
            y += 28

    else:  # step == 4 — Ready
        star_t = now * 0.001
        for i in range(8):
            angle = star_t + i * math.pi / 4
            r = 80 + 20 * math.sin(star_t * 2 + i)
            sx2 = int(WIDTH // 2 + r * math.cos(angle))
            sy2 = int(280 + r * 0.5 * math.sin(angle))
            pygame.draw.circle(game.screen, YELLOW, (sx2, sy2), 4)

        bird_img = game.asset_manager.get_skin_image(game.asset_manager.stats['current_skin'])
        if bird_img:
            scale = 1.0 + 0.08 * math.sin(now * 0.004)
            sz = int(65 * scale)
            bi = pygame.transform.scale(bird_img, (sz, sz))
            game.screen.blit(bi, bi.get_rect(center=(WIDTH // 2, 280)))

        lines = [
            "Visit SHOP to buy SKINS and UPGRADES",
            "Complete ACHIEVEMENTS to earn Credits",
            "Log in every day to claim DAILY REWARDS",
        ]
        y = 345
        for ln in lines:
            s = sf.render(ln, True, WHITE)
            game.screen.blit(s, s.get_rect(center=(WIDTH // 2, y)))
            y += 28

    # Navigation buttons
    skip_f = _f(16, bold=True)
    draw_button(game, "SKIP", WIDTH - 110, 10, 100, 34, GRAY, (200, 200, 200), font=skip_f)

    if step > 0:
        draw_button(game, "< BACK", 20, HEIGHT - 70, 140, 44, GRAY, (200, 200, 200), font=skip_f)

    next_label = "PLAY NOW! >" if step == total - 1 else "NEXT >"
    next_col   = (0, 160, 80) if step == total - 1 else BLUE
    draw_button(game, next_label, WIDTH - 175, HEIGHT - 70, 155, 44, next_col,
                (0, 210, 110) if step == total - 1 else (100, 180, 255), font=skip_f)

# ============================================================= SETTINGS
def draw_settings(game):
    source = getattr(game, '_settings_source', 'LOBBY')
    panel_h = 440 if source == 'PAUSED' else 400
    draw_panel(game, 40, 100, WIDTH - 80, panel_h, "SETTINGS")

    vl = game.font.render(f"Volume: {int(config.master_volume * 100)}%", True, WHITE)
    game.screen.blit(vl, (70, 180))
    draw_button(game, "-", 250, 175, 40, 40, RED,  (255, 100, 100))
    draw_button(game, "+", 310, 175, 40, 40, BLUE, (100, 200, 255))

    bl = game.font.render("Music:", True, WHITE)
    game.screen.blit(bl, (70, 250))
    bc = BLUE if config.bgm_enabled else RED
    draw_button(game, "ON" if config.bgm_enabled else "OFF", 250, 245, 100, 40, bc, (150, 150, 255))

    draw_button(game, "BACK", WIDTH // 2 - 60, 420, 120, 40, GRAY, (220, 220, 220))
    if source == 'PAUSED':
        draw_button(game, "RETURN TO LOBBY", WIDTH // 2 - 80, 472, 160, 40, RED, (255, 100, 100))

# ============================================================= SHOP
def _skin_row(game, skin, y):
    """Draw one skin card spanning the full panel width."""
    stats    = game.asset_manager.stats
    key      = skin['key']
    price    = skin['price']
    owned    = key in stats['unlocked_skins']
    equipped = stats['current_skin'] == key
    now      = pygame.time.get_ticks()

    card_x, card_w, card_h = 22, 356, 48
    card_rect = pygame.Rect(card_x, y, card_w, card_h)
    hovered   = card_rect.collidepoint(pygame.mouse.get_pos())
    btn_col   = skin['btn_color']

    # Card background
    bg = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    if equipped:
        bg.fill((btn_col[0] // 4, btn_col[1] // 4, btn_col[2] // 4, 230))
    elif hovered:
        bg.fill((35, 35, 55, 210))
    else:
        bg.fill((15, 15, 25, 195))
    game.screen.blit(bg, card_rect.topleft)

    # Left color stripe
    pygame.draw.rect(game.screen, btn_col, (card_x, y, 4, card_h), border_radius=2)

    # Card border
    if equipped:
        border_col = YELLOW
    elif hovered:
        border_col = (min(255, btn_col[0] // 2 + 80), min(255, btn_col[1] // 2 + 80), min(255, btn_col[2] // 2 + 80))
    else:
        border_col = (45, 45, 70)
    pygame.draw.rect(game.screen, border_col, card_rect, 2, border_radius=8)

    # Color circle + bird preview
    cx, cy = card_x + 30, y + card_h // 2
    bob = int(math.sin(now * 0.004) * 3) if equipped else 0
    pygame.draw.circle(game.screen, btn_col, (cx, cy + bob), 16)
    ring_col = (240, 220, 80) if equipped else (100, 100, 150)
    pygame.draw.circle(game.screen, ring_col, (cx, cy + bob), 16, 1)
    img = game.asset_manager.get_skin_image(key)
    if img:
        bi = pygame.transform.smoothscale(img, (24, 24))
        game.screen.blit(bi, bi.get_rect(center=(cx, cy + bob)))

    # Skin name
    name_f = _f(15, bold=True)
    ns = name_f.render(skin['name'], True, YELLOW if equipped else WHITE)
    game.screen.blit(ns, (card_x + 54, y + 8))

    # Status badge (right-aligned)
    badge_f = _f(13, bold=True)
    if equipped:
        badge_text, badge_col = "EQUIPPED", YELLOW
    elif owned:
        badge_text, badge_col = "OWNED", GREEN
    else:
        badge_text, badge_col = f"-{price} HS", GOLD
    bs = badge_f.render(badge_text, True, badge_col)
    game.screen.blit(bs, bs.get_rect(midright=(card_x + card_w - 10, cy)))


def _upgrade_row(game, upg, y):
    """Draw one upgrade row."""
    stats = game.asset_manager.stats
    uid   = upg['id']
    owned = uid in stats.get('unlocked_upgrades', [])
    price = upg['price']
    if owned:
        label, bc, hc = f"{upg['name']}  [ OWNED ]", GRAY, (200, 200, 200)
    else:
        label, bc, hc = f"{upg['name']}  -{price} HS", upg['btn_color'], WHITE
    draw_button(game, label, 32, y, 336, 38, bc, hc)


def draw_shop(game):
    draw_panel(game, 18, 50, WIDTH - 36, HEIGHT - 70, "UPGRADE SHOP")

    stats     = game.asset_manager.stats
    tab       = getattr(game, '_shop_tab', 'SKINS')
    sec_font  = _f(15, bold=True)

    # Credits
    cr = game.font.render(f"Credits: {stats['total_credits']} HS", True, YELLOW)
    game.screen.blit(cr, cr.get_rect(center=(WIDTH // 2, 72)))

    # Tab buttons
    tc_skins = (0, 120, 200) if tab == 'SKINS' else (50, 50, 80)
    tc_upg   = (120, 60, 0) if tab == 'UPGRADES' else (50, 50, 80)
    draw_button(game, "[SKIN]",    22,  92, 170, 30, tc_skins, (0, 160, 255),  font=sec_font)
    draw_button(game, "[UPGRADE]", 208, 92, 170, 30, tc_upg,   (200, 100, 0), font=sec_font)
    pygame.draw.line(game.screen, CYAN, (18, 125), (WIDTH - 18, 125), 1)

    if tab == 'SKINS':
        y = 130
        for skin in SKIN_CATALOG:
            _skin_row(game, skin, y)
            y += 52
        draw_button(game, "BACK", WIDTH // 2 - 55, y + 4, 110, 38, GRAY, (220, 220, 220))

    else:  # UPGRADES
        y = 134
        for item in UPGRADE_CATALOG:
            if 'section' in item:
                sec_s = sec_font.render(f"── {item['section']} ──", True, CYAN)
                game.screen.blit(sec_s, sec_s.get_rect(center=(WIDTH // 2, y + 8)))
                y += 24
            else:
                _upgrade_row(game, item, y)
                y += 46
        draw_button(game, "BACK", WIDTH // 2 - 55, y + 4, 110, 38, GRAY, (220, 220, 220))

# ============================================================= ACHIEVEMENTS
def _parse_progress(desc):
    """Trích xuất giá trị hiện tại và mục tiêu từ chuỗi desc dạng 'X/Y'."""
    import re
    m = re.search(r'(\d+)/(\d+)', desc)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def get_all_achievements(stats):
    d  = stats.get('total_destroyed',   0)
    g  = stats.get('total_ghost_passes',0)
    gi = stats.get('total_giant_uses',  0)
    hs = stats.get('high_score',        0)
    gp = stats.get('total_games_played',0)
    bk = stats.get('total_boss_kills',  0)
    nm = stats.get('total_near_misses', 0)
    mc = stats.get('max_combo',         0)
    cr = stats.get('total_credits',     0)
    sk = stats.get('streak_count',      0)

    return [
        {'id':'destroy_10',  'name':'Pipe Breaker',  'tier':'B','desc':f'Destroy {d}/10 pipes',       'unlocked':d>=10,  'reward':20},
        {'id':'destroy_50',  'name':'Demolisher',    'tier':'S','desc':f'Destroy {d}/50 pipes',       'unlocked':d>=50,  'reward':50},
        {'id':'destroy_200', 'name':'Annihilator',   'tier':'G','desc':f'Destroy {d}/200 pipes',      'unlocked':d>=200, 'reward':150},
        {'id':'ghost_5',     'name':'Phantom',       'tier':'B','desc':f'Ghost pass {g}/5 times',     'unlocked':g>=5,   'reward':15},
        {'id':'ghost_20',    'name':'Ghost Master',  'tier':'S','desc':f'Ghost pass {g}/20 times',    'unlocked':g>=20,  'reward':40},
        {'id':'ghost_100',   'name':'Untouchable',   'tier':'G','desc':f'Ghost pass {g}/100 times',   'unlocked':g>=100, 'reward':120},
        {'id':'giant_5',     'name':'Growing Up',    'tier':'B','desc':f'Use Giant {gi}/5 times',     'unlocked':gi>=5,  'reward':15},
        {'id':'giant_20',    'name':'The Titan',     'tier':'S','desc':f'Use Giant {gi}/20 times',    'unlocked':gi>=20, 'reward':40},
        {'id':'score_10',    'name':'Beginner',      'tier':'B','desc':f'Reach score {hs}/10',        'unlocked':hs>=10, 'reward':10},
        {'id':'score_30',    'name':'Intermediate',  'tier':'S','desc':f'Reach score {hs}/30',        'unlocked':hs>=30, 'reward':30},
        {'id':'score_60',    'name':'Pro Gamer',     'tier':'G','desc':f'Reach score {hs}/60',        'unlocked':hs>=60, 'reward':100},
        {'id':'boss_1',      'name':'Boss Slayer',   'tier':'S','desc':f'Defeat {bk}/1 boss',         'unlocked':bk>=1,  'reward':75},
        {'id':'boss_3',      'name':'Boss Hunter',   'tier':'G','desc':f'Defeat {bk}/3 bosses',       'unlocked':bk>=3,  'reward':200},
        {'id':'combo_3',     'name':'Combo King',    'tier':'S','desc':f'Combo x{mc}/3',              'unlocked':mc>=3,  'reward':30},
        {'id':'combo_5',     'name':'Destroyer God', 'tier':'G','desc':f'Combo x{mc}/5',              'unlocked':mc>=5,  'reward':80},
        {'id':'nearmiss_10', 'name':'Daredevil',     'tier':'S','desc':f'Near miss {nm}/10 times',    'unlocked':nm>=10, 'reward':50},
        {'id':'play_10',     'name':'Committed',     'tier':'B','desc':f'Play {gp}/10 games',         'unlocked':gp>=10, 'reward':20},
        {'id':'play_50',     'name':'Addicted',      'tier':'S','desc':f'Play {gp}/50 games',         'unlocked':gp>=50, 'reward':60},
        {'id':'credits_500', 'name':'Rich Bird',     'tier':'S','desc':f'Earn {cr}/500 credits',      'unlocked':cr>=500,'reward':50},
        {'id':'streak_3',    'name':'3-Day Streak',  'tier':'B','desc':f'Login streak {sk}/3 days',   'unlocked':sk>=3,  'reward':30},
        {'id':'streak_7',    'name':'7-Day Streak',  'tier':'G','desc':f'Login streak {sk}/7 days',   'unlocked':sk>=7,  'reward':150},
    ]


def draw_achievements(game):
    TIER_COL  = {'B': (200, 150, 70), 'S': (200, 200, 240), 'G': (255, 210, 40)}
    TIER_BG   = {'B': (60, 40, 10),   'S': (30, 30, 55),    'G': (60, 50,  5) }
    TIER_LABEL= {'B': 'BRONZE',       'S': 'SILVER',        'G': 'GOLD'       }
    stats        = game.asset_manager.stats
    unlocked_ids = stats.get('unlocked_achievements', [])
    claimed_ids  = stats.setdefault('claimed_achievements',  [])
    all_ach      = get_all_achievements(stats)
    done         = sum(1 for a in all_ach if a['unlocked'])
    total_earned = sum(a['reward'] for a in all_ach if a['id'] in claimed_ids)
    now          = pygame.time.get_ticks()

    # ---- Panel header ----
    draw_panel(game, 18, 55, WIDTH - 36, HEIGHT - 85, "AWARDS")

    hdr_f = _f(15, bold=True)
    hdr   = hdr_f.render(f"Completed: {done}/{len(all_ach)}", True, YELLOW)
    game.screen.blit(hdr, hdr.get_rect(midleft=(30, 82)))
    earned_s = _f(13).render(f"Earned: {total_earned} HS", True, GOLD)
    game.screen.blit(earned_s, earned_s.get_rect(midright=(WIDTH - 28, 82)))

    # ---- Scrollable list ----
    list_top = 105
    list_h   = HEIGHT - 175
    row_h    = 68
    list_surf= pygame.Surface((WIDTH - 36, list_h), pygame.SRCALPHA)
    scroll   = getattr(game, '_ach_scroll', 0)
    y        = -scroll
    name_f   = _f(14, bold=True)
    desc_f   = _f(12)
    tier_f   = _f(10, bold=True)
    claim_f  = _f(12, bold=True)

    for ach in all_ach:
        if y + row_h < 0:   y += row_h; continue
        if y > list_h:      break

        tc       = TIER_COL.get(ach['tier'], WHITE)
        bg_tier  = TIER_BG.get(ach['tier'], (20,20,30))
        is_done  = ach['unlocked']
        is_claimed = ach['id'] in claimed_ids
        is_unlocked_unclaimed = is_done and not is_claimed

        # Card background
        card_w = WIDTH - 52
        card   = pygame.Surface((card_w, row_h - 4), pygame.SRCALPHA)
        if is_done:
            card.fill((*bg_tier, 210))
        else:
            card.fill((10, 10, 18, 200))
        list_surf.blit(card, (8, y + 2))

        # Tier stripe (left)
        pygame.draw.rect(list_surf, tc, (8, y + 2, 4, row_h - 4), border_radius=2)

        # Card border
        border_col = tc if is_done else (45, 45, 65)
        pygame.draw.rect(list_surf, border_col, (8, y + 2, card_w, row_h - 4), 1, border_radius=6)

        # Tier badge circle
        pygame.draw.circle(list_surf, tc,    (30, y + row_h // 2), 14)
        pygame.draw.circle(list_surf, BLACK, (30, y + row_h // 2), 14, 1)
        tl = tier_f.render(ach['tier'], True, BLACK if is_done else (60,60,60))
        list_surf.blit(tl, tl.get_rect(center=(30, y + row_h // 2)))

        # Name + desc
        name_col = tc if is_done else (100, 100, 115)
        ns = name_f.render(ach['name'], True, name_col)
        list_surf.blit(ns, (50, y + 8))
        ds = desc_f.render(ach['desc'], True, WHITE if is_done else (80, 80, 95))
        list_surf.blit(ds, (50, y + 26))

        # Progress bar (only if not done)
        if not is_done:
            cur_v, max_v = _parse_progress(ach['desc'])
            if cur_v is not None and max_v and max_v > 0:
                bar_x, bar_y = 50, y + 44
                bar_w = card_w - 110
                ratio = min(1.0, cur_v / max_v)
                pygame.draw.rect(list_surf, (40, 40, 55), (bar_x, bar_y, bar_w, 8), border_radius=4)
                if ratio > 0:
                    prog_col = (100, 180, 255) if ach['tier'] == 'S' else \
                               (255, 190, 30)  if ach['tier'] == 'G' else (180, 130, 60)
                    pygame.draw.rect(list_surf, prog_col,
                                     (bar_x, bar_y, int(bar_w * ratio), 8), border_radius=4)
                pct_s = _f(11).render(f"{int(ratio*100)}%", True, GRAY)
                list_surf.blit(pct_s, (bar_x + bar_w + 4, bar_y - 1))

        # Right side: CLAIM / CLAIMED / lock icon
        right_x = card_w - 8
        mid_y   = y + row_h // 2

        if is_unlocked_unclaimed:
            # Pulsing CLAIM button
            pulse = 0.85 + 0.15 * math.sin(now * 0.005)
            btn_col = (int(220 * pulse), int(160 * pulse), 0)
            btn_rect_local = pygame.Rect(right_x - 95, y + 20, 90, 28)
            pygame.draw.rect(list_surf, btn_col, btn_rect_local, border_radius=8)
            pygame.draw.rect(list_surf, GOLD, btn_rect_local, 1, border_radius=8)
            rew_s = claim_f.render(f"+{ach['reward']} HS", True, BLACK)
            list_surf.blit(rew_s, rew_s.get_rect(center=btn_rect_local.center))

        elif is_claimed:
            # Green checkmark badge
            chk_rect = pygame.Rect(right_x - 80, y + 18, 75, 28)
            pygame.draw.rect(list_surf, (20, 100, 40), chk_rect, border_radius=8)
            pygame.draw.rect(list_surf, GREEN, chk_rect, 1, border_radius=8)
            ck_s = claim_f.render("✓ CLAIMED", True, GREEN)
            list_surf.blit(ck_s, ck_s.get_rect(center=chk_rect.center))

        else:
            # Lock icon for locked achievements
            lk_s = _f(18).render("🔒", True, (70,70,85))
            list_surf.blit(lk_s, lk_s.get_rect(center=(right_x - 20, mid_y)))

        y += row_h

    game.screen.blit(list_surf, (18, list_top))

    # Scrollbar
    max_scroll = max(0, len(all_ach) * row_h - list_h)
    if max_scroll > 0:
        sb_h   = int(list_h * list_h / (len(all_ach) * row_h))
        sb_y   = int(scroll / max_scroll * (list_h - sb_h))
        pygame.draw.rect(game.screen, (50,50,70),
                         (WIDTH - 22, list_top, 6, list_h), border_radius=3)
        pygame.draw.rect(game.screen, CYAN,
                         (WIDTH - 22, list_top + sb_y, 6, max(20, sb_h)), border_radius=3)

    for ev in pygame.event.get(pygame.MOUSEWHEEL):
        pass  # scroll handled in game.py main loop

    draw_button(game, "BACK", WIDTH // 2 - 55, HEIGHT - 65, 110, 40, GRAY, (220, 220, 220))

# ============================================================= PAUSE / GAME OVER
def draw_paused(game):
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    game.screen.blit(ov, (0, 0))
    ts = game.large_font.render("PAUSED", True, WHITE)
    game.screen.blit(ts, ts.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
    draw_button(game, "RESUME",   WIDTH // 2 - 65, HEIGHT // 2 + 50,  130, 44, BLUE, (100,180,255))
    draw_button(game, "SETTINGS", WIDTH // 2 - 65, HEIGHT // 2 + 105, 130, 44, GRAY, (200,200,200))


def draw_game_over(game):
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((100, 0, 0, 100))
    game.screen.blit(ov, (0, 0))

    ts = game.large_font.render("GAME OVER", True, WHITE)
    game.screen.blit(ts, ts.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 110)))

    stats = game.asset_manager.stats
    draw_panel(game, 55, HEIGHT // 2 - 55, WIDTH - 110, 155)

    game.screen.blit(
        game.medium_font.render(f"SCORE: {game.score}", True, WHITE),
        game.medium_font.render(f"SCORE: {game.score}", True, WHITE).get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
    game.screen.blit(
        game.font.render(f"BEST: {stats['high_score']}", True, YELLOW),
        game.font.render(f"BEST: {stats['high_score']}", True, YELLOW).get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
    game.screen.blit(
        game.font.render(f"CREDITS: {stats['total_credits']} HS", True, CYAN),
        game.font.render(f"CREDITS: {stats['total_credits']} HS", True, CYAN).get_rect(center=(WIDTH//2, HEIGHT//2 + 55)))

    draw_button(game, "RETRY", WIDTH//2-75, HEIGHT//2+125, 150, 50, BLUE, (100,180,255))
    draw_button(game, "LOBBY", WIDTH//2-75, HEIGHT//2+190, 150, 50, GRAY, (180,180,180))
