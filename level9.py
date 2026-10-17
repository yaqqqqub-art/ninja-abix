"""
level9.py - Chapter 1 / Level 9 : MILITARY RESEARCH LAB.
main_game.py theke:  level9.run(screen, clock, save, save_fn)

Lokkho: underground military lab theke "WARP TECH SCHEMATICS" (microchip) churi kore vent hatch diye drainage canal e palao.

Notun challenge:
  - TOXIC GAS ZONE:  shobuj gas e dhukle health komte thake.  Gas er age terminal e LAPTOP diye
    ventilation override koro (Python app e  unlock  likho).
  - CEILING TURRET:  lal tracking line charge hoy tarpor shoot.  Dourate thako ba REWIRER PRO (key 6)
    diye permanent short-circuit (tokhon guard der mare).  EMP = 5 sec off.
  - RIOT-SHIELD guard:  shamne theke knife bounce.  Pichon theke / SMOKE (key 7) / DECOY (key 5).
  - AIRLOCK door:  CODE LOCK (keycard kaj kore na) - code ta PAGE e lekha, chamber 1 er por kuriye nao.
  - Terminal: L chaple laptop khole (kache jete hoy na) -> WIRE CONNECT.
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
from heist import (HeistWorld, Feature, DoorFeature, CodeLockDoor, PageFeature, TerminalFeature, LootFeature, Tiled, draw_floor)

LEVEL_W = 6600
GOAL = 6440


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_chip(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 52, (120, 200, 255), 90, 4)
    r = pygame.Rect(0, 0, 44, 44)
    r.center = (x, y)
    SP.v_gradient(surf, r, (50, 70, 120), (20, 30, 60))
    pygame.draw.rect(surf, (140, 200, 255), r, 2, border_radius=4)
    for k in range(5):
        pygame.draw.line(surf, (200, 220, 240), (r.x - 6, r.y + 6 + k * 8), (r.x, r.y + 6 + k * 8), 2)
        pygame.draw.line(surf, (200, 220, 240), (r.right, r.y + 6 + k * 8), (r.right + 6, r.y + 6 + k * 8), 2)
    pygame.draw.circle(surf, (255, 255, 160), (int(x), int(y)), 8)
    pygame.draw.circle(surf, (80, 120, 220), (int(x), int(y)), 8, 2)
    a = t * 3
    pygame.draw.line(surf, (255, 255, 255), (x + math.cos(a) * 5, y + math.sin(a) * 5), (x - math.cos(a) * 5, y - math.sin(a) * 5), 2)


def lab_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (44, 52, 60), (22, 28, 36))
    for px in range(0, w, 120):                                    # steel panels
        pygame.draw.rect(s, (30, 38, 46), (px + 4, 44, 112, GROUND_Y - 50), border_radius=4)
        pygame.draw.rect(s, (70, 82, 94), (px + 4, 44, 112, GROUND_Y - 50), 2, border_radius=4)
        for k in range(4):
            pygame.draw.circle(s, (90, 100, 112), (px + 12 + (k % 2) * 96, 54 + (k // 2) * (GROUND_Y - 78)), 3)
    pygame.draw.rect(s, (14, 18, 24), (0, 0, w, 38))
    pygame.draw.rect(s, (230, 200, 40), (0, 38, w, 5))
    # bio-hazard glass cylinders
    for cx in (110, 340):
        tube = pygame.Rect(cx - 36, 120, 72, GROUND_Y - 124)
        SP.v_gradient(s, tube, (40, 120, 70), (14, 60, 34))
        pygame.draw.rect(s, (150, 200, 170), tube, 3, border_radius=30)
        pygame.draw.rect(s, (30, 34, 40), (cx - 44, 108, 88, 14), border_radius=4)
        pygame.draw.rect(s, (30, 34, 40), (cx - 44, GROUND_Y - 10, 88, 10))
        pygame.draw.ellipse(s, (20, 40, 28), (cx - 14, 230, 28, 70))            # specimen
        pygame.draw.circle(s, (20, 40, 28), (cx, 220), 14)
        for _ in range(10):
            pygame.draw.circle(s, (120, 230, 150), (cx + rnd.randint(-26, 26), rnd.randint(140, GROUND_Y - 30)), rnd.randint(2, 4), 1)
    # hazard sign
    pygame.draw.polygon(s, (230, 200, 40), [(w - 140, 150), (w - 90, 150), (w - 115, 108)])
    pygame.draw.polygon(s, (20, 20, 20), [(w - 140, 150), (w - 90, 150), (w - 115, 108)], 3)
    f = get_font(24, ).render("!", True, (20, 20, 20))
    s.blit(f, f.get_rect(center=(w - 115, 134)))
    # hazard stripes at bottom of wall
    for x in range(0, w, 30):
        pygame.draw.polygon(s, (230, 200, 40), [(x, GROUND_Y - 10), (x + 15, GROUND_Y - 10), (x + 5, GROUND_Y), (x - 10, GROUND_Y)])


def draw_klaxon(surf, x, t):
    pygame.draw.rect(surf, (50, 54, 62), (x - 14, CEIL_Y, 28, 12))
    a = t * 6
    on = math.sin(a) > 0
    col = (255, 50, 40) if on else (110, 20, 20)
    pygame.draw.circle(surf, col, (int(x), CEIL_Y + 22), 11)
    if on:
        SP.glow(surf, (x, CEIL_Y + 22), 80, (255, 60, 40), 40, 3)


def draw_hatch(surf, x, t):
    pygame.draw.ellipse(surf, (20, 22, 26), (x - 60, GROUND_Y - 8, 120, 16))
    pygame.draw.ellipse(surf, (80, 255, 150), (x - 60, GROUND_Y - 8, 120, 16), 3)
    for k in range(5):
        a = (t * 1.5 + k / 5) % 1.0
        pygame.draw.circle(surf, (80, 255, 150), (int(x), int(GROUND_Y - 4 + a * 40)), 3)
    f = get_font(15).render("VENT HATCH  -  DRAINAGE CANAL", True, (80, 255, 150))
    surf.blit(f, f.get_rect(center=(x, GROUND_Y - 130)))
    pygame.draw.line(surf, (80, 255, 150), (x, GROUND_Y - 110), (x, GROUND_Y - 30), 3)
    pygame.draw.polygon(surf, (80, 255, 150), [(x - 8, GROUND_Y - 38), (x + 8, GROUND_Y - 38), (x, GROUND_Y - 24)])


# ------------------------------------------------------------------
# Features
# ------------------------------------------------------------------
class GasZone(Feature):
    DRAIN = 1.0

    def __init__(self, x0, x1):
        self.x0, self.x1 = x0, x1
        self.clear = False
        self.k = 1.0            # gas density (fade out)
        self.tick = 0.0

    def inside(self, w):
        return self.x0 <= w.p.x <= self.x1 and w.p.alive

    def update(self, w, dt):
        if self.clear:
            self.k = max(0.0, self.k - dt * 0.6)
            return
        if self.inside(w) and w.state == "play" and not w.god:
            self.tick += dt
            if self.tick >= self.DRAIN:
                self.tick = 0.0
                p = w.p
                p.health -= 1
                p.flash = 0.3
                sound.play("hurt")
                w.shake = max(w.shake, 0.15)
                w.floats.append({"x": p.x, "y": p.y - 80, "t": 1.0, "txt": "TOXIC!", "c": (130, 255, 120)})
                if p.health <= 0:
                    w.kill("toxic gas")
        else:
            self.tick = max(0.0, self.tick - dt)

    def draw(self, w, surf, cam, t):
        a, b = self.x0 - cam, self.x1 - cam
        if b < -50 or a > WIDTH + 50 or self.k <= 0:
            return
        a0 = int(110 * self.k)
        gs = pygame.Surface((int(b - a), GROUND_Y - CEIL_Y), pygame.SRCALPHA)
        gs.fill((60, 255, 90, int(30 * self.k)))
        surf.blit(gs, (a, CEIL_Y))
        rnd = random.Random(7)
        for i in range(int((b - a) // 26)):
            bx = rnd.uniform(0, b - a)
            by = rnd.uniform(0, GROUND_Y - CEIL_Y)
            ph = rnd.uniform(0, 6)
            rr = rnd.randint(26, 52)
            cx = a + bx + math.sin(t * 0.8 + ph) * 18
            cy = CEIL_Y + (by + t * 14 * (1 if i % 2 else -1)) % (GROUND_Y - CEIL_Y)
            cl = pygame.Surface((rr * 2, rr * 2), pygame.SRCALPHA)
            pygame.draw.circle(cl, (80, 255, 100, int(a0 * 0.55)), (rr, rr), rr)
            surf.blit(cl, (cx - rr, cy - rr))
        for edge in (a, b):
            pygame.draw.rect(surf, (230, 200, 40), (edge - 5, CEIL_Y, 10, GROUND_Y - CEIL_Y))
        f = get_font(15).render("TOXIC GAS  -  override ventilation first", True, (130, 255, 120))
        surf.blit(f, f.get_rect(center=((max(a, 0) + min(b, WIDTH)) / 2, 100)))


class Turret(Feature):
    RANGE, CHARGE, COOL = 560, 1.1, 1.5

    def __init__(self, x):
        self.x = x
        self.y = CEIL_Y + 26
        self.state = "idle"
        self.t = 0.0
        self.dot = None
        self.rewired = False
        self.shot_t = 1.0
        self.beam = 0.0
        self.target = None

    def on_respawn(self, w):
        self.state, self.t, self.dot = "idle", 0.0, None

    def targets(self, w, add):
        d = abs(w.p.x - self.x)
        if not self.rewired and d < 180:
            add("rewirer", d, (self, None))

    def use(self, w, tid, payload):
        self.rewired = True
        sound.play("hack")
        w.burst(self.x, self.y, (120, 255, 190), 20, 200, 0.7, grav=100)
        w.say("TURRET REWIRED  -  now shoots guards")

    def prompt(self, w, tid, payload):
        return (self.x, self.y + 20), ["[E]  REWIRE TURRET", "short-circuit it"]

    def update(self, w, dt):
        p = w.p
        self.beam = max(0.0, self.beam - dt)
        if w.systems_off():
            self.state, self.dot = "idle", None
            return
        if self.rewired:
            self.shot_t -= dt
            if self.shot_t <= 0:
                best = None
                for g in w.guards:
                    if g.alive and abs(g.x - self.x) < self.RANGE and (best is None or abs(g.x - self.x) < abs(best.x - self.x)):
                        best = g
                if best is not None:
                    self.shot_t = 1.6
                    self.beam = 0.18
                    self.target = best.x
                    sound.play("zap")
                    best.die(w)
                    w.floats.append({"x": best.x, "y": GROUND_Y - 90, "t": 1.0, "txt": "TURRET KILL!", "c": (120, 255, 190)})
                else:
                    self.shot_t = 0.4
            return
        vis = p.alive and not p.hidden and not w.smoke_hides(p) and abs(p.x - self.x) < self.RANGE
        if not vis:
            if self.state == "charge":
                self.state, self.dot = "idle", None
            elif self.state == "cool":
                self.t -= dt
                if self.t <= 0:
                    self.state = "idle"
            return
        if self.state == "idle":
            self.state, self.t, self.dot = "charge", self.CHARGE, p.x
            sound.play("beep")
        elif self.state == "charge":
            self.dot += (p.x - self.dot) * min(1.0, 3.2 * dt)
            self.t -= dt
            if self.t <= 0:
                self.state, self.t = "cool", self.COOL
                self.beam = 0.15
                self.target = self.dot
                sound.play("gunshot")
                w.burst(self.dot, GROUND_Y - 20, (255, 200, 120), 8, 180, 0.4)
                if abs(self.dot - p.x) < 34 and w.state == "play":
                    w.hurt_player(1 if p.x > self.x else -1, "turret")
                self.dot = None
        else:
            self.t -= dt
            if self.t <= 0:
                self.state = "idle"

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if not (-80 < x < WIDTH + 80):
            return
        off = w.systems_off()
        col = (255, 70, 70) if not self.rewired else (80, 255, 150)
        if off:
            col = (90, 90, 100)
        pygame.draw.rect(surf, (60, 64, 76), (x - 18, CEIL_Y, 36, 14))
        pygame.draw.circle(surf, (40, 44, 56), (int(x), int(self.y)), 15)
        pygame.draw.circle(surf, col, (int(x), int(self.y)), 15, 3)
        ang = math.pi / 2
        tx = None
        if self.state == "charge" and self.dot is not None and not self.rewired:
            tx = self.dot
        elif self.beam > 0 and self.target is not None:
            tx = self.target
        if tx is not None:
            ang = math.atan2(GROUND_Y - 30 - self.y, tx - self.x)
        pygame.draw.line(surf, (110, 116, 134), (x, self.y), (x + math.cos(ang) * 30, self.y + math.sin(ang) * 30), 6)
        pygame.draw.circle(surf, col, (int(x), int(self.y)), 5)
        if tx is not None:
            k = 1 - self.t / self.CHARGE if self.state == "charge" else 1.0
            c2 = (255, 60, 30) if not self.rewired else (80, 255, 150)
            pygame.draw.line(surf, c2, (x, self.y), (tx - cam, GROUND_Y - 30), 1 + int(2 * k))
            pygame.draw.circle(surf, c2, (int(tx - cam), GROUND_Y - 30), 7, 2)
        if self.rewired:
            f = get_font(11).render("REWIRED", True, (80, 255, 150))
            surf.blit(f, f.get_rect(midtop=(x, self.y + 20)))


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(850, 990, 350),
          (2100, 2210, 365), (2260, 2370, 290), (2420, 2530, 215),
          (4950, 5060, 360), (5110, 5220, 285)]
STARS = [(920, 312), (2480, 177), (5170, 247)]
CASH = [(450, GROUND_Y - 12), (1000, GROUND_Y - 12), (1900, GROUND_Y - 12), (2300, 350),
        (2800, GROUND_Y - 12), (3200, GROUND_Y - 12), (3900, GROUND_Y - 12), (4400, GROUND_Y - 12),
        (4800, GROUND_Y - 12), (5900, GROUND_Y - 12)]
GUARDS = [(600, 900), (2000, 2300, "s"), (2500, 2850, "s"), (3700, 4000), (4600, 4900, "s")]
DOGS = [(3000, 3300), (4300, 4500)]
CAMS = [(1300, 0.0), (2300, 1.7), (3900, 3.0), (5600, 4.4)]
CHECKPOINTS = [1450, 2800, 4350, 5250]
HINTS = [
    (0, 420, "MILITARY RESEARCH LAB  -  steal the WARP TECH SCHEMATICS"),
    (850, 1200, "CEILING TURRET:  red line charges then fires.  Keep moving  or  key 6 REWIRER"),
    (1350, 1700, "TOXIC GAS ahead!  Press L = LAPTOP  ->  WIRE CONNECT  (or Python: unlock)"),
    (2000, 2400, "RIOT-SHIELD guard:  from behind, SMOKE (7) or DECOY (5)"),
    (2450, 2700, "Collect the PAGE  -  it has the AIRLOCK code"),
    (2850, 2990, "AIRLOCK:  press E and type the CODE from the page  (keycard does NOT work)"),
    (3200, 3500, "Second gas chamber - find the vent terminal first"),
    (5100, 5450, "Last chamber holds the SCHEMATICS - override the ventilation"),
    (5600, 6000, "Take the chip, then run to the VENT HATCH"),
]
SPOT_LINES = ["Intruder in the lab!", "Halt! Restricted area!", "Security breach! Hands up!"]
CHAT_LINES = ["Classified project. Stay sharp.", "Gas chambers are on a timer.", "Turrets are armed.",
              "I have CCTV footage in this lab."]


class World9(HeistWorld):
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
    TARGET = "WARP TECH SCHEMATICS"
    REWARD = 2500
    BAIL = 800
    WIN_TITLE = "WARP TECH STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES

    def __init__(self, save, save_fn):
        self.bg = Tiled(560, lab_wall, seed=51)
        super().__init__(save, save_fn)

    def make_guard(self, spec):
        if len(spec) == 3:
            return ShieldGuard(spec[0], spec[1], self)
        return Guard2(spec[0], spec[1], self)

    def make_features(self):
        zones = [GasZone(1700, 2400), GasZone(3500, 4200), GasZone(5450, 6050)]
        self.zones = zones
        feats = []
        for z, tx, nm in zip(zones, (1560, 3360, 5300), ("CHAMBER 1", "CHAMBER 2", "CHAMBER 3")):
            feats.append(z)
            feats.append(TerminalFeature(tx, ["ventilation.override(exhaust=True)", "decon.purge()"],
                                         f"LAPTOP  -  VENTILATION  -  {nm}",
                                         (lambda zz: (lambda w: (setattr(zz, "clear", True), w.say("VENTILATION OVERRIDDEN  -  gas clearing"))))(z)))
        feats += [Turret(1000), Turret(2650), Turret(4500), Turret(5200),
                  PageFeature(2600, "lab_airlock", "AIRLOCK CODE"),
                  CodeLockDoor(2920, "lab_airlock", "AIRLOCK"),
                  LootFeature(5780, "WARP TECH SCHEMATICS", draw_chip)]
        return feats

    def draw_background(self, surf, cam):
        self.bg.draw(surf, cam)
        t = self.t
        for kx in range(500, LEVEL_W, 900):
            sx = kx - cam
            if -40 < sx < WIDTH + 40:
                draw_klaxon(surf, sx, t + kx)
        hx = GOAL + 20 - cam
        if -100 < hx < WIDTH + 100:
            draw_hatch(surf, hx, t)
        draw_floor(surf, cam, (58, 64, 72), (22, 26, 32), (230, 200, 40), stripe=(40, 46, 54), tile=100)

    def draw_fx(self, surf, cam):
        p = self.p
        if any((not z.clear) and z.inside(self) for z in self.zones) and self.state == "play":
            a = int(50 + 20 * math.sin(self.t * 8))
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(ov, (60, 255, 80, a), ov.get_rect(), 14)
            surf.blit(ov, (0, 0))
            img = self.f_small.render("TOXIC GAS  -  health draining!", True, (140, 255, 130))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 150)))
        # red klaxon pulse
        a = int(16 * max(0.0, math.sin(self.t * 6)))
        if a > 1:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((255, 20, 20, a))
            surf.blit(ov, (0, 0))


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((30, 36, 44))
        cache.setdefault("t", Tiled(560, lab_wall, seed=51)).draw(s, off)
        draw_floor(s, off, (58, 64, 72), (22, 26, 32), (230, 200, 40))

    return H.run_heist(screen, clock, save, save_fn, World9, "MILITARY RESEARCH LAB",
                       ["Steal the WARP TECH SCHEMATICS microchip.",
                        "Toxic gas chambers, ceiling turrets, riot-shield guards.",
                        "Override the ventilation with the LAPTOP."],
                       back, lambda s, c, t: draw_chip(s, c, t),
                       "Military research lab. Steal the warp tech schematics.")
