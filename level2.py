"""
level2.py - Chapter 1 / Level 2 : JEWELRY MALL HEIST.
main_game.py theke call hoy:  level2.run(screen, clock, save, save_fn)

Lokkho: raater jewelry mall e dhuke "RUBY CROWN" churi kore Rooftop Exit diye paliye jao.

Notun challenge:
  - Moving laser grid: laser upor-nich othanama kore (niche gele lage, upore gele niche diye hete jao).
  - K9 dog: gondho shunke, HIDE korleo ghew ghew kore, kamray. Smoke Bomb lagbe.
  - Guard ra dead body ba sound (decoy, kach bhanga, kukur er dak) dekhe/shune khujte ashe.
  - Kach (showcase) jore bhangle ALARM. Laser Breaker (/TKDIAMONDLASER) diye nissobde kato,
    ba Laptop diye glass sensor off kore tarpor bhango.
  - Camera hack code: /CAMERA01099 ,   Laser code: /TKDIAMONDLASER
  - Arrest e jamin 500 Tk, na thakle 5 din jail.

Tools (key 1-9, ba Ctrl+Alt / TAB wheel) - E diye use:
  1 LASER BREAKER   2 HACKER   3 LAPTOP   4 EMP DISRUPTOR   5 DECOY DRONE
  6 REWIRER PRO     7 SMOKE BOMB   8 VAULT THERMITE   9 MASTER KEYCARD
"""
import math
import random
import sys
import pygame

import sound
import voice
import tools as TL
import puzzles as PZ
import controls as CT
import sprites as SP
import abix_fx as FX
import level1 as L1
from level1 import Guard, Camera, Player, World, clamp, GROUND_Y, CEIL_Y, START_HEALTH
from animation import WIDTH, HEIGHT, WHITE, RED, GOLD, get_font, fade_overlay

# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEVEL_W = 6200
SPAWN_X = 200
ROOF_X = 5440                                        # er por theke rooftop (khola akash)
EXIT_X = 5960
BAIL = 500
CROWN_X = 4700
CASE_W = 72
TERMINAL_X = 4500
GLASS_DOOR_X = 4150
METAL_DOOR_X = 5400
SAFE_X = 2330
CROWN_REWARD = 800
SAFE_CASH = 300

LEDGES = [(850, 990, 350),
          (1700, 1800, 365), (1850, 1960, 290),
          (3000, 3110, 360), (3160, 3270, 285), (3320, 3440, 215)]
STAR_POS = [(920, 312), (1905, 252), (3380, 177)]
CASH = [(450, GROUND_Y - 12), (1020, GROUND_Y - 12), (1760, 350), (2180, GROUND_Y - 12),
        (2700, GROUND_Y - 12), (3220, 270), (3600, GROUND_Y - 12), (4350, GROUND_Y - 12),
        (4950, GROUND_Y - 12), (5200, GROUND_Y - 12)]
CASH_VALUE = 100
GUARDS = [(600, 900), (1450, 1700), (2400, 2800), (3700, 4000), (4850, 5100)]
DOGS = [(1100, 1350), (3500, 3850), (5150, 5350)]
CAMERAS = [(1300, 0.0), (2200, 1.9), (3900, 3.2), (5000, 4.6)]
GRIDS = [(2000, 2140, 0.0), (2500, 2640, 1.7), (4300, 4440, 3.1)]      # moving laser grid (x0, x1, phase)
CHECKPOINTS = [1500, 2950, 4300]
LASER_MID, LASER_AMP, LASER_SPEED = 330, 200, 1.15
EMP_TIME, EMP_CD = 5.0, 16.0
DECOY_TIME, DECOY_CD = 6.0, 10.0
SMOKE_TIME, SMOKE_CD, SMOKE_R = 3.5, 10.0, 170
MELT_TIME = 2.0

HINTS = [
    (0, 420, "JEWELRY MALL  -  steal the RUBY CROWN, escape from the rooftop"),
    (600, 860, "Guards ar K9 DOGS!  Dog smells you even when HIDDEN"),
    (860, 1060, "Cash + STARS on the counters.  J = knife"),
    (1100, 1420, "CCTV:  key 2 HACKER, E, type /CAMERA01099"),
    (1900, 2400, "MOVING LASERS:  key 1, E, type /TKDIAMONDLASER  (or time your run)"),
    (2330, 2480, "Side safe:  key 8 VAULT THERMITE melts it  (cash!)"),
    (2480, 2800, "Key 6 REWIRER PRO: guards that touch the laser DIE"),
    (3560, 4000, "Key 7 SMOKE BOMB blinds guards and hides your smell"),
    (3450, 3700, "Collect the PAGE  -  it has the GLASS DOOR code"),
    (4020, 4200, "Glass door:  press E and type the CODE from the page  (keycard does NOT work)"),
    (4440, 4640, "Key 3 LAPTOP at the terminal turns the glass sensor OFF"),
    (4640, 4900, "Break the case: punch K = LOUD ALARM, or LASER BREAKER = silent"),
    (5300, 5480, "Reinforced door:  key 8 VAULT THERMITE (2 sec)"),
    (5480, 5900, "Run to the HELICOPTER on the rooftop!"),
]
SPOT_LINES = ["Freeze! Drop the jewels!", "Hey! Stop right there!", "Thief! Hands up!"]
CHAT_LINES = ["Search the jewelry counters!", "The Ruby Crown stays safe tonight.", "K9 unit, stay alert.",
              "I have CCTV footage in this mall."]


