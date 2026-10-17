"""
level13.py - Chapter 1 / Level 13 : POLICE HQ  -  EVIDENCE ROOM HEIST.
main_game.py theke:  level13.run(screen, clock, save, save_fn)

Lokkho: Police headquarter er bhitor dhuke Evidence Room theke "STAR OF DAWN" (zobd kora diamond) churi kore
        roof helipad e palao.

Ei level e:
  - Police HQ, tai guard, kukur, CCTV ar laser shob ache.
  - Alarm hole notun POLICE ashe ar bole "You little thief!"  (police.py)
  - HOLDING CELLS door  : key 3 KEYCARD (glass door) e E chapo.
  - COMMAND LAPTOP      : key 3 LAPTOP e code type kore LOCKDOWN door khulo.
  - EVIDENCE ROOM door  : key 8 VAULT THERMITE (2 sec).
Camera code: /CAMERA01099    Laser code: /TKDIAMONDLASER
"""
import math
import pygame

import sprites as SP
from level1 import GROUND_Y, CEIL_Y
from animation import WIDTH, get_font
import heist as H
from heist import (HeistWorld, DoorFeature, TerminalFeature, SafeFeature, LootFeature,
                   SweepGridFeature, Tiled, draw_floor)

LEVEL_W = 6000
GOAL = 5850


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_evidence_diamond(surf, c, t):
    """Evidence case er bhitor STAR OF DAWN."""
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 50, (150, 220, 255), 60, 4)
    box = pygame.Rect(0, 0, 66, 56)
    box.center = (x, y + 4)
    pygame.draw.rect(surf, (28, 36, 60), box, border_radius=6)
    pygame.draw.rect(surf, (120, 170, 255), box, 3, border_radius=6)
    SP.draw_diamond(surf, (x, y - 2), 26, t)
    f = get_font(11).render("EVIDENCE", True, (200, 215, 255))
    surf.blit(f, f.get_rect(center=(x, y + 34)))


