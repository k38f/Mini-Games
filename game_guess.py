"""game_guess.py — Guess the Number (1-100)."""

import pygame
import sys
import random
from shared import (
    screen, clock, FPS, W, H,
    BG, PANEL, ACCENT, TEXT, MUTED, X_COL, O_COL, GOLD,
    f_big, f_med, f_small,
    draw_text, draw_button, mouse_over, back_btn_rect,
)

MAX_HISTORY = 6


def run():
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
        draw_text(screen, "Guess the Number",              f_big,   TEXT,            W//2, 52)
        draw_text(screen, state["message"],                f_med,   state["msg_col"],W//2, 110)
        draw_text(screen, f"Attempts: {state['attempts']}",f_small, MUTED,           W//2, 148)

        input_rect = pygame.Rect(W//2 - 100, 178, 200, 46)
        pygame.draw.rect(screen, PANEL,  input_rect, border_radius=8)
        pygame.draw.rect(screen, ACCENT, input_rect, 2, border_radius=8)
        draw_text(screen, state["input"] + "|", f_med, TEXT,
                  input_rect.centerx, input_rect.centery)

        btn_guess = pygame.Rect(W//2 - 65, 240, 130, 42)
        draw_button(screen, "Guess!", btn_guess, hover=mouse_over(btn_guess))

        draw_text(screen, "History:", f_small, MUTED, W//2, 308)
        for i, (g, hint) in enumerate(state["history"][-MAX_HISTORY:]):
            hcol = GOLD if hint == "Correct!" else (X_COL if hint == "Too high" else O_COL)
            draw_text(screen, f"{g}  ->  {hint}", f_small, hcol, W//2, 332 + i * 28)

        btn_again = pygame.Rect(W//2 - 95, H - 72, 190, 46)
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
