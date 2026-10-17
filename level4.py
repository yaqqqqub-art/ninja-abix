"""
level4.py - Chapter 1 / Level 4 : ROYAL MUSEUM HEIST.
main_game.py theke:  level4.run(screen, clock, save, save_fn)

Lokkho: raater museum e dhuke "PHARAOH'S GOLD SCEPTER" churi kore service exit diye palao.

Notun challenge:
  - PRESSURE PLATE (floor tile): pa dile security GATE namey ba DART trap chole. Lafiye par ho,
    ba REWIRER PRO (key 6) diye short-circuit koro.
  - Ondhokar museum: Night-Watch guard der TORCH.  Shudhu torch er alor moddhe thakle dekhte pay.
  - SARCOPHAGUS: kache giye E chaple bhitore lukiye jao (guard ar kukur dekhte pabe na).  Nora/ A/D chaple berobe.
  - Case er sensor off korte LAPTOP, ba LASER BREAKER (/TKDIAMONDLASER) diye nissobde kato.
Camera code: /CAMERA01099
"""
import math
import random
import pygame

import sound
import sprites as SP
import level1 as L1
from level1 import Camera, clamp, GROUND_Y, CEIL_Y
from level2 import Guard2, Dog
from animation import WIDTH, HEIGHT, get_font
import heist as H
from heist import (HeistWorld, Feature, DoorFeature, TerminalFeature, LootFeature, CaseFeature,
                   SweepGridFeature, Tiled, draw_floor, light_overlay)

LEVEL_W = 6400
GOAL = 6180


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_scepter(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 46, (255, 210, 90), 70, 4)
    pygame.draw.line(surf, (210, 160, 40), (x - 20, y + 22), (x + 20, y - 22), 6)
    pygame.draw.line(surf, (255, 230, 130), (x - 20, y + 22), (x + 20, y - 22), 2)
    pygame.draw.circle(surf, (40, 120, 220), (x + 22, y - 25), 9)
    pygame.draw.circle(surf, (255, 220, 100), (x + 22, y - 25), 9, 3)
    pygame.draw.polygon(surf, (255, 210, 80), [(x + 12, y - 30), (x + 22, y - 44), (x + 32, y - 30)])


def museum_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (46, 50, 70), (26, 28, 44))
    pygame.draw.rect(s, (16, 18, 28), (0, 0, w, 34))
    pygame.draw.rect(s, (200, 170, 100), (0, 34, w, 4))
    for cx in (20, w - 20):                                     # marble columns
        pygame.draw.rect(s, (150, 152, 168), (cx - 16, 38, 32, GROUND_Y - 38))
        pygame.draw.rect(s, (200, 202, 216), (cx - 16, 38, 8, GROUND_Y - 38))
        pygame.draw.rect(s, (110, 112, 130), (cx - 22, GROUND_Y - 16, 44, 16))
    # paintings
    for i in range(2):
        r = pygame.Rect(90 + i * 230, 100, 130, 100)
        pygame.draw.rect(s, (120, 86, 40), r.inflate(14, 14))
        SP.v_gradient(s, r, rnd.choice(((60, 90, 130), (120, 80, 60), (70, 110, 80))), (24, 28, 40))
        pygame.draw.circle(s, (230, 220, 180), (r.centerx + rnd.randint(-30, 30), r.centery - 8), 14)
    # dinosaur skeleton (rib cage)
    bx = 190
    pygame.draw.line(s, (214, 206, 180), (bx, GROUND_Y - 130), (bx + 250, GROUND_Y - 130), 8)
    for k in range(9):
        x = bx + 40 + k * 22
        pygame.draw.arc(s, (214, 206, 180), (x - 18, GROUND_Y - 130, 36, 90 - abs(k - 4) * 8), math.pi, math.tau, 4)
    pygame.draw.circle(s, (214, 206, 180), (bx - 10, GROUND_Y - 150), 22)
    pygame.draw.rect(s, (214, 206, 180), (bx - 44, GROUND_Y - 150, 34, 18))
    for k in range(6):
        pygame.draw.polygon(s, (240, 236, 220), [(bx - 40 + k * 5, GROUND_Y - 132), (bx - 38 + k * 5, GROUND_Y - 122), (bx - 36 + k * 5, GROUND_Y - 132)])
    for lx in (bx + 80, bx + 170):
        pygame.draw.line(s, (214, 206, 180), (lx, GROUND_Y - 130), (lx - 8, GROUND_Y - 6), 7)
    pygame.draw.line(s, (214, 206, 180), (bx + 250, GROUND_Y - 130), (bx + 360, GROUND_Y - 110), 7)
    # statue
    sx = 520
    pygame.draw.rect(s, (130, 132, 150), (sx - 24, GROUND_Y - 40, 48, 40))
    pygame.draw.rect(s, (200, 202, 216), (sx - 14, GROUND_Y - 130, 28, 90), border_radius=8)
    pygame.draw.circle(s, (210, 212, 226), (sx, GROUND_Y - 146), 14)
    pygame.draw.line(s, (200, 202, 216), (sx + 14, GROUND_Y - 120), (sx + 34, GROUND_Y - 150), 6)


