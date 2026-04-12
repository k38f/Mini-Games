"""
main.py
=======
Entry point for Mini Games Collection.

  - Shows the main menu
  - Checks GitHub for a newer version in the background (non-blocking)
  - Shows a fullscreen popup if an update is available
  - Shows red notice if the check failed (no internet)

Run:
    python main.py

Requirements:
    pip install pygame
"""

import sys
import threading
import urllib.request
import webbrowser
import json

import pygame
from shared import (
    screen, clock, FPS, W, H,
    BG, PANEL, TEXT, MUTED, GOLD, X_COL,
    f_huge, f_big, f_med, f_small, f_tiny,
    draw_text, draw_button, mouse_over,
)

import game_ttt
import game_gomoku
import game_guess
import game_snake

# ==============================================================================
#  VERSION
# ==============================================================================

CURRENT_VERSION = "1.1.0"   # keep in sync with the GitHub release tag (no 'v')

GITHUB_API    = "https://api.github.com/repos/k38f/Mini-Games/releases/latest"
RELEASES_PAGE = "https://github.com/k38f/Mini-Games/releases/latest"


# ==============================================================================
#  VERSION CHECK  (background thread)
# ==============================================================================

def _fetch_latest(result: list):
    """
    Fetch the latest release tag from GitHub.
    Writes tag string (e.g. "1.2.0") or "ERROR" into result[0].
    """
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


def _is_newer(latest: str, current: str) -> bool:
    """
    Compare version strings of any length.
    Pads shorter string with zeros: "1.0" == "1.0.0", "1.1" > "1.0.9" etc.
    """
    try:
        lp = [int(x) for x in latest.split(".")]
        cp = [int(x) for x in current.split(".")]
        n  = max(len(lp), len(cp))
        lp += [0] * (n - len(lp))
        cp += [0] * (n - len(cp))
        return lp > cp
    except ValueError:
        return False


# ==============================================================================
#  UPDATE POPUP  (fullscreen overlay)
# ==============================================================================

def show_update_popup(latest_version: str):
    """
    Fullscreen popup shown when a newer version is found.
    'Go to release' — opens browser on the releases page.
    'OK — play on'  — closes popup and continues.
    Shown only once per session.
    """
    btn_w, btn_h = 200, 50
    btn_go = pygame.Rect(W // 2 - btn_w - 16, H // 2 + 40, btn_w, btn_h)
    btn_ok = pygame.Rect(W // 2 + 16,          H // 2 + 40, btn_w, btn_h)

    while True:
        clock.tick(FPS)

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))

        draw_text(screen, "Update available!", f_big,  GOLD,  W // 2, H // 2 - 100)
        draw_text(screen, f"New version:  v{latest_version}", f_med, TEXT,  W // 2, H // 2 - 45)
        draw_text(screen, f"Your version: v{CURRENT_VERSION}", f_med, MUTED, W // 2, H // 2)

        draw_button(screen, "Go to release", btn_go, hover=mouse_over(btn_go))
        draw_button(screen, "OK - play on",  btn_ok, hover=mouse_over(btn_ok))

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_go.collidepoint(e.pos):
                    webbrowser.open(RELEASES_PAGE)
                    return
                if btn_ok.collidepoint(e.pos):
                    return

        pygame.display.flip()


# ==============================================================================
#  MAIN MENU
# ==============================================================================

def main_menu(version_result: list, update_info: dict, popup_shown: list):
    """
    Show the game picker.
    Polls the version check thread result on every frame so the status
    updates immediately without waiting to return to main().
    """
    entries = [
        ("1   Tic-Tac-Toe  (3x3)",     "ttt"),
        ("2   Gomoku  -  5 in a row",  "gomoku"),
        ("3   Guess the Number",        "guess"),
        ("4   Snake",                   "snake"),
    ]
    btn_w, btn_h, gap = 310, 52, 16
    start_y = 205
    buttons = [(lbl, gid,
                pygame.Rect(W // 2 - btn_w // 2,
                            start_y + i * (btn_h + gap), btn_w, btn_h))
               for i, (lbl, gid) in enumerate(entries)]

    while True:
        clock.tick(FPS)

        # ── Check thread result right here in the menu loop ───────────────────
        if update_info["state"] == "pending" and version_result[0] is not None:
            result = version_result[0]
            if result == "ERROR":
                update_info["state"] = "error"
            elif _is_newer(result, CURRENT_VERSION):
                update_info["state"]  = "newer"
                update_info["latest"] = result
            else:
                update_info["state"] = "ok"

        # Show popup once when newer version is detected
        if update_info["state"] == "newer" and not popup_shown[0]:
            popup_shown[0] = True
            show_update_popup(update_info["latest"])

        # ── Draw ──────────────────────────────────────────────────────────────
        screen.fill(BG)
        draw_text(screen, "Mini Games",  f_huge,  TEXT,  W // 2, 92)
        draw_text(screen, "pick a game", f_small, MUTED, W // 2, 152)

        # Version badge — bottom-left
        draw_text(screen, f"v{CURRENT_VERSION}", f_tiny, MUTED, 38, H - 14)

        # Status line — bottom-centre
        state = update_info["state"]
        if state == "pending":
            draw_text(screen, "Checking for updates...", f_tiny, MUTED, W // 2, H - 14)
        elif state == "ok":
            draw_text(screen, "Version is up to date", f_tiny, MUTED, W // 2, H - 14)
        elif state == "error":
            draw_text(screen, "Failed to check for updates — check your internet", f_tiny, X_COL, W // 2, H - 14)
        elif state == "newer":
            draw_text(screen, f"New version v{update_info['latest']} is available!", f_tiny, GOLD, W // 2, H - 14)

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
#  ENTRY POINT
# ==============================================================================

def main():
    pygame.display.set_caption("Mini Games Collection")

    version_result = [None]   # thread writes result here
    update_info    = {"state": "pending", "latest": ""}
    popup_shown    = [False]  # mutable flag so menu loop can update it

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
    }

    while True:
        choice = main_menu(version_result, update_info, popup_shown)
        games[choice]()


if __name__ == "__main__":
    main()