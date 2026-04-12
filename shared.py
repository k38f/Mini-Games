"""
shared.py
=========
Colours, fonts, and small helper functions used by every game module.
Import everything with:  from shared import *
"""

import pygame

# ==============================================================================
#  WINDOW / CLOCK  (created once here, reused everywhere)
# ==============================================================================

pygame.init()

W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Mini Games Collection")
clock = pygame.time.Clock()
FPS   = 60

# ==============================================================================
#  COLOUR PALETTE
# ==============================================================================

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

# ==============================================================================
#  FONTS
# ==============================================================================

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
#  SHARED DRAW HELPERS
# ==============================================================================

def draw_text(surf, text, font, color, cx, cy):
    """Render text centred at (cx, cy)."""
    s = font.render(text, True, color)
    surf.blit(s, s.get_rect(center=(cx, cy)))


def draw_button(surf, label, rect, hover=False, col=None):
    """Filled rounded-rect button. col overrides the default accent colour."""
    c = col if col else (ACCENT_H if hover else ACCENT)
    pygame.draw.rect(surf, c, rect, border_radius=10)
    draw_text(surf, label, f_med, TEXT, rect.centerx, rect.centery)


def mouse_over(rect):
    """Return True if the mouse is inside rect."""
    return rect.collidepoint(pygame.mouse.get_pos())


def back_btn_rect():
    """Standard Back button in the top-left corner."""
    return pygame.Rect(12, 12, 88, 34)


def mode_select(title):
    """
    Ask the player: 2 Players, Easy AI, Medium AI, or Hard AI.
    Returns ("pvp", None) or ("ai", "easy"/"medium"/"hard").
    Returns None if the player pressed Back.
    """
    options = [
        ("2 Players",      ("pvp",  None)),
        ("vs AI  Easy",    ("ai", "easy")),
        ("vs AI  Medium",  ("ai", "medium")),
        ("vs AI  Hard",    ("ai", "hard")),
    ]
    btn_w, btn_h, gap = 280, 50, 14
    start_y = 210
    buttons = [(lbl, val,
                pygame.Rect(W // 2 - btn_w // 2,
                            start_y + i * (btn_h + gap), btn_w, btn_h))
               for i, (lbl, val) in enumerate(options)]

    back = back_btn_rect()

    while True:
        clock.tick(FPS)
        screen.fill(BG)
        draw_text(screen, title,         f_big,   TEXT,  W // 2, 105)
        draw_text(screen, "choose mode", f_small, MUTED, W // 2, 155)
        draw_button(screen, "Back", back, hover=mouse_over(back))
        for lbl, val, rect in buttons:
            draw_button(screen, lbl, rect, hover=mouse_over(rect))

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                import sys; sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if back.collidepoint(e.pos):
                    return None
                for lbl, val, rect in buttons:
                    if rect.collidepoint(e.pos):
                        return val

        pygame.display.flip()
