"""
level6.py - Chapter 1 / Level 6 : SHADOW DOCKS (HARBOR CARGO).
main_game.py theke:  level6.run(screen, clock, save, save_fn)

Lokkho: borsha-raat er shipyard e sealed container theke "CONTRABAND PLUTONIUM CORE" churi kore SPEEDBOAT e palao.

Notun challenge:
  - PANI (water pit):  porle shonge shonge MORON.  Crane er chalonto platform e uthe par ho.
  - SEALED CONTAINER:  VAULT THERMITE (key 8) 2 sec channel diye gola.
  - SNIPER (lal laser):  charge hoy, tarpor high-damage shot.  Dourate thako (laser dot pichone pore),
    HIDE (H) / SMOKE (key 7) / EMP (key 4) e bachte paro.  Thame thakle lagbe!
Camera code: /CAMERA01099
"""
import math
import random
import pygame

import sound
import voice
import sprites as SP
import level1 as L1
from level1 import Camera, clamp, GROUND_Y, CEIL_Y
from level2 import Guard2
from animation import WIDTH, HEIGHT, get_font
import heist as H
from heist import (HeistWorld, Feature, DoorFeature, LootFeature, Tiled, Mover, draw_floor, TerminalFeature)

LEVEL_W = 6700
GOAL = 6580
SEGS = [(0, 1500), (1800, 2900), (3200, 4300), (4650, 5700), (6000, 6700)]
PITS = [(1500, 1800), (2900, 3200), (4300, 4650), (5700, 6000)]


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_core(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 52, (120, 255, 90), 90, 4)
    pygame.draw.circle(surf, (30, 70, 30), (x, y), 20)
    pygame.draw.circle(surf, (130, 255, 90), (x, y), 14)
    for k in range(3):
        a = t * 2 + k * math.tau / 3
        pygame.draw.polygon(surf, (20, 40, 20), [(x, y), (x + math.cos(a - 0.4) * 14, y + math.sin(a - 0.4) * 14),
                                                 (x + math.cos(a + 0.4) * 14, y + math.sin(a + 0.4) * 14)])
    pygame.draw.circle(surf, (255, 255, 120), (x, y), 4)


def dock_back(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (10, 16, 30), (22, 34, 54))
    # cloud smudges
    for _ in range(6):
        pygame.draw.ellipse(s, (22, 28, 44), (rnd.randint(0, w), rnd.randint(40, 160), rnd.randint(120, 260), 34))
    # cargo cranes silhouette
    cx = 140
    pygame.draw.rect(s, (14, 18, 28), (cx, 100, 14, GROUND_Y - 100))
    pygame.draw.rect(s, (14, 18, 28), (cx + 170, 100, 14, GROUND_Y - 100))
    pygame.draw.rect(s, (14, 18, 28), (cx - 40, 92, 330, 16))
    pygame.draw.line(s, (14, 18, 28), (cx + 7, 100), (cx + 220, 150), 3)
    # container stacks (back)
    cols = ((120, 50, 40), (40, 80, 120), (50, 110, 70), (150, 110, 40), (90, 60, 110))
    for i in range(5):
        bx = 30 + i * 118
        for lv in range(rnd.randint(1, 3)):
            r = pygame.Rect(bx, GROUND_Y - 44 * (lv + 1) - 20, 108, 42)
            base = rnd.choice(cols)
            dark = tuple(int(c * 0.42) for c in base)
            pygame.draw.rect(s, dark, r)
            for k in range(1, 9):
                pygame.draw.line(s, tuple(int(c * 0.3) for c in base), (r.x + k * 12, r.y + 2), (r.x + k * 12, r.bottom - 2), 2)
            pygame.draw.rect(s, tuple(int(c * 0.6) for c in base), r, 2)
    pygame.draw.rect(s, (20, 24, 32), (0, GROUND_Y - 20, w, 20))


def draw_speedboat(surf, x, t):
    y = GROUND_Y + 24 + math.sin(t * 2) * 3
    pygame.draw.polygon(surf, (230, 232, 240), [(x - 110, y - 22), (x + 100, y - 22), (x + 70, y + 20), (x - 90, y + 20)])
    pygame.draw.polygon(surf, (30, 70, 140), [(x - 110, y - 22), (x + 100, y - 22), (x + 96, y - 10), (x - 106, y - 10)])
    pygame.draw.rect(surf, (60, 80, 110), (x - 30, y - 50, 56, 30), border_radius=6)
    pygame.draw.rect(surf, (150, 210, 240), (x - 24, y - 45, 44, 16), border_radius=4)
    f = get_font(16).render("SPEEDBOAT", True, (80, 255, 150))
    surf.blit(f, f.get_rect(center=(x, y - 76)))


