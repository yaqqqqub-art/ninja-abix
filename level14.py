"""
level14.py - Chapter 1 / Level 14 : NIGHT MUSEUM  ("GOLDEN MASK").
main_game.py theke:  level14.run(screen, clock, save, save_fn)

Lokkho: City Museum theke GOLDEN MASK churi kore getaway van e palao.
  - ELITE SQUAD (5 cop) - level 12 er cheye kothin.  FRONT = GOD MODE, BEHIND theke mar.
  - 3 bar dhora porle 3D ARREST -> JAIL.   JAIL e 3 OPTION (jail.py):
        PAY 10000 Tk   /   WAIT 1 MIN   /   BREAK OUT (3 BAR + 2 WINDOW)
  - Keycard door, PAGE e code, code lock, laser grid, thermite vault.
Reward 9000 Tk.
Balance: World14.ELITE_POLICE
"""
import math
import pygame

import hd_animation as HD
import sprites as SP
from level1 import GROUND_Y
from animation import WIDTH, HEIGHT, get_font
import heist as H
from heist import (HeistWorld, DoorFeature, CodeLockDoor, PageFeature, SweepGridFeature,
                   LootFeature, Tiled, draw_floor)
import level11 as L11
import level12 as L12


def draw_mask(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 3
    HD.glow(surf, (x, y), 58, (255, 214, 90), 130, 2.0)
    pygame.draw.ellipse(surf, (236, 196, 60), (x - 22, y - 28, 44, 56))
    pygame.draw.ellipse(surf, (255, 244, 170), (x - 22, y - 28, 44, 56), 3)
    for ex in (-9, 9):
        pygame.draw.ellipse(surf, (30, 24, 10), (x + ex - 6, y - 10, 12, 7))
    pygame.draw.line(surf, (30, 24, 10), (x, y - 2), (x, y + 8), 2)
    pygame.draw.arc(surf, (30, 24, 10), (x - 10, y + 6, 20, 12), math.pi, math.tau, 2)


def museum_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (44, 34, 50), (20, 16, 28))
    for x in range(30, w, 150):                         # thaam
        pygame.draw.rect(s, (86, 74, 92), (x, 40, 26, GROUND_Y - 40))
        pygame.draw.rect(s, (120, 104, 128), (x - 6, 40, 38, 12))
        pygame.draw.rect(s, (120, 104, 128), (x - 6, GROUND_Y - 14, 38, 14))
    for i in range(3):                                  # chhobi
        r = pygame.Rect(70 + i * 190, 110 + rnd.randint(-10, 10), 70, 90)
        pygame.draw.rect(s, (110, 80, 40), r.inflate(12, 12))
        pygame.draw.rect(s, rnd.choice(((60, 90, 140), (140, 70, 70), (70, 120, 90))), r)


LEDGES = [(900, 1040, 350),
          (2300, 2410, 365), (2460, 2570, 295), (2620, 2740, 225),
          (3900, 4000, 360), (4050, 4150, 290), (4200, 4320, 220),
          (5600, 5720, 355), (5780, 5900, 285)]
STARS = [(960, 312), (2680, 187), (4260, 182)]
CASH = [(450, GROUND_Y - 12), (1000, GROUND_Y - 12), (1900, GROUND_Y - 12), (2400, 330), (2680, 190),
        (3200, GROUND_Y - 12), (4100, 252), (4700, GROUND_Y - 12), (5300, GROUND_Y - 12),
        (5840, 250), (6300, GROUND_Y - 12), (7000, GROUND_Y - 12)]
GUARDS = [(700, 1000), (1800, 2100, "s"), (2900, 3250), (3500, 3800, "s"), (4500, 4800), (5400, 5600, "s"), (6100, 6400)]
DOGS = [(2000, 2250), (3100, 3350), (4700, 4950), (6500, 6800)]
CAMS = [(1700, 0.0), (3300, 1.7), (4800, 3.0), (6000, 0.8)]
CHECKPOINTS = [1300, 2800, 4300, 5500, 6900]
HINTS = [
    (0, 420, "NIGHT MUSEUM  -  steal the GOLDEN MASK"),
    (420, 900, "ELITE SQUAD (5 cops)!  Front = GOD MODE.  Hit from BEHIND"),
    (1250, 1480, "3 catches = 3D arrest.  In JAIL:  PAY 10000 / WAIT 1 MIN / BREAK OUT"),
    (1500, 1700, "MUSEUM HALL  -  use the KEYCARD (key 1)"),
    (3000, 3300, "Collect the PAGE  -  it has the CURATOR OFFICE code"),
    (4300, 4500, "CURATOR OFFICE:  press E and type the CODE"),
    (5000, 5300, "Laser grid ahead  -  rewire (key 6), or time it"),
    (5300, 5600, "MASK VAULT:  key 8 THERMITE"),
    (6500, 6900, "Take the MASK and run to the GETAWAY VAN!"),
]
SPOT_LINES = ["Thief in the museum!", "Elite squad, move in!", "Seal every door!"]
CHAT_LINES = ["The Golden Mask is priceless.", "Five of us. One thief.", "Never fight from the front."]