def hq_wall(s, rnd):
    """Police HQ er deyal: nil + dhushor, jaanla, poster, cell er rod."""
    SP.v_gradient(s, s.get_rect(), (40, 52, 82), (22, 28, 48))
    w, h = s.get_size()
    pygame.draw.rect(s, (14, 18, 34), (0, 0, w, 34))
    pygame.draw.rect(s, (60, 100, 230), (0, 34, w, 4))
    pygame.draw.rect(s, (230, 60, 70), (0, 40, w, 2))
    f = get_font(18).render("POLICE", True, (180, 205, 255))
    s.blit(f, f.get_rect(center=(w // 2, 17)))
    for i in range(3):                                          # jaanla
        r = pygame.Rect(40 + i * 160, 90, 90, 110)
        pygame.draw.rect(s, (12, 16, 30), r)
        pygame.draw.rect(s, (110, 130, 180), r, 3)
        pygame.draw.line(s, (110, 130, 180), (r.centerx, r.y), (r.centerx, r.bottom), 2)
        pygame.draw.line(s, (110, 130, 180), (r.x, r.centery), (r.right, r.centery), 2)
    for i in range(2):                                          # WANTED poster
        r = pygame.Rect(30 + i * 250, GROUND_Y - 220, 54, 70)
        pygame.draw.rect(s, (214, 196, 150), r)
        pygame.draw.rect(s, (110, 90, 50), r, 2)
        f2 = get_font(10).render("WANTED", True, (110, 40, 30))
        s.blit(f2, f2.get_rect(center=(r.centerx, r.y + 10)))
        pygame.draw.circle(s, (120, 100, 80), (r.centerx, r.y + 36), 12)
    for i in range(8):                                          # cell er rod (neeche)
        x = 300 + i * 22
        pygame.draw.line(s, (90, 100, 130), (x, GROUND_Y - 130), (x, GROUND_Y), 4)
    pygame.draw.line(s, (90, 100, 130), (294, GROUND_Y - 130), (470, GROUND_Y - 130), 4)
    for i in range(3):                                          # desk
        dx = 20 + i * 170 + rnd.randint(0, 20)
        pygame.draw.rect(s, (70, 56, 46), (dx, GROUND_Y - 44, 90, 44))
        pygame.draw.rect(s, (40, 32, 28), (dx, GROUND_Y - 44, 90, 6))


def draw_helipad_exit(surf, x, t, open_k):
    r = pygame.Rect(0, 0, 120, 250)
    r.midbottom = (x, GROUND_Y)
    pygame.draw.rect(surf, (24, 28, 44), r.inflate(16, 16), border_radius=4)
    pygame.draw.rect(surf, (90, 130, 255), r.inflate(16, 16), 3, border_radius=4)
    SP.v_gradient(surf, r, (110, 130, 170), (70, 84, 120))
    gap = int(r.w / 2 * open_k)
    pygame.draw.rect(surf, (18, 22, 34), (r.centerx - gap, r.y, gap * 2, r.h))
    f = get_font(16).render("ROOF EXIT", True, (80, 255, 150))
    surf.blit(f, f.get_rect(center=(x, r.y - 22)))


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(850, 990, 350),
          (2650, 2760, 365), (2810, 2920, 290),
          (3950, 4060, 360), (4110, 4220, 285), (4270, 4380, 215)]
STARS = [(920, 312), (2870, 252), (4330, 177)]
CASH = [(450, GROUND_Y - 12), (1050, GROUND_Y - 12), (1750, GROUND_Y - 12), (2400, GROUND_Y - 12),
        (2700, 350), (3500, GROUND_Y - 12), (4100, 345), (4900, GROUND_Y - 12), (5400, GROUND_Y - 12)]
GUARDS = [(650, 950), (1500, 1800), (2500, 2800), (3550, 3850), (4600, 4900), (5200, 5450)]
DOGS = [(1900, 2250), (3900, 4250)]
CAMS = [(1300, 0.0), (3000, 1.5), (4700, 3.0)]
CHECKPOINTS = [1950, 3350, 4650]
HINTS = [
    (0, 420, "POLICE HQ  -  steal the STAR OF DAWN from the Evidence Room"),
    (600, 950, "Armed COPS patrol the lobby  -  hide in the shadows or use J (knife)"),
    (1250, 1500, "CCTV ahead:  key 2 HACKER near it, or stay out of the beam"),
    (1900, 2250, "K9 DOGS  -  throw a decoy / smoke, or be quick"),
    (2250, 2450, "HOLDING CELLS door:  key 3 KEYCARD,  press E"),
    (3300, 3450, "Laser grid:  key 1 + /TKDIAMONDLASER  or time it"),
    (3750, 3900, "COMMAND LAPTOP:  key 3, type the code to lift the LOCKDOWN"),
    (5100, 5300, "Evidence Room door:  key 8 VAULT THERMITE (2 sec)"),
    (5400, 5800, "Grab the STAR OF DAWN then run to the ROOF EXIT"),
]
SPOT_LINES = ["Freeze! Police!", "Hey! Intruder in HQ!", "Thief! Sound the alarm!"]
CHAT_LINES = ["Nobody breaks into HQ.", "Evidence room is sealed tight.", "Heard the diamond is in there.",
              "Watch the cameras tonight."]


class World13(HeistWorld):
    LEVEL_W = LEVEL_W
    SPAWN_X = 200
    LEDGES = LEDGES
    STARS = STARS
    CASH = CASH
    GUARDS = GUARDS
    DOGS = DOGS
    CAMS = CAMS
    CHECKPOINTS = CHECKPOINTS
    HINTS = HINTS
    GOAL_X = GOAL
    TARGET = "STAR OF DAWN"
    REWARD = 1500
    BAIL = 600
    WIN_TITLE = "STAR OF DAWN STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES

    def __init__(self, save, save_fn):
        self.bg = Tiled(520, hq_wall, seed=13)
        super().__init__(save, save_fn)

    def make_features(self):
        lockdown = DoorFeature(4500, "terminal", "LOCKDOWN GATE")
        return [DoorFeature(2350, "keycard", "HOLDING CELLS"),
                SafeFeature(3150, 400),
                SweepGridFeature([(3300, 3440, 0.0)]),
                TerminalFeature(3820, ["sudo police --lockdown off", "unlock gate --id 7"],
                                "LAPTOP  -  COMMAND CENTER", lambda w: lockdown.open(w)),
                lockdown,
                DoorFeature(5300, "thermite", "EVIDENCE ROOM"),
                LootFeature(5600, "STAR OF DAWN", draw_evidence_diamond)]

    def draw_background(self, surf, cam):
        self.bg.draw(surf, cam)
        ex = GOAL + 40 - cam
        if -200 < ex < WIDTH + 200:
            draw_helipad_exit(surf, ex, self.t, 1.0 if self.loot else 0.0)
        draw_floor(surf, cam, (52, 60, 84), (26, 30, 48), (110, 140, 220), stripe=(70, 80, 112))

    def draw_fx(self, surf, cam):
        """Siren er nil / lal alo (halka) - police HQ feel."""
        on = int(self.t * 2) % 2 == 0
        col = (230, 50, 60) if on else (60, 100, 255)
        sh = pygame.Surface((WIDTH, 90), pygame.SRCALPHA)
        pygame.draw.circle(sh, col + (16,), (WIDTH // 2 + int(math.sin(self.t) * 300), 10), 160)
        surf.blit(sh, (0, CEIL_Y))


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    def back(s, off):
        s.fill((30, 38, 60))
        w = BACK_CACHE.setdefault("c", Tiled(520, hq_wall, seed=13))
        w.draw(s, off)
        draw_floor(s, off, (52, 60, 84), (26, 30, 48), (110, 140, 220))

    def icon(s, c, t):
        draw_evidence_diamond(s, c, t)

    return H.run_heist(screen, clock, save, save_fn, World13, "POLICE HQ HEIST",
                       ["Break into Police HQ and steal the STAR OF DAWN from the Evidence Room.",
                        "Cops, K9 dogs, CCTV and a laser grid.",
                        "Raise the alarm and the police will come for you."],
                       back, icon, "Police HQ. Steal the Star of Dawn.")


BACK_CACHE = {}
