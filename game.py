"""
Mini Games Collection
=====================
Four mini-games in one window, built with Pygame.

  1   – Tic-Tac-Toe      (3×3, 2P or vs AI with 3 difficulty levels)
  1.2 – Gomoku           (5 in a row, big board, 2P or vs AI)
  2   – Guess the Number
  3   – Snake            (grid field, snake-like visuals)

Requirements:  pip install pygame
Run:           python mini_games.py
"""

import pygame
import sys
import random
import math

# ==============================================================================
#  SETUP
# ==============================================================================

pygame.init()

W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Mini Games Collection")
clock = pygame.time.Clock()
FPS  = 60

# ── Colour palette ─────────────────────────────────────────────────────────────
BG         = ( 15,  15,  25)
PANEL      = ( 28,  28,  45)
BORDER     = ( 55,  55,  85)
ACCENT     = (110,  80, 240)
ACCENT_H   = (140, 110, 255)
TEXT       = (220, 220, 235)
MUTED      = (130, 130, 150)
X_COL      = (240,  90,  90)
O_COL      = ( 80, 160, 240)
GOLD       = (255, 210,  50)
WHITE      = (255, 255, 255)
GREEN_DARK = ( 14,  24,  14)   # snake field background
GRID_DOT   = ( 30,  50,  30)   # faint grid dots on snake field
SN_HEAD    = ( 90, 220, 120)   # snake head — bright green
SN_BODY    = ( 55, 165,  80)   # snake body
SN_SCALE   = ( 45, 140,  65)   # alternating segment shade (scale effect)
FOOD_COL   = (235,  75,  75)   # food apple
GOMOKU_BG  = ( 22,  20,  14)   # warm dark for Gomoku board
GOMOKU_LN  = ( 80,  70,  50)   # Gomoku grid lines
WIN_GLOW   = (255, 220,  60)   # winning cells highlight colour

# ── Fonts ──────────────────────────────────────────────────────────────────────
def _font(size, bold=False):
    for name in ("Segoe UI", "Arial", "DejaVu Sans"):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

f_huge  = _font(56, bold=True)
f_big   = _font(38, bold=True)
f_med   = _font(26)
f_small = _font(20)
f_tiny  = _font(15)


# ==============================================================================
#  SHARED HELPERS
# ==============================================================================

def draw_text(surf, text, font, color, cx, cy):
    """Render text centred at (cx, cy)."""
    s = font.render(text, True, color)
    surf.blit(s, s.get_rect(center=(cx, cy)))


def draw_button(surf, label, rect, hover=False, col=None):
    """Filled rounded-rect button."""
    c = col if col else (ACCENT_H if hover else ACCENT)
    pygame.draw.rect(surf, c, rect, border_radius=10)
    draw_text(surf, label, f_med, TEXT, rect.centerx, rect.centery)


def mouse_over(rect):
    return rect.collidepoint(pygame.mouse.get_pos())


def back_btn_rect():
    return pygame.Rect(12, 12, 88, 34)


# ==============================================================================
#  MODE SELECTION SCREEN  (shared by Tic-Tac-Toe and Gomoku)
# ==============================================================================

