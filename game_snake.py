"""game_snake.py — classic Snake. Arrow keys or WASD."""

import pygame
import sys
import random
import math
from shared import (
    screen, clock, FPS, W, H,
    PANEL, X_COL, GOLD, WHITE,
    GREEN_DARK, GRID_DOT, SN_HEAD, SN_BODY, SN_SCALE, FOOD_COL,
    f_med,
    draw_text, draw_button, mouse_over, back_btn_rect,
)


def run():
    CELL       = 20
    TOP_BAR    = 54
    COLS       = W // CELL
    ROWS       = (H - TOP_BAR) // CELL
    MAX_CELLS  = COLS * ROWS
    BASE_SPEED = 10

    def spawn_food(occupied):
        if len(occupied) >= MAX_CELLS:
            return None
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in occupied:
                return pos

    def new_game():
        snake = [(COLS//2, ROWS//2),
                 (COLS//2 - 1, ROWS//2),
                 (COLS//2 - 2, ROWS//2)]
        direction = (1, 0)
        return snake, direction, spawn_food(set(snake)), 0

    def draw_snake(surf, snake, direction):
        n = len(snake)
        for i, (sx, sy) in enumerate(snake):
            x = sx * CELL
            y = TOP_BAR + sy * CELL

            if i == 0:
                pygame.draw.rect(surf, SN_HEAD,
                                 (x+1, y+1, CELL-2, CELL-2), border_radius=7)
                dx, dy = direction
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

    snake, direction, food, score = new_game()
    next_dir   = direction
    game_over  = False
    move_timer = 0
    btn_back   = back_btn_rect()

    while True:
        dt = clock.tick(FPS)

        # TODO: could pre-render grid dots to a surface instead of every frame
        screen.fill(GREEN_DARK)
        for col in range(COLS + 1):
            for row in range(ROWS + 1):
                pygame.draw.circle(screen, GRID_DOT,
                                   (col * CELL, TOP_BAR + row * CELL), 1)

        pygame.draw.rect(screen, PANEL, (0, 0, W, TOP_BAR))
        draw_button(screen, "Back", btn_back, hover=mouse_over(btn_back))
        draw_text(screen, f"Score: {score}", f_med, GOLD, W//2, TOP_BAR//2)

        speed         = BASE_SPEED + (score // 5) * 2
        move_interval = 1000 // speed

        if not game_over:
            move_timer += dt
            if move_timer >= move_interval:
                move_timer = 0
                direction  = next_dir
                hx, hy     = snake[0]
                new_head   = (hx + direction[0], hy + direction[1])

                if (not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS)
                        or new_head in snake):
                    game_over = True
                else:
                    snake.insert(0, new_head)
                    if new_head == food:
                        score += 1
                        food = spawn_food(set(snake))
                        if food is None:
                            game_over = True   # filled the whole board, gg
                    else:
                        snake.pop()

        # food (pulsing + shine)
        if food:
            pulse = 1 + 0.15 * math.sin(pygame.time.get_ticks() * 0.008)
            fr    = int((CELL // 2 - 3) * pulse)
            fx    = food[0] * CELL + CELL // 2
            fy    = TOP_BAR + food[1] * CELL + CELL // 2
            pygame.draw.circle(screen, FOOD_COL, (fx, fy), fr)
            pygame.draw.circle(screen, (255, 180, 180),
                               (fx - fr//3, fy - fr//3), max(1, fr//4))

        draw_snake(screen, snake, direction)

        btn_restart = pygame.Rect(W//2 - 95, H//2 + 28, 190, 46)
        if game_over:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 170))
            screen.blit(ov, (0, 0))
            draw_text(screen, "Game Over",       f_med, X_COL, W//2, H//2 - 62)
            draw_text(screen, f"Score: {score}", f_med, GOLD,  W//2, H//2 - 12)
            draw_button(screen, "Play Again", btn_restart,
                        hover=mouse_over(btn_restart))

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP,    pygame.K_w) and direction != (0,  1): next_dir = (0, -1)
                if e.key in (pygame.K_DOWN,  pygame.K_s) and direction != (0, -1): next_dir = (0,  1)
                if e.key in (pygame.K_LEFT,  pygame.K_a) and direction != (1,  0): next_dir = (-1, 0)
                if e.key in (pygame.K_RIGHT, pygame.K_d) and direction != (-1, 0): next_dir = (1,  0)

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_back.collidepoint(e.pos): return
                if game_over and btn_restart.collidepoint(e.pos):
                    snake, direction, food, score = new_game()
                    next_dir = direction; game_over = False; move_timer = 0

        pygame.display.flip()