class BigHeist(L12.World12):
    """Level 14 / 15 er common base (World12 er upor)."""
    DOOR_X, IN_END, GOAL = 1500, 6700, 7400
    OUT_PAINT, IN_PAINT, SEEDS = staticmethod(L12.night_city), staticmethod(museum_wall), (141, 142)
    FLOOR = ((36, 34, 56), (14, 14, 28), (255, 200, 70), (50, 48, 76))
    TINT = (12, 4, 34, 70)
    LOOT_DRAW = staticmethod(draw_mask)
    LOOT_X = 6200
    PAGE_KEY = "museum_curator"
    LABELS = ("MUSEUM HALL", "CURATOR OFFICE CODE", "CURATOR OFFICE", "MASK VAULT")
    LASERS = [(5000, 5180, 0.0), (5200, 5380, 1.6)]
    PAGE_X, LOCK_X, VAULT_X = 3000, 4400, 5900
    JAIL3 = True
    JAIL_PAY = 10000

    def __init__(self, save, save_fn):
        self.bg_out = Tiled(600, self.OUT_PAINT, seed=self.SEEDS[0])
        self.bg_in = Tiled(600, self.IN_PAINT, seed=self.SEEDS[1])
        self.bust3d = None
        self.ubust = None
        HeistWorld.__init__(self, save, save_fn)

    def make_features(self):
        L = self.LABELS
        return [DoorFeature(self.DOOR_X, "keycard", L[0]),
                PageFeature(self.PAGE_X, self.PAGE_KEY, L[1]),
                CodeLockDoor(self.LOCK_X, self.PAGE_KEY, L[2]),
                SweepGridFeature(self.LASERS),
                DoorFeature(self.VAULT_X, "thermite", L[3]),
                LootFeature(self.LOOT_X, self.TARGET, self.LOOT_DRAW)]

    def draw_background(self, surf, cam):
        self.bg_out.draw(surf, cam)
        split, send = self.DOOR_X - cam, self.IN_END - cam
        if split < WIDTH and send > 0:
            clip = surf.get_clip()
            surf.set_clip(pygame.Rect(max(0, int(split)), 0, max(0, int(min(send, WIDTH) - max(0, split))), HEIGHT))
            self.bg_in.draw(surf, cam)
            surf.set_clip(clip)
        vx = self.GOAL_X - cam
        if -200 < vx < WIDTH + 200:
            L11.draw_van(surf, vx, self.t)
        top, bot, line, stripe = self.FLOOR
        draw_floor(surf, cam, top, bot, line, stripe=stripe, tile=90)

    def draw_fx(self, surf, cam):
        a0, a1 = self.DOOR_X - cam, self.IN_END - cam
        tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        tint.fill(self.TINT)
        if a1 > 0 and a0 < WIDTH:
            tint.fill((0, 0, 0, 0), (max(0, int(a0)), 0, max(0, int(min(a1, WIDTH) - max(0, a0))), HEIGHT))
        surf.blit(tint, (0, 0))
        st = getattr(self, "_pol", None)
        if st and st["p"] is self.p and st["cops"] and self.state == "play":
            on = int(self.t * 4) % 2 == 0
            wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            wash.fill((255, 40, 60, 18) if on else (60, 110, 255, 18))
            surf.blit(wash, (0, 0))


class World14(BigHeist):
    LEVEL_W = 7600
    LEDGES, STARS, CASH, GUARDS, DOGS, CAMS = LEDGES, STARS, CASH, GUARDS, DOGS, CAMS
    CHECKPOINTS, HINTS = CHECKPOINTS, HINTS
    GOAL_X = 7400
    TARGET = "GOLDEN MASK"
    REWARD = 9000
    BAIL = 10000
    WIN_TITLE = "GOLDEN MASK STOLEN!"
    SPOT_LINES, CHAT_LINES = SPOT_LINES, CHAT_LINES
    ELITE_POLICE = {"from": 300, "max": 5, "hp": 5, "knife": 1, "punch": 2, "catch_time": 1.2, "catch_max": 3,
                    "spawn_every": 5.0, "turn": 0.42, "speed": 215.0, "ko_time": 10.0}


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((6, 8, 22))
        cache.setdefault("t", Tiled(600, L12.night_city, seed=141)).draw(s, off)
        draw_floor(s, off, (36, 34, 56), (14, 14, 28), (255, 200, 70))

    return H.run_heist(screen, clock, save, save_fn, World14, "NIGHT MUSEUM",
                       ["Steal the GOLDEN MASK from the City Museum.",
                        "ELITE SQUAD (5 cops):  FRONT = GOD MODE.  Hit them from BEHIND.",
                        "JAIL:  PAY 10000 Tk  /  WAIT 1 MIN  /  BREAK OUT."],
                       back, lambda s, c, t: draw_mask(s, c, t),
                       "Night museum. Steal the golden mask. Five elite cops are waiting.")
