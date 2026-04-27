"""
game_ttt.py — Tic-Tac-Toe (3×3).
Two players or vs AI (easy / medium / hard).
"""

import pygame
import random
from shared import (
    Game,
    BG, BORDER, TEXT, MUTED, X_COL, O_COL, GOLD, WIN_GLOW,
    f_big, f_med,
    draw_text, draw_button, mouse_over, mode_select,
)


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


# 3×3 is small enough to solve exactly with minimax
# alpha-beta would help but 9 cells doesn't even break a sweat
def _minimax(board, depth, is_max, ai_sym, hu_sym):
    w, _ = _check(board)
    if w == ai_sym: return 10 - depth
    if w == hu_sym: return depth - 10
    empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]
    if not empty:   return 0

    if is_max:
        best = -99
        for r, c in empty:
            board[r][c] = ai_sym
            best = max(best, _minimax(board, depth + 1, False, ai_sym, hu_sym))
            board[r][c] = None
        return best
    else:
        best = 99
        for r, c in empty:
            board[r][c] = hu_sym
            best = min(best, _minimax(board, depth + 1, True, ai_sym, hu_sym))
            board[r][c] = None
        return best


def ai_move(board, ai_sym, hu_sym, difficulty):
    empty = [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]
    if not empty:
        return None

    if difficulty == "easy":
        return random.choice(empty)

    if difficulty == "medium" and random.random() < 0.40:
        return random.choice(empty)

    best_score, best_move = -99, None
    for r, c in empty:
        board[r][c] = ai_sym
        s = _minimax(board, 0, False, ai_sym, hu_sym)
        board[r][c] = None
        if s > best_score:
            best_score, best_move = s, (r, c)
    return best_move


# ---------------------------------------------------------

class TttGame(Game):
    def __init__(self, ai_plays, difficulty):
        self.ai_plays   = ai_plays
        self.difficulty = difficulty
        self.ai_symbol  = "O"
        self.hu_symbol  = "X"
        self._reset()
        self.ai_timer    = 0
        self.ai_thinking = False
        super().__init__()

    def _reset(self):
        self.board    = [[None]*3 for _ in range(3)]
        self.current  = "X"
        self.winner   = None
        self.win_line = None
        self.is_draw  = False

    def on_resize(self, w, h):
        super().on_resize(w, h)
        # cell size scales with the smaller of width/height-margin; capped so
        # it doesn't get absurd on big monitors
        avail = min(w - 80, h - 200)
        self.cell = max(80, min(170, avail // 3))
        self.left = (w - self.cell * 3) // 2
        self.top  = max(70, (h - self.cell * 3) // 2 - 20)

        self.btn_restart = pygame.Rect(w // 2 - 95, h - 78, 190, 46)

    def _cell_rect(self, row, col):
        return pygame.Rect(self.left + col * self.cell,
                           self.top  + row * self.cell,
                           self.cell, self.cell)

    def update(self, dt):
        if (self.ai_plays and self.current == self.ai_symbol
                and not self.winner and not self.is_draw):
            if not self.ai_thinking:
                self.ai_thinking = True
                self.ai_timer = 0
            self.ai_timer += dt
            if self.ai_timer >= 400:
                self.ai_thinking = False
                move = ai_move(self.board, self.ai_symbol, self.hu_symbol,
                               self.difficulty)
                if move:
                    r, c = move
                    self.board[r][c] = self.ai_symbol
                    self.winner, self.win_line = _check(self.board)
                    if not self.winner:
                        if all(self.board[rr][cc]
                               for rr in range(3) for cc in range(3)):
                            self.is_draw = True
                        else:
                            self.current = self.hu_symbol

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if (self.winner or self.is_draw) and self.btn_restart.collidepoint(e.pos):
                self._reset()
                self.ai_thinking = False
                return False

            is_human_turn = not (self.ai_plays and self.current == self.ai_symbol)
            if is_human_turn and not self.winner and not self.is_draw:
                for row in range(3):
                    for col in range(3):
                        if (self._cell_rect(row, col).collidepoint(e.pos)
                                and self.board[row][col] is None):
                            self.board[row][col] = self.current
                            self.winner, self.win_line = _check(self.board)
                            if not self.winner:
                                if all(self.board[rr][cc]
                                       for rr in range(3) for cc in range(3)):
                                    self.is_draw = True
                                else:
                                    self.current = "O" if self.current == "X" else "X"
        return False

    def draw(self, surf):
        surf.fill(BG)
        w = self.w

        # status text
        if self.winner:
            who = "AI" if (self.winner == self.ai_symbol and self.ai_plays) else self.winner
            draw_text(surf, f"{who} wins!", f_big,
                      X_COL if self.winner == "X" else O_COL, w // 2, 32)
        elif self.is_draw:
            draw_text(surf, "Draw!", f_big, GOLD, w // 2, 32)
        elif self.ai_plays and self.current == self.ai_symbol:
            draw_text(surf, "AI is thinking...", f_big, MUTED, w // 2, 32)
        else:
            lbl = "Your" if self.ai_plays else f"{self.current}'s"
            draw_text(surf, f"{lbl} turn  ({self.current})", f_big,
                      X_COL if self.current == "X" else O_COL, w // 2, 32)

        # grid
        cell, left, top = self.cell, self.left, self.top
        for i in range(4):
            x = left + i * cell
            pygame.draw.line(surf, BORDER, (x, top), (x, top + cell*3), 3)
            y = top + i * cell
            pygame.draw.line(surf, BORDER, (left, y), (left + cell*3, y), 3)

        for row in range(3):
            for col in range(3):
                r   = self._cell_rect(row, col)
                val = self.board[row][col]
                pad = max(20, cell // 5)
                if val == "X":
                    pygame.draw.line(surf, X_COL,
                        (r.x+pad, r.y+pad), (r.right-pad, r.bottom-pad), 6)
                    pygame.draw.line(surf, X_COL,
                        (r.right-pad, r.y+pad), (r.x+pad, r.bottom-pad), 6)
                elif val == "O":
                    pygame.draw.circle(surf, O_COL, r.center,
                                       cell // 2 - pad + 4, 6)

        if self.win_line:
            for r, c in self.win_line:
                hl = pygame.Surface((cell, cell), pygame.SRCALPHA)
                hl.fill((255, 215, 0, 55))
                surf.blit(hl, self._cell_rect(r, c).topleft)
            p1 = self._cell_rect(*self.win_line[0]).center
            p2 = self._cell_rect(*self.win_line[2]).center
            pygame.draw.line(surf, WIN_GLOW, p1, p2, 5)

        if self.winner or self.is_draw:
            draw_button(surf, "Play Again", self.btn_restart,
                        hover=mouse_over(self.btn_restart))


def run():
    mode = mode_select("Tic-Tac-Toe")
    if mode is None:
        return
    pvp_mode, difficulty = mode
    TttGame(ai_plays=(pvp_mode == "ai"), difficulty=difficulty).loop()
