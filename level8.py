"""
level8.py - Chapter 1 / Level 8 : METRO SUBWAY GOLD HEIST.
main_game.py theke:  level8.run(screen, clock, save, save_fn)

Lokkho: subway terminal e dhuke cargo train er "BULLION GOLD CRATE" churi kore service tunnel diye palao.

Notun challenge:
  - ELECTRIFIED THIRD RAIL:  tracks e porle (jhapiye porle) sathe sathe shock = MORON.
    Chalonto TRAIN CAR e uthe track par ho (shuru te porjonto dhimey, tarpor othanama).
  - K9 HANDLER:  torch guard + kukur.  Kukur HIDE korleo gondho paye.  SMOKE BOMB (key 7) dao.
  - STATION MASTER door:  CODE LOCK (keycard kaj kore na). Code ta ekta PAGE e lekha - tunnel er age track er pashe kuriye nao.
    Tarpor control room e LAPTOP: L chaplei khole (terminal er kache jete hoy na) -> WIRE CONNECT.
    korle cargo VAULT INTERLOCK khule jay.
  - Cargo vault:  VAULT THERMITE (key 8) 2 sec.  Tarpor service tunnel.
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
from level4 import TorchGuard
from animation import WIDTH, HEIGHT, get_font
import heist as H
from heist import (HeistWorld, Feature, DoorFeature, CodeLockDoor, PageFeature, TerminalFeature, LootFeature, Tiled, Mover,
                   draw_floor, light_overlay)

LEVEL_W = 6700
GOAL = 6540
SEGS = [(0, 1400), (1800, 3000), (3300, 4700), (5100, 6700)]
GAPS = [(1400, 1800), (3000, 3300), (4700, 5100)]


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_bullion(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 2
    SP.glow(surf, (x, y), 54, (255, 210, 80), 90, 4)
    crate = pygame.Rect(0, 0, 66, 42)
    crate.center = (x, y)
    SP.v_gradient(surf, crate, (110, 80, 44), (60, 40, 22))
    pygame.draw.rect(surf, (30, 20, 10), crate, 3)
    for k in range(3):
        bar = pygame.Rect(x - 28 + k * 19, y - 16, 17, 10)
        SP.v_gradient(surf, bar, (255, 236, 130), (200, 150, 30))
        pygame.draw.rect(surf, (120, 80, 10), bar, 1)
    for k in range(2):
        pygame.draw.rect(surf, (255, 220, 100), (x - 18 + k * 28, y, 22, 10))
    f = get_font(13).render("AU  999", True, (255, 230, 150))
    surf.blit(f, f.get_rect(center=(x, y + 16)))


def metro_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (60, 66, 70), (36, 40, 46))
    for tx in range(0, w, 48):                                     # subway tiles
        pygame.draw.line(s, (86, 94, 100), (tx, 40), (tx, GROUND_Y - 6), 1)
    for ty in range(40, GROUND_Y - 6, 36):
        pygame.draw.line(s, (86, 94, 100), (0, ty), (w, ty), 1)
    pygame.draw.rect(s, (20, 22, 28), (0, 0, w, 38))
    pygame.draw.rect(s, (230, 190, 40), (0, 38, w, 5))
    for px in (30, w - 30):                                         # pillars
        pygame.draw.rect(s, (30, 32, 38), (px - 20, 43, 40, GROUND_Y - 43))
        pygame.draw.rect(s, (70, 74, 84), (px - 20, 43, 6, GROUND_Y - 43))
        pygame.draw.rect(s, (230, 190, 40), (px - 20, GROUND_Y - 80, 40, 6))
    # ads & signs
    for i in range(2):
        r = pygame.Rect(130 + i * 230, 110, 150, 96)
        pygame.draw.rect(s, (20, 22, 28), r.inflate(8, 8))
        SP.v_gradient(s, r, rnd.choice(((200, 70, 60), (60, 120, 200), (230, 180, 50))), (30, 30, 40))
        pygame.draw.circle(s, (255, 255, 255), (r.centerx, r.centery - 8), 16, 3)
    # vent grilles
    vr = pygame.Rect(w // 2 - 30, 240, 60, 40)
    pygame.draw.rect(s, (24, 26, 30), vr)
    for k in range(5):
        pygame.draw.line(s, (80, 86, 94), (vr.x + 4, vr.y + 6 + k * 7), (vr.right - 4, vr.y + 6 + k * 7), 2)
    # yellow safety line
    pygame.draw.rect(s, (230, 190, 40), (0, GROUND_Y - 6, w, 6))


class TrainCar(Mover):
    def draw(self, surf, cam):
        x = self.cx - cam
        if not (-220 < x < WIDTH + 220):
            return
        r = pygame.Rect(0, 0, int(self.w), 78)
        r.midtop = (x, self.y)
        SP.v_gradient(surf, r, (150, 160, 175), (70, 78, 92))
        pygame.draw.rect(surf, (20, 22, 30), r, 3, border_radius=4)
        pygame.draw.rect(surf, (230, 70, 50), (r.x, r.y + 34, r.w, 8))
        for k in range(int(self.w // 38)):
            wx = r.x + 10 + k * 38
            pygame.draw.rect(surf, (255, 240, 170), (wx, r.y + 8, 24, 20), border_radius=3)
            pygame.draw.rect(surf, (20, 22, 30), (wx, r.y + 8, 24, 20), 2, border_radius=3)
        pygame.draw.line(surf, (255, 220, 90), (r.x + 4, r.y + 2), (r.right - 4, r.y + 2), 3)
        SP.glow(surf, (x, r.y + 18), 90, (255, 230, 160), 18, 3)


def draw_track_gap(surf, a, b, t):
    r = pygame.Rect(int(a), GROUND_Y, int(b - a), HEIGHT - GROUND_Y)
    SP.v_gradient(surf, r, (24, 24, 30), (8, 8, 12))
    for x in range(int(a) + 10, int(b), 34):                          # sleepers
        pygame.draw.rect(surf, (70, 50, 34), (x, GROUND_Y + 60, 24, 8))
    for yy, col in ((GROUND_Y + 58, (150, 154, 168)), (GROUND_Y + 70, (150, 154, 168))):
        pygame.draw.line(surf, col, (a, yy), (b, yy), 3)
    pygame.draw.line(surf, (255, 220, 70), (a, GROUND_Y + 50), (b, GROUND_Y + 50), 5)     # third rail
    for _ in range(6):                                                # sparks
        sx = random.uniform(a, b)
        sy = GROUND_Y + 50
        k = (t * 9 + sx) % 1.0
        if k < 0.35:
            pygame.draw.line(surf, (160, 220, 255), (sx, sy), (sx + random.randint(-8, 8), sy - random.randint(4, 14)), 2)
    f = get_font(14).render("LIVE THIRD RAIL  -  DEADLY", True, (255, 220, 70))
    surf.blit(f, f.get_rect(center=((a + b) / 2, GROUND_Y + 28)))


def draw_tunnel(surf, x, t):
    r = pygame.Rect(0, 0, 130, 210)
    r.midbottom = (x, GROUND_Y)
    pygame.draw.ellipse(surf, (6, 6, 10), (r.x, r.y, r.w, r.h * 1.1))
    pygame.draw.rect(surf, (6, 6, 10), (r.x, r.y + r.h // 2, r.w, r.h // 2))
    pygame.draw.ellipse(surf, (230, 190, 40), (r.x, r.y, r.w, r.h * 1.1), 4)
    f = get_font(15).render("SERVICE TUNNEL", True, (80, 255, 150))
    surf.blit(f, f.get_rect(center=(x, r.y - 14)))
    for k in range(4):
        a = ((t * 1.5 + k / 4) % 1.0)
        pygame.draw.circle(surf, (80, 255, 150), (int(x), int(GROUND_Y - 60 - a * 60)), 3)


# ------------------------------------------------------------------
# Features
# ------------------------------------------------------------------
class VaultDoor(DoorFeature):
    """Cargo vault: thermite diye gola jabe, kintu age station master terminal theke INTERLOCK release korte hobe."""

    def use(self, w, tid, payload):
        if not w.interlock:
            w.say("INTERLOCK ACTIVE  -  release it at the station master's terminal")
            sound.play("beep")
            return
        super().use(w, tid, payload)

    def prompt(self, w, tid, payload):
        if not w.interlock:
            return (self.x, GROUND_Y - 130), ["[E]  VAULT LOCKED", "interlock still active"]
        return super().prompt(w, tid, payload)


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(850, 990, 350),
          (2100, 2210, 365), (2260, 2370, 290), (2420, 2530, 215),
          (3800, 3910, 360), (3960, 4070, 285)]
STARS = [(920, 312), (2480, 177), (4020, 247)]
CASH = [(450, GROUND_Y - 12), (1000, GROUND_Y - 12), (1250, GROUND_Y - 12), (1950, GROUND_Y - 12),
        (2300, 350), (2800, GROUND_Y - 12), (3500, GROUND_Y - 12), (4200, GROUND_Y - 12),
        (5200, GROUND_Y - 12), (5600, GROUND_Y - 12)]
GUARDS = [(550, 1000), (2000, 2400), (2600, 2900), (3450, 3900), (4100, 4600)]
DOGS = [(550, 1000), (2600, 2900), (3450, 3900)]
CAMS = [(1100, 0.0), (2200, 1.7), (3700, 3.0), (5400, 4.4)]
CHECKPOINTS = [1300, 2700, 4300, 5300]
HINTS = [
    (0, 420, "METRO SUBWAY  -  steal the BULLION GOLD CRATE from the cargo train"),
    (550, 1000, "K9 HANDLERS:  dog smells you even when hidden.  SMOKE (key 7)"),
    (1250, 1400, "LIVE THIRD RAIL below!  Ride the TRAIN CAR across"),
    (3000, 3300, "Vertical train car  -  step on when it's low"),
    (4500, 4700, "Wide gap  -  time the train car"),
    (4250, 4450, "Collect the PAGE  -  it has the STATION MASTER door CODE"),
    (5100, 5260, "STATION MASTER door:  press E and type the CODE from the page  (keycard does NOT work)"),
    (5260, 5600, "Press L = LAPTOP  ->  WIRE CONNECT  ->  release the VAULT INTERLOCK"),
    (5600, 5850, "Cargo vault:  key 8 VAULT THERMITE (2 sec)"),
    (5850, 6500, "Grab the GOLD and jump into the SERVICE TUNNEL"),
]
SPOT_LINES = ["Freeze! Metro Police!", "Hey! Stop right there!", "Thief! Hands up!"]
CHAT_LINES = ["Gold train is on schedule.", "Good boy... keep sniffing.", "Mind the third rail.",
              "I have CCTV footage in this station."]


class World8(HeistWorld):
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
    TARGET = "BULLION GOLD CRATE"
    REWARD = 2200
    BAIL = 700
    WIN_TITLE = "BULLION GOLD STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES
    GROUND_SEGS = SEGS

    def __init__(self, save, save_fn):
        self.bg = Tiled(540, metro_wall, seed=41)
        super().__init__(save, save_fn)

    def make_guard(self, spec):
        return TorchGuard(spec[0], spec[1], self)

    def after_restart(self):
        self.interlock = False
        self.movers = [TrainCar(1600, GROUND_Y, 150, "x", 125, 0.9, 0.0),
                       TrainCar(3150, 408, 120, "y", 34, 1.0, 0.0),
                       TrainCar(4900, GROUND_Y, 160, "x", 120, 0.8, 1.0)]

    def make_features(self):
        def release(w):
            w.interlock = True
            w.say("VAULT INTERLOCK RELEASED")
        return [PageFeature(4300, "metro_master", "STATION MASTER CODE"),
                CodeLockDoor(5260, "metro_master", "STATION MASTER"),
                TerminalFeature(5480, ["ssh master@metro-control", "cargo.interlock(release=True)"],
                                "LAPTOP  -  STATION MASTER CONTROL", release),
                VaultDoor(5850, "thermite", "CARGO VAULT"),
                LootFeature(6060, "BULLION GOLD CRATE", draw_bullion)]

    def extra_update(self, dt):
        p = self.p
        if p.alive and p.y > GROUND_Y + 25 and not p.on_ground:
            self.burst(p.x, GROUND_Y + 50, (160, 220, 255), 30, 300, 0.7, grav=100)
            sound.play("zap")
            self.kill("electrocuted")
            self.say("ZAP!  Third rail = instant death")

    def draw_background(self, surf, cam):
        self.bg.draw(surf, cam)
        t = self.t
        for a, b in GAPS:
            if b - cam > -10 and a - cam < WIDTH + 10:
                draw_track_gap(surf, a - cam, b - cam, t)
        for a, b in SEGS:
            x0, x1 = a - cam, b - cam
            if x1 < -10 or x0 > WIDTH + 10:
                continue
            r = pygame.Rect(int(x0), GROUND_Y, int(x1 - x0), HEIGHT - GROUND_Y)
            SP.v_gradient(surf, r, (84, 88, 96), (38, 40, 48))
            pygame.draw.line(surf, (230, 190, 40), (r.x, GROUND_Y + 2), (r.right, GROUND_Y + 2), 4)
            for k in range(int(r.x - (r.x % 70)), r.right + 70, 70):
                pygame.draw.line(surf, (60, 64, 72), (k, GROUND_Y + 6), (k, HEIGHT), 1)
        tx = GOAL + 60 - cam
        if -200 < tx < WIDTH + 200:
            draw_tunnel(surf, tx, t)
        # cargo train car behind vault
        vx = 5850 - cam
        r = pygame.Rect(int(vx), GROUND_Y - 150, 480, 150)
        if r.right > 0 and r.x < WIDTH:
            pygame.draw.rect(surf, (40, 34, 30), r)
            pygame.draw.rect(surf, (120, 100, 60), r, 4)
            for k in range(1, 12):
                pygame.draw.line(surf, (64, 54, 44), (r.x + k * 40, r.y + 4), (r.x + k * 40, r.bottom - 4), 2)
            f = get_font(15).render("CARGO  VAULT  CAR", True, (255, 210, 120))
            surf.blit(f, f.get_rect(center=(r.centerx, r.y - 16)))

    def draw_fx(self, surf, cam):
        lights = [("circle", (self.p.x - cam, self.p.y - 30), 90, 0.9)]
        for g in self.guards:
            if g.alive and hasattr(g, "cone_pts"):
                lights.append(("circle", (g.x - cam, GROUND_Y - 40), 50, 0.6))
                lights.append(("poly", g.cone_pts(self.t, cam), 1.0))
        for x in range(300, LEVEL_W, 420):
            lights.append(("circle", (x - cam, CEIL_Y + 20), 170, 0.8))
        for c in self.cams:
            if not c.hacked and not self.systems_off():
                lx, ly = c.lens(self.t)
                lights.append(("circle", (lx - cam, ly), 40, 0.6))
        lights.append(("circle", (6060 - cam, GROUND_Y - 40), 140, 0.9))
        lights.append(("circle", (GOAL + 60 - cam, GROUND_Y - 80), 120, 0.8))
        for m in self.movers:
            lights.append(("circle", (m.cx - cam, m.y + 20), 110, 0.8))
        light_overlay(surf, 130, lights)
        for g in self.guards:
            if g.alive and hasattr(g, "cone_pts"):
                pts = g.cone_pts(self.t, cam)
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                bx, by = int(min(xs)), int(min(ys))
                cs = pygame.Surface((int(max(xs)) - bx + 2, int(max(ys)) - by + 2), pygame.SRCALPHA)
                pygame.draw.polygon(cs, (255, 235, 150, 40), [(q[0] - bx, q[1] - by) for q in pts])
                surf.blit(cs, (bx, by))


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((36, 40, 46))
        cache.setdefault("t", Tiled(540, metro_wall, seed=41)).draw(s, off)
        draw_floor(s, off, (84, 88, 96), (38, 40, 48), (230, 190, 40))

    return H.run_heist(screen, clock, save, save_fn, World8, "METRO SUBWAY GOLD HEIST",
                       ["Steal the BULLION GOLD CRATE from the cargo train.",
                        "Electrified rails, moving train cars, K9 handlers.",
                        "Keycard, terminal, thermite - then the service tunnel."],
                       back, lambda s, c, t: draw_bullion(s, c, t),
                       "Metro subway gold heist. Steal the bullion gold crate.")
