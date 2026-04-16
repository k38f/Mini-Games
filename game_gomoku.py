"""
game_gomoku.py — Gomoku (5 in a row) on a scrollable 60×60 board.
Two players or vs AI.
"""

import pygame
import sys
import random
import math
from shared import (
    screen, clock, FPS, W, H,
    PANEL, TEXT, MUTED, X_COL, O_COL, GOLD, WHITE, WIN_GLOW,
    GOMOKU_BG, GOMOKU_LN,
    f_small, f_tiny,
    draw_text, draw_button, mouse_over, back_btn_rect, mode_select,
)

BOARD_SIZE = 60


def _candidates(board, radius=2):
    """Empty cells within `radius` steps of any placed stone."""
    if not board:
        return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
    seen = set()
    for (br, bc) in board:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr, nc = br + dr, bc + dc
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and (nr, nc) not in board:
                    seen.add((nr, nc))
    return list(seen) or [(BOARD_SIZE // 2, BOARD_SIZE // 2)]


def _score_dir(board, row, col, dr, dc, player):
    """
    Score the line through (row,col) in direction ±(dr,dc).
    Counts consecutive stones and open/blocked ends.
    """
    count, open_ends = 1, 0
    for sign in (1, -1):
        r, c = row + dr * sign, col + dc * sign
        while board.get((r, c)) == player:
            count += 1
            r += dr * sign
            c += dc * sign
        # only count as open if the cell is in-bounds AND empty
        if (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE
                and (r, c) not in board):
            open_ends += 1

    if count >= 5: return 200_000
    if count == 4:
        if open_ends == 2: return  78_000
        if open_ends == 1: return   2_500
    if count == 3:
        if open_ends == 2: return   5_800
        if open_ends == 1: return     320
    if count == 2:
        if open_ends == 2: return     180
        if open_ends == 1: return      20
    return 2


def _eval_cell(board, row, col, player):
    board[(row, col)] = player
    score = sum(_score_dir(board, row, col, dr, dc, player)
                for dr, dc in [(0,1), (1,0), (1,1), (1,-1)])
    del board[(row, col)]
    return score


def _find_five(board, row, col, player):
    for dr, dc in [(0,1), (1,0), (1,1), (1,-1)]:
        line = [(row, col)]
        for sign in (1, -1):
            r, c = row + dr * sign, col + dc * sign
            while board.get((r, c)) == player:
                line.append((r, c))
                r += dr * sign
                c += dc * sign
        if len(line) >= 5:
            return line[:5]
    return None


def _ai_move(board, ai, human, difficulty):
    candidates = _candidates(board, radius=1 if difficulty == "easy" else 2)
    candidates = [(r, c) for r, c in candidates if (r, c) not in board]
    if not candidates:
        return (BOARD_SIZE // 2, BOARD_SIZE // 2)

    if difficulty == "easy":
        return random.choice(candidates)

    best_score, best_move = -1, candidates[0]
    for r, c in candidates:
        att = _eval_cell(board, r, c, ai)
        opp = _eval_cell(board, r, c, human)
        # defense = 1.15
        defense = 1.25 if difficulty == "hard" else 0.95
        total   = att + opp * defense
        if total > best_score:
            best_score, best_move = total, (r, c)
    return best_move


# ---------------------------------------------------------

def run():
    mode = mode_select("Gomoku  (5 in a row)")
    if mode is None:
        return

    pvp_mode, difficulty = mode
    ai_plays  = (pvp_mode == "ai")
    ai_symbol = "O"
    hu_symbol = "X"

    CELL      = 38
    TOP_BAR   = 54
    view_cols = W // CELL
    view_rows = (H - TOP_BAR) // CELL

    cam_x = BOARD_SIZE // 2 - view_cols // 2
    cam_y = BOARD_SIZE // 2 - view_rows // 2

    def clamp_cam():
        nonlocal cam_x, cam_y
        cam_x = max(0, min(cam_x, BOARD_SIZE - view_cols))
        cam_y = max(0, min(cam_y, BOARD_SIZE - view_rows))

    board       = {}
    current     = "X"
    winner      = None
    win_cells   = None
    ai_timer    = 0
    ai_thinking = False
    btn_back    = back_btn_rect()

    while True:
        dt = clock.tick(FPS)
        screen.fill(GOMOKU_BG)

        # top bar
        pygame.draw.rect(screen, PANEL, (0, 0, W, TOP_BAR))
        draw_button(screen, "Back", btn_back, hover=mouse_over(btn_back))

        diff_lbl = f"  [{difficulty}]" if ai_plays else ""
        if winner:
            who = "AI" if (winner == ai_symbol and ai_plays) else winner
            draw_text(screen, f"{who} wins!  Press R to restart.",
                      f_small, GOLD, W//2 + 40, TOP_BAR//2)
        elif ai_plays and current == ai_symbol:
            draw_text(screen, f"AI thinking...{diff_lbl}",
                      f_small, MUTED, W//2 + 40, TOP_BAR//2)
        else:
            c = X_COL if current == "X" else O_COL
            draw_text(screen,
                      f"{current}'s turn{diff_lbl}  |  arrows / wheel to scroll",
                      f_small, c, W//2 + 40, TOP_BAR//2)

        # grid lines
        for row in range(view_rows + 1):
            y = TOP_BAR + row * CELL
            pygame.draw.line(screen, GOMOKU_LN, (0, y), (W, y))
        for col in range(view_cols + 1):
            x = col * CELL
            pygame.draw.line(screen, GOMOKU_LN, (x, TOP_BAR), (x, H))

        # stones
        for (br, bc), player in board.items():
            sc = bc - cam_x
            sr = br - cam_y
            if 0 <= sc < view_cols and 0 <= sr < view_rows:
                cx = sc * CELL + CELL // 2
                cy = TOP_BAR + sr * CELL + CELL // 2
                color = X_COL if player == "X" else O_COL
                pygame.draw.circle(screen, color, (cx, cy), CELL//2 - 3)
                draw_text(screen, player, f_tiny, WHITE, cx, cy)

        # winning glow
        if win_cells:
            alpha = int(110 + 80 * math.sin(pygame.time.get_ticks() * 0.006))
            screen_pts = []
            for (br, bc) in win_cells:
                sc = bc - cam_x
                sr = br - cam_y
                cx = sc * CELL + CELL // 2
                cy = TOP_BAR + sr * CELL + CELL // 2
                if 0 <= sc < view_cols and 0 <= sr < view_rows:
                    screen_pts.append((cx, cy))
                    glow = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (*WIN_GLOW, alpha),
                                       (CELL//2, CELL//2), CELL//2 - 1, 4)
                    screen.blit(glow, (cx - CELL//2, cy - CELL//2))
            if len(screen_pts) >= 2:
                pygame.draw.line(screen, WIN_GLOW,
                                 screen_pts[0], screen_pts[-1], 3)

        draw_text(screen, f"({cam_x},{cam_y})", f_tiny, MUTED, W-40, H-10)

        # ai
        if ai_plays and current == ai_symbol and not winner:
            if not ai_thinking:
                ai_thinking = True
                ai_timer    = 0
            ai_timer += dt
            delay = 250 if difficulty == "easy" else 550
            if ai_timer >= delay:
                ai_thinking = False
                r, c = _ai_move(board, ai_symbol, hu_symbol, difficulty)
                board[(r, c)] = ai_symbol
                wc = _find_five(board, r, c, ai_symbol)
                if wc:
                    winner    = ai_symbol
                    win_cells = wc
                else:
                    current = hu_symbol

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_LEFT:  cam_x -= 1
                if e.key == pygame.K_RIGHT: cam_x += 1
                if e.key == pygame.K_UP:    cam_y -= 1
                if e.key == pygame.K_DOWN:  cam_y += 1
                clamp_cam()
                if e.key == pygame.K_r and winner:
                    board = {}; current = "X"
                    winner = None; win_cells = None; ai_thinking = False

            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if btn_back.collidepoint(e.pos):
                        return
                    human_turn = not (ai_plays and current == ai_symbol)
                    if not winner and human_turn and e.pos[1] >= TOP_BAR:
                        bc = e.pos[0] // CELL + cam_x
                        br = (e.pos[1] - TOP_BAR) // CELL + cam_y
                        if (br, bc) not in board and 0 <= br < BOARD_SIZE and 0 <= bc < BOARD_SIZE:
                            board[(br, bc)] = current
                            wc = _find_five(board, br, bc, current)
                            if wc:
                                winner    = current
                                win_cells = wc
                            else:
                                current = "O" if current == "X" else "X"
                                ai_thinking = False
                if e.button == 4: cam_y -= 1; clamp_cam()
                if e.button == 5: cam_y += 1; clamp_cam()

        pygame.display.flip()
