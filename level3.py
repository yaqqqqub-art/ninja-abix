"""
level3.py - Chapter 1 / Level 3 : CASINO ROYALE HEIST.
main_game.py theke:  level3.run(screen, clock, save, save_fn)

Lokkho: VIP casino te dhuke Owner's Suite theke "GOLDEN CRYPTO BRIEFCASE" churi kore elevator diye palao.

Notun challenge:
  - METAL DETECTOR archway: knife niye hete gele ALARM.  EMP (key 4) chalu thakle off. Ba E chepe OVERRIDE CODE type koro
    (code ta PAGE e lekha; MASTER KEYCARD kaj kore na).
  - Patrol DRONE: niche spotlight deye.  Jump diye J (knife) = destroy,  EMP = shob band,  HACKER = off.
  - Armed BOUNCER: 2 ta knife hit ba ekta Super Punch (K) lage.
  - Casino mainframe (LAPTOP) VIP door khole,  Owner's Suite er door e VAULT THERMITE (2 sec).
Camera code: /CAMERA01099    Laser code: /TKDIAMONDLASER
"""
import math
import random
import pygame

import sound
import tools as TL
import puzzles as PZ
import sprites as SP
import level1 as L1
from level1 import Camera, Player, clamp, GROUND_Y, CEIL_Y
from level2 import Guard2
from animation import WIDTH, HEIGHT, GOLD, get_font
import heist as H
from heist import (HeistWorld, Feature, DoorFeature, PageFeature, TerminalFeature, SafeFeature, LootFeature,
                   SweepGridFeature, Tiled, draw_floor)

LEVEL_W = 6300
GOAL = 6120


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_briefcase(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 46, (255, 210, 90), 60, 4)
    r = pygame.Rect(0, 0, 54, 38)
    r.center = (x, y)
    SP.v_gradient(surf, r, (255, 218, 110), (190, 140, 40))
    pygame.draw.rect(surf, (110, 76, 20), r, 3, border_radius=4)
    pygame.draw.rect(surf, (110, 76, 20), (x - 10, y - 24, 20, 8), 3, border_radius=3)
    pygame.draw.rect(surf, (110, 76, 20), (x - 5, y - 4, 10, 8), border_radius=2)
    f = get_font(20).render("B", True, (110, 76, 20))
    surf.blit(f, f.get_rect(center=(x, y - 12)))


def casino_wall(s, rnd):
    SP.v_gradient(s, s.get_rect(), (40, 14, 54), (20, 8, 32))
    w, h = s.get_size()
    pygame.draw.rect(s, (16, 6, 24), (0, 0, w, 34))
    pygame.draw.rect(s, (255, 60, 150), (0, 34, w, 4))
    pygame.draw.rect(s, (70, 220, 255), (0, 40, w, 2))
    for i in range(5):                                         # neon tubes
        x = 40 + i * 100
        col = ((255, 60, 150), (70, 220, 255), (255, 210, 70))[i % 3]
        pygame.draw.line(s, col, (x, 80), (x + 40, 80), 4)
        pygame.draw.line(s, col, (x + 20, 80), (x + 20, 120), 4)
    # slot machines row
    for i in range(6):
        sx = 20 + i * 84
        r = pygame.Rect(sx, GROUND_Y - 160, 62, 160)
        SP.v_gradient(s, r, (130, 20, 50), (60, 8, 28))
        pygame.draw.rect(s, (255, 210, 70), r, 2)
        scr = pygame.Rect(sx + 8, GROUND_Y - 140, 46, 40)
        pygame.draw.rect(s, (10, 10, 24), scr)
        for k in range(3):
            pygame.draw.rect(s, (255, 255, 255), (scr.x + 3 + k * 14, scr.y + 6, 11, 28))
            pygame.draw.circle(s, rnd.choice(((230, 40, 50), (250, 200, 40), (60, 200, 90))),
                               (scr.x + 8 + k * 14, scr.y + 14 + rnd.randint(0, 12)), 4)
        pygame.draw.rect(s, (40, 6, 20), (sx + 8, GROUND_Y - 90, 46, 20))
        for k in range(4):
            pygame.draw.circle(s, rnd.choice(((255, 90, 120), (255, 220, 90), (90, 220, 255))), (sx + 14 + k * 11, GROUND_Y - 80), 3)
        pygame.draw.line(s, (200, 200, 210), (sx + 62, GROUND_Y - 120), (sx + 74, GROUND_Y - 150), 4)
        pygame.draw.circle(s, (230, 40, 50), (sx + 75, GROUND_Y - 152), 6)


