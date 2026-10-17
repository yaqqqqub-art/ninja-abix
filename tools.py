"""
tools.py - Abix er 10 ta tool (v3: + WIRE CUTTER).

  - 3 ta tool ekhon use kora jay: LASER BREAKER, HACKER, LAPTOP
  - baki 6 ta COMING SOON
  - ABIX TOOLS screen (main menu theke) - goll (round) 9 ta tool, click korle detail.
  - Game e Ctrl+Alt (ba TAB) chaple 9 tool er wheel ashe; jegulo unlock segulo scroll kore beche nao.
"""
import math
import pygame

import sprites as SP
from animation import WIDTH, HEIGHT, WHITE, RED, GOLD, get_font, rgb_color

CAM_CODE = "/CAMERA01099"          # CCTV hack korte ei code type korte hobe
LASER_CODE = "/TKDIAMONDLASER"     # laser disable korte ei code type korte hobe

TOOLS = [
    {"id": "laser", "name": "LASER BREAKER", "key": "1",
     "info": ["Breaks / disables security lasers.", "(Level 2: silently cuts glass cases)", "",
              "Select it, stand near a laser, press E",
              "and TYPE the code:", f"      {LASER_CODE}"]},
    {"id": "hacker", "name": "HACKER", "key": "2",
     "info": ["Hacks a CCTV camera and DISABLES it.", "",
              "Select it, go near a camera, press E",
              "and TYPE the code:", f"      {CAM_CODE}", "A camera that sees you RECORDS you!"]},
    {"id": "laptop", "name": "LAPTOP", "key": "3",
     "info": ["Online coder.  Stand at a terminal, press L:", "a USB plugs in, laptop turns on (3D).",
              "Open WIRE CONNECT: join 3-4 wires to",
              "the matching ports (or Python: unlock)."]},
    {"id": "emp", "name": "EMP DISRUPTOR", "key": "4",
     "info": ["Fires a pulse wave through the room.", "",
              "For 5 seconds ALL cameras, lasers and",
              "lights go dead - the room turns dark."]},
    {"id": "decoy", "name": "DECOY DRONE", "key": "5",
     "info": ["Throws a virtual sound clone.", "",
              "Guards and dogs run to the noise,",
              "so the way behind them is clear."]},
    {"id": "rewirer", "name": "REWIRER PRO", "key": "6",
     "info": ["Rewires a laser sensor against the guards.", "",
              "Guards that walk into the laser die",
              "instantly. You can pass it safely."]},
    {"id": "smoke", "name": "SMOKE BOMB", "key": "7",
     "info": ["Spreads thick smoke around you.", "",
              "For 3 seconds guards are blind and dogs",
              "can't smell you - walk right past."]},
    {"id": "thermite", "name": "VAULT THERMITE", "key": "8",
     "info": ["Chemical that melts metal and lockers.", "",
              "No typing: melts a reinforced door or",
              "a side locker in 2 seconds (cash loot)."]},
    {"id": "keycard", "name": "MASTER KEYCARD", "key": "9",
     "info": ["Old clipboard scanner.", "",
              "It does NOT work on CODE LOCKS.",
              "Find the PAGE with the 4-digit code,",
              "press E at the door and type it."]},
    {"id": "cutter", "name": "WIRE CUTTER", "key": "0",
     "info": ["Cuts the wires of a locked terminal.", "(Normal tool - FREE, no money)", "",
              "ONLY in Level 3, 4, 5, 6, 8, 9.",
              "Lv4 = GREEN wire, Lv6 = RED, Lv8 = BLUE.",
              "Stand at a terminal, press E and",
              "cut the wires in the order on the note.",
              "A wrong wire = short circuit, try again."]},
]

UNLOCKED = [i for i, tl in enumerate(TOOLS) if tl["id"]]     # unlock kora tool er index


def tool_by_id(tool_id):
    for tl in TOOLS:
        if tl["id"] == tool_id:
            return tl
    return None


def _grid_centers(cx, cy, gx, gy, cols, rows, n=10):
    """10 ta tool er grid."""
    return [(cx + (c - (cols - 1) / 2.0) * gx, cy + (r - (rows - 1) / 2.0) * gy)
            for r in range(rows) for c in range(cols)][:n]


