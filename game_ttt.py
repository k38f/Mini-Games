"""
game_ttt.py
===========
Game 1 — Tic-Tac-Toe (3×3).
Two players or vs AI (easy / medium / hard).
"""

import pygame
import sys
import random
from shared import (
    screen, clock, FPS, W, H,
    BG, BORDER, TEXT, MUTED, X_COL, O_COL, GOLD, WIN_GLOW,
    f_big, f_med, f_small,
    draw_text, draw_button, mouse_over, back_btn_rect, mode_select,
)

# ==============================================================================
#  WIN DETECTION
# ==============================================================================

def _check(board):
    """Return (symbol, winning_cells) or (None, None)."""
    lines = (
        [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],
        [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],
        [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)],
    )
    for line in lines:
        vals = [board[r][c] for r, c in line]
        if vals[0] and vals[0] == vals[1] == vals[2]:
            return vals[0], list(line)
    return None, None


# ==============================================================================
#  MINIMAX AI
# ==============================================================================

def _minimax(board, depth, is_max, ai_sym, hu_sym):
    """Full minimax — 3×3 is small enough to solve exactly."""
    w, _ = _check(board)
    if w == ai_sym: return 10 - depth
    if w == hu_sym: return depth - 10
    empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]
    if not empty:   return 0

    if is_max:
        best = -99
        for r, c in empty:
            board[r][c] = ai_sym
            best = max(best, _minimax(board, depth+1, False, ai_sym, hu_sym))
            board[r][c] = None
        return best
    else:
        best = 99
        for r, c in empty:
            board[r][c] = hu_sym
            best = min(best, _minimax(board, depth+1, True, ai_sym, hu_sym))
            board[r][c] = None
        return best


def ai_move(board, ai_sym, hu_sym, difficulty):
    """Return (row, col) for the AI to play."""
    empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]
    if not empty:
        return None

    if difficulty == "easy":
        # Purely random — makes obvious mistakes
        return random.choice(empty)

    if difficulty == "medium" and random.random() < 0.40:
        # 40 % of the time pick randomly to feel more human
        return random.choice(empty)

    # Hard (and medium when not random) — perfect play via minimax
    best_score, best_move = -99, None
    for r, c in empty:
        board[r][c] = ai_sym
        s = _minimax(board, 0, False, ai_sym, hu_sym)
        board[r][c] = None
        if s > best_score:
            best_score, best_move = s, (r, c)
    return best_move


# ==============================================================================
#  MAIN GAME FUNCTION
# ==============================================================================

def run():
    """Entry point — called from main.py."""

    mode = mode_select("Tic-Tac-Toe")
    if mode is None:
        return   # player hit Back on the mode screen

    pvp_mode, difficulty = mode
    ai_plays  = (pvp_mode == "ai")
    ai_symbol = "O"   # AI is always O; human is X
    hu_symbol = "X"

    CELL = 132
    LEFT = (W - CELL * 3) // 2
    TOP  = 70

    def cell_rect(row, col):
        return pygame.Rect(LEFT + col * CELL, TOP + row * CELL, CELL, CELL)

    def reset():
        return [[None]*3 for _ in range(3)], "X", None, None, False

    board, current, winner, win_line, is_draw = reset()
    btn_back    = back_btn_rect()
    btn_restart = pygame.Rect(W//2 - 95, H - 78, 190, 46)
    ai_timer    = 0
    ai_thinking = False

    while True:
        dt = clock.tick(FPS)
        screen.fill(BG)

        # ── Status ────────────────────────────────────────────────────────────
        if winner:
            who = "AI" if (winner == ai_symbol and ai_plays) else winner
            draw_text(screen, f"{who} wins!", f_big,
                      X_COL if winner == "X" else O_COL, W//2, 32)
        elif is_draw:
            draw_text(screen, "Draw!", f_big, GOLD, W//2, 32)
        elif ai_plays and current == ai_symbol:
            draw_text(screen, "AI is thinking...", f_big, MUTED, W//2, 32)
        else:
            lbl = "Your" if ai_plays else f"{current}'s"
            draw_text(screen, f"{lbl} turn  ({current})", f_big,
                      X_COL if current == "X" else O_COL, W//2, 32)

        # ── Grid ──────────────────────────────────────────────────────────────
        for i in range(4):
            x = LEFT + i * CELL
            pygame.draw.line(screen, BORDER, (x, TOP), (x, TOP + CELL*3), 3)
            y = TOP + i * CELL
            pygame.draw.line(screen, BORDER, (LEFT, y), (LEFT + CELL*3, y), 3)

        # ── Symbols ───────────────────────────────────────────────────────────
        for row in range(3):
            for col in range(3):
                r   = cell_rect(row, col)
                val = board[row][col]
                pad = 30
                if val == "X":
                    pygame.draw.line(screen, X_COL,
                        (r.x+pad, r.y+pad), (r.right-pad, r.bottom-pad), 6)
                    pygame.draw.line(screen, X_COL,
                        (r.right-pad, r.y+pad), (r.x+pad, r.bottom-pad), 6)
                elif val == "O":
                    pygame.draw.circle(screen, O_COL, r.center,
                                       CELL//2 - pad + 4, 6)

        # ── Winning highlight: glowing cells + line through them ───────────────
        if win_line:
            for r, c in win_line:
                hl = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                hl.fill((255, 215, 0, 55))
                screen.blit(hl, cell_rect(r, c).topleft)
            p1 = cell_rect(*win_line[0]).center
            p2 = cell_rect(*win_line[2]).center
            pygame.draw.line(screen, WIN_GLOW, p1, p2, 5)

        # ── Buttons ───────────────────────────────────────────────────────────
        draw_button(screen, "Back", btn_back, hover=mouse_over(btn_back))
        if winner or is_draw:
            draw_button(screen, "Play Again", btn_restart,
                        hover=mouse_over(btn_restart))

        # ── AI move (small delay so it doesn't feel instant) ──────────────────
        if ai_plays and current == ai_symbol and not winner and not is_draw:
            if not ai_thinking:
                ai_thinking = True
                ai_timer    = 0
            ai_timer += dt
            if ai_timer >= 400:
                ai_thinking = False
                move = ai_move(board, ai_symbol, hu_symbol, difficulty)
                if move:
                    r, c = move
                    board[r][c] = ai_symbol
                    winner, win_line = _check(board)
                    if not winner:
                        if all(board[rr][cc] for rr in range(3) for cc in range(3)):
                            is_draw = True
                        else:
                            current = hu_symbol

        # ── Events ────────────────────────────────────────────────────────────
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_back.collidepoint(e.pos):
                    return
                if (winner or is_draw) and btn_restart.collidepoint(e.pos):
                    board, current, winner, win_line, is_draw = reset()
                    ai_thinking = False
                    continue

                is_human_turn = not (ai_plays and current == ai_symbol)
                if is_human_turn and not winner and not is_draw:
                    for row in range(3):
                        for col in range(3):
                            if (cell_rect(row, col).collidepoint(e.pos)
                                    and board[row][col] is None):
                                board[row][col] = current
                                winner, win_line = _check(board)
                                if not winner:
                                    if all(board[rr][cc]
                                           for rr in range(3) for cc in range(3)):
                                        is_draw = True
                                    else:
                                        current = "O" if current == "X" else "X"

        pygame.display.flip()
