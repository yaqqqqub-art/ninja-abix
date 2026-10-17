"""
level7.py - Chapter 1 / Level 7 : PENTHOUSE ART HEIST.
main_game.py theke:  level7.run(screen, clock, save, save_fn)

Lokkho: top-floor penthouse theke "MONA LISA 2.0" (holographic art) churi kore sky-terrace er zipline diye palao.

Notun challenge:
  - BALCONY WIND:  jhor er gust tomake pichone thele dey.  H (hide) chaple tike thaka jay.  Gust off hole lafao.
  - MULTI-BEAM LASER:  upor-nich + bam-dan beam.  LASER BREAKER (/TKDIAMONDLASER) ba EMP.
  - ARMORED CASE:  LASER BREAKER (silent) - Super Punch (K) mara mane building-wide PANIC SIREN.
  - LUXURY SAFE (key 8 THERMITE)  +450 Tk.
  - SKY-TERRACE LATCH:  Super Punch (K) diye bhango, tarpor zipline.
Camera code: /CAMERA01099    Laser code: /TKDIAMONDLASER
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
from animation import WIDTH, HEIGHT, get_font
import heist as H
from heist import (HeistWorld, Feature, SafeFeature, LootFeature, CaseFeature, Tiled, draw_floor)
from level5 import TripleGrid

LEVEL_W = 6500
GOAL = 6420
SEGS = [(0, 2900), (3100, 4600), (4800, 6600)]
GAPS = [(2900, 3100), (4600, 4800)]


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_mona(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 56, (255, 190, 120), 70, 4)
    r = pygame.Rect(0, 0, 56, 74)
    r.center = (x, y)
    pygame.draw.rect(surf, (170, 120, 40), r.inflate(10, 10), border_radius=4)
    SP.v_gradient(surf, r, (90, 150, 130), (40, 60, 60))
    pygame.draw.ellipse(surf, (240, 205, 160), (x - 11, y - 22, 22, 28))          # face
    pygame.draw.arc(surf, (60, 40, 30), (x - 15, y - 26, 30, 32), 0.2, 2.9, 5)    # hair
    pygame.draw.polygon(surf, (40, 36, 30), [(x - 22, y + 36), (x - 12, y + 6), (x + 12, y + 6), (x + 22, y + 36)])
    pygame.draw.line(surf, (120, 50, 40), (x - 4, y - 4), (x + 4, y - 4), 2)
    for k in range(0, 74, 6):                                                      # hologram scanlines
        a = 60 + int(40 * math.sin(t * 5 + k))
        ls = pygame.Surface((56, 2), pygame.SRCALPHA)
        ls.fill((120, 255, 220, a))
        surf.blit(ls, (r.x, r.y + k))


def penthouse_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (14, 8, 34), (40, 14, 66))
    # night sky + neon moon
    pygame.draw.circle(s, (255, 90, 200), (w - 150, 100), 46)
    pygame.draw.circle(s, (14, 8, 34), (w - 128, 90), 42)
    pygame.draw.circle(s, (255, 120, 220), (w - 150, 100), 46, 3)
    for _ in range(40):
        pygame.draw.circle(s, (200, 200, 255), (rnd.randint(0, w), rnd.randint(40, 180)), 1)
    # skyline
    x = 0
    while x < w:
        bw, bh = rnd.randint(40, 90), rnd.randint(80, 230)
        pygame.draw.rect(s, (18, 10, 36), (x, GROUND_Y - bh, bw, bh))
        for wy in range(GROUND_Y - bh + 8, GROUND_Y - 6, 14):
            for wx in range(x + 6, x + bw - 6, 12):
                if rnd.random() < 0.35:
                    pygame.draw.rect(s, rnd.choice(((255, 220, 120), (120, 220, 255), (255, 120, 200))), (wx, wy, 5, 7))
        x += bw + rnd.randint(0, 12)
    # glass wall mullions
    for gx in range(0, w, 160):
        pygame.draw.rect(s, (60, 56, 84), (gx, 38, 6, GROUND_Y - 38))
    pygame.draw.rect(s, (24, 16, 40), (0, 0, w, 36))
    pygame.draw.rect(s, (255, 190, 90), (0, 36, w, 3))


def draw_chandelier(surf, x, t):
    pygame.draw.line(surf, (160, 140, 100), (x, CEIL_Y), (x, CEIL_Y + 30), 2)
    for k in range(-3, 4):
        yy = CEIL_Y + 34 + abs(k) * 6
        pygame.draw.circle(surf, (255, 235, 170), (int(x + k * 12), yy), 4)
        pygame.draw.line(surf, (200, 180, 120), (x, CEIL_Y + 30), (x + k * 12, yy), 1)
    SP.glow(surf, (x, CEIL_Y + 46), 70, (255, 220, 140), 26, 3)


def draw_zipline(surf, x0, x1, t):
    pygame.draw.line(surf, (200, 205, 220), (x0, GROUND_Y - 160), (x1, GROUND_Y - 40), 3)
    pygame.draw.rect(surf, (60, 64, 80), (x0 - 10, GROUND_Y - 190, 20, 50), border_radius=3)
    pygame.draw.rect(surf, (60, 64, 80), (x1 - 8, GROUND_Y - 80, 16, 40), border_radius=3)
    f = get_font(16).render("ZIPLINE", True, (80, 255, 150))
    surf.blit(f, f.get_rect(center=(x0 + 40, GROUND_Y - 210)))


# ------------------------------------------------------------------
# Features
# ------------------------------------------------------------------
class WindZone(Feature):
    """Gust on/off (periodic).  Gust on hole player ke pichone thele; hidden thakle kichu hoy na."""

    def __init__(self, x0, x1, phase=0.0):
        self.x0, self.x1, self.ph = x0, x1, phase

    def gust(self, w):
        return math.sin(w.t * 1.1 + self.ph) > 0.1

    def update(self, w, dt):
        p = w.p
        if not w.p.alive or p.hidden or not self.gust(w) or not (self.x0 <= p.x <= self.x1):
            return
        p.x = clamp(p.x - 205 * dt, 16, w.level_w - 16)
        for g in range(0):
            pass

    def draw(self, w, surf, cam, t):
        a, b = self.x0 - cam, self.x1 - cam
        if b < -20 or a > WIDTH + 20:
            return
        on = self.gust(w)
        f = get_font(15).render("WIND  -  gust ON  (hide with H!)" if on else "wind calm  -  GO!", True,
                                (255, 120, 120) if on else (120, 255, 190))
        surf.blit(f, f.get_rect(center=((max(a, 0) + min(b, WIDTH)) / 2, 110)))
        if not on:
            return
        rnd = random.Random(int(t * 12))
        for _ in range(26):
            yy = rnd.randint(150, GROUND_Y - 10)
            xx = rnd.uniform(max(a, 0), min(b, WIDTH))
            xx = (xx - t * 700) % max(1, (b - a)) + a
            ln = rnd.randint(40, 110)
            pygame.draw.line(surf, (200, 225, 255), (xx, yy), (xx + ln, yy), 2)


class CrossGrid(TripleGrid):
    """Interlocking beams: 2 ta horizontal (upor-nich) + 1 ta vertical (bam-dan)."""

    def c_seg(self, w):
        y = 330 + 200 * math.sin(w.t * 1.2 + self.ph + math.pi)
        return ((self.x0, y), (self.x1, y))

    def hit(self, w):
        p = w.p
        pr = p.rect()
        if not (self.x0 - 10 <= p.x <= self.x1 + 10):
            return False
        if pr.colliderect(pygame.Rect(self.x0, int(self.a_y(w)) - 5, self.x1 - self.x0, 10)):
            return True
        if pr.colliderect(pygame.Rect(self.x0, int(self.c_seg(w)[0][1]) - 5, self.x1 - self.x0, 10)):
            return True
        return pr.colliderect(pygame.Rect(int(self.b_x(w)) - 5, CEIL_Y, 10, GROUND_Y - CEIL_Y))

    def draw(self, w, surf, cam, t):
        a, b = self.x0 - cam, self.x1 - cam
        if b < -60 or a > WIDTH + 60:
            return
        for px in (a, b):
            pygame.draw.rect(surf, (50, 40, 70), (px - 8, CEIL_Y, 16, GROUND_Y - CEIL_Y))
            pygame.draw.rect(surf, (140, 110, 190), (px - 8, CEIL_Y, 4, GROUND_Y - CEIL_Y))
        if not self.on or w.systems_off():
            if w.emp_t > 0:
                for _ in range(4):
                    sx = random.uniform(a, b)
                    pygame.draw.line(surf, (160, 220, 255), (sx, CEIL_Y + 40), (sx + random.randint(-12, 12), CEIL_Y + 70), 2)
            return
        c1, c2 = (255, 70, 110), (90, 170, 255)
        for y in (min(self.a_y(w), GROUND_Y - 6), min(self.c_seg(w)[0][1], GROUND_Y - 6)):
            SP.glow(surf, ((a + b) / 2, y), (b - a) * 0.5, c1, 34, 3)
            pygame.draw.line(surf, c1, (a, y), (b, y), 5)
            pygame.draw.line(surf, (255, 255, 255), (a, y), (b, y), 1)
        bx = self.b_x(w) - cam
        pygame.draw.line(surf, c2, (bx, CEIL_Y), (bx, GROUND_Y), 5)
        pygame.draw.line(surf, (255, 255, 255), (bx, CEIL_Y), (bx, GROUND_Y), 1)


class ArmoredCase(CaseFeature):
    """Punch = building-wide PANIC SIREN.  Laser breaker = silent."""

    def on_punch(self, w):
        if not self.open and abs(w.p.x - self.x) < 110:
            self.open = True
            sound.play("hit")
            w.burst(self.x, GROUND_Y - 90, (180, 230, 255), 34, 300, 0.9, grav=500)
            w.siren(self.x)

    def draw(self, w, surf, cam, t):
        super().draw(w, surf, cam, t)
        x = self.x - cam
        if not self.open and -120 < x < WIDTH + 120:
            f = get_font(12).render("ARMORED", True, (255, 210, 120))
            surf.blit(f, f.get_rect(midbottom=(x, GROUND_Y - 176)))


class LatchFeature(Feature):
    def __init__(self, x):
        self.x = x
        self.broken = False

    def solids(self, w):
        return [] if self.broken else [pygame.Rect(self.x - 12, CEIL_Y, 24, GROUND_Y - CEIL_Y)]

    def on_punch(self, w):
        if not self.broken and abs(w.p.x - self.x) < 130:
            self.broken = True
            sound.play("hit")
            sound.play("unlock")
            w.burst(self.x, GROUND_Y - 80, (255, 220, 140), 36, 320, 0.9, grav=400)
            w.say("LATCH BROKEN  -  run to the zipline!")

    def prompt(self, w, tid, payload):
        return None

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if not (-80 < x < WIDTH + 80):
            return
        if not self.broken:
            r = pygame.Rect(x - 14, CEIL_Y, 28, GROUND_Y - CEIL_Y)
            SP.v_gradient(surf, r, (110, 110, 130), (60, 60, 80))
            pygame.draw.rect(surf, (30, 30, 40), r, 3)
            pygame.draw.rect(surf, (230, 180, 60), (x - 20, GROUND_Y - 110, 40, 22), border_radius=4)
            pygame.draw.circle(surf, (40, 30, 10), (int(x), GROUND_Y - 99), 5)
            f = get_font(13).render("SKY-TERRACE LATCH", True, (255, 200, 120))
            surf.blit(f, f.get_rect(midbottom=(x, GROUND_Y - 118)))
            f = get_font(13).render("Super Punch  [K]", True, (255, 150, 120))
            surf.blit(f, f.get_rect(midbottom=(x, GROUND_Y - 134)))
        else:
            pygame.draw.line(surf, (110, 110, 130), (x - 14, CEIL_Y), (x - 40, CEIL_Y + 60), 6)
            pygame.draw.line(surf, (110, 110, 130), (x - 40, CEIL_Y + 60), (x - 44, GROUND_Y), 3)


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(850, 990, 350), (1700, 1800, 365), (1850, 1960, 290),
          (3800, 3910, 365), (3960, 4070, 290), (4120, 4230, 215),
          (2945, 3055, GROUND_Y), (4645, 4755, GROUND_Y)]
STARS = [(920, 312), (1905, 252), (4180, 177)]
CASH = [(450, GROUND_Y - 12), (1050, GROUND_Y - 12), (1760, 350), (2150, GROUND_Y - 12),
        (2600, GROUND_Y - 12), (3350, GROUND_Y - 12), (4000, GROUND_Y - 12), (4400, GROUND_Y - 12),
        (5000, GROUND_Y - 12), (5400, GROUND_Y - 12)]
GUARDS = [(600, 950), (1950, 2300), (3300, 3650), (3800, 4300), (5150, 5500)]
DOGS = [(1100, 1350), (4000, 4400)]
CAMS = [(1000, 0.0), (2450, 1.7), (3500, 3.0), (5400, 4.4)]
CHECKPOINTS = [1500, 2700, 4400, 5000]
HINTS = [
    (0, 420, "PENTHOUSE ART HEIST  -  steal MONA LISA 2.0, escape by ZIPLINE"),
    (1200, 1700, "Interlocking lasers:  key 1 + /TKDIAMONDLASER  or  EMP (key 4)"),
    (2100, 2350, "Wall safe:  key 8 VAULT THERMITE  =  +450 Tk"),
    (2400, 2900, "BALCONY WIND:  wait for calm, then jump.  H = hold still"),
    (4150, 4600, "Another windy balcony  -  time your jumps over the gap"),
    (5100, 5500, "Laser gallery  -  keep your cool"),
    (5600, 5780, "ARMORED CASE:  key 1 + /TKDIAMONDLASER = silent.   K = PANIC SIREN!"),
    (5800, 6150, "Break the SKY-TERRACE LATCH with K (Super Punch)"),
    (6150, 6400, "Zipline!  Run!"),
]
SPOT_LINES = ["Intruder in the penthouse!", "Stop right there, thief!", "Security! Hands up!"]
CHAT_LINES = ["The Mona Lisa 2.0 is priceless.", "Wind's strong on the balcony.", "Watch the lasers tonight.",
              "I have CCTV footage in this penthouse."]


class World7(HeistWorld):
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
    TARGET = "MONA LISA 2.0"
    REWARD = 1800
    BAIL = 600
    WIN_TITLE = "MONA LISA 2.0 STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES
    GROUND_SEGS = SEGS

    def __init__(self, save, save_fn):
        self.bg = Tiled(640, penthouse_wall, seed=31, parallax=0.6)
        super().__init__(save, save_fn)

    def after_restart(self):
        self.siren_t = 0.0

    def make_features(self):
        case = ArmoredCase(5700, "", lambda *a: None)
        self.case = case
        return [WindZone(2500, 3500, 0.0), WindZone(4350, 5050, 1.8),
                CrossGrid(1350, 1650, 0.0), CrossGrid(5150, 5450, 1.5),
                SafeFeature(2250, 450),
                case,
                LootFeature(5700, "MONA LISA 2.0", draw_mona, requires=lambda w: case.open, y=GROUND_Y - 78),
                LatchFeature(6150)]

    def siren(self, x):
        sound.play("siren")
        sound.play("alarm")
        self.siren_t = 14.0
        self.add_noise(x, "glass")
        for g in self.guards:
            if g.alive:
                g.alert = max(g.alert, 14.0)
        for d in self.dogs:
            if d.alive:
                d.alert = max(d.alert, 14.0)
        self.say("PANIC SIREN!  Whole building is alerted")
        voice.say("Panic siren. Intruder in the building!")

    def extra_update(self, dt):
        if self.siren_t > 0:
            self.siren_t -= dt
            for g in self.guards:
                if g.alive:
                    g.alert = max(g.alert, 1.0)

    def draw_background(self, surf, cam):
        self.bg.draw(surf, cam)
        t = self.t
        for cx in (400, 1500, 2300, 3700, 4000, 5300, 5800):
            sx = cx - cam
            if -80 < sx < WIDTH + 80:
                draw_chandelier(surf, sx, t)
        zx = GOAL - 160 - cam
        if -200 < zx < WIDTH + 200:
            draw_zipline(surf, zx, zx + 420, t)
        # gaps: open sky
        for a, b in GAPS:
            x0, x1 = a - cam, b - cam
            if x1 < -10 or x0 > WIDTH + 10:
                continue
            r = pygame.Rect(int(x0), GROUND_Y, int(x1 - x0), HEIGHT - GROUND_Y)
            SP.v_gradient(surf, r, (30, 14, 56), (6, 4, 18))
        for a, b in SEGS:
            x0, x1 = a - cam, b - cam
            if x1 < -10 or x0 > WIDTH + 10:
                continue
            r = pygame.Rect(int(x0), GROUND_Y, int(x1 - x0), HEIGHT - GROUND_Y)
            SP.v_gradient(surf, r, (40, 22, 60), (14, 8, 26))
            pygame.draw.line(surf, (255, 190, 90), (r.x, GROUND_Y), (r.right, GROUND_Y), 3)
            for k in range(int(r.x - (r.x % 80)), r.right + 80, 80):
                pygame.draw.line(surf, (60, 36, 86), (k, GROUND_Y + 3), (k - 20, HEIGHT), 1)

    def draw_fx(self, surf, cam):
        if self.siren_t > 0:
            a = int(70 * (0.5 + 0.5 * math.sin(self.t * 10)))
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((255, 20, 40, a))
            surf.blit(ov, (0, 0))
            img = self.f_small.render(f"PANIC SIREN  {self.siren_t:.0f}s", True, (255, 120, 120))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 150)))


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((14, 8, 34))
        cache.setdefault("t", Tiled(640, penthouse_wall, seed=31, parallax=0.6)).draw(s, off)
        draw_floor(s, off, (40, 22, 60), (14, 8, 26), (255, 190, 90))

    return H.run_heist(screen, clock, save, save_fn, World7, "PENTHOUSE ART HEIST",
                       ["Steal MONA LISA 2.0 from the armored case.",
                        "Balcony wind, interlocking lasers, panic siren.",
                        "Break the sky-terrace latch and ride the zipline."],
                       back, lambda s, c, t: draw_mona(s, c, t),
                       "Penthouse art heist. Steal Mona Lisa two point oh.")
