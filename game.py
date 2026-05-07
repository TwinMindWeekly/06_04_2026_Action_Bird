import pygame
import random
import math
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
        self.clock      = pygame.time.Clock()
        self.font        = make_font(24, bold=True)
        self.medium_font = make_font(32, bold=True)
        self.large_font  = make_font(48, bold=True)

        self.asset_manager = AssetManager()
        self.asset_manager.load_assets()

        self.new_record_flag = False
        self.tutorial_step   = 0
        self._shop_tab       = 'SKINS'
        self._ach_scroll     = 0
        self.god_mode            = False
        self._god_input          = ""
        self._god_input_active   = False

        self.reset_game()

        # Check tutorial (first launch)
        if not self.asset_manager.stats.get('tutorial_done', False):
            self.state = TUTORIAL

        # Check daily reward
        can, reward, streak = self.asset_manager.get_daily_reward_info()
        self.daily_reward_pending = can
        self.daily_reward_amount  = reward
        self.daily_reward_streak  = streak

    # ----------------------------------------------------------------- helpers
    def handle_game_over(self):
        if self.state == GAME_OVER:
            return
        self.shake_timer = 40
        self.asset_manager.play_sound('die')

        stats = self.asset_manager.stats
        if self.score > stats['high_score']:
            stats['high_score']  = self.score
            self.new_record_flag = True

        if not self.reward_given:
            stats['total_credits']     += self.score
            stats['total_games_played'] = stats.get('total_games_played', 0) + 1
            self.reward_given = True

        self._check_achievements()
        self.asset_manager.save_stats()
        self.change_state(GAME_OVER)

    def _check_achievements(self):
        stats    = self.asset_manager.stats
        unlocked = stats.setdefault('unlocked_achievements', [])
        for ach in ui.get_all_achievements(stats):
            if ach['id'] not in unlocked and ach['unlocked']:
                unlocked.append(ach['id'])
                stats['total_credits'] += ach.get('reward', 0)
                ft = FloatingText(WIDTH // 2, HEIGHT // 2 - 60,
                                  f"+ {ach['name']}", YELLOW, self.font)
                self.floating_texts.add(ft)
                self.all_sprites.add(ft)

    def apply_current_skin(self):
        img = self.asset_manager.get_skin_image(self.asset_manager.stats['current_skin'])
        if hasattr(self, 'bird'):
            self.bird.original_image = img
            self.bird.image          = img
            self.bird.base_image     = pygame.transform.scale(img, (70, 70)) if self.bird.is_giant else img.copy()
            self.bird.mask           = pygame.mask.from_surface(self.bird.image)

    def _powerup_duration(self, ptype):
        """Return duration ms for a powerup, respecting upgrades."""
        upgrades = self.asset_manager.stats.get('unlocked_upgrades', [])
        dur = POWERUP_DURATION
        if f'longer_{ptype.lower()}' in upgrades:
            dur = int(dur * 1.5)
        return dur

    def reset_game(self):
        self.state          = LOBBY
        self.score          = 0
        self.tube_velocity  = INITIAL_TUBE_VELOCITY

        bird_img = self.asset_manager.get_skin_image(self.asset_manager.stats['current_skin'])
        self.bird = Bird(50, HEIGHT // 2, bird_img)

        self.all_sprites    = pygame.sprite.Group(self.bird)
        self.tubes          = pygame.sprite.Group()
        self.clouds         = pygame.sprite.Group()
        self.items          = pygame.sprite.Group()
        self.lasers         = pygame.sprite.Group()
        self.trails         = pygame.sprite.Group()
        self.floating_texts = pygame.sprite.Group()
        self.particles      = pygame.sprite.Group()
        self.missiles       = pygame.sprite.Group()
        self.energy_balls   = pygame.sprite.Group()

        self.tube_timer  = 0
        self.cloud_timer = 0

        self.active_powerups        = {}
        self.shake_timer            = 0
        self.boss_fight             = False
        self.boss_entity            = None
        self._boss_spawned_score    = -1
        self.boss_prep_active       = False
        self.boss_prep_end          = 0
        self.boss_missile_timer     = 0

        self.combo_count            = 0
        self.last_destruction_time  = 0
        self.near_miss_tubes        = set()
        self.reward_given           = False
        self.score_scale            = 1.0
        self.last_score             = 0

        self.fade_alpha   = 0
        self.fade_speed   = 10
        self.fade_mode    = 'NONE'
        self.target_state = None
        self.temp_surface = pygame.Surface((WIDTH, HEIGHT))

        if self.asset_manager.music_file:
            pygame.mixer.music.stop()

    def change_state(self, next_state):
        if self.fade_mode == 'NONE':
            self.target_state = next_state
            self.fade_mode    = 'OUT'

    # ----------------------------------------------------------------- spawning
    def spawn_tubes(self):
        if self.missiles:
            return False
        if self.tubes:
            last = max(self.tubes, key=lambda t: t.rect.right)
            if WIDTH - last.rect.right < 250:
                return False

        h         = random.randint(100, 300)
        is_moving = self.score > 30 and random.random() < 0.6
        top   = Tube(WIDTH, h, True,  is_moving)
        bot   = Tube(WIDTH, h, False, is_moving)
        pid   = pygame.time.get_ticks()
        top.pair_id = bot.pair_id = pid

        self.tubes.add(top, bot)
        self.all_sprites.add(top, bot)

        if random.random() < ITEM_CHANCE:
            itype = random.choice(['LASER', 'GHOST', 'SLOW', 'GIANT'])
            item  = Item(WIDTH + TUBE_WIDTH // 2, h + TUBE_GAP // 2, itype)
            self.items.add(item)
            self.all_sprites.add(item)
        return True

    def shoot_laser(self):
        if 'LASER' not in self.active_powerups:
            return
        self.asset_manager.play_sound('laser', self.combo_count)
        lsr = Laser((self.bird.rect.right, self.bird.rect.centery))
        self.lasers.add(lsr)
        self.all_sprites.add(lsr)
        self.asset_manager.stats['total_laser_uses'] = \
            self.asset_manager.stats.get('total_laser_uses', 0) + 1

    # ----------------------------------------------------------------- main loop
    def run(self):
        running = True
        while running:
            dt  = self.clock.tick(FPS)
            now = pygame.time.get_ticks()

            # Fade transitions
            if self.fade_mode == 'OUT':
                self.fade_alpha += self.fade_speed
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255
                    self.fade_mode  = 'IN'
                    if self.target_state == PLAYING and self.state != PLAYING:
                        self.reset_game()
                        self.state = PLAYING
                        if self.asset_manager.music_file and config.bgm_enabled:
                            try:
                                pygame.mixer.music.load(self.asset_manager.music_file)
                                pygame.mixer.music.play(-1)
                            except:
                                pass
                    else:
                        if self.target_state == LOBBY:
                            pygame.mixer.music.stop()
                        self.state = self.target_state
                    self.asset_manager.update_volumes()
            elif self.fade_mode == 'IN':
                self.fade_alpha -= self.fade_speed
                if self.fade_alpha <= 0:
                    self.fade_alpha = 0
                    self.fade_mode  = 'NONE'

            # -------- Events --------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if self.fade_mode != 'NONE':
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mp = event.pos
                    self._handle_click(mp, now)

                if event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)

            # -------- Update --------
            if self.state == PLAYING:
                self._update_playing(dt, now)

            # -------- Shake --------
            ox = oy = 0
            if self.shake_timer > 0:
                ox = random.randint(-self.shake_timer // 2, self.shake_timer // 2)
                oy = random.randint(-self.shake_timer // 2, self.shake_timer // 2)
                self.shake_timer -= 2

            # -------- Draw --------
            self.temp_surface.fill(CYAN)
            if self.asset_manager.bg_img:
                self.temp_surface.blit(self.asset_manager.bg_img, (0, 0))
            self.clouds.draw(self.temp_surface)
            self.all_sprites.draw(self.temp_surface)
            pygame.draw.rect(self.temp_surface, (150, 75, 0), (0, HEIGHT - 25, WIDTH, 25))
            self.screen.blit(self.temp_surface, (ox, oy))

            if   self.state == PLAYING:      ui.draw_ui(self)
            elif self.state == LOBBY:        ui.draw_lobby(self)
            elif self.state == SETTINGS:     ui.draw_settings(self)
            elif self.state == SHOP:         ui.draw_shop(self)
            elif self.state == ACHIEVEMENTS: ui.draw_achievements(self)
            elif self.state == PAUSED:       ui.draw_paused(self)
            elif self.state == GAME_OVER:    ui.draw_game_over(self)
            elif self.state == TUTORIAL:     ui.draw_tutorial(self)

            ui.draw_transition(self)
            if self._god_input_active:
                ui.draw_god_input_overlay(self)
            pygame.display.flip()

        self.asset_manager.save_stats()
        pygame.quit()

    # ----------------------------------------------------------------- click
    def _handle_click(self, mp, now):
        state = self.state

        # ---- TUTORIAL ----
        if state == TUTORIAL:
            total = 5
            skip_rect = pygame.Rect(WIDTH - 110, 10, 100, 34)
            if skip_rect.collidepoint(mp):
                self._finish_tutorial(); return
            # Back button
            if self.tutorial_step > 0 and pygame.Rect(20, HEIGHT-70, 140, 44).collidepoint(mp):
                self.tutorial_step -= 1; return
            # Next / Play button
            if pygame.Rect(WIDTH - 175, HEIGHT-70, 155, 44).collidepoint(mp):
                if self.tutorial_step < total - 1:
                    self.tutorial_step += 1
                else:
                    self._finish_tutorial()
            return

        # ---- LOBBY ----
        if state == LOBBY:
            # Daily reward overlay takes priority
            if self.daily_reward_pending:
                pw, ph = 320, 370
                px, py = WIDTH//2 - pw//2, HEIGHT//2 - ph//2
                claim_rect = pygame.Rect(px + pw//2 - 90, py + 240, 180, 48)
                if claim_rect.collidepoint(mp):
                    reward, streak = self.asset_manager.claim_daily_reward()
                    self.daily_reward_pending = False
                    ft = FloatingText(WIDTH//2, HEIGHT//2 - 80,
                                     f"+{reward} CREDITS!", YELLOW, self.font)
                    self.floating_texts.add(ft); self.all_sprites.add(ft)
                return  # block lobby buttons while overlay open

            if pygame.Rect(WIDTH - 45, 10, 35, 35).collidepoint(mp):
                self._settings_source = 'LOBBY'; self.change_state(SETTINGS); return
            if pygame.Rect(WIDTH//2-100, 260, 200, 50).collidepoint(mp): self.change_state(PLAYING)
            elif pygame.Rect(WIDTH//2-100, 330, 200, 50).collidepoint(mp):
                self._shop_tab = 'SKINS'; self.change_state(SHOP)
            elif pygame.Rect(WIDTH//2-100, 400, 200, 50).collidepoint(mp): self.change_state(ACHIEVEMENTS)
            elif pygame.Rect(WIDTH//2-100, 470, 200, 50).collidepoint(mp):
                self._settings_source = 'LOBBY'; self.change_state(SETTINGS)

        # ---- SETTINGS ----
        elif state == SETTINGS:
            if pygame.Rect(250, 175, 40, 40).collidepoint(mp):
                config.master_volume = max(0.0, round(config.master_volume - 0.1, 1))
                self.asset_manager.update_volumes()
            elif pygame.Rect(310, 175, 40, 40).collidepoint(mp):
                config.master_volume = min(1.0, round(config.master_volume + 0.1, 1))
                self.asset_manager.update_volumes()
            elif pygame.Rect(250, 245, 100, 40).collidepoint(mp):
                config.bgm_enabled = not config.bgm_enabled
                if not config.bgm_enabled:
                    pygame.mixer.music.stop()
                elif self.asset_manager.music_file:
                    try:
                        pygame.mixer.music.load(self.asset_manager.music_file)
                        pygame.mixer.music.play(-1)
                    except:
                        pass
                self.asset_manager.update_volumes()
            elif pygame.Rect(WIDTH//2-60, 420, 120, 40).collidepoint(mp):
                if getattr(self, '_settings_source', 'LOBBY') == 'PAUSED':
                    self.state = PAUSED
                else:
                    self.change_state(LOBBY)
            elif pygame.Rect(WIDTH//2-80, 472, 160, 40).collidepoint(mp):
                if getattr(self, '_settings_source', 'LOBBY') == 'PAUSED':
                    pygame.mixer.music.stop()
                    self.change_state(LOBBY)

        # ---- SHOP ----
        elif state == SHOP:
            self._handle_shop_click(mp)

        # ---- ACHIEVEMENTS ----
        elif state == ACHIEVEMENTS:
            if pygame.Rect(WIDTH//2-55, HEIGHT-65, 110, 40).collidepoint(mp):
                self.change_state(LOBBY)

        # ---- PLAYING ----
        elif state == PLAYING:
            if pygame.Rect(WIDTH - 45, 10, 35, 35).collidepoint(mp):
                self.state = PAUSED; pygame.mixer.music.pause(); return
            if mp[0] < WIDTH // 2:
                self.asset_manager.play_sound('wing')
                j = JUMP_STRENGTH * (0.5 if 'SLOW' in self.active_powerups else 1)
                self.bird.jump(j)
            else:
                self.shoot_laser()

        # ---- PAUSED ----
        elif state == PAUSED:
            if pygame.Rect(WIDTH//2-65, HEIGHT//2+50, 130, 44).collidepoint(mp):
                self.state = PLAYING
                pygame.mixer.music.unpause()
            elif pygame.Rect(WIDTH//2-65, HEIGHT//2+105, 130, 44).collidepoint(mp):
                self._settings_source = 'PAUSED'
                self.change_state(SETTINGS)

        # ---- GAME OVER ----
        elif state == GAME_OVER:
            if pygame.Rect(WIDTH//2-75, HEIGHT//2+125, 150, 50).collidepoint(mp):
                self.change_state(PLAYING)
            elif pygame.Rect(WIDTH//2-75, HEIGHT//2+190, 150, 50).collidepoint(mp):
                self.change_state(LOBBY)

    def _finish_tutorial(self):
        self.asset_manager.stats['tutorial_done'] = True
        self.asset_manager.save_stats()
        self.change_state(LOBBY)

    def _handle_shop_click(self, mp):
        stats = self.asset_manager.stats
        tab   = getattr(self, '_shop_tab', 'SKINS')

        # Tab switch buttons
        if pygame.Rect(22, 92, 170, 30).collidepoint(mp):
            self._shop_tab = 'SKINS';    return
        if pygame.Rect(208, 92, 170, 30).collidepoint(mp):
            self._shop_tab = 'UPGRADES'; return

        if tab == 'SKINS':
            y = 130
            for skin in SKIN_CATALOG:
                if pygame.Rect(22, y, 356, 48).collidepoint(mp):
                    key   = skin['key']
                    price = skin['price']
                    if key in stats['unlocked_skins']:
                        stats['current_skin'] = key
                    elif stats['total_credits'] >= price:
                        stats['total_credits']    -= price
                        stats['current_skin']      = key
                        stats['unlocked_skins'].append(key)
                        self.asset_manager.play_sound('collect')
                    self.apply_current_skin()
                    self.asset_manager.save_stats()
                    return
                y += 52
            # Back button
            if pygame.Rect(WIDTH//2-55, y + 4, 110, 38).collidepoint(mp):
                self.change_state(LOBBY)

        else:  # UPGRADES
            y = 134
            for item in UPGRADE_CATALOG:
                if 'section' in item:
                    y += 24; continue
                if pygame.Rect(32, y, 336, 38).collidepoint(mp):
                    uid   = item['id']
                    price = item['price']
                    if uid not in stats.get('unlocked_upgrades', []) and stats['total_credits'] >= price:
                        stats['total_credits'] -= price
                        stats.setdefault('unlocked_upgrades', []).append(uid)
                        self.asset_manager.play_sound('collect')
                        self.asset_manager.save_stats()
                    return
                y += 46
            if pygame.Rect(WIDTH//2-55, y + 4, 110, 38).collidepoint(mp):
                self.change_state(LOBBY)

    # ----------------------------------------------------------------- key
    def _handle_key(self, key):
        # God-mode input intercept
        if self._god_input_active:
            if key == pygame.K_RETURN:
                if self._god_input.lower() == "godmode":
                    self.god_mode = not self.god_mode
                self._god_input = ""; self._god_input_active = False
            elif key == pygame.K_ESCAPE:
                self._god_input = ""; self._god_input_active = False
            elif key == pygame.K_BACKSPACE:
                self._god_input = self._god_input[:-1]
            else:
                name = pygame.key.name(key)
                if len(name) == 1 and len(self._god_input) < 20:
                    self._god_input += name
            return

        if key == pygame.K_SLASH:
            self._god_input = ""; self._god_input_active = True
            return

        if key == pygame.K_ESCAPE:
            if self.state == PLAYING:
                self.state = PAUSED
                pygame.mixer.music.pause()
            elif self.state == PAUSED:
                self.state = PLAYING
                pygame.mixer.music.unpause()

        if key == pygame.K_SPACE and self.state == PLAYING:
            self.asset_manager.play_sound('wing')
            j = JUMP_STRENGTH * (0.5 if 'SLOW' in self.active_powerups else 1)
            self.bird.jump(j)

        if key == pygame.K_f and self.state == PLAYING:
            self.shoot_laser()

    # ----------------------------------------------------------------- update
    def _update_playing(self, dt, now):
        is_ghost = 'GHOST' in self.active_powerups
        is_slow  = 'SLOW'  in self.active_powerups
        is_giant = 'GIANT' in self.active_powerups
        is_any_w = any(isinstance(s, Missile) and s.warning_timer > 0 for s in self.all_sprites)

        cur_v = self.tube_velocity
        cur_g = GRAVITY
        if is_slow:  cur_v *= 0.5; cur_g *= 0.7
        if is_giant: cur_v *= 0.4; cur_g *= 0.7

        if self.bird.update(self.state, cur_g, is_ghost, is_any_w, is_giant):
            if not self.god_mode:
                self.handle_game_over(); return

        # Trail
        if self.active_powerups:
            t = TrailEffect(self.bird.rect.centerx, self.bird.rect.centery, self.bird.image)
            self.trails.add(t); self.all_sprites.add(t)
        self.trails.update()
        self.lasers.update(self.bird.rect)
        self.floating_texts.update()

        # Laser collisions
        for laser in list(self.lasers):
            if not laser.alive():
                continue
            hit = False

            # Destroy only the first pipe pair the laser touches
            closest_tube = None
            closest_dist = float('inf')
            for tube in self.tubes:
                if pygame.sprite.collide_rect(laser, tube) and tube.rect.left < closest_dist:
                    closest_dist = tube.rect.left
                    closest_tube = tube
            if closest_tube:
                closest_tube.kill()
                self.asset_manager.stats['total_destroyed'] += 1
                laser.kill()
                hit = True

            if laser.alive():
                ms = pygame.sprite.Group(
                    s for s in self.all_sprites if isinstance(s, Missile) and s.warning_timer <= 0)
                if pygame.sprite.spritecollide(laser, ms, True):
                    laser.kill()
                    hit = True

            if laser.alive() and self.boss_fight and self.boss_entity and not self.boss_prep_active \
                    and pygame.sprite.collide_rect(laser, self.boss_entity):
                if not hasattr(laser, 'boss_hit_time') or now - laser.boss_hit_time > 500:
                    laser.boss_hit_time = now
                    hit = True
                    laser.kill()
                    if self.boss_entity.take_damage():
                        self._kill_boss()

            if hit:
                self.combo_count = self.combo_count + 1 if now - self.last_destruction_time < 2000 else 1
                self.last_destruction_time = now
                self.score += self.combo_count
                s = self.asset_manager.stats
                s['total_combos'] = s.get('total_combos', 0) + 1
                if self.combo_count > s.get('max_combo', 0):
                    s['max_combo'] = self.combo_count
                if self.combo_count > 1:
                    ft = FloatingText(self.bird.rect.right, self.bird.rect.top - 20,
                                      f"COMBO X{self.combo_count}", RED, self.medium_font)
                    self.floating_texts.add(ft); self.all_sprites.add(ft)
                self.asset_manager.play_sound('explosion', self.combo_count)
                self.shake_timer = 20

        # Particles & projectiles
        self.particles.update(cur_v)
        self.missiles.update(cur_v)
        self.energy_balls.update(cur_v)

        # Fire aura
        upgrades = self.asset_manager.stats.get('unlocked_upgrades', [])
        if 'fire_aura' in upgrades and random.random() < 0.3:
            p = Particle(self.bird.rect.centerx, self.bird.rect.centery,
                         ORANGE if random.random() > 0.5 else RED)
            self.all_sprites.add(p); self.particles.add(p)

        # Boss spawn
        if self.score > 0 and self.score % 50 == 0 and self._boss_spawned_score != self.score:
            self._boss_spawned_score  = self.score
            self.boss_fight           = True
            self.boss_prep_active     = True
            self.boss_prep_end        = now + 5000
            self.boss_missile_timer   = 120
            self.boss_entity          = Boss()
            self.all_sprites.add(self.boss_entity)
            self.active_powerups['LASER'] = now + 999_999_999
            ft = FloatingText(WIDTH // 2, HEIGHT // 2, "!! BOSS APPROACHING!", RED, self.large_font)
            self.floating_texts.add(ft); self.all_sprites.add(ft)

        # Boss update
        if self.boss_fight and self.boss_entity:
            if self.boss_prep_active and now >= self.boss_prep_end:
                self.boss_prep_active = False
            self.boss_entity.update(cur_v)
            if not self.boss_prep_active:
                self.boss_entity.shoot_timer -= 1
                if self.boss_entity.shoot_timer <= 0:
                    self.boss_entity.shoot_timer = 60
                    eb = EnergyBall(self.boss_entity.rect.centerx, self.boss_entity.rect.centery)
                    self.all_sprites.add(eb); self.energy_balls.add(eb)
                if self.boss_entity.hp <= self.boss_entity.max_hp // 2:
                    self.boss_missile_timer -= 1
                    if self.boss_missile_timer <= 0:
                        self.boss_missile_timer = 200
                        m = Missile(self.boss_entity.rect.centery + random.randint(-60, 60))
                        self.all_sprites.add(m); self.missiles.add(m)

        # Missile spawn
        can_spawn_m = not any(t.rect.right > WIDTH // 3 for t in self.tubes)
        if self.score > 20 and not self.boss_fight and can_spawn_m \
                and random.random() < 0.005 and not self.missiles:
            m = Missile(self.bird.rect.centery)
            self.all_sprites.add(m); self.missiles.add(m)

        # Clouds
        self.cloud_timer += dt
        if self.cloud_timer > 2000:
            self.clouds.add(Cloud()); self.cloud_timer = 0
        self.clouds.update(cur_v)

        # Tubes
        self.tube_timer += dt
        sp_int = 1500 / (cur_v / INITIAL_TUBE_VELOCITY)
        if self.tube_timer > sp_int:
            if not self.boss_fight:
                if self.spawn_tubes(): self.tube_timer = 0
            else:
                self.tube_timer = 0
        self.tubes.update(cur_v)

        # Score passing
        for t in list(self.tubes):
            if not hasattr(t, 'passed') and t.rect.right < self.bird.rect.left:
                pid = getattr(t, 'pair_id', None)
                for tg in self.tubes:
                    if getattr(tg, 'pair_id', None) == pid:
                        tg.passed = True
                self.score += 1
                s = self.asset_manager.stats
                if is_ghost:
                    s['total_ghost_passes'] = s.get('total_ghost_passes', 0) + 1
                # near miss check
                for tg in self.tubes:
                    if getattr(tg, 'pair_id', None) == pid:
                        gap_dist = min(abs(self.bird.rect.left  - tg.rect.right),
                                       abs(self.bird.rect.right - tg.rect.left))
                        if gap_dist < 20:
                            s['total_near_misses'] = s.get('total_near_misses', 0) + 1
                            break
                if self.score % 10 == 0:
                    self.tube_velocity += 0.5

        # Item magnet
        if 'item_magnet' in upgrades:
            for item in self.items:
                dx = self.bird.rect.centerx - item.rect.centerx
                dy = self.bird.rect.centery - item.rect.centery
                dist = math.hypot(dx, dy)
                if 0 < dist < 150:
                    spd = 3 * (1 - dist / 150)
                    item.rect.x += int(dx / dist * spd)
                    item.rect.y += int(dy / dist * spd)

        self.items.update(cur_v)

        # Item collection
        for item in pygame.sprite.spritecollide(self.bird, self.items, True):
            self.asset_manager.play_sound('collect')
            dur = self._powerup_duration(item.type)
            self.active_powerups[item.type] = now + dur
            ft = FloatingText(item.rect.centerx, item.rect.centery - 10,
                              item.type, YELLOW, self.font)
            self.floating_texts.add(ft); self.all_sprites.add(ft)
            s = self.asset_manager.stats
            if item.type == 'GIANT': s['total_giant_uses'] = s.get('total_giant_uses', 0) + 1
            elif item.type == 'SLOW': s['total_slow_uses'] = s.get('total_slow_uses', 0) + 1
            is_p = any(v > now for v in self.active_powerups.values())
            self.asset_manager.update_volumes(is_powerup_active=is_p)

        # Powerup expiry
        for k in [k for k, v in list(self.active_powerups.items()) if now > v]:
            del self.active_powerups[k]

        # Collisions (non-ghost, non-godmode)
        if not is_ghost and not self.god_mode:
            hazards = pygame.sprite.Group(
                s for s in self.all_sprites
                if (isinstance(s, Boss) and not self.boss_prep_active)
                or isinstance(s, EnergyBall)
                or (isinstance(s, Missile) and s.warning_timer <= 0))
            for e in pygame.sprite.spritecollide(self.bird, hazards, False):
                if is_giant:
                    if isinstance(e, Boss):
                        if e.take_damage(): self._kill_boss()
                    else:
                        e.kill(); self.score += 1
                else:
                    self.handle_game_over(); return

            hit_tubes = pygame.sprite.spritecollide(self.bird, self.tubes, False, pygame.sprite.collide_mask)
            if hit_tubes:
                if is_giant:
                    nc = pygame.time.get_ticks()
                    self.combo_count = self.combo_count + 1 if nc - self.last_destruction_time < 2000 else 1
                    self.last_destruction_time = nc
                    for tube in hit_tubes:
                        tube.kill()
                        self.score += self.combo_count
                        self.asset_manager.stats['total_destroyed'] = \
                            self.asset_manager.stats.get('total_destroyed', 0) + 1
                    self.asset_manager.play_sound('explosion', self.combo_count)
                    self.shake_timer = 30
                else:
                    self.handle_game_over()

    def _kill_boss(self):
        if self.boss_entity:
            self.boss_entity.kill()
        self.boss_fight = False
        self.score     += 5
        s = self.asset_manager.stats
        s['total_credits']   += 50
        s['total_boss_kills'] = s.get('total_boss_kills', 0) + 1
        if 'LASER' in self.active_powerups:
            del self.active_powerups['LASER']
        bx = self.boss_entity.rect.centerx if self.boss_entity else WIDTH - 80
        by = self.boss_entity.rect.centery if self.boss_entity else HEIGHT // 2
        for _ in range(3):
            it   = random.choice(['LASER', 'GHOST', 'SLOW', 'GIANT'])
            item = Item(bx + random.randint(-20, 20), by + random.randint(-20, 20), it)
            self.items.add(item); self.all_sprites.add(item)
        self.boss_entity = None
