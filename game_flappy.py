"""game_flappy.py — Flappy Bird. Space / click to flap."""

import pygame
import random
import math
from shared import (
    Game,
    PANEL, TEXT, X_COL, GOLD, WHITE,
    f_big, f_med, f_small,
    draw_text, draw_button, mouse_over,
)

# tweak these to change difficulty
GRAVITY      = 0.45
FLAP_V       = -8.2
PIPE_GAP     = 165
PIPE_W       = 70
PIPE_SPACING = 230
PIPE_SPEED   = 3.2

# tried PIPE_GAP=130 for "hard mode" but it just felt unfair, not harder
# PIPE_GAP = 130

TOP_BAR  = 54
GROUND_H = 70

SKY_TOP    = ( 90, 170, 230)
SKY_BOTTOM = (160, 215, 240)
PIPE_LIGHT = (140, 220, 110)
PIPE_COL   = ( 75, 175,  75)
PIPE_DARK  = ( 50, 130,  55)
PIPE_OUTLN = ( 30,  80,  30)
GROUND_COL = (210, 190, 110)
GROUND_DK  = (170, 150,  80)
GRASS_COL  = (110, 200,  90)
GRASS_DK   = ( 70, 150,  60)
BIRD_BODY  = (255, 210,  60)
BIRD_BELLY = (255, 240, 180)
BIRD_WING  = (235, 175,  40)
BIRD_BEAK  = (240, 130,  40)
SUN_COL    = (255, 240, 170)
CLOUD_COL  = (255, 255, 255)


