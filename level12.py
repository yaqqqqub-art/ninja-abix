"""
level12.py - Chapter 1 / Level 12 : CITY POLICE TOWER  ("ELITE SQUAD").
main_game.py theke:  level12.run(screen, clock, save, save_fn)

Lokkho: Police Tower er shesh tola theke CHIEF er GOLD BADGE churi kore pichoner gali te getaway van e palao.

ELITE POLICE (police.py - level 11 er cheye kothin):
  - Level er prai shuru theke shob shomoy ashe.  Ekshathe 4 jon.  5 HP.
  - KNIFE (J) = 1 HP -> 5 knife.        SUPER PUNCH (K) = 2 HP -> 3 punch e KO.
  - GOD MODE:  police er SHAMNE (je dik e mukh) theke mar kaj kore NA.  Lafiye pichone jao, tarpor mar.
  - CATCH BAR:  dhorle matha r upor bar bhore, SPACE mere chharao.  3 bar dhora porle -> 3D ARREST -> JAIL.
        (pip install ursina  thakle REAL 3D Ursina animation, na thakle game er nijer pygame 3D)
Baki:  keycard door, PAGE e lekha CODE LOCK, laser grid, thermite vault.
Camera code: /CAMERA01099
"""
import math
import random
import pygame

import hd_animation as HD
import sprites as SP
import level1 as L1
from level1 import GROUND_Y, CEIL_Y
from animation import WIDTH, HEIGHT, get_font
import heist as H
from heist import (HeistWorld, DoorFeature, CodeLockDoor, PageFeature, SweepGridFeature,
                   LootFeature, Tiled, draw_floor)
import level11 as L11

LEVEL_W = 7600
GOAL = 7400
DOOR_X = 1500                     # TOWER lobby
IN_END = 6700                     # er pore abar bairer


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_badge(surf, c, t):
    """CHIEF's GOLD BADGE."""
    x, y = c
    y += math.sin(t * 3) * 3
    HD.glow(surf, (x, y), 58, (255, 214, 90), 130, 2.0)
    pts = []
    for i in range(10):
        r = 22 if i % 2 == 0 else 11
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
    pygame.draw.polygon(surf, (236, 196, 60), pts)
    pygame.draw.polygon(surf, (255, 244, 170), pts, 3)
    pygame.draw.circle(surf, (30, 50, 130), (int(x), int(y)), 8)
    pygame.draw.circle(surf, (255, 240, 180), (int(x), int(y)), 8, 2)


def night_city(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (6, 8, 22), (40, 26, 58))
    for _ in range(4):
        pygame.draw.ellipse(s, (22, 16, 40), (rnd.randint(-40, w), rnd.randint(10, 100), rnd.randint(180, 320), 50))
    for x in range(0, w, 90):                                       # tall towers
        bh = rnd.randint(160, 330)
        bw = rnd.randint(60, 90)
        pygame.draw.rect(s, (16, 18, 36), (x, GROUND_Y - bh - 40, bw, bh + 40))
        for wy in range(GROUND_Y - bh - 26, GROUND_Y - 50, 24):
            for wx in range(x + 8, x + bw - 10, 16):
                if rnd.random() < 0.4:
                    pygame.draw.rect(s, rnd.choice(((255, 214, 90), (120, 200, 255), (255, 120, 150))), (wx, wy, 7, 11))
    pygame.draw.rect(s, (18, 20, 36), (0, GROUND_Y - 44, w, 44))
    for x in range(40, w, 180):                                     # neon signs
        col = rnd.choice(((255, 60, 120), (60, 220, 255), (120, 255, 150)))
        pygame.draw.rect(s, col, (x, GROUND_Y - 120, 70, 6), border_radius=3)


