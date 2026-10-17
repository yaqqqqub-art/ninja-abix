"""
level11.py - Chapter 1 / Level 11 : POLICE HEADQUARTERS  ("ELITE POLICE").
main_game.py theke:  level11.run(screen, clock, save, save_fn)

Lokkho: City Police HQ theke "EVIDENCE DRIVE" (tomar sob proman) churi kore pichoner gali te getaway van e palao.

NOTUN:  ELITE POLICE  (shob shomoy ashe, level er majh theke shuru)
  - 5 HP.   KNIFE = 1 HP  (5 knife)      SUPER PUNCH (K) = 2 HP  (3 punch e KO)
  - GOD MODE:  police er SHAMNE (je dike mukh) theke knife / punch kaj kore NA!
        -> police er opor diye lafao, tarpor PICHON theke mar.  (ghurte 0.45 sec lage)
        -> mar khele police 0.65 sec atke thake, tokhon abar mar.
  - CATCH BAR:  police dhorle tomar matha r upor bar bhore.  SPACE / W mere (mash) bar kamao, ba dour dao.
        Bar bhorle  CAUGHT 1/3.   3 bar dhora porle  ->  3D ANIMATION:  police tomake JAIL e niye jay.
  - Police er speed (200) tomar (250) cheye kom.  Door / laser police ke atkay.  Hide korle khuje.

Baki:  keycard door,  EVIDENCE ROOM er CODE LOCK (code ta PAGE e lekha),  laser grid,  thermite vault.
Camera code: /CAMERA01099
"""
import math
import random
import pygame

import sound
import voice
import sprites as SP
import tools as TL
import level1 as L1
from level1 import Camera, clamp, GROUND_Y, CEIL_Y
from level2 import Guard2, Dog
from level5 import ShieldGuard
from animation import WIDTH, HEIGHT, get_font
import heist as H
from heist import (HeistWorld, Feature, DoorFeature, CodeLockDoor, PageFeature, SweepGridFeature,
                   LootFeature, Tiled, draw_floor)
from bust3d import Bust3D
import bust_ursina

LEVEL_W = 6600
GOAL = 6400
DOOR_X = 1500                    # HQ entrance
IN_END = 5800                    # er pore abar bairer (pichoner gali)


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_drive(surf, c, t):
    """EVIDENCE DRIVE  (lal USB drive)."""
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 52, (255, 90, 90), 90, 4)
    pygame.draw.rect(surf, (30, 30, 44), (x - 20, y - 12, 40, 24), border_radius=5)
    pygame.draw.rect(surf, (230, 70, 80), (x - 20, y - 12, 40, 24), 3, border_radius=5)
    pygame.draw.rect(surf, (200, 204, 220), (x + 18, y - 7, 14, 14), border_radius=2)
    pygame.draw.rect(surf, (90, 94, 110), (x + 22, y - 3, 8, 3))
    pygame.draw.rect(surf, (90, 94, 110), (x + 22, y + 2, 8, 3))
    pygame.draw.circle(surf, (255, 240, 200), (int(x - 9), int(y)), 4)


