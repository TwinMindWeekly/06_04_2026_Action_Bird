import pygame
import random
import os
from config import *
from asset_manager import AssetManager
from entities import Bird, Tube, Cloud, Item, Laser, TrailEffect, FloatingText, Missile, Boss, EnergyBall, Particle
import ui

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Action Bird")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24, bold=True)
        self.medium_font = pygame.font.SysFont('Arial', 32, bold=True)
        self.large_font = pygame.font.SysFont('Arial', 48, bold=True)
        
        self.asset_manager = AssetManager()
        self.asset_manager.load_assets()

        self.new_record_flag = False 
        self.reset_game()

    def handle_game_over(self):
        if self.state != GAME_OVER:
            self.shake_timer = 40 # Strong shake on death
            self.asset_manager.play_sound('die')
            
            stats = self.asset_manager.stats
            if self.score > stats['high_score']:
                stats['high_score'] = self.score
                self.new_record_flag = True
            
            if not self.reward_given:
                stats['total_credits'] += self.score
                self.reward_given = True
            
            self.asset_manager.save_stats()
            self.change_state(GAME_OVER)

    def apply_current_skin(self):
        new_img = self.asset_manager.get_skin_image(self.asset_manager.stats['current_skin'])
        if hasattr(self, 'bird'):
            self.bird.original_image = new_img
            self.bird.image = new_img
            if self.bird.is_giant:
                self.bird.base_image = pygame.transform.scale(new_img, (70, 70))
            else:
                self.bird.base_image = new_img.copy()
            self.bird.mask = pygame.mask.from_surface(self.bird.image)

    def reset_game(self):
        self.state = LOBBY
        self.score = 0
        self.tube_velocity = INITIAL_TUBE_VELOCITY
        
        bird_skin = self.asset_manager.get_skin_image(self.asset_manager.stats['current_skin'])
        self.bird = Bird(50, HEIGHT // 2, bird_skin)
        self.all_sprites = pygame.sprite.Group(self.bird)
        self.tubes = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.lasers = pygame.sprite.Group()
        self.trails = pygame.sprite.Group()
        self.floating_texts = pygame.sprite.Group()
        
        self.particles = pygame.sprite.Group()
        self.missiles = pygame.sprite.Group()
        self.energy_balls = pygame.sprite.Group()
        self.tube_timer = 0
        self.cloud_timer = 0
        
        self.active_powerups = {}
        self.shake_timer = 0
        self.boss_fight = False
        self.boss_entity = None
        self._boss_spawned_score = -1
        
        self.combo_count = 0
        self.last_destruction_time = 0
        self.near_miss_tubes = set() 
        self.reward_given = False 
        self.score_scale = 1.0
        self.last_score = 0
        
        # UI/UX Transition & Shake
        self.fade_alpha = 0
        self.fade_speed = 10
        self.fade_mode = 'NONE' # NONE, IN, OUT
        self.target_state = None
        self.temp_surface = pygame.Surface((WIDTH, HEIGHT))
        
        if self.asset_manager.music_file:
            pygame.mixer.music.stop()

    def change_state(self, next_state):
        if self.fade_mode == 'NONE':
            self.target_state = next_state
            self.fade_mode = 'OUT'

    def spawn_tubes(self):
        if len(self.missiles) > 0: return False
        if len(self.tubes) > 0:
            last_tube = max(self.tubes, key=lambda t: t.rect.right)
            if WIDTH - last_tube.rect.right < 250: return False

        h = random.randint(100, 300)
        is_moving = self.score > 30 and random.random() < 0.6
            
        top_tube = Tube(WIDTH, h, True, is_moving)
        bottom_tube = Tube(WIDTH, h, False, is_moving)
        pair_id = pygame.time.get_ticks()
        top_tube.pair_id = pair_id
        bottom_tube.pair_id = pair_id
        
        self.tubes.add(top_tube, bottom_tube)
        self.all_sprites.add(top_tube, bottom_tube)
        
        if random.random() < ITEM_CHANCE:
            item_type = random.choice(['LASER', 'GHOST', 'SLOW', 'GIANT'])
            item = Item(WIDTH + TUBE_WIDTH//2, h + TUBE_GAP//2, item_type)
            self.items.add(item); self.all_sprites.add(item)
        return True

    def handle_powerup(self, type):
        duration = POWERUP_DURATION
        if type == 'GIANT' and 'longer_giant' in self.asset_manager.stats.get('unlocked_upgrades', []):
            duration = int(POWERUP_DURATION * 1.5)
        self.active_powerups[type] = pygame.time.get_ticks() + duration
        self.asset_manager.play_sound('collect', self.combo_count)
        if type == 'GIANT': self.asset_manager.stats['total_giant_uses'] += 1
        is_p_active = any(v > pygame.time.get_ticks() for v in self.active_powerups.values())
        self.asset_manager.update_volumes(is_powerup_active=is_p_active)

    def shoot_laser(self):
        if 'LASER' in self.active_powerups:
            self.asset_manager.play_sound('laser', self.combo_count)
            new_laser = Laser((self.bird.rect.right, self.bird.rect.centery))
            self.lasers.add(new_laser); self.all_sprites.add(new_laser)
            
            hit_tubes = pygame.sprite.spritecollide(new_laser, self.tubes, True)
            hit_something = False
            if hit_tubes:
                self.asset_manager.stats['total_destroyed'] += len(hit_tubes)
                hit_something = True
                
            missiles = [s for s in self.all_sprites if isinstance(s, Missile) and s.warning_timer <= 0]
            hit_m = pygame.sprite.spritecollide(new_laser, pygame.sprite.Group(missiles), True)
            if hit_m: hit_something = True

            if getattr(self, 'boss_fight', False) and self.boss_entity in self.all_sprites:
                if pygame.sprite.collide_rect(new_laser, self.boss_entity):
                    hit_something = True
                    if self.boss_entity.take_damage():
                        self.boss_entity.kill(); self.boss_fight = False; self.score += 5
                        self.asset_manager.stats['total_credits'] += 50
                        if 'LASER' in self.active_powerups: del self.active_powerups['LASER']
                        for _ in range(3):
                            it = random.choice(['LASER', 'GHOST', 'SLOW', 'GIANT'])
                            item = Item(self.boss_entity.rect.centerx + random.randint(-20, 20), self.boss_entity.rect.centery + random.randint(-20, 20), it)
                            self.items.add(item); self.all_sprites.add(item)

            if hit_something:
                now = pygame.time.get_ticks()
                if now - self.last_destruction_time < 2000: self.combo_count += 1
                else: self.combo_count = 1
                self.last_destruction_time = now; self.score += 1 * self.combo_count
                if self.combo_count > 1:
                    ft = FloatingText(self.bird.rect.right, self.bird.rect.top - 20, f"COMBO X{self.combo_count}", RED, self.medium_font)
                    self.floating_texts.add(ft); self.all_sprites.add(ft)
                self.asset_manager.play_sound('explosion', self.combo_count)
                self.shake_timer = 20 # Shake on explosion
                pygame.time.delay(30) 

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            now = pygame.time.get_ticks()
            
            # --- Fade Transition Logic ---
            if self.fade_mode == 'OUT':
                self.fade_alpha += self.fade_speed
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255; self.fade_mode = 'IN'
                    if self.target_state == PLAYING and self.state != PLAYING:
                        self.reset_game(); self.state = PLAYING
                        if self.asset_manager.music_file and config.bgm_enabled:
                            try: pygame.mixer.music.load(self.asset_manager.music_file); pygame.mixer.music.play(-1)
                            except: pass
                    else:
                        if self.target_state == LOBBY: pygame.mixer.music.stop()
                        self.state = self.target_state
                    self.asset_manager.update_volumes()
            elif self.fade_mode == 'IN':
                self.fade_alpha -= self.fade_speed
                if self.fade_alpha <= 0: self.fade_alpha = 0; self.fade_mode = 'NONE'

            # --- Events ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if self.fade_mode == 'NONE':
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = event.pos
                        if self.state == LOBBY:
                            if pygame.Rect(WIDTH//2 - 100, 260, 200, 50).collidepoint(mouse_pos): self.change_state(PLAYING)
                            elif pygame.Rect(WIDTH//2 - 100, 330, 200, 50).collidepoint(mouse_pos): self.change_state(SHOP)
                            elif pygame.Rect(WIDTH//2 - 100, 400, 200, 50).collidepoint(mouse_pos): self.change_state(ACHIEVEMENTS)
                            elif pygame.Rect(WIDTH//2 - 100, 470, 200, 50).collidepoint(mouse_pos): self.change_state(SETTINGS)
                        elif self.state == SETTINGS:
                            if pygame.Rect(250, 175, 40, 40).collidepoint(mouse_pos):
                                config.master_volume = max(0.0, config.master_volume - 0.1); self.asset_manager.update_volumes()
                            elif pygame.Rect(310, 175, 40, 40).collidepoint(mouse_pos):
                                config.master_volume = min(1.0, config.master_volume + 0.1); self.asset_manager.update_volumes()
                            elif pygame.Rect(250, 245, 100, 40).collidepoint(mouse_pos):
                                config.bgm_enabled = not config.bgm_enabled
                                if not config.bgm_enabled: pygame.mixer.music.stop()
                                elif self.asset_manager.music_file: 
                                    try: pygame.mixer.music.load(self.asset_manager.music_file); pygame.mixer.music.play(-1)
                                    except: pass
                            elif pygame.Rect(WIDTH//2 - 60, 440, 120, 40).collidepoint(mouse_pos): self.change_state(LOBBY)
                        elif self.state == SHOP:
                            stats = self.asset_manager.stats
                            if pygame.Rect(50, 120, 300, 40).collidepoint(mouse_pos):
                                stats['current_skin'] = 'default'; self.apply_current_skin(); self.asset_manager.save_stats()
                            elif pygame.Rect(50, 175, 300, 40).collidepoint(mouse_pos):
                                if 'red' in stats['unlocked_skins']: stats['current_skin'] = 'red'
                                elif stats['total_credits'] >= 50:
                                    stats['total_credits'] -= 50; stats['current_skin'] = 'red'; stats['unlocked_skins'].append('red')
                                self.apply_current_skin(); self.asset_manager.save_stats(); self.asset_manager.play_sound('collect')
                            elif pygame.Rect(50, 230, 300, 40).collidepoint(mouse_pos):
                                if 'blue' in stats['unlocked_skins']: stats['current_skin'] = 'blue'
                                elif stats['total_credits'] >= 75:
                                    stats['total_credits'] -= 75; stats['current_skin'] = 'blue'; stats['unlocked_skins'].append('blue')
                                self.apply_current_skin(); self.asset_manager.save_stats(); self.asset_manager.play_sound('collect')
                            elif pygame.Rect(50, 325, 300, 40).collidepoint(mouse_pos):
                                if 'longer_giant' not in stats.get('unlocked_upgrades', []):
                                    if stats['total_credits'] >= 100:
                                        stats['total_credits'] -= 100; stats.setdefault('unlocked_upgrades', []).append('longer_giant')
                                        self.asset_manager.save_stats(); self.asset_manager.play_sound('collect')
                            elif pygame.Rect(50, 420, 300, 40).collidepoint(mouse_pos):
                                if 'fire_aura' not in stats.get('unlocked_upgrades', []):
                                    if stats['total_credits'] >= 200:
                                        stats['total_credits'] -= 200; stats.setdefault('unlocked_upgrades', []).append('fire_aura')
                                        self.asset_manager.save_stats(); self.asset_manager.play_sound('collect')
                            elif pygame.Rect(WIDTH//2 - 50, 540, 100, 40).collidepoint(mouse_pos): self.change_state(LOBBY)
                        elif self.state == ACHIEVEMENTS:
                            if pygame.Rect(WIDTH//2 - 50, 520, 100, 40).collidepoint(mouse_pos): self.change_state(LOBBY)
                        elif self.state == PLAYING:
                            if mouse_pos[0] < WIDTH // 2: # Left side
                                self.asset_manager.play_sound('wing'); curr_j = JUMP_STRENGTH
                                if 'SLOW' in self.active_powerups: curr_j *= 0.5
                                self.bird.jump(curr_j)
                            else: # Right side
                                self.shoot_laser()
                        elif self.state == PAUSED:
                            if pygame.Rect(WIDTH//2 - 60, HEIGHT//2 + 50, 120, 40).collidepoint(mouse_pos):
                                self.state = PLAYING; pygame.mixer.music.unpause()
                        elif self.state == GAME_OVER:
                            if pygame.Rect(WIDTH//2 - 70, HEIGHT//2 + 130, 140, 50).collidepoint(mouse_pos): self.change_state(PLAYING)
                            elif pygame.Rect(WIDTH//2 - 70, HEIGHT//2 + 200, 140, 50).collidepoint(mouse_pos): self.change_state(LOBBY)

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            if self.state == PLAYING: self.state = PAUSED; pygame.mixer.music.pause()
                            elif self.state == PAUSED: self.state = PLAYING; pygame.mixer.music.unpause()
                        if event.key == pygame.K_SPACE and self.state == PLAYING:
                            self.asset_manager.play_sound('wing'); curr_j = JUMP_STRENGTH
                            if 'SLOW' in self.active_powerups: curr_j *= 0.5
                            self.bird.jump(curr_j)
                        if event.key == pygame.K_f and self.state == PLAYING: self.shoot_laser()

            # --- Update Logic ---
            if self.state == PLAYING:
                is_ghost = 'GHOST' in self.active_powerups; is_slow = 'SLOW' in self.active_powerups; is_giant = 'GIANT' in self.active_powerups
                is_any_w = any(isinstance(s, Missile) and s.warning_timer > 0 for s in self.all_sprites)
                cur_v = self.tube_velocity; cur_g = GRAVITY
                if is_slow: cur_v *= 0.5; cur_g *= 0.7
                if is_giant: cur_v *= 0.4; cur_g *= 0.7
                if self.bird.update(self.state, cur_g, is_ghost, is_any_w, is_giant): self.handle_game_over()
                if self.active_powerups:
                    trail = TrailEffect(self.bird.rect.centerx, self.bird.rect.centery, self.bird.image)
                    self.trails.add(trail); self.all_sprites.add(trail)
                self.trails.update(); self.lasers.update(self.bird.rect); self.floating_texts.update()
                self.particles.update(cur_v); self.missiles.update(cur_v); self.energy_balls.update(cur_v)
                if 'fire_aura' in self.asset_manager.stats.get('unlocked_upgrades', []):
                    if random.random() < 0.3:
                        p = Particle(self.bird.rect.centerx, self.bird.rect.centery, ORANGE if random.random() > 0.5 else RED)
                        self.all_sprites.add(p); self.particles.add(p)
                if self.score > 0 and self.score % 50 == 0 and self._boss_spawned_score != self.score:
                    self._boss_spawned_score = self.score; self.boss_fight = True; self.boss_entity = Boss()
                    self.all_sprites.add(self.boss_entity); self.active_powerups['LASER'] = pygame.time.get_ticks() + 999999
                    ft = FloatingText(WIDTH//2, HEIGHT//2, "WARNING: BOSS APPROACHING!", RED, self.large_font)
                    self.floating_texts.add(ft); self.all_sprites.add(ft)
                if self.boss_fight and self.boss_entity:
                    self.boss_entity.update(cur_v); self.boss_entity.shoot_timer -= 1
                    if self.boss_entity.shoot_timer <= 0:
                        self.boss_entity.shoot_timer = 60
                        eb = EnergyBall(self.boss_entity.rect.centerx, self.boss_entity.rect.centery)
                        self.all_sprites.add(eb); self.energy_balls.add(eb)
                can_spawn_m = True
                for t in self.tubes:
                    if t.rect.right > WIDTH // 3: can_spawn_m = False; break
                if self.score > 20 and not self.boss_fight and can_spawn_m and random.random() < 0.005:
                    if len(self.missiles) == 0:
                        m = Missile(self.bird.rect.centery); self.all_sprites.add(m); self.missiles.add(m)
                self.cloud_timer += dt
                if self.cloud_timer > 2000: self.clouds.add(Cloud()); self.cloud_timer = 0
                self.clouds.update(cur_v); self.tube_timer += dt
                sp_int = 1500 / (cur_v / INITIAL_TUBE_VELOCITY)
                if self.tube_timer > sp_int:
                    if not self.boss_fight:
                        if self.spawn_tubes(): self.tube_timer = 0
                    else: self.tube_timer = 0
                self.tubes.update(cur_v); self.items.update(cur_v)
                for t in self.tubes:
                    if not hasattr(t, 'passed') and t.rect.right < self.bird.rect.left:
                        pid = getattr(t, 'pair_id', None)
                        for tg in self.tubes:
                            if getattr(tg, 'pair_id', None) == pid: tg.passed = True
                        self.score += 1; self.asset_manager.stats['total_ghost_passes'] += 1 if is_ghost else 0
                        if self.score % 10 == 0: self.tube_velocity += 0.5
                if not is_ghost:
                    es = [s for s in self.all_sprites if isinstance(s, (Boss, EnergyBall)) or (isinstance(s, Missile) and s.warning_timer <= 0)]
                    if pygame.sprite.spritecollide(self.bird, pygame.sprite.Group(es), False):
                        if is_giant:
                            for e in pygame.sprite.spritecollide(self.bird, pygame.sprite.Group(es), False):
                                if isinstance(e, Boss):
                                    if e.take_damage(): e.kill(); self.boss_fight = False; self.score += 5; self.asset_manager.stats['total_credits'] += 50
                                else: e.kill(); self.score += 1
                        else: self.handle_game_over()
                    ct = pygame.sprite.spritecollide(self.bird, self.tubes, False, pygame.sprite.collide_mask)
                    if ct:
                        if is_giant:
                            now = pygame.time.get_ticks()
                            self.combo_count = self.combo_count + 1 if now - self.last_destruction_time < 2000 else 1
                            self.last_destruction_time = now
                            for tube in ct: tube.kill(); self.score += self.combo_count; self.asset_manager.stats['total_destroyed'] += 1
                            self.asset_manager.play_sound('explosion', self.combo_count); self.shake_timer = 30
                        else: self.handle_game_over()

            # --- Shake ---
            off_x, off_y = 0, 0
            if self.shake_timer > 0:
                off_x = random.randint(-self.shake_timer//2, self.shake_timer//2)
                off_y = random.randint(-self.shake_timer//2, self.shake_timer//2)
                self.shake_timer -= 2

            # --- Draw ---
            self.temp_surface.fill(CYAN)
            if self.asset_manager.bg_img: self.temp_surface.blit(self.asset_manager.bg_img, (0, 0))
            self.clouds.draw(self.temp_surface); self.all_sprites.draw(self.temp_surface)
            pygame.draw.rect(self.temp_surface, (150, 75, 0), (0, HEIGHT - 25, WIDTH, 25))
            
            # Blit game world with shake
            self.screen.blit(self.temp_surface, (off_x, off_y))

            # Draw UI on top of screen
            if self.state == PLAYING: ui.draw_ui(self)
            elif self.state == LOBBY: ui.draw_lobby(self)
            elif self.state == SETTINGS: ui.draw_settings(self)
            elif self.state == SHOP: ui.draw_shop(self)
            elif self.state == ACHIEVEMENTS: ui.draw_achievements(self)
            elif self.state == PAUSED: ui.draw_paused(self)
            elif self.state == GAME_OVER: ui.draw_game_over(self)
            
            ui.draw_transition(self); pygame.display.flip()

        self.asset_manager.save_stats(); pygame.quit()
