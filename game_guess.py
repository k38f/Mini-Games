"""game_guess.py — Guess the Number (1-100)."""

import pygame
import random
from shared import (
    Game,
    BG, PANEL, ACCENT, TEXT, MUTED, X_COL, O_COL, GOLD,
    f_big, f_med, f_small,
    draw_text, draw_button, mouse_over,
)

MAX_HISTORY = 6


class GuessGame(Game):
    def __init__(self):
        self._reset_state()
        super().__init__()

    def _reset_state(self):
        self.secret   = random.randint(1, 100)
        self.attempts = 0
        self.input    = ""
        self.message  = "I picked a number from 1 to 100..."
        self.msg_col  = TEXT
        self.won      = False
        self.history  = []

    def on_resize(self, w, h):
        super().on_resize(w, h)
        self.input_rect = pygame.Rect(w // 2 - 100, 178, 200, 46)
        self.btn_guess  = pygame.Rect(w // 2 - 65,  240, 130, 42)
        self.btn_again  = pygame.Rect(w // 2 - 95,  h - 72, 190, 46)

    def _submit(self):
        if not self.input.isdigit():
            self.message = "Type a number!"
            self.msg_col = X_COL
            return
        g = int(self.input)
        self.input = ""
        if not 1 <= g <= 100:
            self.message = "Must be 1-100!"
            self.msg_col = X_COL
            return
        self.attempts += 1
        if g == self.secret:
            self.message = f"Correct! It was {self.secret}."
            self.msg_col = GOLD
            self.won = True
            self.history.append((g, "Correct!"))
        elif g > self.secret:
            self.message = "Too high — go lower."
            self.msg_col = X_COL
            self.history.append((g, "Too high"))
        else:
            self.message = "Too low — go higher."
            self.msg_col = O_COL
            self.history.append((g, "Too low"))

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if not self.won and self.btn_guess.collidepoint(e.pos):
                self._submit()
            elif self.won and self.btn_again.collidepoint(e.pos):
                self._reset_state()
        if e.type == pygame.KEYDOWN and not self.won:
            if e.key == pygame.K_RETURN:
                self._submit()
            elif e.key == pygame.K_BACKSPACE:
                self.input = self.input[:-1]
            elif e.unicode.isdigit() and len(self.input) < 3:
                self.input += e.unicode
        return False

    def draw(self, surf):
        surf.fill(BG)
        w = self.w
        draw_text(surf, "Guess the Number",         f_big,   TEXT,         w // 2, 52)
        draw_text(surf, self.message,               f_med,   self.msg_col, w // 2, 110)
        draw_text(surf, f"Attempts: {self.attempts}", f_small, MUTED,       w // 2, 148)

        pygame.draw.rect(surf, PANEL,  self.input_rect, border_radius=8)
        pygame.draw.rect(surf, ACCENT, self.input_rect, 2, border_radius=8)
        draw_text(surf, self.input + "|", f_med, TEXT,
                  self.input_rect.centerx, self.input_rect.centery)

        draw_button(surf, "Guess!", self.btn_guess, hover=mouse_over(self.btn_guess))

        draw_text(surf, "History:", f_small, MUTED, w // 2, 308)
        for i, (g, hint) in enumerate(self.history[-MAX_HISTORY:]):
            hcol = GOLD if hint == "Correct!" else (X_COL if hint == "Too high" else O_COL)
            draw_text(surf, f"{g}  ->  {hint}", f_small, hcol, w // 2, 332 + i * 28)

        if self.won:
            draw_button(surf, "Play Again", self.btn_again,
                        hover=mouse_over(self.btn_again))


def run():
    GuessGame().loop()
