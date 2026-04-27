"""
game_gomoku.py — Gomoku (5 in a row) on a scrollable 60×60 board.
Two players or vs AI.
"""

import pygame
import random
import math
from shared import (
    Game,
    PANEL, TEXT, MUTED, X_COL, O_COL, GOLD, WHITE, WIN_GLOW,
    GOMOKU_BG, GOMOKU_LN,
    f_small, f_tiny,
    draw_text, draw_button, mouse_over, mode_select,
)

BOARD_SIZE = 60
CELL    = 38
TOP_BAR = 54


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
    count, open_ends = 1, 0
    for sign in (1, -1):
        r, c = row + dr * sign, col + dc * sign
        while board.get((r, c)) == player:
            count += 1
            r += dr * sign
            c += dc * sign
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

class GomokuGame(Game):
    def __init__(self, ai_plays, difficulty):
        self.ai_plays   = ai_plays
        self.difficulty = difficulty
        self.ai_symbol  = "O"
        self.hu_symbol  = "X"

        self.board     = {}
        self.current   = "X"
        self.winner    = None
        self.win_cells = None
        self.ai_timer    = 0
        self.ai_thinking = False
        super().__init__()

        # center camera
        self.cam_x = BOARD_SIZE // 2 - self.view_cols // 2
        self.cam_y = BOARD_SIZE // 2 - self.view_rows // 2
        self._clamp_cam()

    def on_resize(self, w, h):
        super().on_resize(w, h)
        self.view_cols = w // CELL
        self.view_rows = (h - TOP_BAR) // CELL
        if hasattr(self, "cam_x"):
            self._clamp_cam()

    def _clamp_cam(self):
        self.cam_x = max(0, min(self.cam_x, BOARD_SIZE - self.view_cols))
        self.cam_y = max(0, min(self.cam_y, BOARD_SIZE - self.view_rows))

    def _restart(self):
        self.board     = {}
        self.current   = "X"
        self.winner    = None
        self.win_cells = None
        self.ai_thinking = False

    def update(self, dt):
        if self.ai_plays and self.current == self.ai_symbol and not self.winner:
            if not self.ai_thinking:
                self.ai_thinking = True
                self.ai_timer    = 0
            self.ai_timer += dt
            delay = 250 if self.difficulty == "easy" else 550
            if self.ai_timer >= delay:
                self.ai_thinking = False
                r, c = _ai_move(self.board, self.ai_symbol, self.hu_symbol,
                                self.difficulty)
                self.board[(r, c)] = self.ai_symbol
                wc = _find_five(self.board, r, c, self.ai_symbol)
                if wc:
                    self.winner    = self.ai_symbol
                    self.win_cells = wc
                else:
                    self.current = self.hu_symbol

    def handle_event(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_LEFT:  self.cam_x -= 1
            if e.key == pygame.K_RIGHT: self.cam_x += 1
            if e.key == pygame.K_UP:    self.cam_y -= 1
            if e.key == pygame.K_DOWN:  self.cam_y += 1
            self._clamp_cam()
            if e.key == pygame.K_r and self.winner:
                self._restart()

        if e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                human_turn = not (self.ai_plays and self.current == self.ai_symbol)
                if not self.winner and human_turn and e.pos[1] >= TOP_BAR:
                    bc = e.pos[0] // CELL + self.cam_x
                    br = (e.pos[1] - TOP_BAR) // CELL + self.cam_y
                    if ((br, bc) not in self.board
                            and 0 <= br < BOARD_SIZE and 0 <= bc < BOARD_SIZE):
                        self.board[(br, bc)] = self.current
                        wc = _find_five(self.board, br, bc, self.current)
                        if wc:
                            self.winner    = self.current
                            self.win_cells = wc
                        else:
                            self.current = "O" if self.current == "X" else "X"
                            self.ai_thinking = False
            if e.button == 4: self.cam_y -= 1; self._clamp_cam()
            if e.button == 5: self.cam_y += 1; self._clamp_cam()
        return False

    def draw(self, surf):
        surf.fill(GOMOKU_BG)
        w, h = self.w, self.h

        # top bar
        pygame.draw.rect(surf, PANEL, (0, 0, w, TOP_BAR))

        diff_lbl = f"  [{self.difficulty}]" if self.ai_plays else ""
        if self.winner:
            who = "AI" if (self.winner == self.ai_symbol and self.ai_plays) else self.winner
            draw_text(surf, f"{who} wins!  Press R to restart.",
                      f_small, GOLD, w//2 + 40, TOP_BAR//2)
        elif self.ai_plays and self.current == self.ai_symbol:
            draw_text(surf, f"AI thinking...{diff_lbl}",
                      f_small, MUTED, w//2 + 40, TOP_BAR//2)
        else:
            col = X_COL if self.current == "X" else O_COL
            draw_text(surf,
                      f"{self.current}'s turn{diff_lbl}  |  arrows / wheel to scroll",
                      f_small, col, w//2 + 40, TOP_BAR//2)

        # grid lines
        for row in range(self.view_rows + 1):
            y = TOP_BAR + row * CELL
            pygame.draw.line(surf, GOMOKU_LN, (0, y), (w, y))
        for col in range(self.view_cols + 1):
            x = col * CELL
            pygame.draw.line(surf, GOMOKU_LN, (x, TOP_BAR), (x, h))

        # stones
        for (br, bc), player in self.board.items():
            sc = bc - self.cam_x
            sr = br - self.cam_y
            if 0 <= sc < self.view_cols and 0 <= sr < self.view_rows:
                cx = sc * CELL + CELL // 2
                cy = TOP_BAR + sr * CELL + CELL // 2
                color = X_COL if player == "X" else O_COL
                pygame.draw.circle(surf, color, (cx, cy), CELL//2 - 3)
                draw_text(surf, player, f_tiny, WHITE, cx, cy)

        # winning glow
        if self.win_cells:
            alpha = int(110 + 80 * math.sin(pygame.time.get_ticks() * 0.006))
            screen_pts = []
            for (br, bc) in self.win_cells:
                sc = bc - self.cam_x
                sr = br - self.cam_y
                cx = sc * CELL + CELL // 2
                cy = TOP_BAR + sr * CELL + CELL // 2
                if 0 <= sc < self.view_cols and 0 <= sr < self.view_rows:
                    screen_pts.append((cx, cy))
                    glow = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                    pygame.draw.circle(glow, (*WIN_GLOW, alpha),
                                       (CELL//2, CELL//2), CELL//2 - 1, 4)
                    surf.blit(glow, (cx - CELL//2, cy - CELL//2))
            if len(screen_pts) >= 2:
                pygame.draw.line(surf, WIN_GLOW,
                                 screen_pts[0], screen_pts[-1], 3)

        draw_text(surf, f"({self.cam_x},{self.cam_y})",
                  f_tiny, MUTED, w - 40, h - 10)


def run():
    mode = mode_select("Gomoku  (5 in a row)")
    if mode is None:
        return
    pvp_mode, difficulty = mode
    GomokuGame(ai_plays=(pvp_mode == "ai"), difficulty=difficulty).loop()