def draw_container_room(surf, cam):
    x0, x1 = 6150 - cam, 6400 - cam
    if x1 < -20 or x0 > WIDTH + 20:
        return
    r = pygame.Rect(int(x0), GROUND_Y - 170, int(x1 - x0), 170)
    pygame.draw.rect(surf, (6, 10, 8), r)
    SP.glow(surf, (r.centerx + 40, GROUND_Y - 62), 90, (120, 255, 90), 24, 3)
    pygame.draw.rect(surf, (150, 60, 40), (r.x, r.y - 22, r.w, 22))
    for k in range(1, 12):
        pygame.draw.line(surf, (90, 36, 26), (r.x + k * 22, r.y - 20), (r.x + k * 22, r.y - 2), 2)
    pygame.draw.rect(surf, (220, 90, 60), (r.x, r.y - 22, r.w, 22), 3)
    f = get_font(14).render("SEALED  -  CONTAINER 7  -  DANGER", True, (255, 220, 120))
    surf.blit(f, f.get_rect(center=(r.centerx, r.y - 40)))
    pygame.draw.rect(surf, (150, 60, 40), (r.right, r.y - 22, 8, 192))


# ------------------------------------------------------------------
# Sniper
# ------------------------------------------------------------------
class Sniper(Camera):
    """Camera subclass: world.cams e thake (rec feed er jonno lagbe na) - ekhane shudhu mechanic."""
    RANGE_X = 760
    CHARGE = 1.7
    COOL = 2.6

    def __init__(self, x, y=150):
        super().__init__(x, 0.0)
        self.x, self.y = x, y
        self.state = "idle"
        self.t = 0.0
        self.dot = None
        self.flash = 0.0
        self.hacked = False

    # camera bits unused
    def sees(self, t, pt):
        return False

    def draw(self, surf, cam, t):
        x = self.x - cam
        if x < -200 or x > WIDTH + 200:
            return
        # perch
        pygame.draw.rect(surf, (30, 34, 44), (x - 40, self.y + 24, 80, 10))
        pygame.draw.line(surf, (30, 34, 44), (x - 30, self.y + 34), (x - 30, GROUND_Y), 4)
        pygame.draw.line(surf, (30, 34, 44), (x + 30, self.y + 34), (x + 30, GROUND_Y), 4)
        SP.draw_guard(surf, x, self.y + 24, 1 if (self.dot is None or self.dot > self.x) else -1, t,
                      "aim" if self.state == "charge" else "idle", 1.0 if self.state == "charge" else 0.0, s=0.5)
        if self.flash > 0:
            SP.glow(surf, (x, self.y), 40, (255, 240, 160), 120, 3)
        if self.hacked:
            f = get_font(12).render("OFFLINE", True, (120, 140, 160))
            surf.blit(f, f.get_rect(midbottom=(x, self.y - 34)))

    def tick(self, w, dt):
        p = w.p
        self.flash = max(0.0, self.flash - dt)
        off = w.systems_off() or self.hacked
        vis = (p.alive and not p.hidden and not w.smoke_hides(p) and abs(p.x - self.x) < self.RANGE_X)
        if off or not vis:
            if self.state == "charge":
                self.state, self.t, self.dot = "idle", 0.0, None
            elif self.state == "cool":
                self.t -= dt
                if self.t <= 0:
                    self.state = "idle"
            return
        tx = p.x
        if self.state == "idle":
            self.state, self.t, self.dot = "charge", self.CHARGE, tx
            sound.play("beep")
            voice.say("Sniper!") if random.random() < 0.3 else None
        elif self.state == "charge":
            self.dot += (tx - self.dot) * min(1.0, 3.6 * dt)
            self.t -= dt
            if self.t <= 0:
                self.state, self.t = "cool", self.COOL
                self.flash = 0.15
                sound.play("gunshot")
                w.shake = max(w.shake, 0.25)
                w.burst(self.dot, GROUND_Y - 24, (255, 220, 140), 10, 200, 0.4)
                if abs(self.dot - p.x) < 34 and p.inv <= 0 and p.alive and w.state == "play":
                    p.health -= 1
                    w.hurt_player(1 if p.x > self.x else -1, "sniper")
                    w.floats.append({"x": p.x, "y": p.y - 90, "t": 1.0, "txt": "SNIPED!", "c": (255, 90, 90)})
                else:
                    w.floats.append({"x": self.dot, "y": GROUND_Y - 60, "t": 0.8, "txt": "MISSED", "c": (200, 220, 255)})
                self.dot = None
        elif self.state == "cool":
            self.t -= dt
            if self.t <= 0:
                self.state = "idle"

    def draw_beam(self, surf, cam, p):
        if self.state != "charge" or self.dot is None:
            return
        k = 1 - self.t / self.CHARGE
        sx, sy = self.x - cam, self.y + 6
        ex, ey = self.dot - cam, p.y - 30
        col = (255, int(60 * (1 - k)) + 20, 30)
        pygame.draw.line(surf, col, (sx, sy), (ex, ey), 1 + int(2 * k))
        pygame.draw.circle(surf, col, (int(ex), int(ey)), 6 + int(6 * (1 - k)), 2)
        pygame.draw.circle(surf, (255, 255, 255), (int(ex), int(ey)), 2)
        if int(self.t * 10) % 2 == 0:
            f = get_font(26).render("!", True, (255, 70, 70))
            surf.blit(f, f.get_rect(center=(sx, sy - 40)))


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(850, 990, 350),
          (2100, 2210, 365), (2260, 2370, 290), (2420, 2530, 215),
          (5000, 5110, 360), (5160, 5270, 285)]