def _make_sky(w, h):
    """Pre-rendered sky with sun and a few cloud blobs baked in."""
    sky_h = h - TOP_BAR - GROUND_H
    surf  = pygame.Surface((w, sky_h))

    # vertical gradient
    for y in range(sky_h):
        t = y / max(1, sky_h - 1)
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))

    # sun — soft glow built up from concentric translucent circles
    sun_x = int(w * 0.18)
    sun_y = int(sky_h * 0.22)
    glow = pygame.Surface((220, 220), pygame.SRCALPHA)
    for r, a in [(95, 18), (75, 28), (55, 40), (38, 70)]:
        pygame.draw.circle(glow, (*SUN_COL, a), (110, 110), r)
    surf.blit(glow, (sun_x - 110, sun_y - 110))
    pygame.draw.circle(surf, SUN_COL, (sun_x, sun_y), 28)

    # static cloud blobs in the background. moving clouds drawn separately each frame
    rng = random.Random(42)  # fixed seed so they don't jitter on resize
    for _ in range(6):
        cx = rng.randint(40, w - 40)
        cy = rng.randint(20, sky_h // 2)
        _draw_cloud(surf, cx, cy, rng.uniform(0.7, 1.4), alpha=120)

    return surf


def _draw_cloud(surf, cx, cy, scale=1.0, alpha=255):
    """Soft cloud — a few overlapping ellipses on a transparent surface."""
    w = int(110 * scale)
    h = int(46 * scale)
    cloud = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
    col = (*CLOUD_COL, alpha)
    # bunch of overlapping puffs
    pygame.draw.ellipse(cloud, col, (0,           h*0.3, w*0.55, h*0.7))
    pygame.draw.ellipse(cloud, col, (w*0.25,      0,     w*0.55, h*0.85))
    pygame.draw.ellipse(cloud, col, (w*0.45,      h*0.1, w*0.55, h*0.8))
    pygame.draw.ellipse(cloud, col, (w*0.15,      h*0.4, w*0.7,  h*0.6))
    surf.blit(cloud, (cx - (w + 20)//2, cy - (h + 20)//2))


class FlappyGame(Game):
    def __init__(self):
        super().__init__()
        self._new_game()

    def on_resize(self, w, h):
        super().on_resize(w, h)
        self.sky = _make_sky(w, h)
        self.btn_restart = pygame.Rect(w // 2 - 95, h // 2 + 30, 190, 46)

    def _spawn_pipe(self, x):
        play_top    = TOP_BAR + 40
        play_bottom = self.h - GROUND_H - 40
        gap_y = random.randint(play_top + PIPE_GAP // 2,
                               play_bottom - PIPE_GAP // 2)
        return {"x": float(x), "gap_y": gap_y, "scored": False}

    def _new_game(self):
        self.bird_x = 160
        self.bird_y = (TOP_BAR + (self.h - GROUND_H)) / 2
        self.vy     = 0.0
        self.score  = 0
        self.started = False
        self.dead    = False
        self.ground_offset = 0
        self.t = 0
        # seed a few pipes ahead
        first_x = self.w + 80
        self.pipes = [self._spawn_pipe(first_x + i * PIPE_SPACING)
                      for i in range(3)]
        # foreground clouds drift slowly. each one has its own scale + speed.
        self.clouds = []
        for _ in range(4):
            self.clouds.append({
                "x":     random.uniform(0, self.w),
                "y":     random.uniform(40, (self.h - GROUND_H - TOP_BAR) * 0.55),
                "scale": random.uniform(0.8, 1.6),
                "speed": random.uniform(0.15, 0.45),
            })
        # tiny floating dots — pollen / dust / whatever
        self.particles = []
        for _ in range(18):
            self.particles.append({
                "x":  random.uniform(0, self.w),
                "y":  random.uniform(TOP_BAR, self.h - GROUND_H),
                "vy": random.uniform(-0.15, -0.05),
                "vx": random.uniform(-0.2, -0.6),
                "r":  random.choice([1, 1, 2]),
            })

    def _bird_rect(self):
        # smaller than visual for forgiving collisions
        return pygame.Rect(int(self.bird_x) - 12, int(self.bird_y) - 11, 24, 22)

    def _collides(self):
        br = self._bird_rect()
        if br.top <= TOP_BAR:
            return True
        if br.bottom >= self.h - GROUND_H:
            return True
        for p in self.pipes:
            gx, gy = p["x"], p["gap_y"]
            top_rect = pygame.Rect(int(gx), TOP_BAR,
                                   PIPE_W, gy - PIPE_GAP // 2 - TOP_BAR)
            bot_rect = pygame.Rect(int(gx), gy + PIPE_GAP // 2,
                                   PIPE_W, self.h - GROUND_H - (gy + PIPE_GAP // 2))
            if br.colliderect(top_rect) or br.colliderect(bot_rect):
                return True
        return False

    def handle_event(self, e):
        flap = False
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                flap = True
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.dead and self.btn_restart.collidepoint(e.pos):
                self._new_game()
                return False
            # any click (outside back button — base class already filtered) flaps
            if not self.dead:
                flap = True

        if flap and not self.dead:
            self.started = True
            self.vy = FLAP_V
        return False

    def update(self, dt):
        self.t += dt

        # ambient stuff drifts even before game starts — feels alive on the menu
        for c in self.clouds:
            c["x"] -= c["speed"]
            if c["x"] < -150:
                c["x"]     = self.w + 80
                c["y"]     = random.uniform(40, (self.h - GROUND_H - TOP_BAR) * 0.55)
                c["scale"] = random.uniform(0.8, 1.6)
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["x"] < -5 or p["y"] < TOP_BAR - 5:
                p["x"]  = self.w + random.uniform(0, 20)
                p["y"]  = random.uniform(TOP_BAR, self.h - GROUND_H)

        if self.started and not self.dead:
            self.vy += GRAVITY
            self.bird_y += self.vy

            for p in self.pipes:
                p["x"] -= PIPE_SPEED

            # spawn / cull
            if self.pipes and self.pipes[-1]["x"] < self.w - PIPE_SPACING:
                self.pipes.append(
                    self._spawn_pipe(self.pipes[-1]["x"] + PIPE_SPACING))
            self.pipes = [p for p in self.pipes if p["x"] + PIPE_W > -10]

            for p in self.pipes:
                if not p["scored"] and p["x"] + PIPE_W < self.bird_x:
                    p["scored"] = True
                    self.score += 1

            self.ground_offset = (self.ground_offset - PIPE_SPEED) % 40

            if self._collides():
                self.dead = True

        elif not self.started:
            # idle bob before first flap
            self.bird_y += math.sin(self.t * 0.006) * 0.6

        if self.dead:
            self.vy += GRAVITY
            self.bird_y += self.vy
            if self.bird_y > self.h - GROUND_H - 12:
                self.bird_y = self.h - GROUND_H - 12
                self.vy = 0

    def _draw_bird(self, surf):
        # rotation based on velocity — tilts up when flapping, dives nose-down when fallng
        # TODO: smooth this with lerp, looks jittery on slow framerates
        angle = max(-25, min(70, self.vy * 4.5))

        bird = pygame.Surface((54, 54), pygame.SRCALPHA)
        cx, cy = 27, 27
        body_r = 14

        # soft drop shadow behind the body
        sh = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(sh, (0, 0, 0, 60), (20, 20), body_r + 1)
        bird.blit(sh, (cx - 19, cy - 17))

        # body (circle) + lighter belly arc on the lower-front
        pygame.draw.circle(bird, BIRD_BODY, (cx, cy), body_r)
        # belly = light ellipse on the lower half of the body, slightly inset
        pygame.draw.ellipse(bird, BIRD_BELLY,
                            (cx - body_r + 3, cy + 1, (body_r - 3) * 2, body_r - 2))
        # body outline
        pygame.draw.circle(bird, (130, 90, 20), (cx, cy), body_r, 2)

        # tail feathers (small triangle behind)
        pygame.draw.polygon(bird, BIRD_WING,
                            [(cx - 14, cy - 2), (cx - 20, cy + 1), (cx - 14, cy + 4)])
        pygame.draw.polygon(bird, (130, 90, 20),
                            [(cx - 14, cy - 2), (cx - 20, cy + 1), (cx - 14, cy + 4)], 1)

        # wing — flaps up/down with sin. shape is a curved teardrop (3 ellipses stacked)
        flap = math.sin(self.t * 0.022)
        wing_y = cy - 1 + int(flap * 4)
        wing_rect = (cx - 9, wing_y, 16, 10)
        pygame.draw.ellipse(bird, BIRD_WING, wing_rect)
        # inner highlight on the wing — same shape, smaller, lighter
        inner = (cx - 7, wing_y + 1, 12, 6)
        pygame.draw.ellipse(bird, (255, 215, 110), inner)
        pygame.draw.ellipse(bird, (130, 90, 20), wing_rect, 1)

        # eye (white + black pupil + tiny shine)
        pygame.draw.circle(bird, WHITE,        (cx + 5, cy - 4), 4)
        pygame.draw.circle(bird, (20, 20, 20), (cx + 6, cy - 4), 2)
        pygame.draw.circle(bird, WHITE,        (cx + 7, cy - 5), 1)

        # beak — two-tone (lighter top, darker bottom)
        pygame.draw.polygon(bird, BIRD_BEAK,
                            [(cx + 10, cy - 2), (cx + 19, cy + 1), (cx + 10, cy + 4)])
        pygame.draw.polygon(bird, (200, 100, 30),
                            [(cx + 10, cy + 1), (cx + 19, cy + 1), (cx + 10, cy + 4)])
        pygame.draw.polygon(bird, (110,  60,  20),
                            [(cx + 10, cy - 2), (cx + 19, cy + 1), (cx + 10, cy + 4)], 1)

        rotated = pygame.transform.rotate(bird, -angle)
        rect = rotated.get_rect(center=(int(self.bird_x), int(self.bird_y)))
        surf.blit(rotated, rect.topleft)

    def _draw_pipe_body(self, surf, x, y, w, h):
        """Pipe shaft with a vertical light->shadow gradient. Looks tubular-ish."""
        if h <= 0:
            return
        # main body
        pygame.draw.rect(surf, PIPE_COL, (x, y, w, h))
        # bright vertical highlight strip on the left third
        hl_w = max(6, w // 4)
        pygame.draw.rect(surf, PIPE_LIGHT, (x + 4, y, hl_w, h))
        # darker shadow band on the right
        sh_w = max(8, w // 3)
        pygame.draw.rect(surf, PIPE_DARK, (x + w - sh_w, y, sh_w, h))
        # outline
        pygame.draw.rect(surf, PIPE_OUTLN, (x, y, w, h), 2)

    def _draw_pipe_lip(self, surf, x, y):
        """The wider 'cap' at the open end of a pipe."""
        lw, lh = PIPE_W + 12, 24
        pygame.draw.rect(surf, PIPE_COL,   (x - 6, y, lw, lh))
        pygame.draw.rect(surf, PIPE_LIGHT, (x - 2, y + 2, max(8, lw // 4), lh - 4))
        pygame.draw.rect(surf, PIPE_DARK,  (x + lw - 14, y + 2, 10, lh - 4))
        pygame.draw.rect(surf, PIPE_OUTLN, (x - 6, y, lw, lh), 2)

    def _draw_pipe(self, surf, p):
        gx, gy = int(p["x"]), p["gap_y"]
        top_h = gy - PIPE_GAP // 2 - TOP_BAR
        bot_y = gy + PIPE_GAP // 2
        bot_h = self.h - GROUND_H - bot_y

        # soft shadow — small offset down-right, looks like cast shadow
        shadow = pygame.Surface((PIPE_W + 6, self.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 50), (3, TOP_BAR, PIPE_W, top_h))
        pygame.draw.rect(shadow, (0, 0, 0, 50), (3, bot_y,   PIPE_W, bot_h))
        surf.blit(shadow, (gx + 3, 3))

        # top pipe + its lip (lip sits at bottom)
        self._draw_pipe_body(surf, gx, TOP_BAR, PIPE_W, top_h)
        self._draw_pipe_lip(surf, gx, TOP_BAR + top_h - 24)
        # bottom pipe + lip
        self._draw_pipe_body(surf, gx, bot_y, PIPE_W, bot_h)
        self._draw_pipe_lip(surf, gx, bot_y)

    def draw(self, surf):
        surf.blit(self.sky, (0, TOP_BAR))

        # foreground clouds (drift across)
        for c in self.clouds:
            _draw_cloud(surf, int(c["x"]), int(c["y"]), c["scale"], alpha=210)

        # particles
        for p in self.particles:
            pygame.draw.circle(surf, (255, 255, 255, 180),
                               (int(p["x"]), int(p["y"])), p["r"])

        for pipe in self.pipes:
            self._draw_pipe(surf, pipe)

        # ground — sandy base
        gy = self.h - GROUND_H
        pygame.draw.rect(surf, GROUND_COL, (0, gy, self.w, GROUND_H))
        for i in range(-1, self.w // 40 + 2):
            x = i * 40 + self.ground_offset
            pygame.draw.line(surf, GROUND_DK, (x, gy), (x + 20, gy + 16), 2)

        # grass strip on top of the ground — bumpy edge
        pygame.draw.rect(surf, GRASS_DK, (0, gy - 3, self.w, 8))
        pygame.draw.rect(surf, GRASS_COL, (0, gy - 1, self.w, 4))
        # little grass tufts at irregular intervals (deterministic from offset)
        for i in range(self.w // 14 + 2):
            tx = (i * 14 + int(self.ground_offset)) % (self.w + 14) - 7
            pygame.draw.line(surf, GRASS_DK, (tx, gy - 1), (tx + 1, gy - 5), 2)
            pygame.draw.line(surf, GRASS_DK, (tx + 4, gy - 1), (tx + 5, gy - 4), 2)

        self._draw_bird(surf)

        # top bar
        pygame.draw.rect(surf, PANEL, (0, 0, self.w, TOP_BAR))
        draw_text(surf, f"Score: {self.score}", f_med, GOLD,
                  self.w // 2, TOP_BAR // 2)

        if not self.started and not self.dead:
            draw_text(surf, "Press SPACE or click to flap", f_small, TEXT,
                      self.w // 2, self.h // 2 - 70)

        if self.dead:
            ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 170))
            surf.blit(ov, (0, 0))
            draw_text(surf, "Game Over",            f_big, X_COL,
                      self.w // 2, self.h // 2 - 60)
            draw_text(surf, f"Score: {self.score}", f_med, GOLD,
                      self.w // 2, self.h // 2 - 8)
            draw_button(surf, "Play Again", self.btn_restart,
                        hover=mouse_over(self.btn_restart))


def run():
    FlappyGame().loop()
