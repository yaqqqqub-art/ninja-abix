"""
level5.py - Chapter 1 / Level 5 : CENTRAL CYBER VAULT.
main_game.py theke:  level5.run(screen, clock, save, save_fn)

Lokkho: underground data facility theke "QUANTUM MASTER DRIVE" churi kore extraction hatch diye palao.

Notun challenge:
  - TRIPLE LASER GRID: 3 ta laser ekshathe (upor-nich, bam-dan, ghurte thaka).  LASER BREAKER (/TKDIAMONDLASER) diye
    shob ek sathe off,  ba EMP.
  - DUAL TERMINAL:  Terminal A te LAPTOP diye POWER OFF (20 sec).  Tarpor 20 sec er moddhe Terminal B te giye
    LAPTOP code type kore BLAST DOOR khol.  Shomoy shesh hole abar A theke shuru.
  - RIOT-SHIELD cyber guard: shamne theke knife/punch shield e lege fire ashe.  Pichon theke mar,
    SMOKE BOMB (key 7) diye ondho kor, ba DECOY DRONE (key 5) diye ghurie dao.
Camera code: /CAMERA01099    Laser code: /TKDIAMONDLASER
"""
import math
import random
import pygame

import sound
import sprites as SP
import level1 as L1
from level1 import Camera, clamp, GROUND_Y, CEIL_Y
from level2 import Guard2
from animation import WIDTH, HEIGHT, get_font
import heist as H
import tools as TL
import abix_fx as FX
from heist import (HeistWorld, Feature, DoorFeature, SafeFeature, LootFeature, Tiled, draw_floor)

LEVEL_W = 6300
GOAL = 6120
POWER_TIME = 20.0


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_drive(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 50, (80, 230, 255), 80, 4)
    r = pygame.Rect(0, 0, 40, 40)
    r.center = (x, y)
    SP.v_gradient(surf, r, (90, 240, 255), (20, 110, 170))
    pygame.draw.rect(surf, (10, 50, 80), r, 3, border_radius=4)
    for k in range(3):
        pygame.draw.line(surf, (220, 255, 255), (x - 12, y - 8 + k * 8), (x + 12, y - 8 + k * 8), 2)
    pygame.draw.rect(surf, (255, 210, 80), (x - 10, y + 20, 20, 6))


def cyber_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (10, 24, 36), (6, 12, 22))
    pygame.draw.rect(s, (4, 8, 14), (0, 0, w, 34))
    pygame.draw.rect(s, (60, 210, 240), (0, 34, w, 3))
    for i in range(3):                                          # server racks
        rx = 20 + i * 190
        r = pygame.Rect(rx, GROUND_Y - 250, 130, 250)
        SP.v_gradient(s, r, (24, 34, 48), (12, 18, 28))
        pygame.draw.rect(s, (70, 100, 130), r, 2)
        for k in range(10):
            yy = r.y + 10 + k * 24
            pygame.draw.rect(s, (8, 12, 20), (r.x + 8, yy, r.w - 16, 18))
            for j in range(8):
                col = rnd.choice(((60, 255, 140), (60, 200, 255), (255, 170, 60), (40, 60, 70)))
                pygame.draw.circle(s, col, (r.x + 18 + j * 14, yy + 9), 3)
    for y in (70, 110):                                         # cooling pipes
        pygame.draw.rect(s, (60, 76, 96), (0, y, w, 12))
        pygame.draw.rect(s, (110, 134, 160), (0, y, w, 3))
        for x in range(30, w, 120):
            pygame.draw.rect(s, (40, 50, 66), (x, y - 3, 12, 18))
    for x in range(w - 20, w, 6):
        pass


def draw_hologram(surf, x, t):
    y = GROUND_Y - 150
    base = pygame.Rect(0, 0, 70, 14)
    base.midbottom = (x, GROUND_Y)
    pygame.draw.rect(surf, (30, 50, 70), base, border_radius=4)
    pygame.draw.line(surf, (60, 200, 255), (x, GROUND_Y - 14), (x, y + 40), 2)
    col = (70, 220, 255)
    SP.glow(surf, (x, y), 70, col, 30, 3)
    a = t * 1.2
    pts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                X = sx * math.cos(a) - sz * math.sin(a)
                Z = sx * math.sin(a) + sz * math.cos(a)
                pts.append((x + X * 34, y + sy * 34 + Z * 8))
    for i in range(8):
        for j in range(i + 1, 8):
            if bin(i ^ j).count("1") == 1:
                pygame.draw.line(surf, col, pts[i], pts[j], 2)


