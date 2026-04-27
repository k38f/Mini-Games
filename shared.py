"""
shared.py — colours, fonts, helpers, base Game class.
"""

import sys
import pygame

# -------------------------------------------------------
#  window / clock
# -------------------------------------------------------

pygame.init()

# default size, but the window is resizable now
W, H = 800, 600
MIN_W, MIN_H = 640, 480

screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)
pygame.display.set_caption("Mini Games Collection")
clock = pygame.time.Clock()
FPS   = 60


def _resize(new_w, new_h):
    """Resize the global screen surface. Clamped to MIN_W / MIN_H."""
    global W, H, screen
    W = max(MIN_W, new_w)
    H = max(MIN_H, new_h)
    screen = pygame.display.set_mode((W, H), pygame.RESIZABLE)


def quit_app():
    pygame.quit()
    sys.exit()


# -------------------------------------------------------
#  colour palette
# -------------------------------------------------------

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
GREEN_DARK = ( 14,  24,  14)
GRID_DOT   = ( 30,  50,  30)
SN_HEAD    = ( 90, 220, 120)
SN_BODY    = ( 55, 165,  80)
SN_SCALE   = ( 45, 140,  65)
FOOD_COL   = (235,  75,  75)
GOMOKU_BG  = ( 22,  20,  14)
GOMOKU_LN  = ( 80,  70,  50)
WIN_GLOW   = (255, 220,  60)

# -------------------------------------------------------
#  fonts
# -------------------------------------------------------

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

# -------------------------------------------------------
#  draw helpers
# -------------------------------------------------------

def draw_text(surf, text, font, color, cx, cy):
    s = font.render(text, True, color)
    surf.blit(s, s.get_rect(center=(cx, cy)))


def draw_button(surf, label, rect, hover=False, col=None):
    c = col if col else (ACCENT_H if hover else ACCENT)
    pygame.draw.rect(surf, c, rect, border_radius=10)
    draw_text(surf, label, f_med, TEXT, rect.centerx, rect.centery)


def mouse_over(rect):
    return rect.collidepoint(pygame.mouse.get_pos())


def back_btn_rect():
    return pygame.Rect(12, 12, 88, 34)


# -------------------------------------------------------
#  base Game class
# -------------------------------------------------------

class Game:
    """
    Base for a single game / screen.

    Subclasses override:
      handle_event(e)  -> return True to exit back to menu
      update(dt)
      draw(surf)
      on_resize(w, h)  — recompute layout (called on init and on window resize)

    The base class handles QUIT, window resize and the Back button.
    """

    # if True, base class draws Back button automatically and handles its click
    auto_back = True

    def __init__(self):
        self.w = W
        self.h = H
        self._back_rect = back_btn_rect()
        self.on_resize(self.w, self.h)

    # -- override these ----------------------------------

    def on_resize(self, w, h):
        self.w, self.h = w, h

    def handle_event(self, e):
        return False

    def update(self, dt):
        pass

    def draw(self, surf):
        pass

    # -- internals ---------------------------------------

    def _process_event(self, e):
        if e.type == pygame.QUIT:
            quit_app()
        if e.type == pygame.VIDEORESIZE:
            _resize(e.w, e.h)
            self.on_resize(W, H)
            return False
        if (self.auto_back
                and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1
                and self._back_rect.collidepoint(e.pos)):
            return True
        return self.handle_event(e)

    def loop(self):
        while True:
            dt = clock.tick(FPS)

            for e in pygame.event.get():
                if self._process_event(e):
                    return

            self.update(dt)
            self.draw(screen)

            if self.auto_back:
                draw_button(screen, "Back", self._back_rect,
                            hover=mouse_over(self._back_rect))

            pygame.display.flip()


# -------------------------------------------------------
#  mode select (used by TTT and Gomoku)
# -------------------------------------------------------

class _ModeSelect(Game):
    """Internal screen — pick 2P / Easy / Medium / Hard."""

    def __init__(self, title):
        self.title  = title
        self.result = None
        super().__init__()

    def on_resize(self, w, h):
        super().on_resize(w, h)
        options = [
            ("2 Players",      ("pvp",  None)),
            ("vs AI  Easy",    ("ai", "easy")),
            ("vs AI  Medium",  ("ai", "medium")),
            ("vs AI  Hard",    ("ai", "hard")),
        ]
        btn_w, btn_h, gap = 280, 50, 14
        total = len(options) * btn_h + (len(options) - 1) * gap
        start_y = max(200, (h - total) // 2 + 30)
        self.buttons = [
            (lbl, val,
             pygame.Rect(w // 2 - btn_w // 2,
                         start_y + i * (btn_h + gap), btn_w, btn_h))
            for i, (lbl, val) in enumerate(options)
        ]

    def handle_event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for lbl, val, rect in self.buttons:
                if rect.collidepoint(e.pos):
                    self.result = val
                    return True
        return False

    def draw(self, surf):
        surf.fill(BG)
        draw_text(surf, self.title,    f_big,   TEXT,  self.w // 2, 105)
        draw_text(surf, "choose mode", f_small, MUTED, self.w // 2, 155)
        for lbl, val, rect in self.buttons:
            draw_button(surf, lbl, rect, hover=mouse_over(rect))


def mode_select(title):
    """
    Ask the player: 2 Players / Easy / Medium / Hard.
    Returns ("pvp", None) or ("ai", "easy"/"medium"/"hard"), or None on Back.
    """
    m = _ModeSelect(title)
    m.loop()
    return m.result