def mode_select(title):
    """
    Ask the player: 2 Players, Easy AI, Medium AI, or Hard AI.
    Returns ("pvp", None)  or  ("ai", "easy"/"medium"/"hard").
    Returns None if the player pressed Back (go to main menu).
    """
    options = [
        ("2 Players",       ("pvp",  None)),
        ("vs AI  Easy",     ("ai", "easy")),
        ("vs AI  Medium",   ("ai", "medium")),
        ("vs AI  Hard",     ("ai", "hard")),
    ]
    btn_w, btn_h, gap = 280, 50, 14
    start_y = 210
    buttons = [(lbl, val,
                pygame.Rect(W//2 - btn_w//2,
                            start_y + i*(btn_h+gap), btn_w, btn_h))
               for i, (lbl, val) in enumerate(options)]

    back = back_btn_rect()

    while True:
        clock.tick(FPS)
        screen.fill(BG)
        draw_text(screen, title,          f_big,   TEXT,  W//2, 105)
        draw_text(screen, "choose mode",  f_small, MUTED, W//2, 155)
        draw_button(screen, "Back", back, hover=mouse_over(back))
        for lbl, val, rect in buttons:
            draw_button(screen, lbl, rect, hover=mouse_over(rect))

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if back.collidepoint(e.pos):
                    return None
                for lbl, val, rect in buttons:
                    if rect.collidepoint(e.pos):
                        return val

        pygame.display.flip()


# ==============================================================================
#  MAIN MENU
# ==============================================================================

def main_menu():
    entries = [
        ("1    Tic-Tac-Toe  (3x3)",     "ttt"),
        ("1.2  Gomoku  —  5 in a row",  "gomoku"),
        ("2    Guess the Number",        "guess"),
        ("3    Snake",                   "snake"),
    ]
    btn_w, btn_h, gap = 310, 52, 16
    start_y = 200
    buttons = [(lbl, gid,
                pygame.Rect(W//2 - btn_w//2,
                            start_y + i*(btn_h+gap), btn_w, btn_h))
               for i, (lbl, gid) in enumerate(entries)]

    while True:
        clock.tick(FPS)
        screen.fill(BG)
        draw_text(screen, "Mini Games",     f_huge,  TEXT,  W//2, 92)
        draw_text(screen, "pick a game",    f_small, MUTED, W//2, 152)
        for lbl, gid, rect in buttons:
            draw_button(screen, lbl, rect, hover=mouse_over(rect))

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for lbl, gid, rect in buttons:
                    if rect.collidepoint(e.pos):
                        return gid

        pygame.display.flip()


# ==============================================================================
#  GAME 1 — TIC-TAC-TOE  (3×3)
# ==============================================================================

def _ttt_check(board):
    """Return (symbol, winning_cells_list) or (None, None)."""
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


def _ttt_minimax(board, depth, is_max, ai_sym, hu_sym):
    """Full minimax for 3×3 — fast enough to be exact."""
    w, _ = _ttt_check(board)
    if w == ai_sym: return 10 - depth
    if w == hu_sym: return depth - 10
    empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]
    if not empty:   return 0

    if is_max:
        best = -99
        for r, c in empty:
            board[r][c] = ai_sym
            best = max(best, _ttt_minimax(board, depth+1, False, ai_sym, hu_sym))
            board[r][c] = None
        return best
    else:
        best = 99
        for r, c in empty:
            board[r][c] = hu_sym
            best = min(best, _ttt_minimax(board, depth+1, True, ai_sym, hu_sym))
            board[r][c] = None
        return best


def ttt_ai_move(board, ai_sym, hu_sym, difficulty):
    """Return (row, col) for the AI to play."""
    empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]
    if not empty:
        return None

    if difficulty == "easy":
        # Easy — purely random, makes obvious mistakes
        return random.choice(empty)

    if difficulty == "medium":
        # Medium — 40 % of the time picks randomly, otherwise uses minimax
        if random.random() < 0.40:
            return random.choice(empty)

    # Hard (and medium when not random) — perfect play via minimax
    best_score, best_move = -99, None
    for r, c in empty:
        board[r][c] = ai_sym
        s = _ttt_minimax(board, 0, False, ai_sym, hu_sym)
        board[r][c] = None
        if s > best_score:
            best_score, best_move = s, (r, c)
    return best_move


def game_ttt():
    """Tic-Tac-Toe — 3×3, two players or vs AI (easy / medium / hard)."""

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

        # ── Status bar ────────────────────────────────────────────────────────
        if winner:
            who = "AI" if (winner == ai_symbol and ai_plays) else winner
            c   = X_COL if winner == "X" else O_COL
            draw_text(screen, f"{who} wins!", f_big, c, W//2, 32)
        elif is_draw:
            draw_text(screen, "Draw!", f_big, GOLD, W//2, 32)
        elif ai_plays and current == ai_symbol:
            draw_text(screen, "AI is thinking...", f_big, MUTED, W//2, 32)
        else:
            lbl = "Your" if ai_plays else f"{current}'s"
            c   = X_COL if current == "X" else O_COL
            draw_text(screen, f"{lbl} turn  ({current})", f_big, c, W//2, 32)

        # ── Grid lines ────────────────────────────────────────────────────────
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

        # ── Winning highlight: glow cells + line through them ─────────────────
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

        # ── AI move (delayed slightly so it doesn't feel instant) ─────────────
        if ai_plays and current == ai_symbol and not winner and not is_draw:
            if not ai_thinking:
                ai_thinking = True
                ai_timer    = 0
            ai_timer += dt
            if ai_timer >= 400:
                ai_thinking = False
                move = ttt_ai_move(board, ai_symbol, hu_symbol, difficulty)
                if move:
                    r, c = move
                    board[r][c] = ai_symbol
                    winner, win_line = _ttt_check(board)
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
                                winner, win_line = _ttt_check(board)
                                if not winner:
                                    if all(board[rr][cc]
                                           for rr in range(3) for cc in range(3)):
                                        is_draw = True
                                    else:
                                        current = "O" if current == "X" else "X"

        pygame.display.flip()


# ==============================================================================
#  GAME 1.2 — GOMOKU  (5 in a row, scrollable 60×60 board)
# ==============================================================================

# ── AI helpers ────────────────────────────────────────────────────────────────

def _gom_candidates(board, rows, cols, radius=2):
    """Return empty cells within `radius` steps of any existing stone."""
    if not board:
        return [(rows//2, cols//2)]
    seen = set()
    for (br, bc) in board:
        for dr in range(-radius, radius+1):
            for dc in range(-radius, radius+1):
                nr, nc = br+dr, bc+dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in board:
                    seen.add((nr, nc))
    return list(seen) or [(rows//2, cols//2)]


def _gom_score_dir(board, row, col, dr, dc, player):
    """
    Score the line through (row,col) in direction ±(dr,dc) for `player`.
    Counts consecutive stones and open ends to estimate how good/dangerous this line is.
    """
    count = 1
    open_ends = 0
    for sign in (1, -1):
        r, c = row + dr*sign, col + dc*sign
        while board.get((r, c)) == player:
            count += 1
            r += dr*sign
            c += dc*sign
        if (r, c) not in board:   # end cell is empty → open end
            open_ends += 1

    if count >= 5: return 200_000
    if count == 4:
        if open_ends == 2: return  80_000   # open four — essentially wins next turn
        if open_ends == 1: return   2_500
    if count == 3:
        if open_ends == 2: return   6_000
        if open_ends == 1: return     350
    if count == 2:
        if open_ends == 2: return     200
        if open_ends == 1: return      25
    return 2


def _gom_eval_cell(board, row, col, player):
    """Total heuristic score for placing `player`'s stone at (row, col)."""
    board[(row, col)] = player
    score = sum(_gom_score_dir(board, row, col, dr, dc, player)
                for dr, dc in [(0,1),(1,0),(1,1),(1,-1)])
    del board[(row, col)]
    return score


def _gom_find_five(board, row, col, player):
    """
    After placing at (row,col), return the list of 5+ cells that form a winning line.
    Returns None if no 5-in-a-row was made.
    """
    for dr, dc in [(0,1),(1,0),(1,1),(1,-1)]:
        line = [(row, col)]
        for sign in (1, -1):
            r, c = row + dr*sign, col + dc*sign
            while board.get((r, c)) == player:
                line.append((r, c))
                r += dr*sign
                c += dc*sign
        if len(line) >= 5:
            return line[:5]
    return None


def gomoku_ai_move(board, ai, human, difficulty, rows, cols):
    """Return (row, col) for the AI's next stone placement."""
    candidates = _gom_candidates(board, rows, cols,
                                 radius=1 if difficulty == "easy" else 2)
    candidates = [(r, c) for r, c in candidates if (r, c) not in board]
    if not candidates:
        return (rows//2, cols//2)

    if difficulty == "easy":
        # Just pick a random nearby cell — no strategy
        return random.choice(candidates)

    best_score = -1
    best_move  = candidates[0]

    for r, c in candidates:
        ai_score  = _gom_eval_cell(board, r, c, ai)
        opp_score = _gom_eval_cell(board, r, c, human)

        # Hard AI defends threats more aggressively than medium
        defense = 1.25 if difficulty == "hard" else 0.95
        total   = ai_score + opp_score * defense

        if total > best_score:
            best_score = total
            best_move  = (r, c)

    return best_move


def game_gomoku():
    """Gomoku — 5 in a row on a scrollable 60×60 board. 2P or vs AI."""

    mode = mode_select("Gomoku  (5 in a row)")
    if mode is None:
        return

    pvp_mode, difficulty = mode
    ai_plays  = (pvp_mode == "ai")
    ai_symbol = "O"
    hu_symbol = "X"

    CELL      = 38
    COLS      = 60
    ROWS      = 60
    TOP_BAR   = 54
    view_cols = W // CELL
    view_rows = (H - TOP_BAR) // CELL

    # Camera starts centred on the board
    cam_x = COLS // 2 - view_cols // 2
    cam_y = ROWS // 2 - view_rows // 2

    def clamp_cam():
        nonlocal cam_x, cam_y
        cam_x = max(0, min(cam_x, COLS - view_cols))
        cam_y = max(0, min(cam_y, ROWS - view_rows))

    board       = {}    # (row, col) → "X" or "O"
    current     = "X"
    winner      = None
    win_cells   = None  # list of the 5 cells that made 5-in-a-row
    ai_timer    = 0
    ai_thinking = False
    btn_back    = back_btn_rect()

    while True:
        dt = clock.tick(FPS)
        screen.fill(GOMOKU_BG)

        # ── Top bar ───────────────────────────────────────────────────────────
        pygame.draw.rect(screen, PANEL, (0, 0, W, TOP_BAR))
        draw_button(screen, "Back", btn_back, hover=mouse_over(btn_back))

        diff_lbl = f"  [{difficulty}]" if ai_plays else ""
        if winner:
            who = "AI" if (winner == ai_symbol and ai_plays) else winner
            draw_text(screen,
                      f"{who} wins!  Press R to restart.",
                      f_small, GOLD, W//2 + 40, TOP_BAR//2)
        elif ai_plays and current == ai_symbol:
            draw_text(screen, f"AI thinking...{diff_lbl}",
                      f_small, MUTED, W//2 + 40, TOP_BAR//2)
        else:
            c = X_COL if current == "X" else O_COL
            draw_text(screen,
                      f"{current}'s turn{diff_lbl}  |  arrows / wheel to scroll",
                      f_small, c, W//2 + 40, TOP_BAR//2)

        # ── Board grid ────────────────────────────────────────────────────────
        for row in range(view_rows + 1):
            y = TOP_BAR + row * CELL
            pygame.draw.line(screen, GOMOKU_LN, (0, y), (W, y))
        for col in range(view_cols + 1):
            x = col * CELL
            pygame.draw.line(screen, GOMOKU_LN, (x, TOP_BAR), (x, H))

        # ── Stones ────────────────────────────────────────────────────────────
        for (br, bc), player in board.items():
            sc = bc - cam_x
            sr = br - cam_y
            if 0 <= sc < view_cols and 0 <= sr < view_rows:
                cx = sc * CELL + CELL // 2
                cy = TOP_BAR + sr * CELL + CELL // 2
                color = X_COL if player == "X" else O_COL
                pygame.draw.circle(screen, color, (cx, cy), CELL//2 - 3)
                draw_text(screen, player, f_tiny, WHITE, cx, cy)

        # ── Winning-line highlight (pulsing glow + connecting line) ───────────
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
                    # Glowing ring around each winning stone
                    glow = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (*WIN_GLOW, alpha),
                                       (CELL//2, CELL//2), CELL//2 - 1, 4)
                    screen.blit(glow, (cx - CELL//2, cy - CELL//2))
            if len(screen_pts) >= 2:
                pygame.draw.line(screen, WIN_GLOW,
                                 screen_pts[0], screen_pts[-1], 3)

        # Small camera-position indicator (useful while panning)
        draw_text(screen, f"({cam_x},{cam_y})", f_tiny, MUTED, W-40, H-10)

        # ── AI move ───────────────────────────────────────────────────────────
        if ai_plays and current == ai_symbol and not winner:
            if not ai_thinking:
                ai_thinking = True
                ai_timer    = 0
            ai_timer += dt
            delay = 250 if difficulty == "easy" else 550
            if ai_timer >= delay:
                ai_thinking = False
                r, c = gomoku_ai_move(board, ai_symbol, hu_symbol,
                                      difficulty, ROWS, COLS)
                board[(r, c)] = ai_symbol
                wc = _gom_find_five(board, r, c, ai_symbol)
                if wc:
                    winner    = ai_symbol
                    win_cells = wc
                else:
                    current = hu_symbol

        # ── Events ────────────────────────────────────────────────────────────
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
                        if (br, bc) not in board and 0 <= br < ROWS and 0 <= bc < COLS:
                            board[(br, bc)] = current
                            wc = _gom_find_five(board, br, bc, current)
                            if wc:
                                winner    = current
                                win_cells = wc
                            else:
                                current = "O" if current == "X" else "X"
                                ai_thinking = False

                if e.button == 4: cam_y -= 1; clamp_cam()   # scroll up
                if e.button == 5: cam_y += 1; clamp_cam()   # scroll down

        pygame.display.flip()


# ==============================================================================
#  GAME 2 — GUESS THE NUMBER
# ==============================================================================

def game_guess():
    """Computer picks 1–100, player types guesses and gets hints."""

    def start():
        return {
            "secret":   random.randint(1, 100),
            "attempts": 0,
            "input":    "",
            "message":  "I picked a number from 1 to 100...",
            "msg_col":  TEXT,
            "won":      False,
            "history":  [],
        }

    state    = start()
    btn_back = back_btn_rect()

    def submit(st):
        if not st["input"].isdigit():
            st["message"] = "Type a number!"; st["msg_col"] = X_COL; return
        g = int(st["input"]); st["input"] = ""
        if not 1 <= g <= 100:
            st["message"] = "Must be 1-100!"; st["msg_col"] = X_COL; return
        st["attempts"] += 1
        if g == st["secret"]:
            st["message"] = f"Correct! It was {st['secret']}."
            st["msg_col"] = GOLD; st["won"] = True
            st["history"].append((g, "Correct!"))
        elif g > st["secret"]:
            st["message"] = "Too high — go lower."
            st["msg_col"] = X_COL
            st["history"].append((g, "Too high"))
        else:
            st["message"] = "Too low — go higher."
            st["msg_col"] = O_COL
            st["history"].append((g, "Too low"))

    while True:
        clock.tick(FPS)
        screen.fill(BG)

        draw_button(screen, "Back", btn_back, hover=mouse_over(btn_back))
        draw_text(screen, "Guess the Number",     f_big,   TEXT,            W//2, 52)
        draw_text(screen, state["message"],       f_med,   state["msg_col"],W//2, 110)
        draw_text(screen, f"Attempts: {state['attempts']}", f_small, MUTED, W//2, 148)

        input_rect = pygame.Rect(W//2 - 100, 178, 200, 46)
        pygame.draw.rect(screen, PANEL, input_rect, border_radius=8)
        pygame.draw.rect(screen, ACCENT, input_rect, 2, border_radius=8)
        draw_text(screen, state["input"] + "|", f_med, TEXT,
                  input_rect.centerx, input_rect.centery)

        btn_guess = pygame.Rect(W//2 - 65, 240, 130, 42)
        draw_button(screen, "Guess!", btn_guess, hover=mouse_over(btn_guess))

        draw_text(screen, "History:", f_small, MUTED, W//2, 308)
        for i, (g, hint) in enumerate(state["history"][-6:]):
            hcol = GOLD if hint == "Correct!" else (X_COL if hint == "Too high" else O_COL)
            draw_text(screen, f"{g}  ->  {hint}", f_small, hcol, W//2, 332 + i*28)

        btn_again = pygame.Rect(W//2 - 95, H-72, 190, 46)
        if state["won"]:
            draw_button(screen, "Play Again", btn_again, hover=mouse_over(btn_again))

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_back.collidepoint(e.pos): return
                if not state["won"] and btn_guess.collidepoint(e.pos): submit(state)
                if state["won"]     and btn_again.collidepoint(e.pos): state = start()
            if e.type == pygame.KEYDOWN and not state["won"]:
                if e.key == pygame.K_RETURN:       submit(state)
                elif e.key == pygame.K_BACKSPACE:  state["input"] = state["input"][:-1]
                elif e.unicode.isdigit() and len(state["input"]) < 3:
                    state["input"] += e.unicode

        pygame.display.flip()


# ==============================================================================
#  GAME 3 — SNAKE  (grid field + snake-like visuals)
# ==============================================================================

def game_snake():
    """
    Classic Snake.
    The play field shows a subtle dot grid.
    The snake has a proper head (with eyes) and a scaly body.
    Arrow keys or WASD to turn. Speed increases every 5 foods.
    """

    CELL       = 20
    TOP_BAR    = 54
    COLS       = W // CELL
    ROWS       = (H - TOP_BAR) // CELL
    BASE_SPEED = 10   # moves per second at start

    def spawn_food(occupied):
        """Pick a random free cell for the food."""
        while True:
            pos = (random.randint(0, COLS-1), random.randint(0, ROWS-1))
            if pos not in occupied:
                return pos

    def new_game():
        snake = [(COLS//2, ROWS//2),
                 (COLS//2-1, ROWS//2),
                 (COLS//2-2, ROWS//2)]
        direction = (1, 0)
        return snake, direction, spawn_food(set(snake)), 0

    snake, direction, food, score = new_game()
    next_dir   = direction   # buffered input — prevents 180-flip
    game_over  = False
    move_timer = 0
    btn_back   = back_btn_rect()

    def draw_snake_body(surf, snake, direction):
        """
        Draw each segment of the snake.
        Head: rounded rect + two small eyes looking in the movement direction.
        Body: alternating shades to give a scale-like look.
        Tail: slightly smaller to look tapered.
        """
        n = len(snake)
        for i, (sx, sy) in enumerate(snake):
            x = sx * CELL
            y = TOP_BAR + sy * CELL

            if i == 0:
                # ── Head ──────────────────────────────────────────────────────
                pygame.draw.rect(surf, SN_HEAD,
                                 (x+1, y+1, CELL-2, CELL-2), border_radius=7)

                # Eyes — positioned based on which way we're heading
                dx, dy = direction
                # Perpendicular direction for the two eye offsets
                px, py = -dy, dx
                fw  = 4          # how far forward the eyes sit
                sep = 4          # how far apart the two eyes are
                ex  = x + CELL//2 + dx * fw
                ey  = y + CELL//2 + dy * fw
                for side in (1, -1):
                    ecx = int(ex + px * sep * side)
                    ecy = int(ey + py * sep * side)
                    pygame.draw.circle(surf, (20, 20, 20), (ecx, ecy), 3)   # pupil
                    pygame.draw.circle(surf, WHITE, (ecx-1, ecy-1), 1)      # shine

            else:
                # ── Body / Tail ────────────────────────────────────────────────
                # Alternating colour every segment mimics scales
                color  = SN_BODY if i % 2 == 0 else SN_SCALE
                # Tail is drawn a bit smaller so it tapers off visually
                shrink = 3 if i == n-1 else 1
                pygame.draw.rect(surf, color,
                                 (x + shrink, y + shrink,
                                  CELL - shrink*2, CELL - shrink*2),
                                 border_radius=5)

    while True:
        dt = clock.tick(FPS)

        # ── Background: dark green play field ─────────────────────────────────
        screen.fill(GREEN_DARK)

        # Subtle dot grid so the field looks like graph paper
        for col in range(COLS + 1):
            for row in range(ROWS + 1):
                pygame.draw.circle(screen, GRID_DOT,
                                   (col * CELL, TOP_BAR + row * CELL), 1)

        # ── Top bar (score + back button) ─────────────────────────────────────
        pygame.draw.rect(screen, PANEL, (0, 0, W, TOP_BAR))
        draw_button(screen, "Back", btn_back, hover=mouse_over(btn_back))
        draw_text(screen, f"Score: {score}", f_med, GOLD, W//2, TOP_BAR//2)

        speed         = BASE_SPEED + (score // 5) * 2
        move_interval = 1000 // speed   # ms between moves

        # ── Move snake ────────────────────────────────────────────────────────
        if not game_over:
            move_timer += dt
            if move_timer >= move_interval:
                move_timer = 0
                direction  = next_dir
                hx, hy     = snake[0]
                new_head   = (hx + direction[0], hy + direction[1])

                if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
                    game_over = True   # hit a wall
                elif new_head in snake:
                    game_over = True   # hit itself
                else:
                    snake.insert(0, new_head)
                    if new_head == food:
                        score += 1
                        food = spawn_food(set(snake))
                    else:
                        snake.pop()    # normal move — no growth

        # ── Food (pulsing circle with a shine dot) ────────────────────────────
        pulse = 1 + 0.15 * math.sin(pygame.time.get_ticks() * 0.008)
        fr    = int((CELL // 2 - 3) * pulse)
        fx    = food[0] * CELL + CELL // 2
        fy    = TOP_BAR + food[1] * CELL + CELL // 2
        pygame.draw.circle(screen, FOOD_COL, (fx, fy), fr)
        pygame.draw.circle(screen, (255, 180, 180),    # small shine
                           (fx - fr//3, fy - fr//3), max(1, fr//4))

        # ── Snake ─────────────────────────────────────────────────────────────
        draw_snake_body(screen, snake, direction)

        # ── Game-over overlay ─────────────────────────────────────────────────
        btn_restart = pygame.Rect(W//2 - 95, H//2 + 28, 190, 46)
        if game_over:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 170))
            screen.blit(ov, (0, 0))
            draw_text(screen, "Game Over",       f_big, X_COL, W//2, H//2 - 62)
            draw_text(screen, f"Score: {score}", f_med, GOLD,  W//2, H//2 - 12)
            draw_button(screen, "Play Again", btn_restart, hover=mouse_over(btn_restart))

        # ── Events ────────────────────────────────────────────────────────────
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.KEYDOWN:
                # Buffer direction change — can't reverse into yourself
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


# ==============================================================================
#  ENTRY POINT
# ==============================================================================

def main():
    games = {
        "ttt":    game_ttt,
        "gomoku": game_gomoku,
        "guess":  game_guess,
        "snake":  game_snake,
    }
    while True:
        choice = main_menu()
        games[choice]()


if __name__ == "__main__":
    main()