def draw_hatch(surf, x, t):
    r = pygame.Rect(0, 0, 120, 30)
    r.midbottom = (x, GROUND_Y)
    pygame.draw.rect(surf, (30, 36, 46), r)
    pygame.draw.rect(surf, (80, 255, 150), r, 2)
    for k in range(4):
        pygame.draw.polygon(surf, (80, 255, 150), [(x - 45 + k * 24, GROUND_Y - 6), (x - 33 + k * 24, GROUND_Y - 24), (x - 27 + k * 24, GROUND_Y - 24), (x - 39 + k * 24, GROUND_Y - 6)])
    f = get_font(16).render("EXTRACTION", True, (80, 255, 150))
    surf.blit(f, f.get_rect(center=(x, GROUND_Y - 120)))
    pygame.draw.line(surf, (80, 255, 150), (x, GROUND_Y - 100), (x, GROUND_Y - 40), 3)


# ------------------------------------------------------------------
# Triple laser grid
# ------------------------------------------------------------------
class TripleGrid(Feature):
    """Zone [x0, x1].  A: upor-nich beam, B: bam-dan ghurano vertical bar, C: ghurte thaka beam."""
    COLS = ((255, 70, 80), (80, 150, 255), (80, 255, 150))

    def __init__(self, x0, x1, phase=0.0):
        self.x0, self.x1, self.ph = x0, x1, phase
        self.on = True
        self.cx = (x0 + x1) / 2

    def a_y(self, w):
        return 330 + 200 * math.sin(w.t * 1.2 + self.ph)

    def b_x(self, w):
        return self.cx + (self.x1 - self.x0) / 2 * 0.85 * math.sin(w.t * 1.4 + self.ph + 1.0)

    def c_seg(self, w):
        a = w.t * 1.5 + self.ph
        cy = GROUND_Y - 105
        return ((self.cx - math.cos(a) * 110, cy - math.sin(a) * 110), (self.cx + math.cos(a) * 110, cy + math.sin(a) * 110))

    def dist(self, w):
        px = w.p.x
        return 0 if self.x0 <= px <= self.x1 else min(abs(px - self.x0), abs(px - self.x1))

    def targets(self, w, add):
        d = self.dist(w)
        if self.on and d < 160:
            add("laser", d, (self, None))

    def use(self, w, tid, payload):
        w.open_modal("feature", [TL.LASER_CODE], None, "LASER BREAKER  -  type the code")
        w.modal["feature"] = self

    def modal_done(self, w, m):
        self.on = False
        sound.play("laser")
        w.burst(self.cx, GROUND_Y - 110, (255, 200, 90), 30, 260, 0.8, grav=200)
        w.say("TRIPLE GRID DISABLED")

    def prompt(self, w, tid, payload):
        return (self.cx, GROUND_Y - 190), ["[E]  DISABLE GRID", "type code"]

    def hit(self, w):
        p = w.p
        pr = p.rect()
        if not (self.x0 - 10 <= p.x <= self.x1 + 10):
            return False
        if pr.colliderect(pygame.Rect(self.x0, int(self.a_y(w)) - 5, self.x1 - self.x0, 10)):
            return True
        if pr.colliderect(pygame.Rect(int(self.b_x(w)) - 5, CEIL_Y, 10, GROUND_Y - CEIL_Y)):
            return True
        (ax, ay), (bx, by) = self.c_seg(w)
        for k in range(0, 5):
            qy = p.y - 6 - k * 11
            vx, vy = bx - ax, by - ay
            ln = vx * vx + vy * vy
            u = clamp(((p.x - ax) * vx + (qy - ay) * vy) / ln, 0, 1)
            if math.hypot(p.x - (ax + vx * u), qy - (ay + vy * u)) < 14:
                return True
        return False

    def update(self, w, dt):
        if not self.on or w.systems_off() or not w.p.alive:
            return
        if self.hit(w):
            if w.p.inv <= 0:
                w.alarm(w.p.x, "ALARM!  Laser touched", zap=True)
            w.hurt_player(1 if w.p.x > self.cx else -1, "laser")

    def draw(self, w, surf, cam, t):
        a, b = self.x0 - cam, self.x1 - cam
        if b < -60 or a > WIDTH + 60:
            return
        for px in (a, b):
            pygame.draw.rect(surf, (36, 46, 62), (px - 8, CEIL_Y, 16, GROUND_Y - CEIL_Y))
            pygame.draw.rect(surf, (80, 110, 140), (px - 8, CEIL_Y, 4, GROUND_Y - CEIL_Y))
        if not self.on or w.systems_off():
            return
        c1, c2, c3 = self.COLS
        ay = min(self.a_y(w), GROUND_Y - 6)
        SP.glow(surf, ((a + b) / 2, ay), (b - a) * 0.5, c1, 34, 3)
        pygame.draw.line(surf, c1, (a, ay), (b, ay), 5)
        pygame.draw.line(surf, (255, 255, 255), (a, ay), (b, ay), 1)
        bx = self.b_x(w) - cam
        pygame.draw.line(surf, c2, (bx, CEIL_Y), (bx, GROUND_Y), 5)
        pygame.draw.line(surf, (255, 255, 255), (bx, CEIL_Y), (bx, GROUND_Y), 1)
        (ax, ay2), (bx2, by2) = self.c_seg(w)
        pygame.draw.line(surf, c3, (ax - cam, ay2), (bx2 - cam, by2), 5)
        pygame.draw.line(surf, (255, 255, 255), (ax - cam, ay2), (bx2 - cam, by2), 1)
        pygame.draw.circle(surf, (200, 255, 220), (int(self.cx - cam), int(GROUND_Y - 105)), 7)


