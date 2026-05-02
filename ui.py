import pygame
from config import *

def draw_button(game, text, x, y, w, h, base_color, hover_color):
    mouse = pygame.mouse.get_pos()
    rect = pygame.Rect(x, y, w, h)
    is_hover = rect.collidepoint(mouse)
    
    color = hover_color if is_hover else base_color
    
    # Draw Shadow
    shadow_rect = rect.copy()
    shadow_rect.y += 4
    pygame.draw.rect(game.screen, (20, 20, 20), shadow_rect, border_radius=12)
    
    # Draw Main Button
    pygame.draw.rect(game.screen, color, rect, border_radius=12)
    
    # Draw Highlight (Top Edge)
    highlight_rect = pygame.Rect(x + 2, y + 2, w - 4, h // 2)
    highlight_surface = pygame.Surface((w - 4, h // 2), pygame.SRCALPHA)
    highlight_surface.fill((255, 255, 255, 40))
    game.screen.blit(highlight_surface, highlight_rect)
    
    # Draw Border
    pygame.draw.rect(game.screen, BLACK, rect, 2, border_radius=12)
    
    # Text with subtle shadow
    text_shadow = game.font.render(text, True, (0, 0, 0, 100))
    text_surf = game.font.render(text, True, WHITE)
    
    text_rect = text_surf.get_rect(center=rect.center)
    shadow_text_rect = text_rect.copy()
    shadow_text_rect.x += 1
    shadow_text_rect.y += 1
    
    game.screen.blit(text_shadow, shadow_text_rect)
    game.screen.blit(text_surf, text_rect)
    
    return is_hover

def draw_panel(game, x, y, w, h, title=""):
    # Glassmorphism effect
    panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    panel_surf.fill((0, 0, 0, 180)) # Semi-transparent black
    game.screen.blit(panel_surf, (x, y))
    
    # Glowing Border
    pygame.draw.rect(game.screen, CYAN, (x, y, w, h), 2, border_radius=5)
    
    if title:
        title_surf = game.font.render(title, True, CYAN)
        game.screen.blit(title_surf, (x + 10, y - 25))

def draw_transition(game):
    if hasattr(game, 'fade_alpha') and game.fade_alpha > 0:
        fade_surf = pygame.Surface((WIDTH, HEIGHT))
        fade_surf.fill(BLACK)
        fade_surf.set_alpha(game.fade_alpha)
        game.screen.blit(fade_surf, (0, 0))

def draw_ui(game):
    if game.state == PLAYING:
        # Score pop animation
        if game.score != game.last_score:
            game.score_scale = 2.0
            game.last_score = game.score
        game.score_scale += (1.0 - game.score_scale) * 0.15

        score_color = YELLOW if game.score_scale > 1.1 else WHITE
        pop_size = int(24 * game.score_scale)
        score_font = pygame.font.SysFont('Arial', pop_size, bold=True)
        score_surf = score_font.render(f"Score: {game.score}", True, score_color)
        game.screen.blit(score_surf, (20, 20))
        
        y_offset = 60
        now = pygame.time.get_ticks()
        
        # Powerup Bars
        for ptype, end_time in list(game.active_powerups.items()):
            time_left = end_time - now
            if time_left > 0:
                is_longer = 'longer_giant' in game.asset_manager.stats.get('unlocked_upgrades', [])
                total_duration = POWERUP_DURATION * 1.5 if (ptype == 'GIANT' and is_longer) else POWERUP_DURATION
                remaining = time_left / total_duration
                
                if ptype == 'LASER': color = RED
                elif ptype == 'GHOST': color = GRAY
                elif ptype == 'SLOW': color = PURPLE
                elif ptype == 'GIANT': color = ORANGE
                else: color = WHITE
                
                # Visual Bar
                pygame.draw.rect(game.screen, (40, 40, 40), (20, y_offset, 120, 12), border_radius=6)
                pygame.draw.rect(game.screen, color, (22, y_offset + 2, 116 * remaining, 8), border_radius=4)
                
                type_surf = game.font.render(ptype, True, WHITE)
                game.screen.blit(type_surf, (150, y_offset - 8))
                y_offset += 30
        
        # Mobile Controls Hint (Lower half of screen, faint)
        if game.score < 5:
            hint_font = pygame.font.SysFont('Arial', 18)
            jump_hint = hint_font.render("TAP LEFT: JUMP", True, (255, 255, 255, 100))
            shoot_hint = hint_font.render("TAP RIGHT: SHOOT", True, (255, 255, 255, 100))
            game.screen.blit(jump_hint, (50, HEIGHT - 100))
            game.screen.blit(shoot_hint, (WIDTH - 180, HEIGHT - 100))

def draw_lobby(game):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 100))
    game.screen.blit(overlay, (0, 0))
    
    title_shadow = game.large_font.render("ACTION BIRD", True, (50, 50, 0))
    title = game.large_font.render("ACTION BIRD", True, YELLOW)
    game.screen.blit(title_shadow, title_shadow.get_rect(center=(WIDTH//2 + 4, 104)))
    game.screen.blit(title, title.get_rect(center=(WIDTH//2, 100)))
    
    hs_color = WHITE
    if game.new_record_flag:
        hs_color = YELLOW if (pygame.time.get_ticks() // 200) % 2 == 0 else WHITE
        
    hs_surf = game.medium_font.render(f"BEST: {game.asset_manager.stats['high_score']}", True, hs_color)
    game.screen.blit(hs_surf, hs_surf.get_rect(center=(WIDTH//2, 170)))
    
    draw_button(game, "START GAME", WIDTH//2 - 100, 260, 200, 50, BLUE, (100, 180, 255))
    draw_button(game, "SHOP", WIDTH//2 - 100, 330, 200, 50, PURPLE, (200, 100, 255))
    draw_button(game, "AWARDS", WIDTH//2 - 100, 400, 200, 50, ORANGE, (255, 180, 50))
    draw_button(game, "SETTINGS", WIDTH//2 - 100, 470, 200, 50, GRAY, (180, 180, 180))

def draw_settings(game):
    draw_panel(game, 40, 100, WIDTH - 80, 400, "SETTINGS")
    
    vol_label = game.font.render(f"Volume: {int(config.master_volume * 100)}%", True, WHITE)
    game.screen.blit(vol_label, (70, 180))
    draw_button(game, "-", 250, 175, 40, 40, RED, (255, 100, 100))
    draw_button(game, "+", 310, 175, 40, 40, BLUE, (100, 200, 255))
        
    bgm_label = game.font.render("Music:", True, WHITE)
    game.screen.blit(bgm_label, (70, 250))
    bgm_status = "ON" if config.bgm_enabled else "OFF"
    bgm_color = BLUE if config.bgm_enabled else RED
    draw_button(game, bgm_status, 250, 245, 100, 40, bgm_color, (150, 150, 255))

    draw_button(game, "BACK", WIDTH//2 - 60, 440, 120, 40, GRAY, (220, 220, 220))

def draw_shop(game):
    draw_panel(game, 30, 80, WIDTH - 60, 480, "UPGRADE SHOP")
    
    stats = game.asset_manager.stats
    money_surf = game.font.render(f"Credits: {stats['total_credits']} HS", True, YELLOW)
    game.screen.blit(money_surf, (WIDTH - 200, 40))

    y = 120
    # Skins...
    orig_label = "ORIGINAL BIRD" if stats['current_skin'] != 'default' else "[ EQUIPPED ]"
    btn_color = BLUE if stats['current_skin'] != 'default' else GRAY
    draw_button(game, orig_label, 50, y, 300, 40, btn_color, WHITE)
        
    y += 55
    red_label = "RED SKIN - 50 HS" if 'red' not in stats['unlocked_skins'] else ("RED BIRD" if stats['current_skin'] != 'red' else "[ EQUIPPED ]")
    btn_color = (150, 50, 50) if 'red' not in stats['unlocked_skins'] else (ORANGE if stats['current_skin'] != 'red' else GRAY)
    draw_button(game, red_label, 50, y, 300, 40, btn_color, RED)
    
    y += 55
    blue_label = "BLUE SKIN - 75 HS" if 'blue' not in stats['unlocked_skins'] else ("BLUE BIRD" if stats['current_skin'] != 'blue' else "[ EQUIPPED ]")
    btn_color = (0, 50, 150) if 'blue' not in stats['unlocked_skins'] else (BLUE if stats['current_skin'] != 'blue' else GRAY)
    draw_button(game, blue_label, 50, y, 300, 40, btn_color, BLUE)
    
    y += 65
    game.screen.blit(game.font.render("--- UPGRADES ---", True, YELLOW), (50, y))
    y += 30
    giant_label = "Longer Giant - 100 HS" if 'longer_giant' not in stats.get('unlocked_upgrades', []) else "Longer Giant - [ OWNED ]"
    giant_color = ORANGE if 'longer_giant' not in stats.get('unlocked_upgrades', []) else GRAY
    draw_button(game, giant_label, 50, y, 300, 40, giant_color, RED)
    
    y += 65
    game.screen.blit(game.font.render("--- AURAS ---", True, PURPLE), (50, y))
    y += 30
    fire_label = "Fire Aura - 200 HS" if 'fire_aura' not in stats.get('unlocked_upgrades', []) else "Fire Aura - [ OWNED ]"
    fire_color = PURPLE if 'fire_aura' not in stats.get('unlocked_upgrades', []) else GRAY
    draw_button(game, fire_label, 50, y, 300, 40, fire_color, RED)
    
    draw_button(game, "BACK", WIDTH//2 - 50, 540, 100, 40, GRAY, (220, 220, 220))

def draw_achievements(game):
    draw_panel(game, 30, 80, WIDTH - 60, 420, "AWARDS")
    
    stats = game.asset_manager.stats
    achievements = [
        ("Tube Hunter", f"Destroy {stats['total_destroyed']}/100 Pipes", stats['total_destroyed'] >= 100),
        ("Ghost Student", f"Ghost Pass {stats['total_ghost_passes']}/20 Times", stats['total_ghost_passes'] >= 20),
        ("The Giant", f"Use Giant {stats['total_giant_uses']}/10 Times", stats['total_giant_uses'] >= 10)
    ]
    
    y = 150
    for name, desc, unlocked in achievements:
        color = YELLOW if unlocked else GRAY
        name_surf = game.font.render(name, True, color)
        desc_surf = game.font.render(desc, True, WHITE)
        game.screen.blit(name_surf, (60, y))
        game.screen.blit(desc_surf, (60, y + 25))
        if unlocked:
            pygame.draw.circle(game.screen, YELLOW, (45, y + 12), 6)
        y += 80
        
    draw_button(game, "BACK", WIDTH//2 - 50, 520, 100, 40, GRAY, (220, 220, 220))

def draw_paused(game):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    game.screen.blit(overlay, (0, 0))

    title = game.large_font.render("PAUSED", True, WHITE)
    game.screen.blit(title, title.get_rect(center=(WIDTH//2, HEIGHT//2 - 40)))
    
    draw_button(game, "RESUME", WIDTH//2 - 60, HEIGHT//2 + 50, 120, 40, BLUE, (100, 180, 255))

def draw_game_over(game):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((100, 0, 0, 100))
    game.screen.blit(overlay, (0, 0))
    
    msg = game.large_font.render("GAME OVER", True, WHITE)
    game.screen.blit(msg, msg.get_rect(center=(WIDTH//2, HEIGHT//2 - 100)))
    
    stats = game.asset_manager.stats
    draw_panel(game, 60, HEIGHT//2 - 40, WIDTH - 120, 140)
    
    score_msg = game.medium_font.render(f"SCORE: {game.score}", True, WHITE)
    best_msg = game.font.render(f"BEST: {stats['high_score']}", True, YELLOW)
    credits_msg = game.font.render(f"TOTAL CREDITS: {stats['total_credits']}", True, CYAN)
    
    game.screen.blit(score_msg, score_msg.get_rect(center=(WIDTH//2, HEIGHT//2)))
    game.screen.blit(best_msg, best_msg.get_rect(center=(WIDTH//2, HEIGHT//2 + 40)))
    game.screen.blit(credits_msg, credits_msg.get_rect(center=(WIDTH//2, HEIGHT//2 + 75)))
    
    draw_button(game, "RETRY", WIDTH//2 - 70, HEIGHT//2 + 130, 140, 50, BLUE, (100, 180, 255))
    draw_button(game, "LOBBY", WIDTH//2 - 70, HEIGHT//2 + 200, 140, 50, GRAY, (180, 180, 180))