def draw_sarcophagus(surf, x, t, near, inside):
    r = pygame.Rect(0, 0, 58, 130)
    r.midbottom = (x, GROUND_Y)
    SP.v_gradient(surf, r, (210, 170, 70), (130, 96, 36))
    pygame.draw.rect(surf, (70, 44, 14), r, 3, border_radius=18)
    pygame.draw.circle(surf, (230, 190, 90), (x, r.y + 26), 20)
    pygame.draw.rect(surf, (30, 60, 150), (x - 18, r.y + 24, 36, 5))
    for k in range(5):
        pygame.draw.line(surf, (70, 44, 14), (x - 20, r.y + 56 + k * 14), (x + 20, r.y + 56 + k * 14), 3)
    pygame.draw.line(surf, (30, 60, 150), (x, r.y + 48), (x, r.bottom - 6), 3)
    if near and not inside:
        f = get_font(14).render("[E]  HIDE", True, (200, 230, 255))
        surf.blit(f, f.get_rect(midbottom=(x, r.y - 6)))


def draw_exit(surf, x, t):
    r = pygame.Rect(0, 0, 110, 220)
    r.midbottom = (x, GROUND_Y)
    pygame.draw.rect(surf, (20, 22, 30), r.inflate(14, 14))
    SP.v_gradient(surf, r, (30, 50, 90), (90, 120, 170))
    f = get_font(16).render("SERVICE EXIT", True, (80, 255, 150))
    surf.blit(f, f.get_rect(center=(x, r.y - 22)))


# ------------------------------------------------------------------
# Features
# ------------------------------------------------------------------
class SarcFeature(Feature):
    def __init__(self, x):
        self.x = x

    def can_enter(self, w):
        return abs(w.p.x - self.x) < 60 and w.p.on_ground

    def enter(self, w):
        w.in_sarc = self
        w.p.hidden = True
        w.p.x = self.x
        w.p.vx = 0
        sound.play("hide")
        w.say("HIDDEN in the sarcophagus")

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if -80 < x < WIDTH + 80:
            draw_sarcophagus(surf, x, t, self.can_enter(w) and w.state == "play", w.in_sarc is self)