# ------------------------------------------------------------------
# Dual terminals
# ------------------------------------------------------------------
class DualTerminal(Feature):
    def __init__(self, x, which, door):
        self.x, self.which, self.door = x, which, door
        self.done = False

    def locked(self, w):
        return self.which == "B" and w.power_t <= 0

    def targets(self, w, add):
        d = abs(w.p.x - self.x)
        if d < 80 and not self.door.opening and not (self.which == "A" and w.power_t > 0):
            add("laptop", d, (self, None))
            add("cutter", d, (self, None))                 # WIRE CUTTER (Level 5)

    def use(self, w, tid, payload):
        cut = tid == "cutter"
        if self.which == "A":
            if cut:
                w.open_cutter(self, "WIRE BOX  -  TERMINAL A  -  POWER GRID")
                return
            w.open_modal("feature", ["sudo grid --power off", "confirm --duration 20s"], None,
                         "LAPTOP  -  TERMINAL A  -  POWER GRID", os=True)
        else:
            if w.power_t <= 0:
                w.say("ACCESS DENIED  -  power is ONLINE.  Use TERMINAL A first!")
                sound.play("beep")
                return
            if cut:
                w.open_cutter(self, "WIRE BOX  -  TERMINAL B  -  BLAST DOOR")
                return
            w.open_modal("feature", ["sudo blastdoor --override", "open vault_gate --force"], None,
                         "LAPTOP  -  TERMINAL B  -  BLAST DOOR", os=True)
        w.modal["feature"] = self

    def modal_done(self, w, m):
        sound.play("unlock")
        if self.which == "A":
            w.power_t = POWER_TIME
            w.say(f"POWER OFF  -  reach TERMINAL B in {int(POWER_TIME)} s!")
        else:
            if w.power_t <= 0:
                w.say("Too slow!  Power is back online - redo TERMINAL A")
                return
            self.done = True
            self.door.open(w)
            w.say("BLAST DOOR OPEN")
            w.shake = 0.4

    def prompt(self, w, tid, payload):
        if tid == "cutter":
            return (self.x, GROUND_Y - 120), [f"[E]  CUT WIRES  {self.which}", "WIRE CUTTER"]
        return (self.x, GROUND_Y - 120), [f"[E]  TERMINAL {self.which}", "type the code"]

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if -100 < x < WIDTH + 100:
            st = "open" if (self.done or (self.which == "A" and w.power_t > 0)) else "locked"
            SP.draw_terminal(surf, x, GROUND_Y, st, t)
            f = get_font(16).render(f"TERMINAL {self.which}", True, (90, 230, 255))
            surf.blit(f, f.get_rect(midbottom=(x, GROUND_Y - 78)))


