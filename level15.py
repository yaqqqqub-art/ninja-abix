"""
level15.py - Chapter 1 / Level 15 : ROYAL FORTRESS  (\"CROWN OF ABIX\")  - FINALE.
main_game.py theke:  level15.run(screen, clock, save, save_fn)

Lokkho: Fortress er shesh ghor theke CROWN OF ABIX churi kore getaway van e palao.
  - ELITE SQUAD 6 jon, tez, taratari dhore.   FRONT = GOD MODE -> BEHIND theke mar.
  - 3 bar dhora porle 3D ARREST -> JAIL:  PAY 10000 Tk  /  WAIT 1 MIN  /  BREAK OUT (3 BAR + 2 WINDOW)
  - Keycard door, PAGE e code, code lock, 3 ta laser grid, thermite vault.
Reward 15000 Tk.      Balance: World15.ELITE_POLICE
"""
import math
import pygame

import hd_animation as HD
import sprites as SP
from level1 import GROUND_Y
from animation import WIDTH, HEIGHT, get_font
import heist as H
from heist import Tiled, draw_floor
import level12 as L12
import level14 as L14


def draw_crown(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 3
    HD.glow(surf, (x, y), 64, (255, 120, 220), 130, 2.0)
    pts = [(x - 26, y + 14), (x - 26, y - 14), (x - 13, y), (x, y - 20), (x + 13, y), (x + 26, y - 14), (x + 26, y + 14)]
    pygame.draw.polygon(surf, (236, 196, 60), pts)
    pygame.draw.polygon(surf, (255, 244, 170), pts, 3)
    for dx, col in ((-16, (255, 80, 120)), (0, (90, 200, 255)), (16, (120, 255, 150))):
        pygame.draw.circle(surf, col, (x + dx, y + 6), 4)


def fortress_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (30, 30, 40), (14, 12, 20))
    for ry in range(0, GROUND_Y, 36):                   # pathor
        off = 0 if (ry // 36) % 2 == 0 else 40
        for rx in range(-40, w, 80):
            pygame.draw.rect(s, (54, 52, 66), (rx + off, ry, 78, 34), 2)
    for i in range(3):                                  # mosal
        tx = 90 + i * 200
        pygame.draw.rect(s, (80, 50, 30), (tx - 4, 160, 8, 36))
        pygame.draw.circle(s, (255, 170, 60), (tx, 150), 12)
        pygame.draw.circle(s, (255, 230, 140), (tx, 152), 6)


def castle_out(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (10, 6, 24), (46, 24, 52))
    for x in range(0, w, 160):
        th = rnd.randint(140, 260)
        pygame.draw.rect(s, (22, 16, 36), (x + 20, GROUND_Y - th, 90, th))
        for k in range(4):
            pygame.draw.rect(s, (22, 16, 36), (x + 20 + k * 24, GROUND_Y - th - 14, 14, 14))
        pygame.draw.rect(s, (255, 200, 90), (x + 56, GROUND_Y - th + 30, 10, 18))


LEDGES = [(900, 1020, 350), (1100, 1220, 290),
          (2500, 2610, 365), (2660, 2770, 295), (2820, 2940, 225),
          (4200, 4300, 360), (4350, 4450, 290), (4500, 4620, 220),
          (6000, 6120, 355), (6180, 6300, 285)]
STARS = [(1160, 252), (2880, 187), (4560, 182)]
CASH = [(450, GROUND_Y - 12), (1000, GROUND_Y - 12), (1160, 255), (2100, GROUND_Y - 12), (2880, 190),
        (3400, GROUND_Y - 12), (4400, 252), (5000, GROUND_Y - 12), (5600, GROUND_Y - 12),
        (6240, 250), (6800, GROUND_Y - 12), (7500, GROUND_Y - 12)]
GUARDS = [(700, 1000, "s"), (1800, 2100), (2900, 3250, "s"), (3500, 3800), (4700, 5000, "s"),
          (5400, 5700), (6500, 6800, "s"), (7000, 7300)]
DOGS = [(2000, 2300), (3300, 3600), (5000, 5300), (6900, 7200)]
CAMS = [(1700, 0.0), (3300, 1.7), (4900, 3.0), (6500, 0.8), (7300, 2.2)]
CHECKPOINTS = [1300, 3000, 4700, 6000, 7400]
HINTS = [
    (0, 420, "ROYAL FORTRESS  -  steal the CROWN OF ABIX  (FINALE)"),
    (420, 900, "ELITE SQUAD (6 cops)!  Front = GOD MODE.  Jump over and hit from BEHIND"),
    (1250, 1480, "3 catches = JAIL:  PAY 10000 / WAIT 1 MIN / BREAK OUT"),
    (1500, 1700, "FORTRESS GATE  -  KEYCARD (key 1)"),
    (3200, 3500, "Collect the PAGE  -  it has the THRONE ROOM code"),
    (4700, 4900, "THRONE ROOM:  press E and type the CODE"),
    (5400, 5700, "3 laser grids  -  rewire (key 6), or time it"),
    (5700, 6100, "CROWN VAULT:  key 8 THERMITE"),
    (6900, 7300, "Take the CROWN and run to the GETAWAY VAN!"),
]


class World15(L14.BigHeist):
    LEVEL_W = 8400
    DOOR_X, IN_END, GOAL = 1500, 7500, 8200
    GOAL_X = 8200
    OUT_PAINT, IN_PAINT, SEEDS = staticmethod(castle_out), staticmethod(fortress_wall), (151, 152)
    FLOOR = ((40, 36, 52), (14, 12, 22), (255, 120, 220), (56, 50, 72))
    TINT = (30, 4, 30, 80)
    LOOT_DRAW = staticmethod(draw_crown)
    LOOT_X = 7000
    PAGE_X, LOCK_X, VAULT_X = 3200, 4800, 6400
    PAGE_KEY = "fortress_throne"
    LABELS = ("FORTRESS GATE", "THRONE ROOM CODE", "THRONE ROOM", "CROWN VAULT")
    LASERS = [(5400, 5560, 0.0), (5580, 5740, 1.6), (5760, 5920, 3.1)]
    LEDGES, STARS, CASH, GUARDS, DOGS, CAMS = LEDGES, STARS, CASH, GUARDS, DOGS, CAMS
    CHECKPOINTS, HINTS = CHECKPOINTS, HINTS
    TARGET = "CROWN OF ABIX"
    REWARD = 15000
    BAIL = 10000
    WIN_TITLE = "CROWN STOLEN!"
    SPOT_LINES = ["Intruder in the fortress!", "Elite squad, attack!", "Nobody leaves with the crown!"]
    CHAT_LINES = ["The crown never leaves.", "Six of us. One thief.", "Hit him from the front!"]
    ELITE_POLICE = {"from": 300, "max": 6, "hp": 5, "knife": 1, "punch": 2, "catch_time": 1.1, "catch_max": 3,
                    "spawn_every": 4.2, "turn": 0.40, "speed": 225.0, "ko_time": 10.0}


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((10, 6, 24))
        cache.setdefault("t", Tiled(600, castle_out, seed=151)).draw(s, off)
        draw_floor(s, off, (40, 36, 52), (14, 12, 22), (255, 120, 220))

    return H.run_heist(screen, clock, save, save_fn, World15, "ROYAL FORTRESS",
                       ["FINALE:  steal the CROWN OF ABIX from the Royal Fortress.",
                        "ELITE SQUAD (6 cops):  FRONT = GOD MODE.  Hit them from BEHIND.",
                        "JAIL:  PAY 10000 Tk  /  WAIT 1 MIN  /  BREAK OUT."],
                       back, lambda s, c, t: draw_crown(s, c, t),
                       "Royal fortress. Steal the crown of Abix. Six elite cops guard it.")
