"""game_snake.py — classic Snake. Arrow keys or WASD."""

import pygame
import random
import math
from shared import (
    Game,
    PANEL, X_COL, GOLD, WHITE,
    GREEN_DARK, GRID_DOT, SN_HEAD, SN_BODY, SN_SCALE, FOOD_COL,
    f_med,
    draw_text, draw_button, mouse_over,
)


CELL       = 20
TOP_BAR    = 54
BASE_SPEED = 10


def _make_bg(w, h, cols, rows):
    """Pre-render the green field with grid dots — saves 1k+ draw_circle calls per frame."""
    surf = pygame.Surface((w, h))
    surf.fill(GREEN_DARK)
    for col in range(cols + 1):
        for row in range(rows + 1):
            pygame.draw.circle(surf, GRID_DOT,
                               (col * CELL, TOP_BAR + row * CELL), 1)
    return surf


class SnakeGame(Game):
    def __init__(self):
        # state initialised from on_resize-derived dimensions
        super().__init__()
        self._new_game()

    def on_resize(self, w, h):
        super().on_resize(w, h)
        self.cols = w // CELL
        self.rows = (h - TOP_BAR) // CELL
        self.max_cells = self.cols * self.rows
        self.bg = _make_bg(w, h, self.cols, self.rows)
        self.btn_restart = pygame.Rect(w // 2 - 95, h // 2 + 28, 190, 46)

        # if a game is already in progress, clamp snake/food to new bounds
        if hasattr(self, "snake"):
            self.snake = [(min(x, self.cols-1), min(y, self.rows-1))
                          for x, y in self.snake]
            if self.food:
                fx, fy = self.food
                if fx >= self.cols or fy >= self.rows:
                    self.food = self._spawn_food()

    def _spawn_food(self):
        occupied = set(self.snake)
        if len(occupied) >= self.max_cells:
            return None
        # could get slow if board is nearly full but it's fine for ~20x27
        while True:
            pos = (random.randint(0, self.cols - 1),
                   random.randint(0, self.rows - 1))
            if pos not in occupied:
                return pos

    def _new_game(self):
        cx, cy = self.cols // 2, self.rows // 2
        self.snake     = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        # 5 segments felt too easy on smaller boards, 1 was too punishing
        self.direction = (1, 0)
        self.next_dir  = self.direction
        self.food      = self._spawn_food()
        self.score     = 0
        self.game_over = False
        self.move_timer = 0

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            d = self.direction
            if e.key in (pygame.K_UP,    pygame.K_w) and d != (0,  1): self.next_dir = (0, -1)
            if e.key in (pygame.K_DOWN,  pygame.K_s) and d != (0, -1): self.next_dir = (0,  1)
            if e.key in (pygame.K_LEFT,  pygame.K_a) and d != (1,  0): self.next_dir = (-1, 0)
            if e.key in (pygame.K_RIGHT, pygame.K_d) and d != (-1, 0): self.next_dir = (1,  0)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.game_over and self.btn_restart.collidepoint(e.pos):
                self._new_game()
        return False

    def update(self, dt):
        if self.game_over:
            return
        speed = BASE_SPEED + (self.score // 5) * 2
        move_interval = 1000 // speed
        self.move_timer += dt
        if self.move_timer >= move_interval:
            self.move_timer = 0
            self.direction  = self.next_dir
            hx, hy = self.snake[0]
            new_head = (hx + self.direction[0], hy + self.direction[1])

            if (not (0 <= new_head[0] < self.cols and 0 <= new_head[1] < self.rows)
                    or new_head in self.snake):
                self.game_over = True
            else:
                self.snake.insert(0, new_head)
                if new_head == self.food:
                    self.score += 1
                    self.food = self._spawn_food()
                    if self.food is None:
                        self.game_over = True   # filled the whole board, gg
                else:
                    self.snake.pop()

    def _draw_snake(self, surf):
        n = len(self.snake)
        dx, dy = self.direction
        for i, (sx, sy) in enumerate(self.snake):
            x = sx * CELL
            y = TOP_BAR + sy * CELL

            if i == 0:
                pygame.draw.rect(surf, SN_HEAD,
                                 (x+1, y+1, CELL-2, CELL-2), border_radius=7)
                px, py = -dy, dx
                fw, sep = 4, 4
                ex = x + CELL//2 + dx * fw
                ey = y + CELL//2 + dy * fw
                for side in (1, -1):
                    ecx = int(ex + px * sep * side)
                    ecy = int(ey + py * sep * side)
                    pygame.draw.circle(surf, (20, 20, 20), (ecx, ecy), 3)
                    pygame.draw.circle(surf, WHITE, (ecx - 1, ecy - 1), 1)
            else:
                color  = SN_BODY if i % 2 == 0 else SN_SCALE
                shrink = 3 if i == n - 1 else 1
                pygame.draw.rect(surf, color,
                                 (x + shrink, y + shrink,
                                  CELL - shrink*2, CELL - shrink*2),
                                 border_radius=5)

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))

        # food (pulsing + shine)
        if self.food:
            pulse = 1 + 0.15 * math.sin(pygame.time.get_ticks() * 0.008)
            fr    = int((CELL // 2 - 3) * pulse)
            fx    = self.food[0] * CELL + CELL // 2
            fy    = TOP_BAR + self.food[1] * CELL + CELL // 2
            pygame.draw.circle(surf, FOOD_COL, (fx, fy), fr)
            pygame.draw.circle(surf, (255, 180, 180),
                               (fx - fr//3, fy - fr//3), max(1, fr//4))

        self._draw_snake(surf)

        pygame.draw.rect(surf, PANEL, (0, 0, self.w, TOP_BAR))
        draw_text(surf, f"Score: {self.score}", f_med, GOLD,
                  self.w // 2, TOP_BAR // 2)

        if self.game_over:
            ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 170))
            surf.blit(ov, (0, 0))
            draw_text(surf, "Game Over",            f_med, X_COL, self.w//2, self.h//2 - 62)
            draw_text(surf, f"Score: {self.score}", f_med, GOLD,  self.w//2, self.h//2 - 12)
            draw_button(surf, "Play Again", self.btn_restart,
                        hover=mouse_over(self.btn_restart))


def run():
    SnakeGame().loop()