# ------------------------------------------------------------------
# Riot shield guard
# ------------------------------------------------------------------
class ShieldGuard(Guard2):
    def blinded(self):
        return self.world.smoke_hides_at(self.x)

    def front(self, p):
        return (p.x - self.x) * self.facing > 0 and not self.blinded()

    def bounce(self, w, p):
        sound.play("hit")
        w.burst(self.x + self.facing * 24, GROUND_Y - 50, (160, 220, 255), 12, 220, 0.5, grav=0)
        w.floats.append({"x": self.x, "y": GROUND_Y - 110, "t": 0.9, "txt": "BLOCKED!", "c": (160, 220, 255)})
        p.vx = -self.facing * 0
        self.state, self.timer, self.excl = "aim", self.AIM, 0.8
        self.alert = max(self.alert, 6.0)
        self.say(w, "Nice try, thief!")

    def stab(self, w, p):
        if self.front(p):
            self.bounce(w, p)
        else:
            self.die(w)
            w.floats.append({"x": self.x, "y": GROUND_Y - 100, "t": 1.0, "txt": "BACKSTAB!", "c": (255, 120, 120)})

    def punched(self, w):
        p = w.p
        if self.front(p):
            self.bounce(w, p)
        else:
            self.die(w)

    def draw(self, surf, cam, t):
        super().draw(surf, cam, t)
        if not self.alive:
            return
        x = self.x - cam
        if x < -120 or x > WIDTH + 120:
            return
        sx = x + self.facing * 24
        r = pygame.Rect(0, 0, 18, 70)
        r.center = (sx, GROUND_Y - 38)
        SP.v_gradient(surf, r, (140, 200, 240), (60, 100, 150))
        pygame.draw.rect(surf, (20, 40, 70), r, 2, border_radius=6)
        pygame.draw.line(surf, (230, 250, 255), (r.x + 4, r.y + 6), (r.x + 4, r.y + 30), 2)
        if self.blinded():
            f = get_font(20).render("?", True, (230, 230, 240))
            surf.blit(f, f.get_rect(center=(x, GROUND_Y - 108)))


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(850, 990, 350),
          (2900, 3010, 365), (3060, 3170, 290), (3220, 3340, 215),
          (5000, 5100, 360), (5150, 5250, 285)]
STARS = [(920, 312), (3280, 177), (5200, 247)]
CASH = [(450, GROUND_Y - 12), (1050, GROUND_Y - 12), (1650, GROUND_Y - 12), (2200, GROUND_Y - 12),
        (2950, 350), (3250, 200), (3700, GROUND_Y - 12), (4550, GROUND_Y - 12), (5050, GROUND_Y - 12),
        (5600, GROUND_Y - 12)]
GUARDS = [(600, 900), (1250, 1500, "s"), (2350, 2700, "s"), (3300, 3650, "s"), (4550, 4800, "s"), (5000, 5300, "s")]
CAMS = [(1100, 0.0), (2600, 1.7), (3900, 3.0), (4750, 4.4)]
CHECKPOINTS = [1550, 2800, 4000, 5350]
HINTS = [
    (0, 420, "CENTRAL CYBER VAULT  -  steal the QUANTUM MASTER DRIVE"),
    (900, 1250, "SHIELD guards:  frontal knife BOUNCES.  Attack from BEHIND"),
    (1250, 1500, "Blind with SMOKE (key 7)  or turn him with DECOY (key 5)"),
    (1500, 1950, "TRIPLE LASER GRID:  key 1 + /TKDIAMONDLASER  or  EMP (key 4)"),
    (2150, 2350, "Side safe:  key 8 VAULT THERMITE melts it  (cash!)"),
    (3850, 3950, "TERMINAL A:  key 3 LAPTOP  ->  POWER OFF for 20 seconds"),
    (4000, 4800, "Run to TERMINAL B before power returns!  Lasers/cams are OFF now"),
    (4850, 5000, "TERMINAL B:  LAPTOP  ->  open the BLAST DOOR  (power must be OFF)"),
    (5400, 6000, "Grab the QUANTUM DRIVE and escape through the EXTRACTION hatch"),
]
SPOT_LINES = ["Intruder detected!", "Halt! Drop the data!", "Cyber breach! Hands up!"]
CHAT_LINES = ["The vault is unbreachable.", "Shields up, stay sharp.", "Watch for rewired terminals.",
              "I have CCTV footage in this facility."]