class PlateFeature(Feature):
    """Floor pressure plate. kind: gate | dart"""

    def __init__(self, x0, x1, kind, gx=None):
        self.x0, self.x1, self.kind, self.gx = x0, x1, kind, gx
        self.disabled = False
        self.cool = 0.0
        self.gate_t = 0.0
        self.darts = 0
        self.dart_t = 0.0
        self.flash = 0.0

    def on_respawn(self, w):
        self.gate_t = self.darts = 0
        self.cool = 0.0

    def solids(self, w):
        if self.gate_t > 0:
            return [pygame.Rect(self.gx - 10, CEIL_Y, 20, GROUND_Y - CEIL_Y)]
        return []

    def targets(self, w, add):
        d = 0 if self.x0 <= w.p.x <= self.x1 else min(abs(w.p.x - self.x0), abs(w.p.x - self.x1))
        if not self.disabled and d < 170:
            add("rewirer", d, (self, None))

    def use(self, w, tid, payload):
        self.disabled = True
        sound.play("hack")
        w.burst((self.x0 + self.x1) / 2, GROUND_Y - 4, (120, 255, 190), 18, 180, 0.7, grav=100)
        w.say("PLATE SHORT-CIRCUITED")

    def prompt(self, w, tid, payload):
        return ((self.x0 + self.x1) / 2, GROUND_Y - 80), ["[E]  REWIRE PLATE", "short-circuit trap"]

    def update(self, w, dt):
        self.cool = max(0.0, self.cool - dt)
        self.flash = max(0.0, self.flash - dt)
        p = w.p
        if self.gate_t > 0:
            self.gate_t = max(0.0, self.gate_t - dt)
        if self.darts > 0:
            self.dart_t -= dt
            if self.dart_t <= 0:
                self.dart_t = 0.18
                self.darts -= 1
                ex = self.x1 + 150
                w.bullets.append({"x": ex, "y": GROUND_Y - 30, "vx": -560.0, "life": 1.1, "cause": "dart"})
                ex2 = self.x0 - 150
                w.bullets.append({"x": ex2, "y": GROUND_Y - 30, "vx": 560.0, "life": 1.1, "cause": "dart"})
                sound.play("whoosh", 0.5)
        if self.disabled or w.systems_off() or not p.alive:
            return
        on = self.x0 <= p.x <= self.x1 and p.y >= GROUND_Y - 3 and not p.hidden
        if on and self.cool <= 0:
            self.cool = 5.0
            self.flash = 0.6
            sound.play("beep")
            if self.kind == "gate":
                self.gate_t = 5.0
                sound.play("alarm", 0.6)
                w.add_noise(self.gx, "glass")
                w.say("PRESSURE PLATE!  Gate is closing")
            else:
                self.darts = 4
                self.dart_t = 0.0
                w.say("PRESSURE PLATE!  DART TRAP")

    def draw(self, w, surf, cam, t):
        a, b = self.x0 - cam, self.x1 - cam
        if b < -100 or a > WIDTH + 100:
            return
        live = not self.disabled and not w.systems_off()
        col = (255, 70, 70) if live else (70, 200, 120)
        if self.flash > 0:
            col = (255, 255, 255)
        r = pygame.Rect(a, GROUND_Y + 2, b - a, 8)
        pygame.draw.rect(surf, (50, 50, 60), r.inflate(0, 6))
        pygame.draw.rect(surf, col, r)
        if live:
            for i in range(int((b - a) // 20)):
                pygame.draw.rect(surf, (20, 20, 26), (a + 5 + i * 20, GROUND_Y + 3, 8, 6))
        if self.kind == "dart":
            for ex, d in ((self.x1 + 150, -1), (self.x0 - 150, 1)):
                sx = ex - cam
                pygame.draw.rect(surf, (70, 66, 80), (sx - 10, GROUND_Y - 46, 20, 32), border_radius=4)
                pygame.draw.circle(surf, (20, 20, 26), (int(sx + d * 6), GROUND_Y - 30), 5)
        else:
            gx = self.gx - cam
            pygame.draw.rect(surf, (60, 62, 76), (gx - 14, CEIL_Y, 28, 18))
            if self.gate_t > 0:
                k = clamp((5.0 - self.gate_t) / 0.35, 0, 1) if self.gate_t > 4.65 else (1.0 if self.gate_t > 0.4 else self.gate_t / 0.4)
                hgt = int((GROUND_Y - CEIL_Y - 18) * k)
                for i in range(-8, 9, 4):
                    pygame.draw.line(surf, (170, 176, 196), (gx + i, CEIL_Y + 18), (gx + i, CEIL_Y + 18 + hgt), 3)
                pygame.draw.line(surf, (170, 176, 196), (gx - 9, CEIL_Y + 18 + hgt), (gx + 9, CEIL_Y + 18 + hgt), 5)
            else:
                pygame.draw.line(surf, (110, 114, 134), (gx - 9, CEIL_Y + 18), (gx + 9, CEIL_Y + 18), 4)


class TorchGuard(Guard2):
    RANGE, HALF = 350, 0.30

    def torch(self, t):
        ang = (0.0 if self.facing > 0 else math.pi) + self.facing * (0.12 + 0.18 * math.sin(t * 1.5 + self.x0))
        return (self.x + self.facing * 22, GROUND_Y - 42), ang

    def sees(self, p):
        if p.hidden or not p.alive or self.world.smoke_hides(p):
            return False
        dx, dy = p.x - self.x, abs(p.y - GROUND_Y)
        if dy > 90:
            return False
        if self.alert > 0:
            return abs(dx) < 520
        if abs(dx) < 50:
            return True
        (ox, oy), ang = self.torch(self.world.t)
        vx, vy = p.x - ox, (p.y - 30) - oy
        d = math.hypot(vx, vy)
        if d > self.RANGE:
            return False
        diff = (math.atan2(vy, vx) - ang + math.pi) % math.tau - math.pi
        return abs(diff) <= self.HALF

    def cone_pts(self, t, cam):
        (ox, oy), ang = self.torch(t)
        pts = [(ox - cam, oy)]
        for k in (-self.HALF, -self.HALF / 2, 0, self.HALF / 2, self.HALF):
            pts.append((ox - cam + math.cos(ang + k) * self.RANGE, oy + math.sin(ang + k) * self.RANGE))
        return pts


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(850, 990, 350),
          (3000, 3110, 365), (3160, 3270, 290), (3320, 3430, 215),
          (4650, 4750, 360), (4800, 4900, 285)]
STARS = [(920, 312), (3380, 177), (4850, 247)]
CASH = [(450, GROUND_Y - 12), (1000, GROUND_Y - 12), (1550, GROUND_Y - 12), (2150, GROUND_Y - 12),
        (3050, 350), (3350, 200), (3750, GROUND_Y - 12), (4450, GROUND_Y - 12), (5000, GROUND_Y - 12),
        (5550, GROUND_Y - 12)]
GUARDS = [(700, 1000), (1750, 2050), (2600, 2950), (3650, 3950), (4950, 5250)]
DOGS = [(3000, 3350), (5300, 5550)]
CAMS = [(1350, 0.0), (3300, 1.5), (5250, 3.0)]
CHECKPOINTS = [1500, 2450, 4550]
HINTS = [
    (0, 420, "ROYAL MUSEUM  -  steal the PHARAOH'S GOLD SCEPTER.  It is DARK in here"),
    (500, 800, "Night-watch TORCH:  guards only see you inside the light"),
    (1000, 1250, "RED PLATE = gate trap.  Jump over it or key 6 REWIRER PRO"),
    (1500, 1750, "SARCOPHAGUS:  press E to hide inside  (A / D to come out)"),
    (2150, 2500, "DART TRAP plate:  jump over it, or REWIRE it"),
    (3000, 3400, "Dogs smell you...  hide in a sarcophagus or use SMOKE (key 7)"),
    (4250, 4400, "Moving laser:  key 1 + /TKDIAMONDLASER"),
    (5250, 5450, "Key 3 LAPTOP turns the case SENSOR off  (or cut glass: key 1)"),
    (5650, 6000, "Take the SCEPTER and run to the SERVICE EXIT"),
]
SPOT_LINES = ["Intruder in the museum!", "Hey! Stop right there!", "Thief! Hands up!"]
CHAT_LINES = ["Nothing touches the Pharaoh's Scepter.", "Watch your step, the plates are live.",
              "Dark tonight...", "I have CCTV footage in this museum."]


class World4(HeistWorld):
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
    TARGET = "PHARAOH'S GOLD SCEPTER"
    REWARD = 1200
    BAIL = 500
    WIN_TITLE = "PHARAOH'S SCEPTER STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES

    def __init__(self, save, save_fn):
        self.bg = Tiled(640, museum_wall, seed=9)
        super().__init__(save, save_fn)

    def make_guard(self, spec):
        return TorchGuard(spec[0], spec[1], self)

    def make_features(self):
        case = CaseFeature(5700, "", lambda *a: None, item_y=GROUND_Y - 78)
        self.case = case
        return [SarcFeature(x) for x in (600, 1650, 2400, 3550, 4600)] + [
            PlateFeature(1100, 1210, "gate", gx=1400),
            PlateFeature(2650, 2750, "dart"),
            PlateFeature(3850, 3950, "dart"),
            PlateFeature(5050, 5160, "gate", gx=5420),
            SweepGridFeature([(4200, 4340, 0.0), (5480, 5600, 2.0)]),
            TerminalFeature(5300, ["sudo museum --sensors off", "disable case_0 --scepter"],
                            "LAPTOP  -  MUSEUM SECURITY", lambda w: setattr(case, "sensor_on", False)),
            case,
            LootFeature(5700, "PHARAOH'S GOLD SCEPTER", draw_scepter, requires=lambda w: case.open, y=GROUND_Y - 78),
        ]

    def interact(self):
        if self.in_sarc is not None:
            return False
        for f in self.features:
            if isinstance(f, SarcFeature) and f.can_enter(self):
                f.enter(self)
                return True
        return False

    def draw_background(self, surf, cam):
        self.bg.draw(surf, cam)
        ex = GOAL + 40 - cam
        if -200 < ex < WIDTH + 200:
            draw_exit(surf, ex, self.t)
        draw_floor(surf, cam, (70, 70, 88), (36, 36, 50), (190, 160, 100), stripe=(90, 90, 110), tile=120)

    def draw_fx(self, surf, cam):
        t = self.t
        lights = []
        px, py = self.p.x - cam, self.p.y - 30
        lights.append(("circle", (px, py), 62, 0.9))
        for g in self.guards:
            if g.alive:
                lights.append(("circle", (g.x - cam, GROUND_Y - 40), 40, 0.5))
                lights.append(("poly", g.cone_pts(t, cam), 1.0))
        for c in self.cams:
            if not c.hacked and not self.systems_off():
                lx, ly = c.lens(t)
                lights.append(("circle", (lx - cam, ly), 40, 0.6))
        sx = 5700 - cam
        lights.append(("circle", (sx, GROUND_Y - 70), 130, 0.9))
        for f in self.features:
            if isinstance(f, PlateFeature):
                lights.append(("circle", ((f.x0 + f.x1) / 2 - cam, GROUND_Y), 90, 0.5))
            if isinstance(f, SarcFeature):
                lights.append(("circle", (f.x - cam, GROUND_Y - 60), 70, 0.45))
        for i, (sx_, sy_) in enumerate(STARS):
            if not self.got[i]:
                lights.append(("circle", (sx_ - cam, sy_), 60, 0.7))
        ex = GOAL + 40 - cam
        lights.append(("circle", (ex, GROUND_Y - 100), 120, 0.7))
        light_overlay(surf, 190, lights)
        for g in self.guards:                              # torch er halka rong
            if g.alive:
                pts = g.cone_pts(t, cam)
                xs, ys = [q[0] for q in pts], [q[1] for q in pts]
                bx, by = int(min(xs)), int(min(ys))
                cs = pygame.Surface((int(max(xs)) - bx + 2, int(max(ys)) - by + 2), pygame.SRCALPHA)
                pygame.draw.polygon(cs, (255, 235, 150, 40), [(q[0] - bx, q[1] - by) for q in pts])
                surf.blit(cs, (bx, by))
        if self.in_sarc is not None:
            pass


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((20, 22, 36))
        cache.setdefault("t", Tiled(640, museum_wall, seed=9)).draw(s, off)
        draw_floor(s, off, (70, 70, 88), (36, 36, 50), (190, 160, 100))

    return H.run_heist(screen, clock, save, save_fn, World4, "ROYAL MUSEUM HEIST",
                       ["Steal the PHARAOH'S GOLD SCEPTER.",
                        "Dark halls, torch guards, pressure plates.",
                        "Hide in sarcophagi with E."],
                       back, lambda s, c, t: draw_scepter(s, c, t),
                       "Royal Museum. Steal the Pharaoh's gold scepter.")