# ------------------------------------------------------------------
# Background
# ------------------------------------------------------------------
class Backdrop2:
    TILE = 520

    def __init__(self):
        rnd = random.Random(5)
        w = pygame.Surface((self.TILE, GROUND_Y))
        SP.v_gradient(w, w.get_rect(), (46, 30, 62), (24, 18, 40))
        pygame.draw.rect(w, (20, 14, 30), (0, 0, self.TILE, 34))
        pygame.draw.rect(w, (200, 160, 80), (0, 34, self.TILE, 4))
        pygame.draw.rect(w, (18, 12, 28), (0, 0, 7, GROUND_Y))
        # dokan er window (alo jholmol)
        win = pygame.Rect(70, 96, 380, 230)
        inner = pygame.Surface(win.size)
        SP.v_gradient(inner, inner.get_rect(), (110, 76, 52), (62, 40, 34))
        for k in range(3):                                                   # shelf
            y = 66 + k * 66
            pygame.draw.rect(inner, (180, 140, 80), (0, y, win.w, 5))
            for j in range(9):
                gx = 22 + j * 40 + rnd.randint(-4, 4)
                col = rnd.choice([(230, 60, 90), (90, 200, 255), (255, 220, 90), (120, 255, 170), (240, 240, 255)])
                pygame.draw.polygon(inner, col, [(gx, y - 18), (gx + 9, y - 8), (gx, y), (gx - 9, y - 8)])
                pygame.draw.polygon(inner, (255, 255, 255), [(gx, y - 18), (gx + 9, y - 8), (gx + 1, y - 10)])
        w.blit(inner, win.topleft)
        gl = pygame.Surface(win.size, pygame.SRCALPHA)
        pygame.draw.polygon(gl, (255, 255, 255, 22), [(0, 0), (150, 0), (60, win.h), (0, win.h)])
        w.blit(gl, win.topleft)
        pygame.draw.rect(w, (210, 170, 80), win.inflate(14, 14), 7, border_radius=6)
        pygame.draw.line(w, (210, 170, 80), (win.centerx, win.y), (win.centerx, win.bottom), 5)
        sign = pygame.Rect(0, 0, 150, 30)
        sign.midbottom = (win.centerx, win.y - 14)
        pygame.draw.rect(w, (30, 14, 40), sign, border_radius=6)
        pygame.draw.rect(w, (255, 90, 200), sign, 2, border_radius=6)
        f = get_font(18)
        img = f.render(rnd.choice(["GEMS", "GOLD", "DIAMONDS", "ROYAL"]), True, (255, 130, 220))
        w.blit(img, img.get_rect(center=sign.center))
        pygame.draw.rect(w, (40, 26, 44), (0, 340, self.TILE, GROUND_Y - 340))
        pygame.draw.rect(w, (200, 160, 80), (0, 340, self.TILE, 4))
        self.wall = w
        self.glow = pygame.Surface((340, 180), pygame.SRCALPHA)
        for i in range(6):
            pygame.draw.ellipse(self.glow, (255, 200, 150, 10), self.glow.get_rect().inflate(-i * 46, -i * 24))

    def draw(self, surf, cam):
        off = -int(cam * 0.6) % self.TILE
        x = off - self.TILE
        while x < WIDTH:
            surf.blit(self.wall, (x, 0))
            surf.blit(self.glow, (x + self.TILE // 2 - 170, 24))
            x += self.TILE


def draw_floor2(surf, cam):
    r = pygame.Rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y)
    SP.v_gradient(surf, r, (38, 30, 52), (16, 12, 26))
    tile = 80
    base = int(cam) // tile
    for i in range(0, WIDTH // tile + 3):
        wx = base + i
        sx = wx * tile - int(cam)
        for row in range(2):
            if (wx + row) % 2 == 0:
                s = pygame.Surface((tile, 48), pygame.SRCALPHA)
                s.fill((230, 200, 140, 26))
                surf.blit(s, (sx, GROUND_Y + 8 + row * 48))
    pygame.draw.rect(surf, (40, 26, 20), (0, GROUND_Y - 4, WIDTH, 12))
    pygame.draw.rect(surf, (214, 170, 70), (0, GROUND_Y - 4, WIDTH, 2))
    g = pygame.Surface((WIDTH, 24), pygame.SRCALPHA)
    pygame.draw.rect(g, (255, 255, 255, 22), (0, 0, WIDTH, 24))
    surf.blit(g, (0, GROUND_Y + 8))


def draw_escalator(surf, x, cam, t):
    """Shudhu sajano (chole thaka escalator)."""
    x0, y0, x1, y1 = x - cam, GROUND_Y, x - cam + 280, 190
    if x1 < -20 or x0 > WIDTH + 20:
        return
    pygame.draw.polygon(surf, (30, 30, 42), [(x0, y0), (x1, y1), (x1, y1 + 36), (x0 + 30, y0)])
    n = 14
    for i in range(n):
        k = ((i + t * 1.4) % n) / n
        sx, sy = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
        pygame.draw.line(surf, (150, 156, 176), (sx, sy), (sx + 14, sy), 3)
    pygame.draw.line(surf, (200, 170, 80), (x0, y0 - 50), (x1, y1 - 50), 4)
    pygame.draw.line(surf, (110, 90, 50), (x0, y0 - 46), (x1, y1 - 46), 2)
    for k in range(0, 6):
        px = x0 + (x1 - x0) * k / 5
        py = y0 + (y1 - y0) * k / 5
        pygame.draw.line(surf, (80, 84, 100), (px, py), (px, py - 50), 3)


def draw_chandelier(surf, x, t):
    pygame.draw.line(surf, (200, 170, 80), (x, 38), (x, 78), 3)
    pygame.draw.ellipse(surf, (210, 170, 80), (x - 36, 76, 72, 14))
    for k in range(-3, 4):
        cx = x + k * 11
        cy = 94 + abs(k) * 3 + int(math.sin(t * 3 + k) * 1)
        pygame.draw.line(surf, (220, 225, 245), (cx, 88), (cx, cy + 8), 1)
        pygame.draw.polygon(surf, (230, 238, 255), [(cx, cy), (cx + 4, cy + 8), (cx, cy + 14), (cx - 4, cy + 8)])
    SP.glow(surf, (x, 96), 60, (255, 225, 170), 40, 4)
    if int(t * 2 + x) % 5 == 0:
        pygame.draw.line(surf, WHITE, (x - 5, 100), (x + 5, 110), 1)
        pygame.draw.line(surf, WHITE, (x + 5, 100), (x - 5, 110), 1)


def draw_counter(surf, x, cam, t):
    """Kach er jewelry counter (shudhu sajano)."""
    sx = x - cam
    if sx < -260 or sx > WIDTH + 40:
        return
    r = pygame.Rect(sx, GROUND_Y - 58, 180, 58)
    SP.v_gradient(surf, r, (80, 56, 40), (44, 30, 24))
    pygame.draw.rect(surf, (210, 170, 80), r, 2)
    gl = pygame.Rect(sx + 4, GROUND_Y - 100, 172, 44)
    gs = pygame.Surface(gl.size, pygame.SRCALPHA)
    gs.fill((150, 200, 240, 40))
    surf.blit(gs, gl.topleft)
    pygame.draw.rect(surf, (180, 215, 245), gl, 2)
    for j in range(6):
        gx = sx + 18 + j * 28
        col = [(230, 60, 90), (90, 200, 255), (255, 220, 90), (120, 255, 170)][j % 4]
        pygame.draw.polygon(surf, col, [(gx, GROUND_Y - 84), (gx + 7, GROUND_Y - 76), (gx, GROUND_Y - 66), (gx - 7, GROUND_Y - 76)])
        if int(t * 3 + j + x) % 4 == 0:
            pygame.draw.line(surf, WHITE, (gx - 6, GROUND_Y - 88), (gx + 6, GROUND_Y - 78), 1)
            pygame.draw.line(surf, WHITE, (gx + 6, GROUND_Y - 88), (gx - 6, GROUND_Y - 78), 1)


def draw_ruby_crown(surf, c, t, size=1.0):
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 40 * size, (255, 60, 80), 60, 4)
    w = 38 * size
    base = [(x - w / 2, y + 12 * size), (x + w / 2, y + 12 * size), (x + w / 2, y - 2 * size), (x + w / 4, y - 14 * size),
            (x, y - 2 * size), (x - w / 4, y - 14 * size), (x - w / 2, y - 2 * size)]
    pygame.draw.polygon(surf, (230, 180, 60), base)
    pygame.draw.polygon(surf, (255, 235, 150), base, 2)
    for dx, dy in ((-w / 4, -14), (w / 4, -14), (0, -2)):
        pygame.draw.circle(surf, (235, 40, 70), (int(x + dx), int(y + dy * size)), max(3, int(5 * size)))
        pygame.draw.circle(surf, (255, 170, 190), (int(x + dx - 1), int(y + dy * size - 1)), max(1, int(2 * size)))
    pygame.draw.rect(surf, (240, 50, 80), (int(x - 5 * size), int(y + 2 * size), int(10 * size), int(7 * size)), border_radius=2)


def draw_helicopter(surf, x, y, t):
    pygame.draw.ellipse(surf, (40, 46, 60), (x - 70, y - 50, 140, 54))
    pygame.draw.ellipse(surf, (90, 100, 124), (x - 70, y - 50, 140, 54), 3)
    pygame.draw.polygon(surf, (110, 190, 240), [(x + 30, y - 44), (x + 66, y - 28), (x + 58, y - 8), (x + 24, y - 8)])
    pygame.draw.polygon(surf, (40, 46, 60), [(x - 66, y - 34), (x - 150, y - 44), (x - 150, y - 34), (x - 66, y - 18)])
    pygame.draw.line(surf, (150, 156, 170), (x - 50, y + 12), (x + 50, y + 12), 4)
    pygame.draw.line(surf, (150, 156, 170), (x - 30, y + 2), (x - 34, y + 12), 3)
    pygame.draw.line(surf, (150, 156, 170), (x + 30, y + 2), (x + 34, y + 12), 3)
    pygame.draw.line(surf, (60, 64, 80), (x, y - 52), (x, y - 62), 5)
    span = 150 + math.sin(t * 40) * 12
    pygame.draw.line(surf, (200, 204, 220), (x - span, y - 64), (x + span, y - 64), 4)
    pygame.draw.circle(surf, (255, 60, 60), (x - 146, y - 40), 4)


def draw_safe(surf, x, cam, state, t):
    sx = x - cam
    if sx < -80 or sx > WIDTH + 80:
        return
    r = pygame.Rect(0, 0, 70, 90)
    r.midbottom = (sx, GROUND_Y)
    if state == "melted":
        pygame.draw.rect(surf, (36, 30, 28), r, border_radius=4)
        pygame.draw.rect(surf, (120, 60, 30), r, 3, border_radius=4)
        pygame.draw.ellipse(surf, (255, 130, 40), (r.x + 8, r.y + 22, 54, 36))
        SP.glow(surf, r.center, 50, (255, 130, 40), 40, 3)
        return
    v = pygame.Rect(r)
    SP.v_gradient(surf, v, (110, 114, 128), (60, 62, 74))
    pygame.draw.rect(surf, (28, 30, 38), r, 3, border_radius=4)
    pygame.draw.circle(surf, (50, 54, 66), (r.centerx, r.centery), 22)
    pygame.draw.circle(surf, (190, 196, 212), (r.centerx, r.centery), 22, 3)
    for k in range(4):
        a = math.radians(k * 90 + 20)
        pygame.draw.line(surf, (220, 225, 240), r.center, (r.centerx + math.cos(a) * 18, r.centery + math.sin(a) * 18), 3)
    pygame.draw.circle(surf, GOLD, r.center, 4)
    f = get_font(13)
    img = f.render("SAFE", True, (240, 200, 80))
    surf.blit(img, img.get_rect(midbottom=(r.centerx, r.y - 2)))


# ------------------------------------------------------------------
# K9 dog
# ------------------------------------------------------------------
class Dog:
    HW, HH = 56, 34
    SMELL, PATROL, CHASE = 240, 70, 215

    def __init__(self, x0, x1):
        self.x0, self.x1 = x0, x1
        self.reset()

    def reset(self):
        self.x = (self.x0 + self.x1) / 2
        self.facing = 1
        self.alive = True
        self.dead_t = 0.0
        self.found = False
        self.anim_t = random.uniform(0, 5)
        self.calm()

    def calm(self):
        self.state = "patrol"
        self.pause = self.alert = self.bite_cd = self.bark_t = self.lost = self.look_t = 0.0
        self.target = None
        self.bubble_t = 0.0

    def rect(self):
        return pygame.Rect(int(self.x - self.HW / 2), GROUND_Y - self.HH, self.HW, self.HH)

    def die(self, world):
        if not self.alive:
            return
        self.alive = False
        self.dead_t = 0.0
        sound.play("stab")
        world.burst(self.x, GROUND_Y - 20, (200, 30, 40), 12, 170, 0.6)

    def update(self, dt, p, world):
        self.anim_t += dt
        if not self.alive:
            self.dead_t += dt
            return
        self.alert = max(0.0, self.alert - dt)
        self.bite_cd = max(0.0, self.bite_cd - dt)
        self.bark_t = max(0.0, self.bark_t - dt)
        self.bubble_t = max(0.0, self.bubble_t - dt)
        dx = p.x - self.x
        smells = (p.alive and abs(dx) < self.SMELL and abs(p.y - GROUND_Y) < 130 and not world.smoke_hides(p))
        if self.alert > 0 and p.alive and not world.smoke_hides(p):
            smells = smells or abs(dx) < 520
        n = world.noise_for(self, 700)
        if self.state == "patrol" and n and not smells:
            self.state, self.target, self.look_t = "inv", n["x"], 3.0
        if smells:
            if self.state != "chase":
                self.state = "chase"
                self.bark_t = 0.6
                self.bubble_t = 1.0
                sound.play("alert", 0.8)
                world.add_noise(self.x, "bark")
            self.lost = 0.0
        if self.state == "patrol":
            if self.pause > 0:
                self.pause -= dt
            else:
                self.x += self.facing * self.PATROL * dt
                if self.x <= self.x0:
                    self.x, self.facing, self.pause = self.x0, 1, 0.6
                elif self.x >= self.x1:
                    self.x, self.facing, self.pause = self.x1, -1, 0.6
        elif self.state == "inv":
            d = self.target - self.x
            if abs(d) > 10:
                self.facing = 1 if d > 0 else -1
                self.x += self.facing * self.CHASE * 0.8 * dt
            else:
                self.look_t -= dt
            if self.look_t <= 0 or abs(d) <= 10 and self.look_t < 1.5:
                self.state, self.pause = "patrol", 0.5
        elif self.state == "chase":
            self.lost += dt * (4 if world.smoke_hides(p) else 1)
            if self.lost > 2.0 or not p.alive:
                self.state, self.pause = "patrol", 0.4
            else:
                self.facing = 1 if dx > 0 else -1
                if abs(dx) > 28:
                    self.x = clamp(self.x + self.facing * self.CHASE * dt, self.x0 - 160, self.x1 + 160)
                if abs(dx) < 40 and abs(p.y - GROUND_Y) < 70 and self.bite_cd <= 0 and p.alive and not world.smoke_hides(p):
                    self.bite_cd = 1.1
                    sound.play("hit")
                    world.hurt_player(self.facing, "dog")

    def draw(self, surf, cam, t):
        x = self.x - cam
        if x < -100 or x > WIDTH + 100:
            return
        if not self.alive:
            SP.draw_dog(surf, x, GROUND_Y, self.facing, t, "dead", alpha=int(clamp(255 - (self.dead_t - 1.4) * 180, 0, 255)))
            return
        anim = "idle" if (self.state == "patrol" and self.pause > 0) else "run"
        if self.bark_t > 0:
            anim = "bark"
        SP.draw_dog(surf, x, GROUND_Y, self.facing, self.anim_t, anim)
        if self.bubble_t > 0:
            img = get_font(20).render("WOOF! WOOF!", True, (255, 90, 90))
            surf.blit(img, img.get_rect(midbottom=(x, GROUND_Y - 52)))


# ------------------------------------------------------------------
# Guard (L2) : body / noise dekhe khujte ashe, smoke e ondho
# ------------------------------------------------------------------
class Guard2(Guard):
    def __init__(self, x0, x1, world):
        self.world = world
        super().__init__(x0, x1)

    def calm(self):
        super().calm()
        self.heard = 0
        self.inv_x = None
        self.inv_t = 0.0

    def sees(self, p):
        if self.world.smoke_hides(p):
            return False
        return super().sees(p)

    def update(self, dt, p, world):
        if not self.alive:
            super().update(dt, p, world)
            return
        if self.state == "inv":
            self.anim_t += dt
            self.alert = max(0.0, self.alert - dt)
            self.bubble_t = max(0.0, self.bubble_t - dt)
            if self.sees(p):
                self.state, self.timer, self.excl = "aim", self.AIM, 0.8
                self.facing = 1 if p.x > self.x else -1
                sound.play("alert", 0.7)
                self.say(world, random.choice(SPOT_LINES))
                return
            d = self.inv_x - self.x
            if abs(d) > 12:
                self.facing = 1 if d > 0 else -1
                self.x += self.facing * 115 * dt
            else:
                self.inv_t -= dt
            if self.inv_t <= 0:
                self.state, self.pause = "patrol", 0.8
            return
        if self.state == "patrol":
            # dead body dekhle
            for o in list(world.guards) + list(world.dogs):
                if o is not self and not o.alive and not o.found and abs(o.x - self.x) < 340 \
                        and (o.x - self.x) * self.facing > 0 and not world.smoke_hides_at(self.x):
                    o.found = True
                    self.go_investigate(world, o.x, "Man down! Search the jewelry counters!")
                    world.add_noise(o.x, "body")
                    return
            n = world.noise_for(self, 900)
            if n and n["id"] > self.heard:
                self.heard = n["id"]
                txt = {"decoy": "What was that noise?!", "glass": "Glass breaking! Intruder!",
                       "bark": "K9 spotted movement!", "body": "Search the jewelry counters!"}.get(n["kind"], "Who's there?")
                self.go_investigate(world, n["x"], txt)
                if n["kind"] in ("glass",):
                    self.alert = 8.0
                return
        super().update(dt, p, world)

    def go_investigate(self, world, x, text):
        self.state, self.inv_x, self.inv_t = "inv", x, 2.2
        self.facing = 1 if x > self.x else -1
        self.excl = 0.8
        self.say(world, text)


# ------------------------------------------------------------------
# World
# ------------------------------------------------------------------
class World2(World):
    def __init__(self, save, save_fn):
        self.back2 = Backdrop2()
        super().__init__(save, save_fn)

    def preset_loot(self):
        self.crown = True               # mukut ager bar nise - ar nei

    def apply_progress(self):
        super().apply_progress()
        if "safe" in self.bonus_prior:
            self.safe_open = True       # safe ager bar gola hoyechilo, khali

    def restart(self):
        super().restart()
        self.pages = {}
        self.page_spots = [PZ.PageSpot(3560, "jewel_glass", "GLASS DOOR CODE", GROUND_Y - 48)]
        self.level_w = LEVEL_W
        self.ledges = LEDGES
        self.hints = HINTS
        self.bail = BAIL
        self.win_title = "RUBY CROWN STOLEN!"
        self.p = Player(SPAWN_X)
        self.cam = clamp(self.p.x - WIDTH * 0.38, 0, LEVEL_W - WIDTH)
        self.guards = [Guard2(a, b, self) for a, b in GUARDS]
        for g in self.guards:
            g.spot_lines, g.chat_lines = SPOT_LINES, CHAT_LINES
        self.dogs = [Dog(a, b) for a, b in DOGS]
        self.cams = [Camera(x, ph) for x, ph in CAMERAS]
        self.got = [False] * len(STAR_POS)
        self.cash_taken = [False] * len(CASH)
        self.cp_on = [False] * len(CHECKPOINTS)
        self.grid_state = ["on"] * len(GRIDS)          # on | broken | rewired
        self.case_open = False
        self.sensor_on = True
        self.crown = False
        self.glass_open = False
        self.metal_open = 0.0
        self.metal_melt = False
        self.safe_open = False
        self.term_open = False
        self.emp_t = 0.0
        self.cd = {"emp": 0.0, "decoy": 0.0, "smoke": 0.0}
        self.decoy = None
        self.smoke = None
        self.melt = None                                # thermite channel
        self.noises, self.noise_id = [], 0
        self.warned_exit = False
        self.won_loot = 0
        self.tool = 0
        self.wheel_sel = 0
        self.vault_open = 0.0

    def respawn(self):
        p = Player(CHECKPOINTS[self.cp_idx] if self.cp_idx >= 0 else SPAWN_X)
        p.inv = 1.5
        self.p = p
        for g in self.guards:
            if g.alive:
                g.calm()
                g.x = clamp(g.x, g.x0, g.x1)
        for d in self.dogs:
            if d.alive:
                d.calm()
                d.x = clamp(d.x, d.x0, d.x1)
        for c in self.cams:
            c.danger, c.beeped = 0.0, False
        self.bullets.clear()
        self.waves.clear()
        self.noises.clear()
        self.melt = None
        self.hack = None
        self.modal = None
        self.state, self.state_t = "play", 0.0
        self.cam = clamp(p.x - WIDTH * 0.38, 0, LEVEL_W - WIDTH)

    # ---------------- noise / smoke ----------------
    def add_noise(self, x, kind):
        self.noise_id += 1
        self.noises.append({"x": x, "kind": kind, "t": 1.5, "id": self.noise_id})

    def noise_for(self, who, rng):
        best = None
        for n in self.noises:
            if abs(n["x"] - who.x) < rng and who is not None:
                if best is None or n["id"] > best["id"]:
                    best = n
        if best is not None and isinstance(who, Dog):
            if best["kind"] == "bark" or abs(best["x"] - who.x) < 3:
                return None
        return best

    def smoke_hides(self, p):
        return bool(self.smoke) and abs(p.x - self.smoke["x"]) < SMOKE_R

    def smoke_hides_at(self, x):
        return bool(self.smoke) and abs(x - self.smoke["x"]) < SMOKE_R

    # ---------------- geometry ----------------
    def beam_y(self, i):
        st = self.grid_state[i]
        if st == "rewired":
            return GROUND_Y - 30
        return LASER_MID + LASER_AMP * math.sin(self.t * LASER_SPEED + GRIDS[i][2])

    def grid_active(self, i):
        return self.grid_state[i] != "broken" and self.emp_t <= 0

    def solids(self):
        out = [pygame.Rect(-200, GROUND_Y, LEVEL_W + 400, 400)]
        if not self.glass_open:
            out.append(pygame.Rect(GLASS_DOOR_X - 8, CEIL_Y, 16, GROUND_Y - CEIL_Y))
        if self.metal_open < 0.6:
            out.append(pygame.Rect(METAL_DOOR_X - 16, CEIL_Y, 32, GROUND_Y - CEIL_Y))
        if not self.case_open:
            out.append(pygame.Rect(CROWN_X - CASE_W // 2, GROUND_Y - 170, CASE_W, 170))
        if not self.safe_open:
            out.append(pygame.Rect(SAFE_X - 35, GROUND_Y - 90, 70, 90))
        return out

    # ---------------- targets / tools ----------------
    def grid_dist(self, i):
        x0, x1, _ = GRIDS[i]
        px = self.p.x
        return 0 if x0 <= px <= x1 else min(abs(px - x0), abs(px - x1))

    def targets(self):
        p = self.p
        out = {}
        best = 9e9
        for i, c in enumerate(self.cams):
            d = abs(c.x - p.x)
            if not c.hacked and d < 280 and d < best:
                best, out["hacker"] = d, i
        best = 9e9
        for i in range(len(GRIDS)):
            d = self.grid_dist(i)
            if self.grid_state[i] == "on" and d < 150 and d < best:
                best, out["laser"] = d, ("grid", i)
                out["rewirer"] = i
        if "laser" not in out and not self.case_open and abs(p.x - CROWN_X) < 130:
            out["laser"] = ("case", 0)
        if abs(p.x - TERMINAL_X) < 80 and self.sensor_on:
            out["laptop"] = 0
        if not self.metal_open and abs(p.x - METAL_DOOR_X) < 120 and not self.metal_melt:
            out["thermite"] = ("door", 0)
        elif not self.safe_open and abs(p.x - SAFE_X) < 100:
            out["thermite"] = ("safe", 0)
        return out

    GOAL_TEXT = "Steal the RUBY CROWN and escape by helicopter from the rooftop."

    def open_modal(self, kind, lines, target, title, os=None):
        super().open_modal(kind, lines, target, title, os)

    def finish_modal(self, m):
        k = m["kind"]
        if k == "camera":
            super().finish_modal(m)
        elif k == "laser":
            kind, i = m["target"]
            sound.play("laser")
            if kind == "grid":
                self.grid_state[i] = "broken"
                x0, x1, _ = GRIDS[i]
                self.burst((x0 + x1) / 2, GROUND_Y - 120, (255, 200, 90), 22, 240, 0.7, grav=260)
                self.say("LASER GRID DISABLED")
            else:
                self.case_open = True
                self.burst(CROWN_X, GROUND_Y - 90, (180, 230, 255), 26, 200, 0.8, grav=100)
                self.say("GLASS CUT  -  silent")
        elif k == "laptop":
            self.sensor_on = False
            sound.play("unlock")
            self.say("GLASS SENSOR OFF")
        elif k == "glass":
            self.glass_open = True
            sound.play("unlock")
            self.say("CODE ACCEPTED  -  GLASS DOOR OPEN")

    def remote_terminal(self):
        if not self.sensor_on:
            return None
        return lambda: self.open_modal("laptop", ["ssh root@jewel-mall.net", "sensor.off(glass=1)"], 0,
                                       "ABIX ONLINE CODER v1.0      TARGET: GLASS SENSOR")

    def glass_code_try(self):
        """Glass door e CODE LOCK. E chaple keypad (keycard kaj kore na)."""
        p = self.p
        if self.glass_open or abs(p.x - GLASS_DOOR_X) >= 110:
            return False
        if TL.TOOLS[self.tool]["id"] == "keycard":
            sound.play("lock")
            self.say("CODE LOCK  -  the KEYCARD does not work here")
            return True
        self.open_pad(None, "GLASS DOOR", PZ.code_for("jewel_glass"), kind="glass")
        return True

    def use_tool(self):
        p = self.p
        if not self.can_do() or not p.on_ground:
            return
        if self.glass_code_try():
            return
        tid = TL.TOOLS[self.tool]["id"]
        tg = self.targets()
        if tid == "cutter":
            self.say("WIRE CUTTER works only in Level " + FX.CUTTER_TEXT)
            return
        if tid in ("emp", "decoy", "smoke"):
            return self.use_instant(tid)
        if tid in tg:
            tv = tg[tid]
            if tid == "laser":
                self.open_modal("laser", [TL.LASER_CODE], tv, "LASER BREAKER  -  type the code")
            elif tid == "hacker":
                self.open_modal("camera", [TL.CAM_CODE], tv, "CCTV HACK  -  LITE 3D  -  type the code")
            elif tid == "laptop":
                self.open_modal("laptop", ["ssh root@jewel-mall.net", "sensor.off(glass=1)"], 0,
                                "ABIX ONLINE CODER v1.0      TARGET: GLASS SENSOR")
            elif tid == "rewirer":
                self.grid_state[tv] = "rewired"
                sound.play("hack")
                self.say("REWIRED  -  lasers now kill guards")
                x0, x1, _ = GRIDS[tv]
                self.burst((x0 + x1) / 2, GROUND_Y - 30, (80, 255, 140), 20, 220, 0.7)
            elif tid == "keycard":
                self.glass_open = True
                sound.play("unlock")
                self.say("GLASS DOOR UNLOCKED")
            elif tid == "thermite":
                self.melt = {"kind": tv[0], "t": 0.0}
                sound.play("laser")
            return
        names = {"hacker": "HACKER", "laser": "LASER BREAKER", "laptop": "LAPTOP", "rewirer": "REWIRER PRO",
                 "keycard": "MASTER KEYCARD", "thermite": "VAULT THERMITE"}
        if tg:
            need = next(iter(tg))
            self.say(f"Need {names.get(need, need)}  -  press Ctrl+Alt")
        else:
            self.say("Nothing to use here")

    def use_instant(self, tid):
        p = self.p
        if self.cd[tid] > 0:
            self.say(f"{TL.tool_by_id(tid)['name']} recharging  {self.cd[tid]:.0f}s")
            return
        if tid == "emp":
            self.emp_t, self.cd["emp"] = EMP_TIME, EMP_CD
            self.waves.append({"x": p.x, "y": p.y, "t": 0.0})
            sound.play("zap")
            self.shake = 0.3
            self.say("EMP  -  all systems DEAD")
        elif tid == "decoy":
            x = clamp(p.x + p.facing * 380, 60, LEVEL_W - 60)
            self.decoy = {"x": x, "t": DECOY_TIME}
            self.cd["decoy"] = DECOY_CD
            self.add_noise(x, "decoy")
            sound.play("beep")
            self.say("DECOY DRONE launched")
        else:
            self.smoke = {"x": p.x, "t": SMOKE_TIME}
            self.cd["smoke"] = SMOKE_CD
            sound.play("hide")
            self.say("SMOKE BOMB")

    # ---------------- player actions ----------------
    def press_knife(self):
        p = self.p
        can = self.can_do() and p.knife_cd <= 0
        super().press_knife()
        if can:
            reach = pygame.Rect(0, int(p.y - 40), L1.KNIFE_REACH + 14, 44)
            if p.facing > 0:
                reach.left = int(p.x - 6)
            else:
                reach.right = int(p.x + 6)
            for d in self.dogs:
                if d.alive and reach.colliderect(d.rect()):
                    d.die(self)

    def do_punch(self):
        super().do_punch()
        p = self.p
        for d in self.dogs:
            if d.alive and abs(d.x - p.x) <= L1.PUNCH_RADIUS and abs(p.y - GROUND_Y) < 90:
                d.die(self)
        if not self.case_open and abs(p.x - CROWN_X) < 110:
            self.case_open = True
            sound.play("hit")
            self.burst(CROWN_X, GROUND_Y - 90, (180, 230, 255), 34, 300, 0.9, grav=500)
            if self.sensor_on:
                sound.play("alarm")
                self.add_noise(CROWN_X, "glass")
                for g in self.guards:
                    if g.alive:
                        g.alert = 8.0
                for d in self.dogs:
                    if d.alive:
                        d.alert = 8.0
                self.say("GLASS SMASHED  -  ALARM!")
            else:
                self.say("Glass broken (sensor off)")

    # ---------------- update ----------------
    def update(self, dt, keys):
        if not self.paused and not self.wheel and not self.modal:
            for k in self.cd:
                self.cd[k] = max(0.0, self.cd[k] - dt)
            self.emp_t = max(0.0, self.emp_t - dt)
            for n in self.noises:
                n["t"] -= dt
            self.noises = [n for n in self.noises if n["t"] > 0]
            if self.decoy:
                self.decoy["t"] -= dt
                if self.decoy["t"] <= 0:
                    self.decoy = None
            if self.smoke:
                self.smoke["t"] -= dt
                if self.smoke["t"] <= 0:
                    self.smoke = None
        super().update(dt, keys)

    def update_play(self, dt, keys):
        for sp in self.page_spots:
            sp.update(self)
        # thermite channel
        if self.melt is not None:
            keys = L1_K()
            self.melt["t"] += dt
            self.p.vx = 0
            if self.melt["t"] >= MELT_TIME:
                m = self.melt
                self.melt = None
                sound.play("unlock")
                if m["kind"] == "door":
                    self.metal_melt = True
                    self.metal_open = 0.001
                    self.say("DOOR MELTED")
                    self.burst(METAL_DOOR_X, GROUND_Y - 80, (255, 150, 40), 30, 260, 0.8, grav=300)
                else:
                    self.safe_open = True
                    self.bonus_new.add("safe")
                    self.money += SAFE_CASH
                    sound.play("cash")
                    self.say(f"SAFE MELTED  +{SAFE_CASH} Tk")
                    self.burst(SAFE_X, GROUND_Y - 50, (255, 150, 40), 26, 240, 0.8, grav=300)
        if self.metal_melt and self.metal_open < 1.0:
            self.metal_open = min(1.0, self.metal_open + dt * 0.8)

        self.player_physics(dt, keys)
        p = self.p
        if self.state != "play":
            return

        # laser grid
        pr = p.rect()
        for i, (x0, x1, _) in enumerate(GRIDS):
            if not self.grid_active(i):
                continue
            by = self.beam_y(i)
            band = pygame.Rect(x0, int(by) - 5, x1 - x0, 10)
            if self.grid_state[i] == "on":
                if pr.colliderect(band):
                    d = 1 if p.x > (x0 + x1) / 2 else -1
                    if p.inv <= 0:
                        sound.play("zap")
                        sound.play("alarm", 0.6)
                        for g in self.guards:
                            if g.alive and abs(g.x - p.x) < 800:
                                g.alert = 5.0
                        self.say("ALARM!  Laser touched")
                    self.hurt_player(d, "laser")
                    if self.state != "play":
                        return
            else:                                                     # rewired: guard/dog mare
                for g in list(self.guards) + list(self.dogs):
                    if g.alive and g.rect().colliderect(band):
                        g.die(self)
                        sound.play("zap")
                        self.burst(g.x, GROUND_Y - 30, (200, 20, 30), 22, 240, 0.9)
                        self.floats.append({"x": g.x, "y": GROUND_Y - 90, "t": 1.2, "txt": "ZAPPED!", "c": (255, 100, 100)})
        if p.y > HEIGHT + 90:
            self.kill("fell")
            return

        # checkpoint
        for i, cx in enumerate(CHECKPOINTS):
            if not self.cp_on[i] and abs(p.x - cx) < 46 and p.y > GROUND_Y - 90:
                self.cp_on[i] = True
                self.cp_idx = i
                p.health = START_HEALTH
                sound.play("checkpoint")
                self.burst(cx, GROUND_Y - 50, (90, 235, 255), 16, 200, 0.8, grav=-80)
                self.say("CHECKPOINT SAVED  -  health refilled")
        for i, (sx, sy) in enumerate(STAR_POS):
            if not self.got[i] and math.hypot(p.x - sx, (p.y - 28) - sy) < 34:
                self.got[i] = True
                sound.play("star")
                self.burst(sx, sy, GOLD, 18, 220, 0.8, grav=120)
                self.say(f"STAR {sum(self.got)} / {len(STAR_POS)}")
        for i, (cx, cy) in enumerate(CASH):
            if not self.cash_taken[i] and abs(p.x - cx) < 30 and abs((p.y - 20) - cy) < 40:
                self.cash_taken[i] = True
                self.money += CASH_VALUE
                sound.play("cash")
                self.burst(cx, cy, (120, 255, 150), 12, 160, 0.6, grav=120)
                self.floats.append({"x": cx, "y": cy - 20, "t": 1.0, "txt": f"+{CASH_VALUE} Tk", "c": (120, 255, 150)})

        # crown
        if self.case_open and not self.crown and abs(p.x - CROWN_X) < 70 and p.y > GROUND_Y - 90:
            self.crown = True
            sound.play("star")
            self.burst(CROWN_X, GROUND_Y - 80, (255, 70, 100), 30, 260, 0.9, grav=120)
            self.say("RUBY CROWN STOLEN!")
            voice.say("Ruby crown stolen. Now get to the rooftop!")

        # goli
        for b in self.bullets:
            b["x"] += b["vx"] * dt
            b["life"] -= dt
            if not p.hidden and p.alive and p.rect().inflate(6, 4).collidepoint(b["x"], b["y"]):
                b["life"] = 0
                self.hurt_player(1 if b["vx"] > 0 else -1, "shot")
                if self.state != "play":
                    return
        self.bullets = [b for b in self.bullets if b["life"] > 0 and -100 < b["x"] < LEVEL_W + 100]
        for g in self.guards:
            g.update(dt * self.guard_dt(), p, self)
        for d in self.dogs:
            d.update(dt * self.guard_dt(), p, self)
        if self.state != "play":
            return

        # CCTV
        pts = [(p.x, p.y - 30), (p.x, p.y - 8), (p.x, p.y - 50)]
        for i, c in enumerate(self.cams):
            seen = (self.emp_t <= 0 and not p.hidden and p.alive and not self.smoke_hides(p)
                    and any(c.sees(self.t, q) for q in pts))
            if seen:
                c.danger = min(1.0, c.danger + dt / 0.9)
                if not c.beeped:
                    c.beeped = True
                    sound.play("beep")
                if c.danger >= 1.0:
                    c.danger, c.beeped = 0.0, False
                    self.record(i)
                    return
            else:
                c.danger = max(0.0, c.danger - dt / 1.5)
                if c.danger <= 0:
                    c.beeped = False

        # prompt
        self.prompt = None
        tid = TL.TOOLS[self.tool]["id"]
        tg = self.targets()
        if self.can_do() and tid not in ("emp", "decoy", "smoke"):
            if tid in tg:
                self.prompt = (tid, tg[tid], True)
            elif tg:
                need = next(iter(tg))
                self.prompt = (need, tg[need], False)

        # rooftop exit
        if p.x > EXIT_X - 70 and p.alive:
            if self.crown:
                self.state, self.state_t = "win", 0.0
                p.vx = 0
                p.hidden = False
                self.won_loot = 0 if self.looted_before else CROWN_REWARD
                self.money += self.won_loot
                sound.stop_music(500)
                sound.play("win")
                self.burst(EXIT_X, GROUND_Y - 90, (255, 80, 110), 44, 320, 1.2, grav=160, r=4)
            elif not self.warned_exit:
                self.warned_exit = True
                self.say("Take the RUBY CROWN first!")
        if p.x < EXIT_X - 200:
            self.warned_exit = False

        hi = -1
        for i, (a, b, _) in enumerate(self.hints):
            if a <= p.x < b:
                hi = i
        if hi != self.hint_i:
            self.hint_i, self.hint_t = hi, 0.0
        self.hint_t += dt
        tx = p.x - WIDTH * 0.38 + p.facing * 40
        self.cam += (tx - self.cam) * min(1.0, 7 * dt)
        self.cam = clamp(self.cam, 0, LEVEL_W - WIDTH)

    # ---------------- draw ----------------
    def draw_world(self, surf):
        cam = int(self.cam)
        t = self.t
        self.back2.draw(surf, cam)
        # rooftop (khola akash)
        rx = ROOF_X - cam
        if rx < WIDTH:
            sky = pygame.Rect(max(0, rx), 0, WIDTH - max(0, rx), GROUND_Y)
            SP.v_gradient(surf, sky, (8, 10, 30), (40, 44, 88))
            rnd = random.Random(3)
            for _ in range(70):
                sx = rnd.randint(sky.x, sky.right)
                pygame.draw.circle(surf, (230, 232, 255), (sx, rnd.randint(10, 300)), rnd.choice((1, 1, 2)))
            pygame.draw.circle(surf, (240, 240, 220), (rx + 420, 90), 26)
            for k in range(14):
                bx = rx + 10 + k * 60
                bh = 70 + (k * 37) % 90
                pygame.draw.rect(surf, (14, 16, 34), (bx, GROUND_Y - bh, 50, bh))
                for _ in range(5):
                    pygame.draw.rect(surf, (255, 220, 120), (bx + rnd.randint(4, 40), GROUND_Y - rnd.randint(8, bh - 4), 4, 5))
        for x in range(150, LEVEL_W, 520):
            if x < ROOF_X - 60:
                draw_chandelier(surf, x - cam, t)
        for x in (270, 700, 1180, 2540, 3000, 3560, 4000, 5000):
            draw_counter(surf, x, cam, t)
        draw_escalator(surf, 1560, cam, t)
        draw_escalator(surf, 2850, cam, t)
        draw_floor2(surf, cam)
        if rx < WIDTH:
            rr = pygame.Rect(max(0, rx), GROUND_Y - 4, WIDTH, HEIGHT - GROUND_Y + 4)
            SP.v_gradient(surf, rr, (74, 76, 90), (36, 38, 50))
            pygame.draw.rect(surf, (130, 134, 150), (rr.x, rr.y, rr.w, 6))
            hp = (EXIT_X - cam, GROUND_Y - 2)
            pygame.draw.ellipse(surf, (50, 54, 66), (hp[0] - 120, hp[1] - 14, 240, 28))
            pygame.draw.ellipse(surf, (240, 200, 70), (hp[0] - 120, hp[1] - 14, 240, 28), 3)
            hf = get_font(30).render("H", True, (240, 200, 70))
            surf.blit(hf, hf.get_rect(center=hp))
            draw_helicopter(surf, EXIT_X - cam - 20, GROUND_Y - 90, t)
        for x0, x1, y in LEDGES:
            if x1 - cam > -20 and x0 - cam < WIDTH + 20:
                SP.draw_ledge(surf, x0 - cam, x1 - cam, y)
        for i, cx in enumerate(CHECKPOINTS):
            SP.draw_locker(surf, cx - cam, GROUND_Y, self.cp_on[i], t)
        draw_safe(surf, SAFE_X, cam, "melted" if self.safe_open else "closed", t)
        SP.draw_terminal(surf, TERMINAL_X - cam, GROUND_Y, "locked" if self.sensor_on else "open", t)
        self.draw_doors(surf, cam, t)
        self.draw_case(surf, cam, t)
        for i, (x0, x1, _) in enumerate(GRIDS):
            self.draw_grid(surf, cam, i, t)
        for c in self.cams:
            saved = c.hacked
            c.hacked = saved or self.emp_t > 0
            c.draw(surf, cam, t)
            c.hacked = saved
        for i, (sx, sy) in enumerate(STAR_POS):
            if not self.got[i]:
                SP.draw_star_icon(surf, (sx - cam, sy + math.sin(t * 3 + i) * 5), 15, True, t, True)
        for i, (cx, cy) in enumerate(CASH):
            if not self.cash_taken[i] and -40 < cx - cam < WIDTH + 40:
                SP.draw_cash(surf, (cx - cam, cy), t)
        for d in self.dogs:
            d.draw(surf, cam, t)
        for g in self.guards:
            g.draw(surf, cam, t)
        if self.decoy:
            dx = self.decoy["x"] - cam
            yy = GROUND_Y - 100 + math.sin(t * 5) * 4
            SP.draw_tool_icon(surf, "decoy", (dx, yy), 26, t)
            for k in range(3):
                rr = ((t * 1.6 + k / 3) % 1.0) * 90
                a = int(160 * (1 - rr / 90))
                ring = pygame.Surface((200, 200), pygame.SRCALPHA)
                pygame.draw.circle(ring, (255, 220, 90, a), (100, 100), int(rr) + 4, 3)
                surf.blit(ring, (dx - 100, yy - 100))
        if self.state == "police":
            SP.draw_police_car(surf, self.car_x - cam, GROUND_Y, self.car_dir, t)
        self.draw_player(surf, cam)
        if self.state == "win" and False:
            pass
        for b in self.bullets:
            SP.draw_bullet(surf, b["x"] - cam, b["y"], 1 if b["vx"] > 0 else -1)
        for w in self.waves:
            k = w["t"] / 0.5
            rad = (L1.PUNCH_RADIUS if self.emp_t <= 0 else 520) * (1 - (1 - k) ** 2)
            h = 26 + 10 * k
            a = int(220 * (1 - k))
            sw = pygame.Surface((int(rad * 2) + 12, int(h * 2) + 12), pygame.SRCALPHA)
            col = (255, 235, 160, a) if self.emp_t <= 0 else (110, 200, 255, a)
            pygame.draw.ellipse(sw, col, sw.get_rect().inflate(-8, -8), 6)
            surf.blit(sw, sw.get_rect(center=(w["x"] - cam, w["y"] - 6)))
        if self.smoke:
            k = clamp(self.smoke["t"] / SMOKE_TIME, 0, 1)
            sm = pygame.Surface((SMOKE_R * 2 + 80, 300), pygame.SRCALPHA)
            rnd = random.Random(8)
            for _ in range(26):
                ox = rnd.uniform(-SMOKE_R, SMOKE_R)
                oy = rnd.uniform(-90, 30) - (1 - k) * 20
                rr = rnd.uniform(32, 60) * (1.2 - 0.3 * k)
                pygame.draw.circle(sm, (170, 172, 182, int(150 * min(1, k * 1.6))), (int(SMOKE_R + 40 + ox), int(200 + oy)), int(rr))
            surf.blit(sm, (self.smoke["x"] - cam - SMOKE_R - 40, GROUND_Y - 200))
        for pt in self.parts:
            k = pt["life"] / pt["max"]
            r = max(1, int(pt["r"] * (0.4 + 0.6 * k)))
            pygame.draw.circle(surf, pt["c"], (int(pt["x"] - cam), int(pt["y"])), r)
        for f in self.floats:
            img = self.f_med.render(f["txt"], True, f["c"])
            img.set_alpha(int(255 * clamp(f["t"] / 0.4, 0, 1)))
            surf.blit(img, img.get_rect(center=(f["x"] - cam, f["y"])))
        self.draw_prompt2(surf, cam)
        if self.emp_t > 0:                                         # alo nibhe ondhokar
            a = int(170 * clamp(min(self.emp_t, 0.5) / 0.5, 0, 1) * (0.88 + 0.12 * math.sin(t * 30)))
            dk = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dk.fill((2, 4, 14, a))
            surf.blit(dk, (0, 0))
            img = self.f_small.render(f"EMP  {self.emp_t:.1f}s", True, (120, 210, 255))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 150)))

    def draw_doors(self, surf, cam, t):
        for sp in self.page_spots:
            sp.draw(self, surf, cam, t)
        gx = GLASS_DOOR_X - cam
        if -60 < gx < WIDTH + 60:
            if not self.glass_open:
                gs = pygame.Surface((22, GROUND_Y - CEIL_Y), pygame.SRCALPHA)
                gs.fill((130, 200, 255, 70))
                surf.blit(gs, (gx - 11, CEIL_Y))
                pygame.draw.rect(surf, (190, 225, 250), (gx - 11, CEIL_Y, 22, GROUND_Y - CEIL_Y), 3)
                pygame.draw.rect(surf, (30, 34, 44), (gx + 14, GROUND_Y - 150, 12, 30), border_radius=3)
                pygame.draw.circle(surf, (255, 60, 60) if int(t * 2) % 2 else (120, 20, 20), (gx + 20, GROUND_Y - 142), 3)
                pad = pygame.Rect(gx + 14, GROUND_Y - 178, 34, 52)
                pygame.draw.rect(surf, (24, 26, 36), pad, border_radius=5)
                pygame.draw.rect(surf, (120, 126, 150), pad, 2, border_radius=5)
                for r_ in range(3):
                    for c_ in range(3):
                        pygame.draw.circle(surf, (170, 176, 200), (pad.x + 9 + c_ * 8, pad.y + 22 + r_ * 8), 2)
                if abs(self.p.x - GLASS_DOOR_X) < 110:
                    hf = get_font(14).render("[E]  ENTER CODE", True, (255, 220, 100))
                    surf.blit(hf, hf.get_rect(center=(gx, GROUND_Y - 196)))
            else:
                pygame.draw.rect(surf, (190, 225, 250), (gx - 11, CEIL_Y, 4, 50), 2)
                pygame.draw.rect(surf, (190, 225, 250), (gx + 7, CEIL_Y, 4, 50), 2)
                pygame.draw.circle(surf, (60, 255, 130), (gx + 20, GROUND_Y - 142), 3)
        mx = METAL_DOOR_X - cam
        if -60 < mx < WIDTH + 60:
            h = GROUND_Y - CEIL_Y
            pygame.draw.rect(surf, (14, 16, 22), (mx - 20, CEIL_Y, 40, h))
            if self.metal_open < 0.999:
                off = int(h * self.metal_open)
                slab = pygame.Rect(mx - 16, CEIL_Y - off, 32, h)
                for i in range(slab.w):
                    kk = i / slab.w
                    c = SP.lerp_color((70, 74, 88), (170, 176, 192), math.sin(kk * math.pi))
                    pygame.draw.line(surf, c, (slab.x + i, slab.y), (slab.x + i, slab.bottom))
                pygame.draw.rect(surf, (30, 32, 40), slab, 3)
                for yy in range(slab.y + 20, slab.bottom, 50):
                    pygame.draw.circle(surf, (30, 32, 40), (slab.x + 6, yy), 2)
                    pygame.draw.circle(surf, (30, 32, 40), (slab.right - 6, yy), 2)
                pygame.draw.rect(surf, (230, 90, 40) if self.metal_melt else (200, 200, 60), (mx - 5, GROUND_Y - 90, 10, 20))
                if self.metal_melt:
                    SP.glow(surf, (mx, GROUND_Y - 80), 50, (255, 140, 40), 70, 3)
            f = get_font(14).render("REINFORCED", True, (240, 90, 90))
            surf.blit(f, f.get_rect(center=(mx, 90)))

    def draw_case(self, surf, cam, t):
        x = CROWN_X - cam
        if not (-120 < x < WIDTH + 120):
            return
        ped = pygame.Rect(0, 0, 60, 60)
        ped.midbottom = (x, GROUND_Y)
        SP.v_gradient(surf, ped, (90, 76, 104), (46, 38, 58))
        pygame.draw.rect(surf, (210, 170, 80), ped, 2)
        if not self.crown:
            draw_ruby_crown(surf, (x, GROUND_Y - 78), t, 1.25)
        if not self.case_open:
            r = pygame.Rect(0, 0, CASE_W, 112)
            r.midbottom = (x, GROUND_Y - 58)
            gs = pygame.Surface(r.size, pygame.SRCALPHA)
            gs.fill((170, 220, 255, 50))
            pygame.draw.polygon(gs, (255, 255, 255, 40), [(0, 0), (26, 0), (8, r.h), (0, r.h)])
            surf.blit(gs, r.topleft)
            pygame.draw.rect(surf, (200, 230, 255), r, 3)
            if self.sensor_on:
                col = (255, 60, 60) if int(t * 3) % 2 else (120, 20, 20)
                pygame.draw.circle(surf, col, (r.right - 8, r.y + 8), 4)
                f = get_font(13).render("SOUND SENSOR", True, col)
                surf.blit(f, f.get_rect(midbottom=(x, r.y - 4)))
            else:
                pygame.draw.circle(surf, (60, 255, 130), (r.right - 8, r.y + 8), 4)
        f = get_font(14).render("RUBY CROWN", True, (255, 120, 150))
        surf.blit(f, f.get_rect(midtop=(x, GROUND_Y + 14)))

    def draw_grid(self, surf, cam, i, t):
        x0, x1, _ = GRIDS[i]
        a, b = x0 - cam, x1 - cam
        if b < -40 or a > WIDTH + 40:
            return
        st = self.grid_state[i]
        for px in (a, b):
            pygame.draw.rect(surf, (54, 56, 66), (px - 8, CEIL_Y, 16, GROUND_Y - CEIL_Y))
            pygame.draw.rect(surf, (90, 94, 108), (px - 8, CEIL_Y, 4, GROUND_Y - CEIL_Y))
        if st == "broken" or self.emp_t > 0:
            for px in (a, b):
                pygame.draw.circle(surf, (40, 10, 10), (px, CEIL_Y + 30), 4)
            return
        by = self.beam_y(i)
        by = min(by, GROUND_Y - 6)
        col = (255, 60, 70) if st == "on" else (70, 255, 140)
        for px in (a, b):
            pygame.draw.circle(surf, col, (px, int(by)), 6)
        SP.glow(surf, ((a + b) / 2, by), (b - a) * 0.5, col, 40, 3)
        pygame.draw.line(surf, col, (a, by), (b, by), 5)
        pygame.draw.line(surf, (255, 255, 255), (a, by), (b, by), 1)

    def draw_prompt2(self, surf, cam):
        p = self.p
        if self.state != "play":
            return
        dmax = max((c.danger for c in self.cams), default=0.0)
        if dmax > 0.02:
            w = 46
            r = pygame.Rect(0, 0, w, 7)
            r.center = (p.x - cam, p.y - 76)
            pygame.draw.rect(surf, (40, 20, 24), r.inflate(4, 4), border_radius=4)
            pygame.draw.rect(surf, (255, 60, 60), (r.x, r.y, int(w * dmax), r.h), border_radius=3)
            img = self.f_small.render("REC", True, (255, 70, 70))
            surf.blit(img, img.get_rect(midbottom=(r.centerx, r.y - 3)))
        if self.melt is not None:
            r = pygame.Rect(0, 0, 70, 8)
            r.center = (p.x - cam, p.y - 76)
            pygame.draw.rect(surf, (40, 20, 10), r.inflate(4, 4), border_radius=4)
            pygame.draw.rect(surf, (255, 150, 40), (r.x, r.y, int(r.w * self.melt["t"] / MELT_TIME), r.h), border_radius=3)
            img = self.f_small.render("MELTING...", True, (255, 170, 60))
            surf.blit(img, img.get_rect(midbottom=(r.centerx, r.y - 3)))
            return
        if not self.prompt:
            return
        kind, idx, ok = self.prompt
        names = {"hacker": ("[E]  HACK CAMERA", "LITE 3D  -  type code", 2), "laser": ("[E]  DISABLE / CUT", "type code", 1),
                 "laptop": ("[E]  USE LAPTOP", "glass sensor OFF", 3), "rewirer": ("[E]  REWIRE LASER", "guards will die", 6),
                 "keycard": ("[E]  SCAN KEYCARD", "open glass door", 9), "thermite": ("[E]  MELT", "2 seconds", 8)}
        l1, l2, key = names[kind]
        tl = TL.tool_by_id(kind)["name"]
        if kind == "hacker":
            c = self.cams[idx]
            lx, ly = c.lens(self.t)
            tgt = (lx, ly)
        elif kind in ("laser", "rewirer"):
            gi = idx[1] if isinstance(idx, tuple) and idx[0] == "grid" else (idx if isinstance(idx, int) else None)
            if gi is not None:
                tgt = ((GRIDS[gi][0] + GRIDS[gi][1]) / 2, GROUND_Y - 150)
            else:
                tgt = (CROWN_X, GROUND_Y - 150)
        elif kind == "laptop":
            tgt = (TERMINAL_X, GROUND_Y - 110)
        elif kind == "keycard":
            tgt = (GLASS_DOOR_X, GROUND_Y - 160)
        else:
            tgt = (METAL_DOOR_X if (isinstance(idx, tuple) and idx[0] == "door") else SAFE_X, GROUND_Y - 120)
        col = (120, 255, 190) if ok else (150, 150, 170)
        lines = [l1, l2] if ok else [f"Select {tl}", f"Ctrl+Alt  or  key {key}"]
        self.dashed(surf, (p.x - cam, p.y - 50), (tgt[0] - cam, tgt[1]), col)
        mid = ((p.x + tgt[0]) / 2 - cam, (p.y - 50 + tgt[1]) / 2 - 18)
        imgs = [self.f_small.render(s_, True, col) for s_ in lines]
        w = max(i.get_width() for i in imgs) + 20
        h = sum(i.get_height() for i in imgs) + 12
        box = pygame.Rect(0, 0, w, h)
        box.center = (int(mid[0]), int(mid[1]))
        bg = pygame.Surface(box.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (8, 12, 20, 200), bg.get_rect(), border_radius=8)
        pygame.draw.rect(bg, col + (255,), bg.get_rect(), 2, border_radius=8)
        surf.blit(bg, box.topleft)
        y = box.y + 6
        for im in imgs:
            surf.blit(im, im.get_rect(midtop=(box.centerx, y)))
            y += im.get_height()

    def draw_prompt(self, surf, cam):                        # base draw_world er jonno (L2 e lage na)
        pass

    def draw_hud(self, surf, mouse):
        super().draw_hud(surf, mouse)
        # crown + cooldown chip
        if self.crown:
            draw_ruby_crown(surf, (WIDTH - 40, 140), self.t, 0.8)
        x = 12
        for tid, key in (("emp", "4"), ("decoy", "5"), ("smoke", "7")):
            cdv = self.cd[tid]
            c = (x + 20, HEIGHT - 70)
            pygame.draw.circle(surf, (22, 22, 40), c, 18)
            SP.draw_tool_icon(surf, tid, c, 13, self.t)
            if cdv > 0:
                ov = pygame.Surface((36, 36), pygame.SRCALPHA)
                pygame.draw.circle(ov, (0, 0, 0, 170), (18, 18), 18)
                surf.blit(ov, (c[0] - 18, c[1] - 18))
                img = self.f_small.render(f"{cdv:.0f}", True, WHITE)
                surf.blit(img, img.get_rect(center=c))
            pygame.draw.circle(surf, (110, 120, 160) if cdv > 0 else (110, 255, 160), c, 18, 2)
            kk = self.f_small.render(key, True, (170, 175, 200))
            surf.blit(kk, kk.get_rect(midtop=(c[0], c[1] + 19)))
            x += 48