STARS = [(920, 312), (2480, 177), (5220, 247)]
CASH = [(450, GROUND_Y - 12), (1000, GROUND_Y - 12), (1250, GROUND_Y - 12), (2050, GROUND_Y - 12),
        (2300, 350), (2700, GROUND_Y - 12), (3500, GROUND_Y - 12), (4000, GROUND_Y - 12),
        (4900, GROUND_Y - 12), (5500, GROUND_Y - 12), (6050, GROUND_Y - 12)]
GUARDS = [(550, 950), (1950, 2300), (3350, 3700), (3800, 4200), (4800, 5150), (5300, 5600)]
CAMS = [(1000, 0.0), (2700, 1.7), (3900, 3.0), (5400, 4.4)]
CHECKPOINTS = [1350, 2750, 4100, 5550, 6050]
HINTS = [
    (0, 420, "SHADOW DOCKS  -  steal the PLUTONIUM CORE from the sealed container"),
    (1250, 1500, "WATER = instant death.  Ride the CRANE PLATFORM across"),
    (800, 1250, "SNIPER:  red laser charges, then BANG.  Keep MOVING or hide (H)"),
    (2900, 3200, "Another crane platform  (it goes up and down)"),
    (3200, 3500, "SMOKE (key 7) / EMP (key 4) blinds snipers"),
    (4100, 4300, "Wide gap ahead - time the platform"),
    (5100, 5500, "RED WIRE BOX:  key 0 WIRE CUTTER - cut the RED main wire LAST  (snipers off 12 s)"),
    (5700, 6000, "Last crane platform... then the container"),
    (6000, 6150, "SEALED CONTAINER:  key 8 VAULT THERMITE (2 sec)"),
    (6400, 6560, "Take the CORE and run to the SPEEDBOAT!"),
]
SPOT_LINES = ["Intruder on the docks!", "Halt! Dockyard security!", "Thief! Stop right there!"]
CHAT_LINES = ["Contraband stays sealed.", "Rain never stops here...", "Watch the water, mate.",
              "I have CCTV footage on this dock."]