class World5(HeistWorld):
    LEVEL_W = LEVEL_W
    LEDGES = LEDGES
    STARS = STARS
    CASH = CASH
    GUARDS = GUARDS
    CAMS = CAMS
    CHECKPOINTS = CHECKPOINTS
    HINTS = HINTS
    GOAL_X = GOAL
    TARGET = "QUANTUM MASTER DRIVE"
    REWARD = 1500
    BAIL = 500
    WIN_TITLE = "QUANTUM DRIVE STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES

    def __init__(self, save, save_fn):
        self.bg = Tiled(600, cyber_wall, seed=13)
        super().__init__(save, save_fn)

    def make_guard(self, spec):
        if len(spec) == 3:
            return ShieldGuard(spec[0], spec[1], self)
        return Guard2(spec[0], spec[1], self)

    def make_features(self):
        door = DoorFeature(5420, "blast", "BLAST DOOR")
        self.door = door
        return [TripleGrid(1700, 1960, 0.0), TripleGrid(4200, 4480, 1.7),
                SafeFeature(2200, 300),
                DualTerminal(3900, "A", door), DualTerminal(4950, "B", door),
                door,
                LootFeature(5750, "QUANTUM MASTER DRIVE", draw_drive)]

    def draw_background(self, surf, cam):
        self.bg.draw(surf, cam)
        t = self.t
        for hx in (700, 2050, 3500, 5600):
            sx = hx - cam
            if -100 < sx < WIDTH + 100:
                draw_hologram(surf, sx, t)
        ex = GOAL + 40 - cam
        if -150 < ex < WIDTH + 150:
            draw_hatch(surf, ex, t)
        draw_floor(surf, cam, (22, 34, 48), (8, 14, 22), (60, 210, 240), stripe=(30, 70, 90), tile=60)

    def draw_fx(self, surf, cam):
        if self.power_t > 0:
            a = 70
            dk = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dk.fill((0, 4, 10, a))
            surf.blit(dk, (0, 0))
            k = self.power_t / POWER_TIME
            r = pygame.Rect(0, 0, 300, 12)
            r.center = (WIDTH // 2, 190)
            pygame.draw.rect(surf, (30, 30, 20), r.inflate(4, 4), border_radius=6)
            pygame.draw.rect(surf, (255, 200, 80) if k > 0.3 else (255, 70, 70), (r.x, r.y, int(r.w * k), r.h), border_radius=5)
            img = self.f_small.render("GO TO TERMINAL B  -  power returns soon" if not self.door.opening else "BLAST DOOR OPEN",
                                      True, (255, 220, 120))
            surf.blit(img, img.get_rect(midbottom=(WIDTH // 2, r.y - 6)))


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((8, 16, 26))
        cache.setdefault("t", Tiled(600, cyber_wall, seed=13)).draw(s, off)
        draw_floor(s, off, (22, 34, 48), (8, 14, 22), (60, 210, 240))

    return H.run_heist(screen, clock, save, save_fn, World5, "CENTRAL CYBER VAULT",
                       ["Steal the QUANTUM MASTER DRIVE.",
                        "Triple lasers, dual terminals, riot-shield guards.",
                        "Terminal A cuts power - Terminal B opens the blast door."],
                       back, lambda s, c, t: draw_drive(s, c, t),
                       "Central Cyber Vault. Steal the quantum master drive.")