def L1_K():
    class K(dict):
        def __missing__(self, k):
            return False
    return K()


# ------------------------------------------------------------------
# Title card + entry point
# ------------------------------------------------------------------
def play_title(screen, clock):
    t = 0.0
    f = get_font(54)
    f2 = get_font(24)
    back = Backdrop2()
    said = False
    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        t += dt
        CT.set_ctx(True)
        for e in CT.filter(pygame.event.get()):
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                return
        if not said and t > 0.8:
            said = True
            voice.say("Jewelry mall. Steal the Ruby Crown.")
        back.draw(screen, t * 40)
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((4, 4, 12, 200))
        screen.blit(dim, (0, 0))
        a = clamp(t / 0.6, 0, 1)
        img = f.render("LEVEL 2  -  JEWELRY MALL HEIST", True, GOLD)
        img.set_alpha(int(255 * a))
        screen.blit(img, img.get_rect(center=(WIDTH // 2, 190)))
        draw_ruby_crown(screen, (WIDTH // 2, 300), t, 2.2)
        for i, ln in enumerate(["Steal the RUBY CROWN.  Dodge guards, K9 dogs and moving lasers.",
                                "Escape from the rooftop by helicopter.   Bail if arrested: 500 Tk"]):
            im = f2.render(ln, True, (210, 215, 235))
            im.set_alpha(int(255 * clamp((t - 0.8 - i * 0.4) / 0.5, 0, 1)))
            screen.blit(im, im.get_rect(center=(WIDTH // 2, 385 + i * 34)))
        im = get_font(15).render("ENTER = start", True, (130, 130, 160))
        screen.blit(im, im.get_rect(bottomright=(WIDTH - 16, HEIGHT - 12)))
        fade_overlay(screen, 1 - t / 0.6)
        if t > 5.0:
            return
        pygame.display.flip()


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    return L1.run_level(screen, clock, save, save_fn, World2, lambda: play_title(screen, clock))