class World6(HeistWorld):
    LEVEL_W = LEVEL_W
    LEDGES = LEDGES
    STARS = STARS
    CASH = CASH
    GUARDS = GUARDS
    CAMS = CAMS
    CHECKPOINTS = CHECKPOINTS
    HINTS = HINTS
    GOAL_X = GOAL
    TARGET = "PLUTONIUM CORE"
    REWARD = 2000
    BAIL = 500
    WIN_TITLE = "PLUTONIUM CORE STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES
    GROUND_SEGS = SEGS

    def __init__(self, save, save_fn):
        self.bg = Tiled(600, dock_back, seed=21, parallax=0.5)
        self.rain = [(random.random() * WIDTH, random.random() * HEIGHT, random.uniform(0.7, 1.4)) for _ in range(110)]
        super().__init__(save, save_fn)

    def make_cams(self):
        return [Sniper(1250, 150), Sniper(3050, 140), Sniper(4500, 150), Sniper(5850, 140), Sniper(6300, 160)]

    def after_restart(self):
        self.movers = [Mover(1650, GROUND_Y, 110, "x", 70, 0.9, 0.0),
                       Mover(3050, 405, 110, "y", 38, 1.0, 0.0),
                       Mover(4475, GROUND_Y, 120, "x", 100, 0.8, 1.0),
                       Mover(5850, 405, 110, "y", 38, 1.1, 2.0)]

    def make_features(self):
        def dock_power(w):
            w.emp_t = max(w.emp_t, 12.0)
            w.say("DOCK POWER CUT  -  snipers and cameras are DEAD for 12 s")
        return [TerminalFeature(5350, ["sudo dock --power cut", "crane.lights --off"],
                                "LAPTOP  -  DOCK POWER BOX", dock_power),
                DoorFeature(6150, "thermite", "CONTAINER 7"),
                LootFeature(6290, "PLUTONIUM CORE", draw_core)]

    def extra_update(self, dt):
        for c in self.cams:
            if hasattr(c, "tick"):
                c.tick(self, dt)
        p = self.p
        if p.alive and p.y > GROUND_Y + 30 and not p.on_ground:
            self.burst(p.x, GROUND_Y + 10, (150, 200, 255), 24, 260, 0.9, grav=500)
            sound.play("pop")
            self.kill("drowned")
            self.say("SPLASH!  Water = instant death")
        for i, (rx, ry, sp) in enumerate(self.rain):
            ry += 620 * sp * dt
            rx -= 90 * sp * dt
            if ry > HEIGHT:
                ry, rx = -10, random.random() * (WIDTH + 100)
            self.rain[i] = (rx % WIDTH, ry, sp)

    def draw_background(self, surf, cam):
        self.bg.draw(surf, cam)
        t = self.t
        # water
        wr = pygame.Rect(0, GROUND_Y - 6, WIDTH, HEIGHT - GROUND_Y + 6)
        SP.v_gradient(surf, wr, (16, 44, 78), (4, 14, 30))
        for k in range(0, WIDTH, 36):
            yy = GROUND_Y + 4 + 10 * ((k // 36) % 4) + math.sin(t * 2 + k * 0.05 + cam * 0.01) * 3
            pygame.draw.line(surf, (60, 110, 160), (k, yy), (k + 22, yy), 2)
        # patrol boat decor
        bx = (t * 40) % (WIDTH + 400) - 200
        pygame.draw.polygon(surf, (40, 46, 60), [(bx - 60, GROUND_Y + 40), (bx + 60, GROUND_Y + 40), (bx + 44, GROUND_Y + 62), (bx - 50, GROUND_Y + 62)])
        pygame.draw.rect(surf, (60, 70, 90), (bx - 14, GROUND_Y + 22, 28, 18))
        SP.glow(surf, (bx + 30, GROUND_Y + 28), 70, (255, 240, 170), 36, 3)
        # dock planks
        for a, b in SEGS:
            x0, x1 = a - cam, b - cam
            if x1 < -10 or x0 > WIDTH + 10:
                continue
            r = pygame.Rect(int(x0), GROUND_Y, int(x1 - x0), HEIGHT - GROUND_Y)
            SP.v_gradient(surf, r, (74, 64, 56), (34, 30, 28))
            pygame.draw.line(surf, (150, 130, 100), (r.x, GROUND_Y), (r.right, GROUND_Y), 3)
            for k in range(int(r.x - (r.x % 60)), r.right + 60, 60):
                pygame.draw.line(surf, (46, 40, 36), (k, GROUND_Y + 3), (k, HEIGHT), 2)
            pygame.draw.rect(surf, (28, 26, 28), (r.x, GROUND_Y + 40, 12, HEIGHT))
            pygame.draw.rect(surf, (28, 26, 28), (r.right - 12, GROUND_Y + 40, 12, HEIGHT))
        draw_container_room(surf, cam)
        bx = GOAL + 60 - cam
        if -200 < bx < WIDTH + 200:
            draw_speedboat(surf, bx, t)

    def draw_fx(self, surf, cam):
        for c in self.cams:
            if hasattr(c, "draw_beam"):
                c.draw_beam(surf, cam, self.p)
        tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        tint.fill((4, 10, 30, 70))
        surf.blit(tint, (0, 0))
        for rx, ry, sp in self.rain:
            pygame.draw.line(surf, (150, 180, 220), (rx, ry), (rx + 5 * sp, ry + 14 * sp), 1)
        danger = any(getattr(c, "state", "") == "charge" for c in self.cams)
        if danger and self.state == "play":
            a = int(60 + 40 * math.sin(self.t * 16))
            edge = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(edge, (255, 30, 30, a), edge.get_rect(), 10)
            surf.blit(edge, (0, 0))
            img = self.f_small.render("SNIPER LOCKING ON  -  KEEP MOVING!", True, (255, 90, 90))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 150)))


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((10, 16, 30))
        cache.setdefault("t", Tiled(600, dock_back, seed=21, parallax=0.5)).draw(s, off * 0.5)
        pygame.draw.rect(s, (20, 40, 70), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))

    return H.run_heist(screen, clock, save, save_fn, World6, "SHADOW DOCKS",
                       ["Steal the CONTRABAND PLUTONIUM CORE.",
                        "Rain, water pits, crane platforms, snipers.",
                        "Melt the container with VAULT THERMITE."],
                       back, lambda s, c, t: draw_core(s, c, t),
                       "Shadow Docks. Steal the plutonium core and escape by speedboat.")