def tower_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (26, 24, 56), (12, 12, 30))
    pygame.draw.rect(s, (8, 8, 22), (0, 0, w, 38))
    pygame.draw.rect(s, (255, 200, 70), (0, 38, w, 4))
    for x in range(0, w, 120):                                      # glass panels
        pygame.draw.rect(s, (20, 26, 60), (x + 6, 64, 108, GROUND_Y - 74), border_radius=4)
        pygame.draw.rect(s, (80, 90, 160), (x + 6, 64, 108, GROUND_Y - 74), 2, border_radius=4)
        pygame.draw.line(s, (50, 60, 120), (x + 60, 64), (x + 60, GROUND_Y - 10), 1)
    cx, cy = 300, 190                                               # big police emblem
    pygame.draw.circle(s, (230, 200, 60), (cx, cy), 56)
    pygame.draw.circle(s, (24, 40, 120), (cx, cy), 44)
    pygame.draw.circle(s, (230, 200, 60), (cx, cy), 44, 3)
    f = SP._font(18).render("ELITE", True, (255, 240, 180))
    s.blit(f, f.get_rect(center=(cx, cy)))


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(900, 1040, 350),
          (2300, 2410, 365), (2460, 2570, 295), (2620, 2740, 225),
          (3900, 4000, 360), (4050, 4150, 290), (4200, 4320, 220),
          (5600, 5720, 355), (5780, 5900, 285)]
STARS = [(960, 312), (2680, 187), (4260, 182)]
CASH = [(450, GROUND_Y - 12), (1000, GROUND_Y - 12), (1900, GROUND_Y - 12), (2400, 330), (2680, 190),
        (3200, GROUND_Y - 12), (4100, 252), (4700, GROUND_Y - 12), (5300, GROUND_Y - 12),
        (5840, 250), (6300, GROUND_Y - 12), (7000, GROUND_Y - 12)]
GUARDS = [(700, 1000), (1800, 2100), (2900, 3250), (3500, 3800), (4500, 4800, "s"), (5400, 5600), (6100, 6400, "s")]
DOGS = [(2000, 2250), (3100, 3350), (4700, 4950)]
CAMS = [(1700, 0.0), (3300, 1.7), (4800, 3.0), (6000, 0.8)]
CHECKPOINTS = [1300, 2800, 4300, 5500, 6900]
HINTS = [
    (0, 420, "CITY POLICE TOWER  -  steal the CHIEF'S GOLD BADGE"),
    (420, 900, "ELITE SQUAD (4 cops)!  FRONT = GOD MODE.  Jump over them and stab from BEHIND"),
    (900, 1250, "5 KNIFE hits (J) or 3 SUPER PUNCHES (K) - only from BEHIND.  Or outrun them"),
    (1250, 1480, "They grab you -> CATCH BAR fills.  Mash SPACE.  3 catches = 3D ARREST + JAIL"),
    (1500, 1700, "TOWER LOBBY  -  use the KEYCARD (key 1).  Closed doors stop the police too!"),
    (3000, 3300, "Collect the PAGE  -  it has the CHIEF OFFICE code"),
    (4300, 4500, "CHIEF OFFICE:  press E and type the CODE  (keycard does NOT work)"),
    (5000, 5300, "Laser grid ahead  -  rewire (key 6), or time it"),
    (5300, 5600, "BADGE VAULT:  key 8 THERMITE.  Police can't follow through a closed door"),
    (6500, 6900, "Take the BADGE and run to the GETAWAY VAN!"),
]
SPOT_LINES = ["Intruder in the Tower!", "Call the elite squad!", "Lock down the building!"]
CHAT_LINES = ["Elite squad is on patrol.", "Nobody reaches the Chief.", "They never fight from behind.",
              "Four of us. One thief."]


