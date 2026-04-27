"""
main.py — entry point for Mini Games Collection.
Run: python main.py
"""

import threading
import urllib.request
import webbrowser
import json

import pygame
import shared
from shared import (
    Game, quit_app,
    BG, TEXT, MUTED, GOLD, X_COL,
    f_huge, f_big, f_med, f_small, f_tiny,
    draw_text, draw_button, mouse_over,
)

import game_ttt
import game_gomoku
import game_guess
import game_snake
import game_flappy

# ---------------------------------------------------------

CURRENT_VERSION = "1.2.0"

GITHUB_API    = "https://api.github.com/repos/k38f/Mini-Games/releases/latest"
RELEASES_PAGE = "https://github.com/k38f/Mini-Games/releases/latest"


def _fetch_latest(result):
    """Fetch the latest release tag from GitHub into result[0]."""
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "MiniGames-VersionCheck"}
        )
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
            tag  = data.get("tag_name", "").lstrip("v")
            result[0] = tag if tag else "ERROR"
    except Exception:
        result[0] = "ERROR"


def _is_newer(latest, current):
    try:
        lp = [int(x) for x in latest.split(".")]
        cp = [int(x) for x in current.split(".")]
        n  = max(len(lp), len(cp))
        lp += [0] * (n - len(lp))
        cp += [0] * (n - len(cp))
        return lp > cp
    except ValueError:
        return False


# -- update popup ----------------------------------------

class UpdatePopup(Game):
    auto_back = False  # this screen has its own buttons

    def __init__(self, latest_version):
        self.latest_version = latest_version
        super().__init__()

    def on_resize(self, w, h):
        super().on_resize(w, h)
        btn_w, btn_h = 200, 50
        self.btn_go = pygame.Rect(w // 2 - btn_w - 16, h // 2 + 40, btn_w, btn_h)
        self.btn_ok = pygame.Rect(w // 2 + 16,         h // 2 + 40, btn_w, btn_h)

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.btn_go.collidepoint(e.pos):
                webbrowser.open(RELEASES_PAGE)
                return True
            if self.btn_ok.collidepoint(e.pos):
                return True
        return False

    def draw(self, surf):
        # popup is drawn over a darkened backdrop, but since we navigate
        # back to the menu after, just fill it black.
        ov = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        surf.fill(BG)
        surf.blit(ov, (0, 0))

        draw_text(surf, "Update available!", f_big, GOLD,
                  self.w // 2, self.h // 2 - 100)
        draw_text(surf, f"New version:  v{self.latest_version}", f_med, TEXT,
                  self.w // 2, self.h // 2 - 45)
        draw_text(surf, f"Your version: v{CURRENT_VERSION}", f_med, MUTED,
                  self.w // 2, self.h // 2)

        draw_button(surf, "Go to release", self.btn_go,
                    hover=mouse_over(self.btn_go))
        draw_button(surf, "OK - play on",  self.btn_ok,
                    hover=mouse_over(self.btn_ok))


# -- main menu -------------------------------------------

class MainMenu(Game):
    auto_back = False  # main menu has no Back

    def __init__(self, version_result, update_info, popup_shown):
        self.version_result = version_result
        self.update_info    = update_info
        self.popup_shown    = popup_shown
        self.choice         = None
        self.entries = [
            ("1   Tic-Tac-Toe  (3x3)",     "ttt"),
            ("2   Gomoku  -  5 in a row",  "gomoku"),
            ("3   Guess the Number",        "guess"),
            ("4   Snake",                   "snake"),
            ("5   Flappy Bird",             "flappy"),
        ]
        super().__init__()

    def on_resize(self, w, h):
        super().on_resize(w, h)
        btn_w, btn_h, gap = 310, 52, 16
        n = len(self.entries)
        total = n * btn_h + (n - 1) * gap
        start_y = max(185, (h - total) // 2 + 30)
        self.buttons = [
            (lbl, gid,
             pygame.Rect(w // 2 - btn_w // 2,
                         start_y + i * (btn_h + gap), btn_w, btn_h))
            for i, (lbl, gid) in enumerate(self.entries)
        ]

    def update(self, dt):
        # poll version check
        info = self.update_info
        if info["state"] == "pending" and self.version_result[0] is not None:
            r = self.version_result[0]
            if r == "ERROR":
                info["state"] = "error"
            elif _is_newer(r, CURRENT_VERSION):
                info["state"]  = "newer"
                info["latest"] = r
            else:
                info["state"] = "ok"

        if info["state"] == "newer" and not self.popup_shown[0]:
            self.popup_shown[0] = True
            UpdatePopup(info["latest"]).loop()

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for lbl, gid, rect in self.buttons:
                if rect.collidepoint(e.pos):
                    self.choice = gid
                    return True
        return False

    def draw(self, surf):
        surf.fill(BG)
        draw_text(surf, "Mini Games",  f_huge,  TEXT,  self.w // 2, 92)
        draw_text(surf, "pick a game", f_small, MUTED, self.w // 2, 152)

        draw_text(surf, f"v{CURRENT_VERSION}", f_tiny, MUTED, 38, self.h - 14)

        state = self.update_info["state"]
        if state == "pending":
            draw_text(surf, "Checking for updates...", f_tiny, MUTED,
                      self.w // 2, self.h - 14)
        elif state == "ok":
            draw_text(surf, "Version is up to date", f_tiny, MUTED,
                      self.w // 2, self.h - 14)
        elif state == "error":
            draw_text(surf, "Failed to check for updates — check your internet",
                      f_tiny, X_COL, self.w // 2, self.h - 14)
        elif state == "newer":
            draw_text(surf, f"New version v{self.update_info['latest']} is available!",
                      f_tiny, GOLD, self.w // 2, self.h - 14)

        for lbl, gid, rect in self.buttons:
            draw_button(surf, lbl, rect, hover=mouse_over(rect))


# ---------------------------------------------------------

def main():
    pygame.display.set_caption("Mini Games Collection")

    version_result = [None]
    update_info    = {"state": "pending", "latest": ""}
    popup_shown    = [False]

    checker = threading.Thread(
        target=_fetch_latest,
        args=(version_result,),
        daemon=True
    )
    checker.start()

    games = {
        "ttt":    game_ttt.run,
        "gomoku": game_gomoku.run,
        "guess":  game_guess.run,
        "snake":  game_snake.run,
        "flappy": game_flappy.run,
    }

    while True:
        menu = MainMenu(version_result, update_info, popup_shown)
        menu.loop()
        if menu.choice:
            games[menu.choice]()


if __name__ == "__main__":
    main()