CASINO_BG = None


def draw_roulette(surf, x, t):
    r = pygame.Rect(0, 0, 150, 52)
    r.midbottom = (x, GROUND_Y)
    SP.v_gradient(surf, r, (20, 110, 60), (10, 60, 34))
    pygame.draw.rect(surf, (90, 56, 24), r, 3, border_radius=6)
    pygame.draw.rect(surf, (90, 56, 24), (r.x + 8, r.bottom - 16, 12, 16))
    pygame.draw.rect(surf, (90, 56, 24), (r.right - 20, r.bottom - 16, 12, 16))
    c = (x - 34, r.y + 20)
    pygame.draw.ellipse(surf, (60, 30, 14), (c[0] - 34, c[1] - 12, 68, 24))
    for k in range(10):
        a = t * 3 + k * math.tau / 10
        col = (220, 40, 50) if k % 2 else (20, 20, 24)
        px, py = c[0] + math.cos(a) * 26, c[1] + math.sin(a) * 8
        pygame.draw.circle(surf, col, (int(px), int(py)), 4)
    pygame.draw.circle(surf, (255, 230, 120), (c[0], c[1]), 5)
    for k in range(4):
        pygame.draw.circle(surf, (240, 240, 250), (x + 10 + k * 14, r.y + 22), 6)
        pygame.draw.circle(surf, (200, 40, 60), (x + 10 + k * 14, r.y + 22), 3)


def draw_bar(surf, x, t):
    r = pygame.Rect(0, 0, 230, 78)
    r.midbottom = (x, GROUND_Y)
    SP.v_gradient(surf, r, (100, 54, 30), (50, 26, 16))
    pygame.draw.rect(surf, (210, 160, 80), (r.x - 6, r.y - 6, r.w + 12, 8), border_radius=3)
    for k in range(7):
        bx = r.x + 16 + k * 30
        pygame.draw.rect(surf, (60, 150, 80) if k % 2 else (230, 190, 70), (bx, r.y - 40, 12, 34), border_radius=3)
        pygame.draw.rect(surf, (230, 230, 240), (bx + 3, r.y - 52, 6, 14))
    SP.glow(surf, (x, r.y - 20), 110, (255, 190, 90), 24, 3)