def draw_tool_circle(surf, tl, c, r, t, selected=False, hover=False, label=True):
    unlocked = tl["id"] is not None
    ring = rgb_color(t, offset=c[0] * 0.001) if (unlocked and (selected or hover)) else \
        ((90, 200, 130) if unlocked else (75, 75, 100))
    SP.glow(surf, c, r * 1.35, ring if unlocked else (60, 60, 90), 70 if selected else 28, 3)
    pygame.draw.circle(surf, (22, 24, 40) if unlocked else (24, 24, 38), (int(c[0]), int(c[1])), r)
    pygame.draw.circle(surf, ring, (int(c[0]), int(c[1])), r, 5 if selected else 3)
    SP.draw_tool_icon(surf, tl["id"], c, r * 0.62, t)
    if label:
        f = get_font(13)
        img = f.render(tl["name"] if unlocked else "COMING SOON", True, WHITE if unlocked else (120, 120, 145))
        surf.blit(img, img.get_rect(center=(int(c[0]), int(c[1] + r + 14))))


# ------------------------------------------------------------------
# ABIX TOOLS screen (main menu)
# ------------------------------------------------------------------
class ToolsScreen:
    R = 44

    def __init__(self):
        self.centers = _grid_centers(700, 285, 122, 122, 4, 3)
        self.selected = 0
        self.title = get_font(40)
        self.name_f = get_font(30)
        self.body_f = get_font(18)
        self.small = get_font(16)
        self.t = 0.0

    def open(self):
        self.selected = 0
        self.t = 0.0

    def index_at(self, mouse):
        for i, c in enumerate(self.centers):
            if (mouse[0] - c[0]) ** 2 + (mouse[1] - c[1]) ** 2 <= self.R ** 2:
                return i
        return None

    def click(self, mouse):
        i = self.index_at(mouse)
        if i is not None:
            self.selected = i
            return True
        return False

    def draw(self, screen, t, mouse, money):
        self.t = t
        title = self.title.render("ABIX TOOLS", True, WHITE)
        screen.blit(title, (40, 28))
        # wallet
        SP.draw_tk_coin(screen, (WIDTH - 150, 48), 17)
        w = self.name_f.render(f"{money} Tk", True, (110, 240, 150))
        screen.blit(w, w.get_rect(midleft=(WIDTH - 124, 48)))

        hover = self.index_at(mouse)
        for i, (tl, c) in enumerate(zip(TOOLS, self.centers)):
            draw_tool_circle(screen, tl, c, self.R, t, selected=(i == self.selected), hover=(i == hover))

        # detail panel
        panel = pygame.Rect(40, 110, 400, 330)
        pygame.draw.rect(screen, (20, 22, 38), panel, border_radius=18)
        pygame.draw.rect(screen, (90, 96, 130), panel, 3, border_radius=18)
        tl = TOOLS[self.selected]
        SP.draw_tool_icon(screen, tl["id"], (panel.x + 62, panel.y + 66), 40, t)
        nm = self.name_f.render(tl["name"], True, GOLD if tl["id"] else (140, 140, 165))
        screen.blit(nm, (panel.x + 120, panel.y + 40))
        y = panel.y + 130
        for ln in tl["info"]:
            img = self.body_f.render(ln, True, (205, 210, 230))
            screen.blit(img, (panel.x + 24, y))
            y += 28
        if tl["id"]:
            tag = self.small.render("UNLOCKED", True, (110, 240, 150))
            screen.blit(tag, (panel.x + 24, panel.bottom - 36))
        hint = self.small.render("Press ESC to go back   -   Click a tool to see details", True, (150, 150, 170))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 26)))


# ------------------------------------------------------------------
# Game-er bhitor Ctrl+Alt wheel
# ------------------------------------------------------------------
class ToolWheel:
    R = 46

    def __init__(self):
        self.centers = _grid_centers(WIDTH // 2, 255, 150, 130, 5, 2)
        self.title = get_font(30)
        self.small = get_font(15)

    def index_at(self, mouse):
        for i, c in enumerate(self.centers):
            if (mouse[0] - c[0]) ** 2 + (mouse[1] - c[1]) ** 2 <= self.R ** 2:
                return i
        return None

    def draw(self, surf, t, active_idx, mouse):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((4, 6, 14, 200))
        surf.blit(ov, (0, 0))
        img = self.title.render("TOOLS", True, WHITE)
        surf.blit(img, img.get_rect(center=(WIDTH // 2, 36)))
        hover = self.index_at(mouse)
        for i, (tl, c) in enumerate(zip(TOOLS, self.centers)):
            draw_tool_circle(surf, tl, c, self.R, t, selected=(i == active_idx), hover=(i == hover and tl["id"] is not None),
                             label=True)
        h1 = self.small.render("Scroll / Left Right = choose tool      Enter or click = use this tool      Ctrl+Alt / ESC = close",
                               True, (170, 175, 200))
        surf.blit(h1, h1.get_rect(center=(WIDTH // 2, HEIGHT - 24)))
        info = TOOLS[active_idx]
        if info["id"]:
            ln = self.small.render(info["info"][0], True, GOLD)
            surf.blit(ln, ln.get_rect(center=(WIDTH // 2, HEIGHT - 52)))