class World12(L11.World11):
    LEVEL_W = LEVEL_W
    LEDGES = LEDGES
    STARS = STARS
    CASH = CASH
    GUARDS = GUARDS
    DOGS = DOGS
    CAMS = CAMS
    CHECKPOINTS = CHECKPOINTS
    HINTS = HINTS
    GOAL_X = GOAL
    TARGET = "CHIEF'S GOLD BADGE"
    REWARD = 6000
    BAIL = 1200
    WIN_TITLE = "BADGE STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES
    # level 11 er cheye kothin:  4 jon, drut ashe, ektu tez, dhora tara-tari
    ELITE_POLICE = {"from": 300, "max": 4, "hp": 5, "knife": 1, "punch": 2, "catch_time": 1.3, "catch_max": 3,
                    "spawn_every": 5.5, "turn": 0.45, "speed": 210.0, "ko_time": 10.0}

    def __init__(self, save, save_fn):
        self.bg_out = Tiled(600, night_city, seed=91)
        self.bg_in = Tiled(600, tower_wall, seed=92)
        self.bust3d = None
        self.ubust = None
        HeistWorld.__init__(self, save, save_fn)      # World11.__init__ er notun bg bad (nijer bg)

    def make_features(self):
        return [DoorFeature(DOOR_X, "keycard", "TOWER LOBBY"),
                PageFeature(3000, "police_tower", "CHIEF OFFICE CODE"),
                CodeLockDoor(4400, "police_tower", "CHIEF OFFICE"),
                SweepGridFeature([(5000, 5180, 0.0), (5200, 5380, 1.6)]),
                DoorFeature(5700 + 200, "thermite", "BADGE VAULT"),
                LootFeature(6200, "CHIEF'S GOLD BADGE", draw_badge)]

    # ---------- look ----------
    def draw_background(self, surf, cam):
        self.bg_out.draw(surf, cam)
        split, send = DOOR_X - cam, IN_END - cam
        if split < WIDTH and send > 0:
            clip = surf.get_clip()
            surf.set_clip(pygame.Rect(max(0, int(split)), 0, max(0, int(min(send, WIDTH) - max(0, split))), HEIGHT))
            self.bg_in.draw(surf, cam)
            surf.set_clip(clip)
        vx = GOAL - cam
        if -200 < vx < WIDTH + 200:
            L11.draw_van(surf, vx, self.t)
        draw_floor(surf, cam, (36, 34, 56), (14, 14, 28), (255, 200, 70), stripe=(50, 48, 76), tile=90)
        if split < WIDTH and send > 0:
            clip = surf.get_clip()
            surf.set_clip(pygame.Rect(max(0, int(split)), GROUND_Y, max(0, int(min(send, WIDTH) - max(0, split))), HEIGHT - GROUND_Y))
            SP.v_gradient(surf, pygame.Rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y), (50, 44, 90), (16, 16, 40))
            pygame.draw.line(surf, (255, 200, 70), (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
            surf.set_clip(clip)

    def draw_fx(self, surf, cam):
        a0, a1 = DOOR_X - cam, IN_END - cam
        tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        tint.fill((12, 4, 34, 70))
        if a1 > 0 and a0 < WIDTH:
            tint.fill((0, 0, 0, 0), (max(0, int(a0)), 0, max(0, int(min(a1, WIDTH) - max(0, a0))), HEIGHT))
        surf.blit(tint, (0, 0))
        st = getattr(self, "_pol", None)
        if st and st["p"] is self.p and st["cops"] and self.state == "play":      # police light wash
            on = int(self.t * 4) % 2 == 0
            wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            wash.fill((255, 40, 60, 18) if on else (60, 110, 255, 18))
            surf.blit(wash, (0, 0))


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((6, 8, 22))
        cache.setdefault("t", Tiled(600, night_city, seed=91)).draw(s, off)
        draw_floor(s, off, (36, 34, 56), (14, 14, 28), (255, 200, 70))

    return H.run_heist(screen, clock, save, save_fn, World12, "CITY POLICE TOWER",
                       ["Steal the CHIEF'S GOLD BADGE from the top of the Police Tower.",
                        "ELITE SQUAD (4 cops):  FRONT = GOD MODE.  Hit them from BEHIND.",
                        "3 catches = 3D arrest and JAIL.  Reach the getaway van."],
                       back, lambda s, c, t: draw_badge(s, c, t),
                       "City police tower. Steal the chief's badge. The elite squad is waiting.")