def draw_elevator(surf, x, t, open_k):
    r = pygame.Rect(0, 0, 120, 250)
    r.midbottom = (x, GROUND_Y)
    pygame.draw.rect(surf, (30, 30, 40), r.inflate(16, 16), border_radius=4)
    pygame.draw.rect(surf, (210, 170, 80), r.inflate(16, 16), 3, border_radius=4)
    SP.v_gradient(surf, r, (150, 160, 180), (90, 98, 120))
    gap = int(r.w / 2 * open_k)
    pygame.draw.rect(surf, (20, 22, 30), (r.centerx - gap, r.y, gap * 2, r.h))
    pygame.draw.rect(surf, (60, 66, 84), (r.x, r.y, r.w // 2 - gap, r.h))
    pygame.draw.rect(surf, (60, 66, 84), (r.centerx + gap, r.y, r.w // 2 - gap, r.h))
    f = get_font(16).render("EXIT", True, (80, 255, 150))
    surf.blit(f, f.get_rect(center=(x, r.y - 22)))


# ------------------------------------------------------------------
# Hazards
# ------------------------------------------------------------------
class DetectorFeature(Feature):
    def __init__(self, x):
        self.x = x
        self.on = True
        self.tripped = False

    def interact(self, w):
        """E chaple OVERRIDE CODE keypad (keycard kaj kore na). Code ta PAGE e lekha."""
        if not self.on or abs(w.p.x - self.x) >= 110:
            return False
        if TL.TOOLS[w.tool]["id"] == "keycard":
            sound.play("lock")
            w.say("METAL DETECTOR  -  the KEYCARD does not work, type the CODE")
            return True
        w.open_pad(self, "METAL DETECTOR OVERRIDE", PZ.code_for("l3detector"))
        return True

    def modal_done(self, w, m):
        self.on = False
        sound.play("unlock")
        w.say("METAL DETECTOR OFF")

    def update(self, w, dt):
        p = w.p
        if not self.on or w.systems_off():
            return
        d = abs(p.x - self.x)
        if d < 20 and p.y > GROUND_Y - 150 and not self.tripped:
            self.tripped = True
            sound.play("beep")
            w.alarm(self.x, "METAL DETECTED!  ALARM!")
        elif d > 70:
            self.tripped = False

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if not (-80 < x < WIDTH + 80):
            return
        if self.on and abs(w.p.x - self.x) < 110:
            hf = get_font(14).render("[E]  ENTER OVERRIDE CODE", True, (255, 220, 100))
            surf.blit(hf, hf.get_rect(center=(x, GROUND_Y - 226)))
        live = self.on and not w.systems_off()
        col = ((255, 60, 60) if int(t * 4) % 2 else (130, 20, 20)) if (live and self.tripped) else \
              ((70, 255, 140) if live else (90, 90, 100))
        for px in (x - 34, x + 34):
            pygame.draw.rect(surf, (60, 62, 76), (px - 7, GROUND_Y - 190, 14, 190))
            pygame.draw.rect(surf, (110, 114, 134), (px - 7, GROUND_Y - 190, 4, 190))
        pygame.draw.rect(surf, (60, 62, 76), (x - 44, GROUND_Y - 204, 88, 18), border_radius=5)
        pygame.draw.circle(surf, col, (int(x), GROUND_Y - 195), 5)
        if live:
            gs = pygame.Surface((60, 186), pygame.SRCALPHA)
            gs.fill(col[:3] + (26 + int(14 * math.sin(t * 6)),))
            surf.blit(gs, (x - 30, GROUND_Y - 186))
        f = get_font(12).render("METAL DETECTOR" if live else "DETECTOR OFF", True, col)
        surf.blit(f, f.get_rect(midbottom=(x, GROUND_Y - 208)))


class Drone(Camera):
    RANGE, HALF = 300, math.radians(24)

    def __init__(self, x0, x1, y=255, speed=85, phase=0.0):
        super().__init__(x0, 0.0)
        self.x0, self.x1, self.speed, self.by = x0, x1, speed, y
        self.dir = 1
        self.x, self.y = (x0 + x1) / 2, y
        self.dead = False
        self.ph = phase
        self.rot = 0.0

    def angle(self, t):
        return 90

    def lens(self, t):
        return (self.x, self.y + 10)

    def sees(self, t, pt):
        if self.dead:
            return False
        return Camera.sees(self, t, pt)

    def tick(self, w, dt):
        self.rot += dt * 22
        if self.dead:
            self.y = min(GROUND_Y - 8, self.y + 260 * dt)
            return
        if self.hacked or w.systems_off():
            self.y += (self.by + 70 - self.y) * min(1, dt * 3)
            return
        self.x += self.dir * self.speed * dt
        if self.x > self.x1:
            self.x, self.dir = self.x1, -1
        elif self.x < self.x0:
            self.x, self.dir = self.x0, 1
        self.y = self.by + math.sin(w.t * 2 + self.ph) * 12

    def slash(self, w, reach):
        if self.dead:
            return False
        if reach is not None and not reach.inflate(10, 30).collidepoint(self.x, self.y):
            return False
        self.dead, self.hacked, self.danger = True, True, 0.0
        sound.play("zap")
        w.burst(self.x, self.y, (255, 200, 90), 22, 240, 0.8, grav=260)
        return True

    def draw(self, surf, cam, t):
        x = self.x - cam
        if x < -200 or x > WIDTH + 200:
            return
        live = not self.dead and not self.hacked
        if live:
            lx, ly = x, self.y + 10
            col = SP.lerp_color((255, 235, 140), (255, 50, 50), clamp(self.danger, 0, 1))
            half = self.HALF
            pts = [(lx, ly), (lx - math.sin(half) * self.RANGE, ly + math.cos(half) * self.RANGE),
                   (lx, ly + self.RANGE), (lx + math.sin(half) * self.RANGE, ly + math.cos(half) * self.RANGE)]
            cs = pygame.Surface((int(self.RANGE), int(self.RANGE) + 20), pygame.SRCALPHA)
            loc = [(a - (lx - self.RANGE / 2), b - ly) for a, b in pts]
            pygame.draw.polygon(cs, col + (34 + int(70 * self.danger),), loc)
            surf.blit(cs, (lx - self.RANGE / 2, ly))
        y = int(self.y)
        pygame.draw.ellipse(surf, (50, 54, 70), (x - 18, y - 8, 36, 18))
        pygame.draw.ellipse(surf, (120, 126, 150), (x - 18, y - 8, 36, 18), 2)
        eye = (255, 60, 60) if live else (60, 60, 70)
        pygame.draw.circle(surf, eye, (int(x), y + 2), 5)
        for sx in (-1, 1):
            pygame.draw.line(surf, (110, 114, 134), (x + sx * 16, y - 6), (x + sx * 28, y - 12), 3)
            ang = self.rot if live else 0.0
            pygame.draw.line(surf, (200, 204, 220), (x + sx * 28 - 9 * math.cos(ang), y - 12),
                             (x + sx * 28 + 9 * math.cos(ang), y - 12), 2)


class Bouncer(Guard2):
    HP = 2

    def reset(self):
        super().reset()
        self.hp = self.HP
        self.stun = 0.0
        self.hit_t = 0.0

    def stab(self, w, p):
        self.hp -= 1
        self.hit_t = 0.4
        sound.play("hit")
        w.burst(self.x, GROUND_Y - 40, (200, 30, 40), 10, 160, 0.6)
        if self.hp <= 0:
            self.die(w)
            w.floats.append({"x": self.x, "y": GROUND_Y - 100, "t": 1.0, "txt": "BOUNCER DOWN", "c": (255, 120, 120)})
        else:
            self.state, self.timer, self.excl = "aim", self.AIM, 0.8
            self.facing = 1 if p.x > self.x else -1
            self.alert = max(self.alert, 6.0)
            self.stun = 0.35
            self.say(w, "You'll pay for that!")
            w.floats.append({"x": self.x, "y": GROUND_Y - 100, "t": 0.8, "txt": "1 more hit!", "c": (255, 220, 120)})

    def punched(self, w):
        self.hp = 0
        self.die(w)
        w.floats.append({"x": self.x, "y": GROUND_Y - 100, "t": 1.0, "txt": "SUPER PUNCH!", "c": (255, 220, 120)})

    def update(self, dt, p, world):
        self.hit_t = max(0.0, self.hit_t - dt)
        super().update(dt, p, world)

    def draw(self, surf, cam, t):
        x = self.x - cam
        if x < -120 or x > WIDTH + 120:
            return
        super().draw(surf, cam, t)
        if not self.alive:
            return
        # bulky vest
        pygame.draw.rect(surf, (20, 20, 26), (x - 17, GROUND_Y - 62, 34, 26), border_radius=6)
        pygame.draw.rect(surf, (255, 190, 60), (x - 17, GROUND_Y - 62, 34, 26), 2, border_radius=6)
        if self.hit_t > 0:
            SP.glow(surf, (x, GROUND_Y - 46), 40, (255, 90, 90), 80, 3)
        for k in range(self.HP):
            col = (255, 80, 80) if k < self.hp else (60, 40, 40)
            pygame.draw.rect(surf, col, (x - 14 + k * 16, GROUND_Y - 80, 12, 5), border_radius=2)
        f = get_font(11).render("BOUNCER", True, (255, 200, 90))
        surf.blit(f, f.get_rect(midbottom=(x, GROUND_Y - 84)))


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(850, 990, 350),
          (2900, 3010, 365), (3060, 3170, 290), (3220, 3340, 215),
          (4350, 4450, 360), (4500, 4610, 285)]
STARS = [(920, 312), (3280, 177), (4560, 247)]
CASH = [(450, GROUND_Y - 12), (1020, GROUND_Y - 12), (1800, GROUND_Y - 12), (2500, GROUND_Y - 12),
        (2950, 350), (3250, 200), (3700, GROUND_Y - 12), (4400, GROUND_Y - 12), (4950, GROUND_Y - 12),
        (5350, GROUND_Y - 12)]
GUARDS = [(650, 950), (1650, 1900, "b"), (2400, 2750), (3500, 3800, "b"), (4300, 4600), (5100, 5400, "b")]
CAMS = [(1250, 0.0), (2900, 1.6), (4700, 3.0)]
CHECKPOINTS = [1550, 3050, 4650]
HINTS = [
    (0, 420, "CASINO ROYALE  -  steal the GOLDEN CRYPTO BRIEFCASE from the Owner's Suite"),
    (600, 860, "BOUNCERS are heavy:  2 x J (knife)  or  K (Super Punch)"),
    (950, 1150, "Collect the PAGE  -  it has the METAL DETECTOR override code"),
    (1150, 1400, "METAL DETECTOR ahead:  E + CODE from the page  or  EMP (key 4) - or alarm!"),
    (1600, 2400, "DRONES:  jump + J destroys them,  EMP kills them,  or HACK them"),
    (2200, 2400, "Side safe:  key 8 VAULT THERMITE melts it  (cash!)"),
    (3800, 4300, "Laser hallway:  key 1 + /TKDIAMONDLASER  or  time it"),
    (4750, 4950, "Key 3 LAPTOP at the mainframe unlocks the VIP door"),
    (5430, 5560, "Owner's Suite:  key 8 VAULT THERMITE (2 sec)"),
    (5600, 6000, "Grab the BRIEFCASE then run to the ELEVATOR"),
]
SPOT_LINES = ["Freeze! Drop the chips!", "Hey! You're not a VIP!", "Thief! Security!"]
CHAT_LINES = ["The house always wins.", "VIP lounge is off limits.", "Watch the drones tonight.",
              "I have CCTV footage in this casino."]


class World3(HeistWorld):
    LEVEL_W = LEVEL_W
    SPAWN_X = 200
    LEDGES = LEDGES
    STARS = STARS
    CASH = CASH
    GUARDS = GUARDS
    CAMS = CAMS
    CHECKPOINTS = CHECKPOINTS
    HINTS = HINTS
    GOAL_X = GOAL
    TARGET = "GOLDEN CRYPTO BRIEFCASE"
    REWARD = 1000
    BAIL = 500
    WIN_TITLE = "CRYPTO BRIEFCASE STOLEN!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES

    def __init__(self, save, save_fn):
        self.bg = Tiled(520, casino_wall, seed=5)
        super().__init__(save, save_fn)

    def make_guard(self, spec):
        if len(spec) == 3:
            return Bouncer(spec[0], spec[1], self)
        return Guard2(spec[0], spec[1], self)

    def make_cams(self):
        return [Drone(1700, 2300, phase=0.0), Drone(3000, 3500, phase=1.3),
                Drone(4750, 5050, phase=2.2), Drone(5450, 5950, phase=3.1)]

    def make_features(self):
        vip = DoorFeature(5000, "terminal", "VIP LOUNGE")
        return [PageFeature(1150, "l3detector", "DETECTOR OVERRIDE CODE"),
                DetectorFeature(1400), DetectorFeature(3300), DetectorFeature(5250),
                SafeFeature(2250, 300),
                SweepGridFeature([(3950, 4090, 0.0)]),
                vip,
                TerminalFeature(4850, ["sudo casino --lockdown off", "unlock vip_lounge --door 5"],
                                "LAPTOP  -  CASINO MAINFRAME", lambda w: vip.open(w)),
                DoorFeature(5560, "thermite", "OWNER'S SUITE"),
                LootFeature(5780, "GOLDEN CRYPTO BRIEFCASE", draw_briefcase)]

    def extra_update(self, dt):
        for c in self.cams:
            if hasattr(c, "tick"):
                c.tick(self, dt)

    def draw_background(self, surf, cam):
        self.bg.draw(surf, cam)
        t = self.t
        for rx in (780, 1900, 2650, 3550, 4100, 5700):
            sx = rx - cam
            if -200 < sx < WIDTH + 200:
                draw_roulette(surf, sx, t)
        sx = 3700 - cam
        if -300 < sx < WIDTH + 300:
            draw_bar(surf, sx, t)
        ex = GOAL + 40 - cam
        if -200 < ex < WIDTH + 200:
            draw_elevator(surf, ex, t, 1.0 if self.loot else 0.0)
        # red velvet carpet
        draw_floor(surf, cam, (120, 18, 40), (60, 8, 24), (230, 190, 90), stripe=(150, 30, 56))

    def draw_fx(self, surf, cam):
        sh = pygame.Surface((WIDTH, 120), pygame.SRCALPHA)
        for i in range(6):
            col = ((255, 60, 150), (70, 220, 255), (255, 210, 70))[i % 3]
            cx = (i * 180 + t_off(self.t)) % (WIDTH + 200) - 100
            pygame.draw.circle(sh, col + (14,), (int(cx), 20), 90)
        surf.blit(sh, (0, CEIL_Y))


def t_off(t):
    return t * 18


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    def back(s, off):
        s.fill((30, 10, 44))
        w = BACK_CACHE.setdefault("c", Tiled(520, casino_wall, seed=5))
        w.draw(s, off)
        draw_floor(s, off, (120, 18, 40), (60, 8, 24), (230, 190, 90))

    def icon(s, c, t):
        draw_briefcase(s, c, t)

    return H.run_heist(screen, clock, save, save_fn, World3, "CASINO ROYALE HEIST",
                       ["Steal the GOLDEN CRYPTO BRIEFCASE from the Owner's Suite.",
                        "Metal detectors, patrol drones, armed bouncers.",
                        "Use EMP, CODES and THERMITE wisely."],
                       back, icon, "Casino Royale. Steal the golden crypto briefcase.")


BACK_CACHE = {}