def draw_van(surf, x, t):
    """Getaway van (pichoner gali te)."""
    w, h = 190, 100
    tmp = pygame.Surface((w, h), pygame.SRCALPHA)
    by = h - 14
    pygame.draw.ellipse(tmp, (0, 0, 0, 90), (10, by - 2, w - 20, 12))
    pygame.draw.rect(tmp, (36, 40, 56), (10, by - 66, 150, 60), border_radius=8)
    pygame.draw.polygon(tmp, (36, 40, 56), [(150, by - 66), (150, by - 6), (184, by - 6), (184, by - 28), (168, by - 46)])
    pygame.draw.polygon(tmp, (90, 140, 190), [(152, by - 60), (152, by - 34), (176, by - 34), (164, by - 50)])
    pygame.draw.rect(tmp, (230, 200, 40), (10, by - 30, 150, 5))
    pygame.draw.rect(tmp, (20, 22, 32), (10, by - 66, 150, 60), 3, border_radius=8)
    for wx in (42, 140):
        pygame.draw.circle(tmp, (14, 14, 18), (wx, by - 4), 16)
        pygame.draw.circle(tmp, (150, 154, 166), (wx, by - 4), 7)
    surf.blit(tmp, (int(x) - w // 2, GROUND_Y - (h - 14) - 2))
    f = get_font(15).render("GETAWAY VAN", True, (80, 255, 150))
    surf.blit(f, f.get_rect(center=(x, GROUND_Y - 120)))
    SP.glow(surf, (x + 78, GROUND_Y - 24), 40, (255, 240, 170), 60, 3)


def outdoor_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (8, 10, 26), (34, 30, 56))
    for _ in range(5):
        pygame.draw.ellipse(s, (18, 18, 38), (rnd.randint(-40, w), rnd.randint(20, 120), rnd.randint(160, 300), 54))
    for x in range(0, w, 100):                                    # city skyline
        bh = rnd.randint(110, 260)
        bw = rnd.randint(60, 96)
        pygame.draw.rect(s, (20, 22, 40), (x, GROUND_Y - bh - 40, bw, bh + 40))
        for wy in range(GROUND_Y - bh - 26, GROUND_Y - 50, 26):
            for wx in range(x + 8, x + bw - 10, 18):
                if rnd.random() < 0.45:
                    pygame.draw.rect(s, rnd.choice(((230, 200, 90), (120, 180, 240))), (wx, wy, 8, 12))
    pygame.draw.rect(s, (22, 24, 40), (0, GROUND_Y - 44, w, 44))
    for x in range(30, w, 160):                                   # street lamps
        pygame.draw.rect(s, (60, 64, 80), (x, GROUND_Y - 150, 5, 110))
        pygame.draw.circle(s, (255, 236, 170), (x + 2, GROUND_Y - 152), 8)


def indoor_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (36, 50, 92), (18, 24, 50))
    pygame.draw.rect(s, (10, 14, 34), (0, 0, w, 38))
    pygame.draw.rect(s, (60, 110, 240), (0, 38, w, 4))
    for x in range(0, w, 150):                                    # panels
        pygame.draw.rect(s, (24, 34, 70), (x + 6, 60, 138, GROUND_Y - 70), border_radius=4)
        pygame.draw.rect(s, (60, 80, 140), (x + 6, 60, 138, GROUND_Y - 70), 2, border_radius=4)
    # WANTED poster board
    pygame.draw.rect(s, (110, 80, 50), (60, 120, 200, 150))
    for i in range(4):
        r = pygame.Rect(72 + (i % 2) * 90, 132 + (i // 2) * 68, 76, 58)
        pygame.draw.rect(s, (226, 208, 160), r)
        pygame.draw.rect(s, (40, 36, 40), (r.x + 22, r.y + 10, 32, 28))
        pygame.draw.rect(s, (160, 40, 40), (r.x + 6, r.y + 44, 64, 5))
    # police badge
    cx, cy = 430, 190
    pygame.draw.circle(s, (230, 200, 60), (cx, cy), 48)
    pygame.draw.circle(s, (30, 50, 130), (cx, cy), 38)
    pygame.draw.circle(s, (230, 200, 60), (cx, cy), 38, 3)
    f = SP._font(18).render("POLICE", True, (255, 240, 180))
    s.blit(f, f.get_rect(center=(cx, cy)))


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(900, 1040, 350),
          (2400, 2510, 365), (2560, 2670, 290), (2720, 2840, 215),
          (4200, 4300, 360), (4350, 4450, 285)]
STARS = [(970, 312), (2780, 177), (4400, 247)]
CASH = [(450, GROUND_Y - 12), (1000, GROUND_Y - 12), (1900, GROUND_Y - 12), (2500, 330),
        (2780, 180), (3300, GROUND_Y - 12), (3800, GROUND_Y - 12), (4400, 250),
        (5000, GROUND_Y - 12), (5900, GROUND_Y - 12)]
GUARDS = [(700, 1000), (1800, 2100), (2900, 3250), (3600, 3900), (4650, 4950, "s")]
DOGS = [(2000, 2300), (4100, 4400)]
CAMS = [(1700, 0.0), (3300, 1.7), (4800, 3.0)]
CHECKPOINTS = [1300, 2600, 3800, 5100]
HINTS = [
    (0, 420, "POLICE HEADQUARTERS  -  steal the EVIDENCE DRIVE"),
    (480, 900, "ELITE POLICE are coming!  FRONT = GOD MODE.  Jump over them and stab from BEHIND"),
    (900, 1250, "5 KNIFE hits (J) or 3 SUPER PUNCHES (K) from behind.  Or just outrun them (they are slower)"),
    (1250, 1480, "They grab you -> CATCH BAR fills.  Mash SPACE to break free.  3 catches = JAIL"),
    (1500, 1700, "HQ ENTRANCE  -  use the KEYCARD (key 1).  Doors block the police too!"),
    (2800, 3100, "Collect the PAGE  -  it has the EVIDENCE ROOM code"),
    (3900, 4100, "EVIDENCE ROOM:  press E and type the CODE  (keycard does NOT work)"),
    (4450, 4800, "Laser grid ahead  -  rewire (key 6), or time it"),
    (5000, 5300, "EVIDENCE VAULT:  key 8 THERMITE.  Police can't follow through a closed door"),
    (5450, 5900, "Take the DRIVE and run to the GETAWAY VAN!"),
]
SPOT_LINES = ["Intruder in police HQ!", "Cop killer! Stop!", "Call the elite squad!"]
CHAT_LINES = ["Elite squad is on patrol.", "Nobody steals from HQ.", "They never fight from behind.",
              "I have CCTV footage in this precinct."]


class World11(HeistWorld):
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
    TARGET = "EVIDENCE DRIVE"
    REWARD = 4500
    BAIL = 900
    WIN_TITLE = "EVIDENCE STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES
    # police.py ei config dekhe ELITE POLICE chalu kore
    ELITE_POLICE = {"from": 600, "max": 3, "hp": 5, "knife": 1, "punch": 2, "catch_time": 1.5, "catch_max": 3,
                    "spawn_every": 7.0, "turn": 0.45, "speed": 200.0, "ko_time": 10.0}

    def __init__(self, save, save_fn):
        self.bg_out = Tiled(600, outdoor_wall, seed=71)
        self.bg_in = Tiled(600, indoor_wall, seed=72)
        self.bust3d = None
        self.ubust = None
        super().__init__(save, save_fn)

    def make_guard(self, spec):
        if len(spec) == 3:
            return ShieldGuard(spec[0], spec[1], self)
        return Guard2(spec[0], spec[1], self)

    def restart(self):
        super().restart()
        if getattr(self, "ubust", None):
            self.ubust.close()
        self.bust3d = None
        self.ubust = None

    def make_features(self):
        return [DoorFeature(DOOR_X, "keycard", "HQ ENTRANCE"),
                PageFeature(3000, "police_evidence", "EVIDENCE ROOM CODE"),
                CodeLockDoor(4000, "police_evidence", "EVIDENCE ROOM"),
                SweepGridFeature([(4520, 4700, 0.0)]),
                DoorFeature(5200, "thermite", "EVIDENCE VAULT"),
                LootFeature(5400, "EVIDENCE DRIVE", draw_drive)]

    # ---------- 3D ARREST ----------
    def start_bust(self, cop=None):
        """Elite police 3 bar dhorle:  3D animation e jail e niye jay."""
        if self.state != "play":
            return
        p = self.p
        self.state, self.state_t = "bust", 0.0
        p.vx, p.hidden = 0.0, False
        self.hack = None
        self.modal = None
        self.melt = None
        self.arrests += 1
        rounds = self.ELITE_POLICE["catch_max"]
        self.bust3d, self.ubust = None, None
        if bust_ursina.available():                       # pip install ursina  ->  REAL 3D (Ursina)
            try:
                self.ubust = bust_ursina.UrsinaBust(rounds)
            except Exception as ex:
                print("ursina bust failed, using pygame 3D:", ex)
        if self.ubust is None:
            self.bust3d = Bust3D(rounds=rounds)
        voice.say("Busted! You are going to jail")

    def update(self, dt, keys):
        if self.state == "bust":
            if self.paused:
                return
            self.t += dt
            self.state_t += dt
            if self.ubust is not None:
                self.ubust.update(dt)
                if self.ubust.failed:                              # Ursina chalu hoy ni -> pygame 3D
                    self.ubust.close()
                    self.ubust = None
                    self.bust3d = Bust3D(rounds=self.ELITE_POLICE["catch_max"])
                    return
                finished = self.ubust.done
            else:
                self.bust3d.update(dt)
                finished = self.bust3d.done
            if finished:
                self.enter_jail()
                if self.ubust is not None:
                    self.ubust.close()
                self.bust3d = self.ubust = None
            return
        super().update(dt, keys)

    def draw(self, surf, mouse, sel):
        if self.state == "bust" and self.ubust is not None:
            self.ubust.draw(surf)
            return []
        if self.state == "bust" and self.bust3d is not None:
            self.bust3d.draw(surf)
            return []
        return super().draw(surf, mouse, sel)

    # ---------- look ----------
    def draw_background(self, surf, cam):
        self.bg_out.draw(surf, cam)
        split = DOOR_X - cam
        send = IN_END - cam
        if split < WIDTH and send > 0:
            clip = surf.get_clip()
            surf.set_clip(pygame.Rect(max(0, int(split)), 0, max(0, int(min(send, WIDTH) - max(0, split))), HEIGHT))
            self.bg_in.draw(surf, cam)
            surf.set_clip(clip)
        vx = GOAL - cam
        if -200 < vx < WIDTH + 200:
            draw_van(surf, vx, self.t)
        draw_floor(surf, cam, (40, 42, 56), (16, 18, 28), (120, 124, 150), stripe=(54, 58, 76), tile=90)
        if split < WIDTH and send > 0:
            clip = surf.get_clip()
            surf.set_clip(pygame.Rect(max(0, int(split)), GROUND_Y, max(0, int(min(send, WIDTH) - max(0, split))), HEIGHT - GROUND_Y))
            SP.v_gradient(surf, pygame.Rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y), (46, 60, 110), (16, 20, 44))
            pygame.draw.line(surf, (70, 130, 255), (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
            surf.set_clip(clip)

    def draw_fx(self, surf, cam):
        a0, a1 = DOOR_X - cam, IN_END - cam
        tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        tint.fill((4, 8, 30, 70))
        if a1 > 0 and a0 < WIDTH:
            tint.fill((0, 0, 0, 0), (max(0, int(a0)), 0, max(0, int(min(a1, WIDTH) - max(0, a0))), HEIGHT))
        surf.blit(tint, (0, 0))
        st = getattr(self, "_pol", None)
        if st and st["p"] is self.p and st["cops"] and self.state == "play":      # police light wash
            on = int(self.t * 4) % 2 == 0
            wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            wash.fill((255, 40, 60, 16) if on else (60, 110, 255, 16))
            surf.blit(wash, (0, 0))


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((8, 10, 22))
        cache.setdefault("t", Tiled(600, outdoor_wall, seed=71)).draw(s, off)
        draw_floor(s, off, (40, 42, 56), (16, 18, 28), (120, 124, 150))

    return H.run_heist(screen, clock, save, save_fn, World11, "POLICE HEADQUARTERS",
                       ["Steal the EVIDENCE DRIVE from the City Police HQ.",
                        "ELITE POLICE:  FRONT = GOD MODE.  Hit them from BEHIND.",
                        "3 catches = 3D arrest and JAIL.  Reach the getaway van."],
                       back, lambda s, c, t: draw_drive(s, c, t),
                       "Police headquarters. Steal the evidence drive. Elite police are everywhere.")
