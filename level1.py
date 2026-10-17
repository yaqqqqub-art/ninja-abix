"""
level1.py - Chapter 1 / Level 1 : CITY BANK HEIST (hacker bank loot game).
main_game.py theke call hoy:  level1.run(screen, clock, save, save_fn)

Prothom bar khelle age TV intro: TV te boro DIAMOND dekhay (news), Abix bole "my dream place".
Tarpor level: bank er bhitor dhuke 3 ta star, taka (Tk) ar shesh e vault theke DIAMOND churi.

Control:
  A D / <- ->      cholo
  W / SPACE / Up   lafao (dhore rakhle uchu)
  J / X            KNIFE  - guard ke ek kope (shamne)
  H / S / Down     HIDE   - guard, camera dekhte pay na
  K / F            SUPER PUNCH - 5 meter er moddhe shob guard more
  Ctrl+Alt / TAB   9 TOOL er wheel (scroll / <- -> diye unlock kora tool beche nao)
  1 - 9            shorashori tool (level 1 e 1 2 3 kaj kore)
  mouse scroll     tool badlao
  E                tool use koro (code type korte hobe: camera = /CAMERA01099, laser = /TKDIAMONDLASER)
  ESC              Pause

Niyom:
  - 3 health. Guard er goli lagle 1 health jay. Laser chhuile o lage + alarm.
  - Health 0 hole mrittu: 1 live kome, shesh checkpoint (locker) theke abar shuru.
  - 3 live shesh -> GAME OVER -> RESTART. Total mrittur count save thake.
  - CCTV camera dekhle RECORD hoy -> police ashe -> ARREST. Jamin (300 Tk) thakle bair hobe,
    na thakle 5 din jail. (arrest e live kome na)
  - HACKER tool diye camera disable korle record hoy na. HIDE korle o camera dekhte pay na.
  - LAPTOP e code type kore vault khulo, DIAMOND nao = jeet.
"""
import math
import random
import sys
import time
import pygame

import sound
import laptop as LP
import puzzles as PZ
import controls as CT
import voice
import tools as TL
import abix_fx as FX
import sprites as SP
from animation import WIDTH, HEIGHT, WHITE, RED, GOLD, get_font, fade_overlay, rgb_color, draw_shuriken

# ------------------------------------------------------------------
# Level data (1 meter = 40 pixel)
# ------------------------------------------------------------------
M = 40
GROUND_Y = 440
CEIL_Y = 62
LEVEL_W = 5400
SPAWN_X = 200

LEDGES = [(900, 1060, 350),                       # (x0, x1, uporer y)  - counter / shelf
          (2040, 2150, 365), (2200, 2320, 290),
          (3500, 3620, 360), (3680, 3800, 285), (3840, 3980, 215)]
STAR_POS = [(980, 312), (2260, 252), (3910, 177)]
CASH = [(480, GROUND_Y - 12), (1000, GROUND_Y - 12), (1250, GROUND_Y - 12), (1660, GROUND_Y - 12),
        (2090, 350), (2650, GROUND_Y - 12), (3250, GROUND_Y - 12), (3760, 270), (4450, GROUND_Y - 12)]
CASH_VALUE = 100
GUARDS = [(700, 980), (1900, 2250), (3000, 3350), (4000, 4250)]
CAMERAS = [(1400, 0.0), (2800, 1.6), (3750, 3.1), (4800, 4.4)]
LASER_X = [1800, 3450, 4600]
LASER_TOP = 96
CHECKPOINTS = [1600, 2700, 4350]
TERMINAL_X = 4880
VAULT_X = 5050
DIAMOND_X = 5210
BAIL = 300
CAM_CODE, LASER_CODE = TL.CAM_CODE, TL.LASER_CODE
JAIL_DAYS = 5
DIAMOND_REWARD = 500

HINTS = [
    (0, 380, "MOVE  -  A / D  or  Left / Right"),
    (380, 620, "JUMP  -  W / SPACE / Up   (hold = higher)"),
    (620, 800, "A GUARD with a gun!  HIDE  -  hold H (or S / Down)"),
    (800, 1000, "KNIFE  -  press J near a guard.   K = Super Punch (5 m)"),
    (1000, 1250, "Collect all 3 STARS  -  some are up high.  Grab the cash!"),
    (1250, 1560, "CCTV!  Key 2 = HACKER, press E near camera, type /CAMERA01099"),
    (1560, 1740, "Touch a safe LOCKER to save your checkpoint"),
    (1740, 1900, "LASER!  Key 1 = LASER BREAKER, press E, type /TKDIAMONDLASER"),
    (4640, 5000, "Press L anywhere = open the LAPTOP  >  WIRE CONNECT app (or Python: unlock)"),
    (5000, 5300, "The vault is open  -  take the DIAMOND!"),
]

SPEED, ACC_G, ACC_A = 250.0, 2800.0, 1700.0
GRAV, JUMP_V, MAXFALL = 2000.0, 700.0, 900.0
KNIFE_CD, KNIFE_T, KNIFE_REACH = 0.45, 0.25, 62
PUNCH_CD, PUNCH_WIND = 4.0, 0.34
PUNCH_RADIUS = 5 * M
START_LIVES, START_HEALTH = 3, 3
HACK_TIME = 0.9
TYPE_LINES = ["ssh root@city-bank.net", "bypass --firewall --all", "vault.unlock(door=1)"]

SPOT_LINES = ["Freeze! Drop the loot!", "Hey! Stop right there!", "Intruder! Hands up!"]
CHAT_LINES = ["I have CCTV footage in this place.", "Nobody gets past me.", "All quiet tonight...",
              "Cameras are watching everything."]


def clamp(v, a, b):
    return max(a, min(b, v))


_voice_last = [0.0]


def speak(text):
    """Guard er kotha mukhe bole (beshi baar na)."""
    now = time.time()
    if now - _voice_last[0] < 1.6:
        return
    _voice_last[0] = now
    voice.say(text)


# ------------------------------------------------------------------
# Background - bank er bhitor
# ------------------------------------------------------------------
class Backdrop:
    TILE = 480

    def __init__(self):
        rnd = random.Random(11)
        w = pygame.Surface((self.TILE, GROUND_Y))
        SP.v_gradient(w, w.get_rect(), (52, 50, 74), (34, 32, 52))
        pygame.draw.rect(w, (24, 22, 38), (0, 0, 8, GROUND_Y))                 # pilaster
        pygame.draw.rect(w, (66, 64, 90), (8, 0, 3, GROUND_Y))
        # crown molding
        pygame.draw.rect(w, (24, 22, 36), (0, 0, self.TILE, 34))
        pygame.draw.rect(w, (190, 150, 70), (0, 34, self.TILE, 4))
        pygame.draw.rect(w, (110, 84, 40), (0, 38, self.TILE, 3))
        # arch window (night city)
        win = pygame.Rect(165, 86, 150, 238)
        sky = pygame.Surface(win.size)
        SP.v_gradient(sky, sky.get_rect(), (12, 18, 46), (50, 62, 112))
        pygame.draw.circle(sky, (235, 238, 215), (108, 54), 17)
        pygame.draw.circle(sky, (12, 18, 46), (116, 50), 15)
        bx = 0
        while bx < win.w:
            bw, bh = rnd.randint(18, 38), rnd.randint(40, 120)
            pygame.draw.rect(sky, (14, 16, 32), (bx, win.h - bh, bw, bh))
            for _ in range(bw * bh // 150):
                if rnd.random() < 0.55:
                    pygame.draw.rect(sky, (255, 220, 120), (bx + rnd.randint(2, bw - 5), win.h - rnd.randint(6, bh - 3), 3, 4))
            bx += bw + 2
        mask = pygame.Surface(win.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 60, win.w, win.h - 60))
        pygame.draw.ellipse(mask, (255, 255, 255, 255), (0, 0, win.w, 120))
        sky = sky.convert_alpha()
        sky.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        w.blit(sky, win.topleft)
        pygame.draw.rect(w, (160, 150, 130), (win.x - 8, win.y + 60, win.w + 16, win.h - 50), 8)
        pygame.draw.arc(w, (160, 150, 130), (win.x - 8, win.y - 2, win.w + 16, 126), 0, math.pi, 8)
        pygame.draw.line(w, (110, 104, 92), (win.centerx, win.y), (win.centerx, win.bottom), 4)
        pygame.draw.line(w, (110, 104, 92), (win.x, win.y + 130), (win.right, win.y + 130), 4)
        pygame.draw.rect(w, (190, 180, 160), (win.x - 14, win.bottom + 2, win.w + 28, 9), border_radius=3)
        # wainscot (lower wood panel)
        pygame.draw.rect(w, (74, 48, 32), (0, 340, self.TILE, GROUND_Y - 340))
        pygame.draw.rect(w, (140, 100, 56), (0, 340, self.TILE, 5))
        for i in range(3):
            r = pygame.Rect(26 + i * 150, 358, 118, 66)
            pygame.draw.rect(w, (92, 62, 40), r, border_radius=3)
            pygame.draw.rect(w, (52, 34, 22), r, 3, border_radius=3)
        self.wall = w
        self.glow = pygame.Surface((300, 160), pygame.SRCALPHA)
        for i in range(6):
            pygame.draw.ellipse(self.glow, (255, 230, 160, 12), self.glow.get_rect().inflate(-i * 40, -i * 22))

    def draw(self, surf, cam):
        off = -int(cam * 0.6) % self.TILE
        x = off - self.TILE
        while x < WIDTH:
            surf.blit(self.wall, (x, 0))
            surf.blit(self.glow, (x + self.TILE // 2 - 150, 20))
            x += self.TILE


def draw_floor(surf, cam):
    r = pygame.Rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y)
    SP.v_gradient(surf, r, (176, 170, 186), (98, 94, 112))
    tile = 90
    # checker (simple loop)
    base = int(cam) // tile
    for i in range(0, WIDTH // tile + 3):
        wx = base + i
        sx = wx * tile - int(cam)
        for row in range(2):
            if (wx + row) % 2 == 0:
                s = pygame.Surface((tile, 48), pygame.SRCALPHA)
                s.fill((20, 18, 34, 46))
                surf.blit(s, (sx, GROUND_Y + 8 + row * 48))
    pygame.draw.rect(surf, (52, 36, 24), (0, GROUND_Y - 4, WIDTH, 12))
    pygame.draw.rect(surf, (214, 170, 70), (0, GROUND_Y - 4, WIDTH, 2))
    g = pygame.Surface((WIDTH, 26), pygame.SRCALPHA)
    pygame.draw.rect(g, (255, 255, 255, 34), (0, 0, WIDTH, 26))
    surf.blit(g, (0, GROUND_Y + 8))


def draw_decor(surf, cam, t):
    c = int(cam)
    # marble columns
    for i in range(0, 10):
        x = 330 + i * 560 - c
        if -80 < x < WIDTH + 80:
            col = pygame.Rect(x - 26, 40, 52, GROUND_Y - 40)
            for k in range(col.w):
                kk = k / col.w
                cc = SP.lerp_color((92, 90, 108), (214, 212, 224), math.sin(kk * math.pi))
                pygame.draw.line(surf, cc, (col.x + k, col.y), (col.x + k, col.bottom))
            pygame.draw.rect(surf, (60, 58, 76), (x - 34, 40, 68, 12), border_radius=3)
            pygame.draw.rect(surf, (60, 58, 76), (x - 34, GROUND_Y - 14, 68, 14), border_radius=3)
    # teller counters (sudhu sajano)
    for x0 in (230, 560, 1450, 2480, 3100, 4150):
        x = x0 - c
        if -260 < x < WIDTH + 40:
            r = pygame.Rect(x, GROUND_Y - 62, 190, 62)
            SP.v_gradient(surf, r, (112, 78, 48), (66, 44, 28))
            pygame.draw.rect(surf, (190, 150, 90), (x - 4, GROUND_Y - 66, 198, 6), border_radius=2)
            pygame.draw.rect(surf, (34, 22, 14), r, 2)
            gl = pygame.Rect(x + 20, GROUND_Y - 150, 150, 84)
            gs = pygame.Surface(gl.size, pygame.SRCALPHA)
            gs.fill((150, 190, 230, 36))
            surf.blit(gs, gl.topleft)
            pygame.draw.rect(surf, (170, 200, 230), gl, 2)
            pygame.draw.rect(surf, (36, 40, 52), (x + 70, GROUND_Y - 100, 50, 38))
            pygame.draw.rect(surf, (80, 190, 130), (x + 74, GROUND_Y - 96, 42, 26))
    # paintings
    for x0, col in ((620, (140, 60, 60)), (1180, (60, 100, 140)), (2380, (110, 130, 60)), (3320, (130, 80, 140)),
                    (4000, (60, 120, 120))):
        x = x0 - c
        if -120 < x < WIDTH + 60:
            r = pygame.Rect(x, 150, 90, 66)
            pygame.draw.rect(surf, (176, 140, 60), r.inflate(14, 14), border_radius=3)
            pygame.draw.rect(surf, col, r)
            pygame.draw.polygon(surf, tuple(max(0, v - 50) for v in col), [(r.x, r.bottom), (r.x + 34, r.y + 30), (r.x + 60, r.bottom)])
            pygame.draw.circle(surf, (240, 230, 190), (r.x + 66, r.y + 16), 8)
    # plants
    for x0 in (120, 780, 1570, 2420, 3040, 3600, 4700):
        x = x0 - c
        if -60 < x < WIDTH + 60:
            pygame.draw.polygon(surf, (120, 64, 44), [(x - 14, GROUND_Y - 30), (x + 14, GROUND_Y - 30), (x + 10, GROUND_Y), (x - 10, GROUND_Y)])
            for k in range(7):
                a = -math.pi / 2 + (k - 3) * 0.38
                pygame.draw.line(surf, (46, 130, 70), (x, GROUND_Y - 30), (x + math.cos(a) * 34, GROUND_Y - 30 + math.sin(a) * 40), 4)
    # signs
    x = 300 - c
    if -300 < x < WIDTH + 100:
        f = get_font(44)
        img = f.render("CITY BANK", True, (232, 190, 80))
        surf.blit(f.render("CITY BANK", True, (60, 40, 10)), (x + 3, 63))
        surf.blit(img, (x, 60))
    x = 5050 - c
    if -200 < x < WIDTH + 100:
        f = get_font(26)
        img = f.render("VAULT", True, (255, 80, 80))
        surf.blit(img, img.get_rect(center=(x, 120)))
    for ex in (1190, 2330, 3290, 4440):
        x = ex - c
        if -80 < x < WIDTH + 80:
            pygame.draw.rect(surf, (20, 90, 50), (x - 26, 108, 52, 20), border_radius=3)
            img = get_font(14).render("EXIT", True, (150, 255, 190))
            surf.blit(img, img.get_rect(center=(x, 118)))
    # vault room (darker) ar pedestal
    vx = VAULT_X + 22 - c
    if vx < WIDTH:
        ov = pygame.Surface((WIDTH, GROUND_Y - CEIL_Y), pygame.SRCALPHA)
        ov.fill((6, 8, 16, 190))
        surf.blit(ov, (vx, CEIL_Y))
        for row in range(3):
            for col in range(10):
                r = pygame.Rect(vx + 40 + col * 42, 100 + row * 70, 32, 52)
                pygame.draw.rect(surf, (54, 58, 72), r, border_radius=2)
                pygame.draw.rect(surf, (28, 30, 40), r, 2, border_radius=2)
                pygame.draw.circle(surf, (170, 150, 80), r.center, 4)


# ------------------------------------------------------------------
# CCTV camera
# ------------------------------------------------------------------
class Camera:
    RANGE, HALF, SWAY, SPEED = 380, math.radians(21), 34.0, 0.9

    def __init__(self, x, phase):
        self.x, self.y = x, CEIL_Y - 2
        self.phase = phase
        self.hacked = False
        self.danger = 0.0
        self.beeped = False

    def angle(self, t):
        return 90 + self.SWAY * math.sin(t * self.SPEED + self.phase)

    def lens(self, t):
        a = math.radians(self.angle(t))
        return (self.x + math.cos(a) * 37, self.y + 12 + math.sin(a) * 37)

    def sees(self, t, pt):
        if self.hacked:
            return False
        lx, ly = self.lens(t)
        vx, vy = pt[0] - lx, pt[1] - ly
        d = math.hypot(vx, vy)
        if d > self.RANGE or d < 4:
            return False
        a = math.radians(self.angle(t))
        diff = (math.atan2(vy, vx) - a + math.pi) % math.tau - math.pi
        return abs(diff) <= self.HALF

    def draw(self, surf, cam, t):
        x = self.x - cam
        if x < -200 or x > WIDTH + 200:
            return
        if not self.hacked:                                  # alo er cone
            lx, ly = self.lens(t)
            a = math.radians(self.angle(t))
            pts = [(lx, ly)] + [(lx + math.cos(a + k) * self.RANGE, ly + math.sin(a + k) * self.RANGE)
                                for k in (-self.HALF, -self.HALF / 2, 0, self.HALF / 2, self.HALF)]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            bx, by = int(min(xs)) - 2, int(min(ys)) - 2
            cs = pygame.Surface((int(max(xs)) - bx + 4, int(max(ys)) - by + 4), pygame.SRCALPHA)
            col = SP.lerp_color((255, 235, 140), (255, 50, 50), clamp(self.danger, 0, 1))
            loc = [(p[0] - bx, p[1] - by) for p in pts]
            pygame.draw.polygon(cs, col + (34 + int(70 * self.danger),), loc)
            pygame.draw.lines(cs, col + (110,), False, [loc[1], loc[0], loc[-1]], 2)
            surf.blit(cs, (bx - cam, by))
        SP.draw_cctv(surf, x, self.y, self.angle(t), not self.hacked, t, self.danger)


# ------------------------------------------------------------------
# Guard (hate gun wala asol manush)
# ------------------------------------------------------------------
class Guard:
    HW, HH = 30, 60
    SIGHT, PATROL = 400, 62
    AIM, SHOOT, RECOVER = 0.6, 0.18, 1.0

    def __init__(self, x0, x1):
        self.x0, self.x1 = x0, x1
        self.reset()

    def reset(self):
        self.x = (self.x0 + self.x1) / 2
        self.facing = -1
        self.alive = True
        self.found = False
        self.spot_lines, self.chat_lines = SPOT_LINES, CHAT_LINES
        self.dead_t = 0.0
        self.anim_t = random.uniform(0, 5)
        self.calm()

    def calm(self):
        self.state = "patrol"
        self.timer = self.pause = self.alert = self.excl = 0.0
        self.bubble, self.bubble_t = "", 0.0
        self.chat = random.uniform(4, 9)
        self.fired = False

    def rect(self):
        return pygame.Rect(int(self.x - self.HW / 2), GROUND_Y - self.HH, self.HW, self.HH)

    def say(self, world, text, voiced=True):
        self.bubble, self.bubble_t = text, 2.2
        if voiced and abs(self.x - world.p.x) < 700:
            speak(text)

    def sees(self, p):
        if p.hidden or not p.alive:
            return False
        dx, dy = p.x - self.x, abs(p.y - GROUND_Y)
        if dy > 80:
            return False
        if self.alert > 0:
            return abs(dx) < 520
        return abs(dx) < 60 or (dx * self.facing > 0 and abs(dx) < self.SIGHT)

    def die(self, world):
        if not self.alive:
            return
        self.alive = False
        self.dead_t = 0.0
        self.bubble_t = 0.0
        sound.play("stab")
        world.burst(self.x, GROUND_Y - 34, (200, 30, 40), 14, 190, 0.7)
        world.burst(self.x, GROUND_Y - 30, (210, 215, 235), 8, 120, 0.6, grav=-40, r=4)

    def update(self, dt, p, world):
        self.anim_t += dt
        if not self.alive:
            self.dead_t += dt
            return
        self.alert = max(0.0, self.alert - dt)
        self.excl = max(0.0, self.excl - dt)
        self.bubble_t = max(0.0, self.bubble_t - dt)
        dx = p.x - self.x
        see = self.sees(p)

        if self.state == "patrol":
            if self.pause > 0:
                self.pause -= dt
            else:
                self.x += self.facing * self.PATROL * dt
                if self.x <= self.x0:
                    self.x, self.facing, self.pause = self.x0, 1, 0.9
                elif self.x >= self.x1:
                    self.x, self.facing, self.pause = self.x1, -1, 0.9
            self.chat -= dt
            if self.chat <= 0:
                self.chat = random.uniform(7, 12)
                if self.bubble_t <= 0 and abs(self.x - world.p.x) < 520:
                    self.say(world, random.choice(self.chat_lines))
            if see:
                self.state, self.timer, self.excl = "aim", self.AIM, 0.8
                self.facing = 1 if dx > 0 else -1
                sound.play("alert", 0.7)
                self.say(world, random.choice(self.spot_lines))
        elif self.state == "aim":
            self.timer -= dt
            if abs(dx) > 8:
                self.facing = 1 if dx > 0 else -1
            if self.timer <= 0:
                self.state, self.timer, self.fired = "shoot", self.SHOOT, False
        elif self.state == "shoot":
            if not self.fired:
                self.fired = True
                world.bullets.append({"x": self.x + self.facing * 34, "y": GROUND_Y - 41,
                                      "vx": self.facing * 720.0, "life": 1.3})
                sound.play("gunshot", 0.9)
                world.shake = max(world.shake, 0.08)
            self.timer -= dt
            if self.timer <= 0:
                self.state, self.timer = "recover", self.RECOVER
        elif self.state == "recover":
            self.timer -= dt
            if self.timer <= 0:
                if see:
                    self.state, self.timer = "aim", self.AIM * 0.8
                    self.facing = 1 if dx > 0 else -1
                    if self.bubble_t <= 0:
                        self.say(world, "Don't move!", voiced=False)
                else:
                    self.state, self.pause = "patrol", 0.6

    def draw(self, surf, cam, t):
        x = self.x - cam
        if x < -120 or x > WIDTH + 120:
            return
        if not self.alive:
            alpha = clamp(255 - (self.dead_t - 1.4) * 180, 0, 255)
            if alpha > 0:
                SP.draw_guard(surf, x, GROUND_Y, self.facing, t, "dead", alpha=alpha)
            return
        ap, anim = 0.0, "walk"
        if self.state == "patrol":
            anim = "idle" if self.pause > 0 else "walk"
        elif self.state == "aim":
            anim, ap = "aim", clamp(1 - self.timer / self.AIM, 0, 1)
        elif self.state == "shoot":
            anim = "shoot"
        elif self.state == "inv":
            anim = "walk"
        else:
            anim = "recover"
        SP.draw_guard(surf, x, GROUND_Y, self.facing, self.anim_t, anim, ap)
        if self.state == "aim" or self.excl > 0:
            img = get_font(30).render("!", True, (255, 60, 60) if self.state == "aim" else GOLD)
            surf.blit(img, img.get_rect(center=(x, GROUND_Y - 108)))
        if self.bubble_t > 0:
            SP.draw_speech(surf, self.bubble, (x, GROUND_Y - 118), get_font(16), shake=0.0)


# ------------------------------------------------------------------
# Player
# ------------------------------------------------------------------
class Player:
    W, H = 26, 54

    def __init__(self, x):
        self.x, self.y = x, GROUND_Y
        self.vx = self.vy = 0.0
        self.on_ground = True
        self.facing = 1
        self.health = START_HEALTH
        self.alive = True
        self.hidden = False
        self.hide_e = 1.0
        self.hide_lock = False
        self.inv = self.knife_cd = self.knife_t = self.punch_cd = 0.0
        self.jump_buf = self.coyote = 0.0
        self.punch_wind = 0.0
        self.punch_fired = False
        self.flash = 0.0
        self.spin = 0.0

    def rect(self):
        return pygame.Rect(int(self.x - self.W / 2), int(self.y - self.H), self.W, self.H)


def cycle_tool(idx, d):
    """Unlock kora tool er moddhe ghure ashe."""
    if idx not in TL.UNLOCKED:
        return TL.UNLOCKED[0]
    k = TL.UNLOCKED.index(idx)
    return TL.UNLOCKED[(k + d) % len(TL.UNLOCKED)]


# ------------------------------------------------------------------
# World = pura level
# ------------------------------------------------------------------
class World:
    def __init__(self, save, save_fn):
        self.save, self.save_fn = save, save_fn
        self.back = Backdrop()
        self.f_small, self.f_med, self.f_big = get_font(16), get_font(22), get_font(54)
        self.wheel_ui = TL.ToolWheel()
        self.restart()

    # ---------------- tool (select korle animation) ----------------
    @property
    def tool(self):
        return self._tool

    @tool.setter
    def tool(self, v):
        old = getattr(self, "_tool", None)
        self._tool = v
        if old is not None and old != v and not getattr(self, "_quiet_tool", False):
            self.tool_t0 = time.time()
            sound.play("pop", 0.5)

    # ---------------- state ----------------
    def restart(self):
        self._tool = None
        self.tool_t0 = -9.0
        self.tut = FX.Tutorial()
        self.pages = {}              # collect kora PAGE (code lock er code): key -> (label, code)
        self.p = Player(SPAWN_X)
        self.guards = [Guard(a, b) for a, b in GUARDS]
        self.cams = [Camera(x, ph) for x, ph in CAMERAS]
        self.laser_broken = [False] * len(LASER_X)
        self.term_open = False
        self.vault_open = 0.0
        self.lives = START_LIVES
        self.money = int(self.save.get("money", 0))
        self.got = [False] * len(STAR_POS)
        self.cash_taken = [False] * len(CASH)
        self.cp_idx = -1
        self.cp_on = [False] * len(CHECKPOINTS)
        self.state = "play"          # play | dying | over | win | rec | police | jail
        self.state_t = 0.0
        self.t = 0.0
        self.cam = clamp(self.p.x - WIDTH * 0.38, 0, LEVEL_W - WIDTH)
        self.shake = 0.0
        self.red_flash = 0.0
        self.bullets, self.waves, self.parts, self.floats = [], [], [], []
        self.run_deaths = 0
        self.arrests = 0
        self.toast, self.toast_t = "", 0.0
        self.hint_i, self.hint_t = -1, 0.0
        self.paused = False
        self.tool = TL.UNLOCKED[0]
        self.wheel = False
        self.wheel_sel = self.tool
        self.hack = None
        self.modal = None            # None | {"li","ci","err","done"}
        self.prompt = None
        self.rec_cam = 0
        self.car_x = 0.0
        self.car_dir = -1
        self.jail_paid = False
        self.won_loot = 0
        self.bail = BAIL
        self.hints = HINTS
        self.ledges = LEDGES
        self.level_w = LEVEL_W
        self.win_title = "DIAMOND STOLEN!"
        self.god = bool(self.save.get("god", False))      # PC / laptop er secret code theke chalu thakte pare
        self.stun_t = self.electric_cd = self.star_cd = self.auto_t = 0.0      # Special Tools
        self.stars_proj, self.autotype = [], False
        self.last_safe = self.p.x
        self.looted_before = False
        self.bonus_prior, self.bonus_new = set(), set()
        self.kill_cd = 0.0
        self._prog = False          # progress (nilo jinish) ekhono apply hoyni

    JAIL3 = False                  # True hole jail e 3 ta option (PAY 10000 / WAIT 1 MIN / BREAK OUT)  - level 14, 15, 3D

    def enter_jail(self):
        """Dhora porle jail e jao.  JAIL3 hole 3 option screen, nahole ager bail / 5 din."""
        if self.JAIL3:
            import jail as _jail
            self.state, self.state_t = "jail3", 0.0
            self.jail_ui = _jail.JailUI(self.money, pay_cost=getattr(self, "JAIL_PAY", _jail.PAY_COST))
            sound.play("jail")
            return
        self.state, self.state_t = "jail", 0.0
        self.jail_paid = self.money >= self.bail
        if self.jail_paid:
            self.money -= self.bail
        sound.play("jail")

    def say(self, text):
        self.toast, self.toast_t = text, 2.2

    def burst(self, x, y, color, n=10, speed=140, life=0.6, grav=320, r=3):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.3, 1.0) * speed
            self.parts.append({"x": x, "y": y, "vx": math.cos(a) * v, "vy": math.sin(a) * v - speed * 0.3,
                               "life": life * random.uniform(0.6, 1.0), "max": life, "c": color, "r": r, "g": grav})
        if len(self.parts) > 400:
            del self.parts[:100]

    # ---------------- solids ----------------
    def solids(self):
        out = [pygame.Rect(-200, GROUND_Y, LEVEL_W + 400, 400)]
        for x, br in zip(LASER_X, self.laser_broken):
            if not br:
                out.append(pygame.Rect(x - 8, LASER_TOP, 16, GROUND_Y - LASER_TOP))
        if self.vault_open < 0.6:
            out.append(pygame.Rect(VAULT_X - 22, CEIL_Y, 44, GROUND_Y - CEIL_Y))
        return out

    # ---------------- player events ----------------
    def press_jump(self):
        self.p.jump_buf = 0.12

    def can_do(self):
        p = self.p
        return self.state == "play" and not p.hidden and p.punch_wind <= 0 and self.hack is None and not self.modal and not getattr(self, "melt", None)

    def press_knife(self):
        p = self.p
        if not self.can_do() or p.knife_cd > 0:
            return
        p.knife_cd, p.knife_t = KNIFE_CD, KNIFE_T
        sound.play("stab", 0.8)
        reach = pygame.Rect(0, int(p.y - 62), KNIFE_REACH + 14, 66)
        if p.facing > 0:
            reach.left = int(p.x - 6)
        else:
            reach.right = int(p.x + 6)
        for g in self.guards:
            if g.alive and reach.colliderect(g.rect()):
                g.die(self)
                self.floats.append({"x": g.x, "y": GROUND_Y - 90, "t": 1.0, "txt": "KNIFE!", "c": (255, 120, 120)})

    def press_punch(self):
        p = self.p
        if not self.can_do() or not p.on_ground or p.punch_cd > 0:
            return
        p.punch_wind, p.punch_fired = PUNCH_WIND, False

    def do_punch(self):
        p = self.p
        p.punch_cd = PUNCH_CD
        p.punch_fired = True
        sound.play("punch")
        self.shake = 0.35
        self.waves.append({"x": p.x, "y": p.y, "t": 0.0})
        for g in self.guards:
            if g.alive and abs(g.x - p.x) <= PUNCH_RADIUS and abs(p.y - GROUND_Y) < 90:
                g.die(self)
        for i in range(24):
            d = random.choice((-1, 1))
            self.parts.append({"x": p.x + d * random.uniform(10, 40), "y": p.y - 4, "vx": d * random.uniform(60, 420),
                               "vy": -random.uniform(40, 200), "life": 0.6, "max": 0.6, "c": (225, 225, 235),
                               "r": random.randint(2, 4), "g": 600})

    def hurt_player(self, direction, cause="shot"):
        p = self.p
        if p.inv > 0 or not p.alive or self.state != "play" or self.god:
            return
        p.health -= 1
        p.inv, p.flash = 1.3, 0.3
        p.vx, p.vy, p.on_ground = direction * 260, -300, False
        self.hack = None
        self.shake, self.red_flash = 0.25, 0.25
        sound.play("hurt")
        self.burst(p.x, p.y - 30, (230, 40, 60), 10, 170, 0.5)
        if p.health <= 0:
            self.kill(cause)

    def kill(self, cause):
        p = self.p
        if self.state != "play":
            return
        if self.god:
            p.x, p.y, p.vx, p.vy, p.on_ground, p.inv = self.last_safe, GROUND_Y, 0.0, 0.0, True, 1.0
            return
        self.state, self.state_t = "dying", 0.0
        p.alive, p.hidden = False, False
        p.vy = -520
        p.vx = -p.facing * 140
        self.lives -= 1
        self.run_deaths += 1
        self.hack = None
        self.modal = None
        self.save["deaths"] = self.save.get("deaths", 0) + 1
        self.save_fn()
        sound.play("die")
        self.red_flash, self.shake = 0.4, 0.3
        self.burst(p.x, p.y - 30, (230, 40, 60), 16, 200, 0.8)

    def respawn(self):
        p = Player(CHECKPOINTS[self.cp_idx] if self.cp_idx >= 0 else SPAWN_X)
        p.inv = 1.5
        self.p = p
        for g in self.guards:
            if g.alive:
                g.calm()
                g.x = clamp(g.x, g.x0, g.x1)
        for c in self.cams:
            c.danger, c.beeped = 0.0, False
        self.bullets.clear()
        self.waves.clear()
        self.hack = None
        self.modal = None
        self.state, self.state_t = "play", 0.0
        self.cam = clamp(p.x - WIDTH * 0.38, 0, LEVEL_W - WIDTH)

    # ---------------- tools ----------------
    def targets(self):
        """Kache kon kon jinish use kora jay."""
        p = self.p
        out = {}
        best = 99999
        for i, c in enumerate(self.cams):
            d = abs(c.x - p.x)
            if not c.hacked and d < 280 and d < best:
                best, out["hacker"] = d, i
        best = 99999
        for i, x in enumerate(LASER_X):
            d = abs(x - p.x)
            if not self.laser_broken[i] and d < 120 and d < best:
                best, out["laser"] = d, i
        if abs(TERMINAL_X - p.x) < 80 and not self.term_open:
            out["laptop"] = 0
        return out

    def update_modal(self, dt):
        """Code type korar somoy: shob pause, shudhu typing ar 'ACCESS GRANTED' chole."""
        m = self.modal
        m["err"] = max(0.0, m["err"] - dt)
        m["age"] = m.get("age", 0.0) + dt
        if m.get("pad"):
            m["pad"].update(dt)
        if m.get("os") and (not m.get("usb") or m["age"] >= FX.USB_TIME):
            m["os"].update(dt)
            if m["os"].want_close:
                self.close_modal()
                sound.play("back")
                return
        if m["done"] > 0:
            m["done"] += dt
            if m["done"] > 1.3:
                self.close_modal()
                self.finish_modal(m)

    GOAL_TEXT = "Open the vault with the LAPTOP, steal the DIAMOND and run to the exit."

    def open_modal(self, kind, lines, target, title, os=None):
        self.modal = {"kind": kind, "lines": lines, "li": 0, "ci": 0, "err": 0.0, "done": 0.0,
                      "target": target, "title": title, "age": 0.0}
        self.p.vx = 0
        if os is None:
            os = kind in ("laptop", "laptop_free")
        if os:
            m = self.modal
            m["usb"] = kind != "laptop_free"          # terminal er shamne: USB lagano 3D animation age
            m["os"] = LP.LaptopOS(title, lines, self.os_info, self.toggle_god,
                                  lambda: m.__setitem__("done", max(m["done"], 0.01)), world=self,
                                  free=(kind == "laptop_free"))
            sound.play("pop")
        else:
            sound.play("key")

    def close_modal(self):
        """Laptop / typing window bondho. Notepad er draft save hoye jay."""
        m = self.modal
        self.modal = None
        if m and m.get("os"):
            try:
                m["os"].shutdown()
            except Exception:
                pass

    # ---------- nilo jinish (diamond / cash / star) replay te ar thakbe na ----------
    def level_key(self):
        mod = type(self).__module__
        return mod if mod.startswith("level") else "x"

    def apply_progress(self):
        """Ager bar win korar somoy je jinish nilo (loot, cash, star, safe), ekhon sheta nei.
        Je gulo nei ni, shegulo thakbe."""
        self._prog = True
        rec = self.save.get("taken", {}).get(self.level_key())
        self.bonus_prior, self.bonus_new = set(), set()
        if not rec:
            return
        for i, v in enumerate(rec.get("got", [])):
            if v and i < len(self.got):
                self.got[i] = True
        for i, v in enumerate(rec.get("cash", [])):
            if v and i < len(self.cash_taken):
                self.cash_taken[i] = True
        self.bonus_prior = set(rec.get("bonus", []))
        if rec.get("loot"):
            self.looted_before = True
            self.preset_loot()
        self.say("REPLAY  -  taken loot / cash / stars are gone")

    def preset_loot(self):
        """Loot ager bar niye felechhe: level er moto kore 'loot nawa' dhorbe."""

    def commit_progress(self):
        """Win korle je jinish nilo seta save e likhe rakho."""
        t = self.save.setdefault("taken", {})
        rec = t.setdefault(self.level_key(), {"loot": False, "got": [], "cash": [], "bonus": []})
        rec["loot"] = True
        for key, arr in (("got", self.got), ("cash", self.cash_taken)):
            old = rec.get(key, [])
            rec[key] = [bool(arr[i]) or (i < len(old) and bool(old[i])) for i in range(len(arr))]
        rec["bonus"] = sorted(set(rec.get("bonus", [])) | set(self.bonus_new) | set(self.bonus_prior))

    def tick_meta(self, dt):
        if not self._prog:
            self.apply_progress()
        if self.state == "play" and not self.paused and not self.modal:
            self.kill_cd = max(0.0, self.kill_cd - dt)

    # ---------- laptop: Task Manager e alert process ----------
    def os_alerts(self):
        """[(process nam, bornona, kill_fn)]  -  ekhon je alert cholche."""
        out = []
        al = [g for g in self.guards if g.alive and (g.state != "patrol" or g.alert > 0)]
        if al:
            def k_guard():
                for g in al:
                    g.calm()
            out.append(("guard_alert.exe", f"{len(al)} guard(s) on ALERT", k_guard))
        rec = [c for c in self.cams if c.danger > 0.05 and not getattr(c, "hacked", False)]
        if rec:
            def k_cam():
                for c in rec:
                    c.danger, c.beeped = 0.0, False
            out.append(("cctv_record.exe", f"{len(rec)} camera(s) RECORDING you", k_cam))
        if getattr(self, "siren_t", 0) > 0:
            out.append(("panic_siren.exe", f"building siren {self.siren_t:.0f}s",
                        lambda: setattr(self, "siren_t", 0.0)))
        if getattr(self, "extra_danger", 0) > 0.05:
            out.append(("police_dispatch.exe", "police being called",
                        lambda: setattr(self, "extra_danger", 0.0)))
        return out

    def kill_alert(self, fn):
        """True hole kill holo. Misuse thamate 25s cooldown."""
        if self.kill_cd > 0:
            return False
        fn()
        self.kill_cd = 25.0
        sound.play("hack")
        return True

    def remote_terminal(self):
        """Level er je terminal ekhono LOCKED, seta khulte hole je function call korte hobe (ba None).
        L chaple laptop kothao theke ei terminal hack kore - terminal er kache jete hoy na."""
        if self.term_open:
            return None
        return lambda: self.open_modal("laptop", TYPE_LINES, 0, "ABIX ONLINE CODER v1.0      TARGET: CITY BANK VAULT")

    def hotkey_laptop(self):
        """L (ba Ctrl+Alt+Tab): LAPTOP kholo.
        v9: terminal theke dure thakle laptop shudhu 'free' mode e khole - 'unlock all' kichu korbe na, 'no terminal found' dekhabe.
        Terminal er SHAMNE gele USB lagano 3D animation hoy, tarpor laptop on hoy ar terminal unlock kora jay."""
        if self.state != "play" or self.paused or self.modal or not self.can_do():
            return False
        idx = next(i for i, t in enumerate(TL.TOOLS) if t["id"] == "laptop")
        old = self.tool
        self._quiet_tool = True
        self.tool = idx
        if "laptop" in self.targets() and self.p.on_ground:      # terminal er shamne: USB animation + laptop
            self.use_tool()
        if not self.modal:                                       # terminal nei: shudhu free laptop (no terminal found)
            self.open_modal("laptop_free", [], None, "ABIX OS 11  -  no terminal found", os=True)
        self.tool = old
        self._quiet_tool = False
        return bool(self.modal)

    def open_pad(self, feature, title, code, kind="feature"):
        """CODE LOCK number pad. Code thik hole modal 'done' hoy -> finish_modal."""
        self.modal = {"kind": kind, "lines": [""], "li": 0, "ci": 0, "err": 0.0, "done": 0.0,
                      "target": None, "title": title, "feature": feature, "age": 0.0}
        m = self.modal
        m["pad"] = PZ.Keypad(title, code, self.pages, lambda: m.__setitem__("done", max(m["done"], 0.01)))
        self.p.vx = 0
        sound.play("pop")

    def open_cutter(self, feature, title):
        """WIRE CUTTER mini game (Level 3, 4, 5, 6, 8, 9).  Tar kata shesh hole modal 'done' hoy -> finish_modal."""
        self.modal = {"kind": "feature", "lines": [""], "li": 0, "ci": 0, "err": 0.0, "done": 0.0,
                      "target": None, "title": title, "feature": feature, "age": 0.0}
        m = self.modal
        m["pad"] = FX.WireCutGame(title, lambda: m.__setitem__("done", max(m["done"], 0.01)),
                                  theme=FX.CUTTER_THEME.get(self.level_key()))
        self.p.vx = 0
        sound.play("pop")

    def modal_event(self, e):
        m = self.modal
        if not m or m["done"] > 0:
            return
        if m.get("usb") and m.get("age", 0.0) < FX.USB_TIME:
            return                                    # USB animation cholar somoy input nei
        if m.get("pad"):
            m["pad"].event(e)
        elif m.get("os"):
            m["os"].event(e)
        else:
            self.type_key(getattr(e, "unicode", ""))

    def os_info(self):
        g = [x for x in self.guards if x.alive]
        cams = [c for c in self.cams if not c.hacked]
        dogs = [d for d in getattr(self, "dogs", []) if d.alive]
        got = sum(1 for x in self.got if x)
        loot = bool(getattr(self, "loot", False))
        scan = (f"guards {len(g)}/{len(self.guards)} alive, cameras online {len(cams)}/{len(self.cams)}, "
                f"dogs {len(dogs)}, stars {got}/{len(self.got)}, cash {self.money} Tk, loot "
                f"{'STOLEN - run to the exit!' if loot else 'not yet stolen'}.")
        x = self.p.x
        cur, nxt = None, None
        for a, b, txt in self.hints:
            if a <= x < b:
                cur = txt
            elif a > x and (nxt is None or a < nxt[0]):
                nxt = (a, txt)
        hint = cur or (nxt[1] if nxt else "Head for the exit with the loot.")
        return {"scan": scan, "goal": self.GOAL_TEXT, "hint": hint,
                "brief": f"Goal: {self.GOAL_TEXT}"}

    # ------------------------------------------------------------------
    # Special Tools (SPECIAL TOOLS screen theke kena): Ninja Star / Mini Code Writer / Electric
    # ------------------------------------------------------------------
    def owns(self, tid):
        return bool(self.save.get("special", {}).get(tid))

    def guard_dt(self):
        """Electric chalu thakle guard / kukur er shomoy thame jay (0), na hole 1."""
        return 0.0 if self.stun_t > 0 else 1.0

    def press_star(self):
        p = self.p
        if not self.owns("star"):
            self.say("NINJA STAR is locked  -  buy it in SPECIAL TOOLS")
            return
        if not self.can_do() or self.star_cd > 0:
            return
        self.star_cd = 0.45
        sound.play("throw")
        self.stars_proj.append({"x": p.x + p.facing * 24, "y": p.y - 44, "vx": p.facing * 900.0, "life": 0.9, "a": 0.0})

    def toggle_autotype(self):
        if not self.owns("code"):
            self.say("MINI CODE WRITER is locked  -  buy it in SPECIAL TOOLS")
            return
        self.autotype = not self.autotype
        sound.play("click")
        self.say("MINI CODE WRITER " + ("ON  -  it types codes for you" if self.autotype else "OFF"))

    def press_electric(self):
        if not self.owns("electric"):
            self.say("ELECTRIC is locked  -  buy it in SPECIAL TOOLS")
            return
        if self.state != "play" or self.paused or self.modal:
            return
        if self.electric_cd > 0:
            self.say(f"ELECTRIC is recharging  ({int(self.electric_cd) + 1}s)")
            return
        self.stun_t, self.electric_cd = 5.0, 30.0
        sound.play("zap")
        self.shake = 0.4
        self.say("ELECTRIC!  all guards are frozen for 5 seconds")

    def special_update(self, dt):
        if self.state != "play" or self.paused or self.wheel:
            return
        m = self.modal
        if m:
            # Mini Code Writer: jekhane code type korar dorkar (CCTV, laser, LAPTOP terminal, CODE LOCK) sekhane nijei likhe
            self.auto_label, self.auto_frac = "", 0.0
            if self.autotype and m["done"] <= 0 and m.get("age", 0.0) > FX.LID_TIME + (FX.USB_TIME if m.get("usb") else 0.0):
                if m.get("os"):
                    self.auto_laptop(m, dt)
                elif m.get("pad") and hasattr(m["pad"], "code"):
                    self.auto_pad(m, dt)
                elif m.get("pad"):
                    self.auto_label = "cut the wires yourself"
                else:
                    self.auto_t += dt
                    tot = max(1, sum(len(x) for x in m["lines"]))
                    self.auto_label = "writing code"
                    self.auto_frac = (sum(len(m["lines"][i]) for i in range(m["li"])) +
                                      (0 if m["li"] >= len(m["lines"]) else m["ci"])) / tot
                    while self.auto_t >= 0.06 and self.modal and self.modal["done"] <= 0:
                        self.auto_t -= 0.06
                        mm = self.modal
                        line = mm["lines"][mm["li"]] if mm["li"] < len(mm["lines"]) else ""
                        if mm["ci"] >= len(line):
                            break
                        self.type_key(line[mm["ci"]])
            return
        self.stun_t = max(0.0, self.stun_t - dt)
        self.electric_cd = max(0.0, self.electric_cd - dt)
        self.star_cd = max(0.0, self.star_cd - dt)
        for s_ in self.stars_proj[:]:
            s_["x"] += s_["vx"] * dt
            s_["life"] -= dt
            s_["a"] += dt * 25
            gone = s_["life"] <= 0 or not (0 <= s_["x"] <= self.level_w)
            for g in self.guards:
                if g.alive and g.rect().inflate(12, 12).collidepoint((s_["x"], s_["y"])):
                    g.die(self)
                    sound.play("hit")
                    self.floats.append({"x": g.x, "y": GROUND_Y - 90, "t": 1.0, "txt": "STAR!", "c": (200, 230, 255)})
                    gone = True
                    break
            if gone:
                self.stars_proj.remove(s_)

    # ---- AUTO CODE WRITER: laptop terminal (Python window) ----
    def auto_laptop(self, m, dt):
        os_ = m["os"]
        if os_.done or os_.boot < 1.8:
            return
        if os_.free:
            self.auto_label = "no locked terminal here"
            return
        if "py" in os_.hidden:
            return
        w = os_.wins.get("py")
        if not w or not w["open"] or w["min"]:
            os_.open_win("py")                       # Python window nijei khole
        os_.raise_win("py")
        os_.focus = "py"
        target = os_.accept[min(os_.prog, len(os_.accept) - 1)] if os_.accept else "unlock"
        self.auto_label = "writing: " + target[:24]
        self.auto_frac = (os_.prog + min(1.0, len(os_.py_in) / max(1, len(target)))) / max(1, len(os_.accept))
        self.auto_t += dt
        while self.auto_t >= 0.07:
            self.auto_t -= 0.07
            if os_.py_in != target[:len(os_.py_in)]:
                os_.py_in = ""                       # bhul likha thakle muche notun kore
            if len(os_.py_in) < len(target):
                os_.py_in += target[len(os_.py_in)]
                os_.key_flash = 0.12
                sound.play("key", 0.4)
            else:
                os_.run_py(os_.py_in)               # ENTER
                os_.py_in = ""
                break

    # ---- AUTO CODE WRITER: CODE LOCK keypad ----
    def auto_pad(self, m, dt):
        pad = m["pad"]
        known = {c for _, c in self.pages.values()}
        if pad.code not in known:
            self.auto_label = "find the PAGE with the code first"
            return
        if pad.ok or pad.err > 0:
            return
        self.auto_label = "typing code " + pad.code
        self.auto_frac = len(pad.entered) / max(1, len(pad.code))
        self.auto_t += dt
        while self.auto_t >= 0.22:
            self.auto_t -= 0.22
            if pad.entered != pad.code[:len(pad.entered)]:
                pad.press("C")
            elif len(pad.entered) < len(pad.code):
                pad.press(pad.code[len(pad.entered)])
            break

    def draw_special(self, surf):
        cam = self.cam
        for s_ in self.stars_proj:
            draw_shuriken(surf, (s_["x"] - cam, s_["y"]), 11, s_["a"], (225, 230, 245), (20, 22, 34))
        if self.stun_t > 0:
            for g in self.guards:
                if g.alive:
                    x = g.x - cam
                    pts = [(x + random.randint(-14, 14), GROUND_Y - 135 + i * 22) for i in range(7)]
                    pygame.draw.lines(surf, (130, 225, 255), False, pts, 3)
                    pygame.draw.circle(surf, (200, 245, 255), (int(x), GROUND_Y - 70), 40, 2)

    def draw_special_hud(self, surf):
        if self.state != "play":
            return
        rows = []
        if self.owns("star"):
            rows.append(("T / A   NINJA STAR", (225, 230, 245)))
        if self.owns("code"):
            rows.append(("C / R3   CODE WRITER " + ("ON" if self.autotype else "off"),
                         (110, 240, 150) if self.autotype else (150, 156, 180)))
        if self.owns("electric"):
            if self.stun_t > 0:
                rows.append((f"Q / LT   ELECTRIC  {self.stun_t:.1f}s", (130, 225, 255)))
            elif self.electric_cd > 0:
                rows.append((f"Q / LT   ELECTRIC  wait {int(self.electric_cd) + 1}s", (150, 156, 180)))
            else:
                rows.append(("Q / LT   ELECTRIC  ready", (255, 225, 90)))
        y = HEIGHT - 20 - 18 * len(rows)
        for txt, col in rows:
            img = get_font(13).render(txt, True, col)
            surf.blit(img, img.get_rect(topright=(WIDTH - 12, y)))
            y += 18

    def toggle_god(self):
        self.god = not self.god
        self.save["god"] = self.god
        if self.god:
            self.p.health = START_HEALTH
            self.burst(self.p.x, self.p.y - 40, (255, 220, 90), 40, 320, 1.0, grav=-60, r=4)
            self.say("GOD SUMMONED  -  nothing can touch you")
            voice.say("God summoned")
        else:
            self.say("God mode off")
        return self.god

    def finish_modal(self, m):
        """Code type shesh hole ki hobe."""
        k = m["kind"]
        if k == "laptop":
            self.term_open = True
            self.vault_open = max(self.vault_open, 0.001)
            self.say("VAULT OPENING!")
            sound.play("unlock")
        elif k == "camera":
            c = self.cams[m["target"]]
            c.hacked, c.danger = True, 0.0
            sound.play("hack")
            self.burst(c.x, CEIL_Y + 30, (90, 255, 200), 18, 200, 0.7, grav=100)
            self.say("CAMERA HACKED  -  DISABLED")
        elif k == "laser":
            i = m["target"]
            self.laser_broken[i] = True
            sound.play("laser")
            self.burst(LASER_X[i], GROUND_Y - 150, (255, 200, 90), 24, 260, 0.7, grav=300, r=3)
            self.say("LASER DISABLED")

    def use_tool(self):
        p = self.p
        if not self.can_do() or not p.on_ground:
            return
        tid = TL.TOOLS[self.tool]["id"]
        tg = self.targets()
        if tid == "cutter":
            self.say("WIRE CUTTER works only in Level " + FX.CUTTER_TEXT)
            return
        if tid in tg:
            if tid == "laser":
                self.open_modal("laser", [LASER_CODE], tg["laser"], "LASER BREAKER  -  type the code")
            elif tid == "hacker":
                self.open_modal("camera", [CAM_CODE], tg["hacker"], "CCTV HACK  -  LITE 3D  -  type the code")
            elif tid == "laptop":
                self.open_modal("laptop", TYPE_LINES, 0, "ABIX ONLINE CODER v1.0      TARGET: CITY BANK VAULT")
            return
        if tid not in ("laser", "hacker", "laptop"):
            self.say("Not needed in this level")
        elif tg:
            need = next(iter(tg))
            name = TL.tool_by_id(need)["name"]
            self.say(f"Need {name}  -  press Ctrl+Alt")
        elif tid == "laptop" and self.term_open:
            self.say("Vault is already open")
        else:
            self.say("Nothing to use here")

    def type_key(self, ch):
        m = self.modal
        if not m or m["done"] > 0 or not ch:
            return
        line = m["lines"][m["li"]]
        if ch.lower() == line[m["ci"]].lower():
            m["ci"] += 1
            sound.play("key", 0.5)
            if m["ci"] >= len(line):
                m["li"] += 1
                m["ci"] = 0
                if m["li"] >= len(m["lines"]):
                    m["done"] = 0.01
                    sound.play("unlock")
        else:
            m["err"] = 0.25
            sound.play("hover", 0.5)

    def record(self, cam_idx):
        if self.state != "play" or self.god:
            return
        self.state, self.state_t = "rec", 0.0
        self.rec_cam = cam_idx
        self.hack = None
        self.modal = None
        self.arrests += 1
        self.p.vx = 0
        self.p.hidden = False
        sound.play("alarm")
        sound.play("beep")
        near = min((g for g in self.guards if g.alive), key=lambda g: abs(g.x - self.p.x), default=None)
        if near:
            near.say(self, "I have CCTV footage in this place!")
        else:
            voice.say("I have CCTV footage in this place!")

    # ---------------- update ----------------
    def update(self, dt, keys):
        self.special_update(dt)
        if self.god and self.state == "play" and self.p.alive:
            self.p.inv = max(self.p.inv, 0.4)
            self.p.health = START_HEALTH
            for k in getattr(self, "cd", {}):
                self.cd[k] = 0.0
        if self.state == "play" and self.p.alive and self.p.on_ground and not self.modal:
            self.last_safe = self.p.x
        self.toast_t = max(0.0, self.toast_t - dt)
        self.shake = max(0.0, self.shake - dt)
        self.red_flash = max(0.0, self.red_flash - dt)
        modal_on = self.state == "play" and bool(self.modal)
        if not modal_on:                       # code type korar somoy shob thame (camera, guard, laser, kotha)
            self.t += dt
        if self.paused or self.wheel:
            return
        if modal_on:
            self.update_modal(dt)
            return
        self.state_t += dt
        for pt in self.parts:
            pt["life"] -= dt
            pt["x"] += pt["vx"] * dt
            pt["y"] += pt["vy"] * dt
            pt["vy"] += pt["g"] * dt
        self.parts = [pt for pt in self.parts if pt["life"] > 0]
        for w in self.waves:
            w["t"] += dt
        self.waves = [w for w in self.waves if w["t"] < 0.5]
        for f in self.floats:
            f["t"] -= dt
            f["y"] -= 34 * dt
        self.floats = [f for f in self.floats if f["t"] > 0]
        if self.vault_open > 0 and self.term_open:
            self.vault_open = min(1.0, self.vault_open + dt * 0.45)

        if self.state == "play":
            self.update_play(dt, keys)
        elif self.state == "dying":
            p = self.p
            p.vy = min(MAXFALL, p.vy + GRAV * dt)
            p.x += p.vx * dt
            p.y = min(GROUND_Y, p.y + p.vy * dt)
            p.spin += dt * 540
            if self.state_t > 1.4:
                if self.lives > 0:
                    self.respawn()
                else:
                    self.state, self.state_t = "over", 0.0
                    sound.stop_music(400)
                    sound.play("gameover")
        elif self.state == "rec":
            if self.state_t > 2.8:
                self.state, self.state_t = "police", 0.0
                self.car_dir = -1 if self.p.x < self.level_w - 700 else 1
                self.car_x = self.cam + WIDTH + 220 if self.car_dir < 0 else self.cam - 220
                sound.play("siren")
        elif self.state == "police":
            k = clamp(self.state_t / 2.4, 0, 1)
            tx = self.p.x + 120 * (-self.car_dir)
            start = self.cam + WIDTH + 220 if self.car_dir < 0 else self.cam - 220
            self.car_x = start + (tx - start) * (1 - (1 - k) ** 2)
            if self.state_t > 3.4:
                self.enter_jail()
        elif self.state == "jail3":
            self.jail_ui.update(dt)
            if self.jail_ui.result == "free":
                self.money = self.jail_ui.money
                self.jail_ui = None
                self.respawn()
        elif self.state == "jail":
            total = 3.6 if self.jail_paid else 1.2 + JAIL_DAYS * 0.65 + 1.4
            if self.state_t > total:
                self.respawn()
        elif self.state == "win":
            for g in self.guards:
                g.anim_t += dt

    def player_physics(self, dt, keys):
        """Abix er chola, lafano, hide, punch, modal (level 2 o eta bebohar kore)."""
        p = self.p
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        jump_held = keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]
        hide_held = keys[pygame.K_h] or keys[pygame.K_s] or keys[pygame.K_DOWN]
        busy = bool(self.modal) or self.hack is not None
        if self.modal:
            left = right = jump_held = hide_held = False
        p.inv = max(0.0, p.inv - dt)
        p.flash = max(0.0, p.flash - dt)
        p.knife_cd = max(0.0, p.knife_cd - dt)
        p.punch_cd = max(0.0, p.punch_cd - dt)
        p.knife_t = max(0.0, p.knife_t - dt)
        p.jump_buf = max(0.0, p.jump_buf - dt)

        # hack progress
        if self.hack is not None:
            self.hack["t"] += dt
            if self.hack["t"] >= HACK_TIME:
                c = self.cams[self.hack["i"]]
                c.hacked, c.danger = True, 0.0
                sound.play("hack")
                self.burst(c.x, CEIL_Y + 30, (90, 255, 200), 18, 200, 0.7, grav=100)
                self.say("CAMERA HACKED  -  DISABLED")
                self.hack = None

        # super punch
        if p.punch_wind > 0:
            p.punch_wind -= dt
            if not p.punch_fired and p.punch_wind <= 0.10:
                self.do_punch()
            if p.punch_wind <= 0:
                p.punch_wind = 0.0

        # hide
        if p.hide_lock and p.hide_e >= 0.35:
            p.hide_lock = False
        want = hide_held and p.on_ground and p.punch_wind <= 0 and not p.hide_lock and p.hide_e > 0 and not busy
        if want and not p.hidden:
            p.hidden = True
            sound.play("hide")
            self.burst(p.x, p.y - 20, (170, 180, 210), 10, 90, 0.5, grav=-60, r=5)
        elif not want and p.hidden:
            p.hidden = False
            self.burst(p.x, p.y - 20, (170, 180, 210), 8, 90, 0.4, grav=-60, r=4)
        if p.hidden:
            p.hide_e -= dt / 3.0
            if p.hide_e <= 0:
                p.hide_e, p.hidden, p.hide_lock = 0.0, False, True
                self.burst(p.x, p.y - 20, (170, 180, 210), 8, 90, 0.4, grav=-60, r=4)
        else:
            p.hide_e = min(1.0, p.hide_e + dt / 4.0)

        # move
        can_act = not p.hidden and p.punch_wind <= 0 and not busy
        target = 0.0
        if can_act:
            target = (int(bool(right)) - int(bool(left))) * SPEED
            if target:
                p.facing = 1 if target > 0 else -1
        accel = ACC_G if p.on_ground else ACC_A
        if not can_act:
            accel = 4200.0
        step = accel * dt
        p.vx += clamp(target - p.vx, -step, step)

        p.coyote = 0.09 if p.on_ground else p.coyote - dt
        if p.jump_buf > 0 and p.coyote > 0 and can_act:
            p.vy, p.on_ground, p.coyote, p.jump_buf = -JUMP_V, False, 0.0, 0.0
            sound.play("jump", 0.8)
            self.burst(p.x, p.y, (225, 225, 235), 5, 80, 0.3, r=2)
        if not jump_held and p.vy < -260:
            p.vy += 3200 * dt
        p.vy = min(MAXFALL, p.vy + GRAV * dt)
        was_air = not p.on_ground
        self.move_player(dt)
        if was_air and p.on_ground:
            self.burst(p.x, p.y, (225, 225, 235), 5, 90, 0.3, r=2)

    def update_play(self, dt, keys):
        self.player_physics(dt, keys)
        p = self.p

        # laser chhuile
        pr = p.rect().inflate(8, 0)
        for x, br in zip(LASER_X, self.laser_broken):
            if not br and pr.colliderect(pygame.Rect(x - 8, LASER_TOP, 16, GROUND_Y - LASER_TOP)):
                d = 1 if p.x > x else -1
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
        if p.y > HEIGHT + 90:
            self.kill("fell")
            return

        # checkpoint (locker)
        for i, cx in enumerate(CHECKPOINTS):
            if not self.cp_on[i] and abs(p.x - cx) < 46 and p.y > GROUND_Y - 90:
                self.cp_on[i] = True
                self.cp_idx = i
                p.health = START_HEALTH
                sound.play("checkpoint")
                self.burst(cx, GROUND_Y - 50, (90, 235, 255), 16, 200, 0.8, grav=-80)
                self.say("CHECKPOINT SAVED  -  health refilled")

        # star
        for i, (sx, sy) in enumerate(STAR_POS):
            if not self.got[i] and math.hypot(p.x - sx, (p.y - 28) - sy) < 34:
                self.got[i] = True
                sound.play("star")
                self.burst(sx, sy, GOLD, 18, 220, 0.8, grav=120)
                self.say(f"STAR {sum(self.got)} / {len(STAR_POS)}")

        # cash
        for i, (cx, cy) in enumerate(CASH):
            if not self.cash_taken[i] and abs(p.x - cx) < 30 and abs((p.y - 20) - cy) < 40:
                self.cash_taken[i] = True
                self.money += CASH_VALUE
                sound.play("cash")
                self.burst(cx, cy, (120, 255, 150), 12, 160, 0.6, grav=120)
                self.floats.append({"x": cx, "y": cy - 20, "t": 1.0, "txt": f"+{CASH_VALUE} Tk", "c": (120, 255, 150)})

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

        # CCTV
        pts = [(p.x, p.y - 30), (p.x, p.y - 8), (p.x, p.y - 50)]
        for i, c in enumerate(self.cams):
            seen = (not p.hidden) and p.alive and any(c.sees(self.t, q) for q in pts)
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

        # tool prompt
        self.prompt = None
        tid = TL.TOOLS[self.tool]["id"]
        tg = self.targets()
        if self.can_do():
            if tid in tg:
                self.prompt = (tid, tg[tid], True)
            elif tg:
                need = next(iter(tg))
                self.prompt = (need, tg[need], False)

        # diamond
        if self.vault_open >= 0.99 and abs(p.x - DIAMOND_X) < 48 and p.alive:
            self.state, self.state_t = "win", 0.0
            p.vx = 0
            p.hidden = False
            self.won_loot = 0 if self.looted_before else DIAMOND_REWARD
            self.money += self.won_loot
            sound.stop_music(500)
            sound.play("win")
            self.burst(DIAMOND_X, GROUND_Y - 90, (180, 235, 255), 44, 320, 1.2, grav=160, r=4)

        # hint
        hi = -1
        for i, (a, b, _) in enumerate(self.hints):
            if a <= p.x < b:
                hi = i
        if hi != self.hint_i:
            self.hint_i, self.hint_t = hi, 0.0
        self.hint_t += dt

        # camera
        tx = p.x - WIDTH * 0.38 + p.facing * 40
        self.cam += (tx - self.cam) * min(1.0, 7 * dt)
        self.cam = clamp(self.cam, 0, LEVEL_W - WIDTH)

    def move_player(self, dt):
        p = self.p
        sol = self.solids()
        p.x = clamp(p.x + p.vx * dt, 16, self.level_w - 16)
        r = p.rect()
        for s in sol:
            if s.top >= GROUND_Y:
                continue
            if r.colliderect(s):
                if p.vx > 0:
                    p.x = s.left - p.W / 2
                elif p.vx < 0:
                    p.x = s.right + p.W / 2
                else:
                    p.x += -1 if p.x < s.centerx else 1
                p.vx = 0
                r = p.rect()
        prev = p.y
        p.y += p.vy * dt
        p.on_ground = False
        if p.vy >= 0:                      # uporer pith e daray (float diye, jate flicker na kore)
            if prev <= GROUND_Y + 0.5 and p.y >= GROUND_Y:
                p.y, p.vy, p.on_ground = GROUND_Y, 0.0, True
            for x0, x1, y in self.ledges:
                if p.x + p.W / 2 > x0 and p.x - p.W / 2 < x1 and prev <= y + 2 and p.y >= y:
                    p.y, p.vy, p.on_ground = y, 0.0, True

    # ---------------- draw ----------------
    def draw_world(self, surf):
        cam = int(self.cam)
        t = self.t
        self.back.draw(surf, cam)
        draw_decor(surf, cam, t)
        draw_floor(surf, cam)
        for x0, x1, y in LEDGES:
            if x1 - cam > -20 and x0 - cam < WIDTH + 20:
                SP.draw_ledge(surf, x0 - cam, x1 - cam, y)
        for i, cx in enumerate(CHECKPOINTS):
            SP.draw_locker(surf, cx - cam, GROUND_Y, self.cp_on[i], t)
        # terminal ar vault
        SP.draw_terminal(surf, TERMINAL_X - cam, GROUND_Y, "open" if self.term_open else "locked", t)
        SP.draw_vault_door(surf, VAULT_X - cam, GROUND_Y, CEIL_Y, self.vault_open, t)
        # diamond (pedestal e)
        px = DIAMOND_X - cam
        if self.state != "win":
            pygame.draw.rect(surf, (70, 72, 90), (px - 26, GROUND_Y - 52, 52, 52))
            pygame.draw.rect(surf, (150, 154, 176), (px - 30, GROUND_Y - 58, 60, 8), border_radius=2)
            if not self.looted_before:
                SP.draw_diamond(surf, (px, GROUND_Y - 96), 48, t)
            gs = pygame.Surface((54, 62), pygame.SRCALPHA)
            gs.fill((170, 220, 255, 36))
            surf.blit(gs, (px - 27, GROUND_Y - 124))
            pygame.draw.rect(surf, (190, 225, 250), (px - 27, GROUND_Y - 124, 54, 62), 2)
        # laser
        for x, br in zip(LASER_X, self.laser_broken):
            if -40 < x - cam < WIDTH + 40:
                SP.draw_laser(surf, x - cam, LASER_TOP, GROUND_Y, br, t)
        # camera
        for c in self.cams:
            c.draw(surf, cam, t)
        # star / cash
        for i, (sx, sy) in enumerate(STAR_POS):
            if not self.got[i]:
                SP.draw_star_icon(surf, (sx - cam, sy + math.sin(t * 3 + i) * 5), 15, True, t, True)
        for i, (cx, cy) in enumerate(CASH):
            if not self.cash_taken[i] and -40 < cx - cam < WIDTH + 40:
                SP.draw_cash(surf, (cx - cam, cy), t)
        for g in self.guards:
            g.draw(surf, cam, t)
        if self.state in ("police",):
            SP.draw_police_car(surf, self.car_x - cam, GROUND_Y, self.car_dir, t)
        self.draw_player(surf, cam)
        for b in self.bullets:
            SP.draw_bullet(surf, b["x"] - cam, b["y"], 1 if b["vx"] > 0 else -1)
        for w in self.waves:
            k = w["t"] / 0.5
            rad = PUNCH_RADIUS * (1 - (1 - k) ** 2)
            h = 26 + 10 * k
            a = int(220 * (1 - k))
            sw = pygame.Surface((int(rad * 2) + 12, int(h * 2) + 12), pygame.SRCALPHA)
            pygame.draw.ellipse(sw, (255, 235, 160, a), sw.get_rect().inflate(-8, -8), 6)
            pygame.draw.ellipse(sw, (255, 255, 255, a // 2), sw.get_rect().inflate(-26, -26), 3)
            surf.blit(sw, sw.get_rect(center=(w["x"] - cam, w["y"] - 6)))
        for pt in self.parts:
            k = pt["life"] / pt["max"]
            r = max(1, int(pt["r"] * (0.4 + 0.6 * k)))
            pygame.draw.circle(surf, pt["c"], (int(pt["x"] - cam), int(pt["y"])), r)
        for f in self.floats:
            img = self.f_med.render(f["txt"], True, f["c"])
            img.set_alpha(int(255 * clamp(f["t"] / 0.4, 0, 1)))
            surf.blit(img, img.get_rect(center=(f["x"] - cam, f["y"])))
        self.draw_prompt(surf, cam)

    def draw_prompt(self, surf, cam):
        p = self.p
        if self.state != "play":
            return
        # recording er danger meter (Abix er matha r upor)
        dmax = max((c.danger for c in self.cams), default=0.0)
        if dmax > 0.02:
            w = 46
            r = pygame.Rect(0, 0, w, 7)
            r.center = (p.x - cam, p.y - 76)
            pygame.draw.rect(surf, (40, 20, 24), r.inflate(4, 4), border_radius=4)
            pygame.draw.rect(surf, (255, 60, 60), (r.x, r.y, int(w * dmax), r.h), border_radius=3)
            img = self.f_small.render("REC", True, (255, 70, 70))
            surf.blit(img, img.get_rect(midbottom=(r.centerx, r.y - 3)))
        if self.hack is not None:                                  # hack progress bar
            c = self.cams[self.hack["i"]]
            r = pygame.Rect(0, 0, 70, 8)
            r.center = (p.x - cam, p.y - 76)
            pygame.draw.rect(surf, (10, 30, 30), r.inflate(4, 4), border_radius=4)
            pygame.draw.rect(surf, (90, 255, 200), (r.x, r.y, int(r.w * self.hack["t"] / HACK_TIME), r.h), border_radius=3)
            img = self.f_small.render("HACKING...", True, (90, 255, 200))
            surf.blit(img, img.get_rect(midbottom=(r.centerx, r.y - 3)))
            lx, ly = c.lens(self.t)
            self.dashed(surf, (p.x - cam, p.y - 50), (lx - cam, ly), (90, 255, 200))
            return
        if not self.prompt:
            return
        kind, idx, ok = self.prompt
        if kind == "hacker":
            c = self.cams[idx]
            lx, ly = c.lens(self.t)
            col = (90, 255, 200) if ok else (150, 150, 170)
            self.dashed(surf, (p.x - cam, p.y - 50), (lx - cam, ly), col)
            mid = ((p.x + lx) / 2 - cam, (p.y - 50 + ly) / 2)
            lines = ["[E]  HACK CAMERA", "LITE 3D  -  type code"] if ok else ["Select HACKER", "Ctrl+Alt  or  key 2"]
        elif kind == "laser":
            mid = (LASER_X[idx] - cam, GROUND_Y - 170)
            col = (255, 200, 90) if ok else (150, 150, 170)
            lines = ["[E]  DISABLE LASER", "type code"] if ok else ["Select LASER BREAKER", "Ctrl+Alt  or  key 1"]
        else:
            mid = (TERMINAL_X - cam, GROUND_Y - 120)
            col = (120, 255, 150) if ok else (150, 150, 170)
            lines = ["[E]  USE LAPTOP", "type the code"] if ok else ["Select LAPTOP", "Ctrl+Alt  or  key 3"]
        imgs = [self.f_small.render(s, True, col) for s in lines]
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

    def dashed(self, surf, a, b, col):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        if d < 1:
            return
        n = int(d // 14)
        for i in range(n):
            k0, k1 = i / n, (i + 0.55) / n
            pygame.draw.line(surf, col, (a[0] + (b[0] - a[0]) * k0, a[1] + (b[1] - a[1]) * k0),
                             (a[0] + (b[0] - a[0]) * k1, a[1] + (b[1] - a[1]) * k1), 2)

    def draw_player(self, surf, cam):
        p = self.p
        x = p.x - cam
        t = self.t
        if self.god and self.state == "play":
            SP.glow(surf, (x, p.y - 30), 54 + 6 * math.sin(t * 6), (255, 215, 90), 90, 4)
        alpha, rot = 255, 0.0
        ap = 0.0
        if self.state == "dying":
            anim, rot = "air", p.spin
            alpha = clamp(255 - max(0, self.state_t - 0.7) * 380, 0, 255)
            if alpha <= 0:
                return
        elif self.state == "win":
            anim = "wave"
        elif self.state in ("police", "rec") or (self.state == "jail"):
            anim = "wave"
        elif p.hidden:
            anim, alpha = "hide", 105
            glow_a = 30 + int(20 * math.sin(t * 6))
            ring = pygame.Surface((70, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (160, 175, 210, glow_a + 30), ring.get_rect(), 3)
            surf.blit(ring, ring.get_rect(center=(x, p.y - 2)))
        elif self.hack is not None or self.modal or getattr(self, "melt", None):
            anim = "type"
        elif p.punch_wind > 0:
            anim, ap = "punch", 1 - p.punch_wind / PUNCH_WIND
        elif p.knife_t > 0:
            anim, ap = "stab", 1 - p.knife_t / KNIFE_T
        elif not p.on_ground:
            anim, ap = "air", clamp(p.vy / 500, -1, 1)
        elif abs(p.vx) > 40:
            anim = "run"
        else:
            anim = "idle"
        if p.inv > 0 and int(t * 22) % 2 == 0 and self.state == "play":
            alpha = min(alpha, 110)
        SP.draw_ninja(surf, x, p.y, p.facing, t, anim, ap, alpha, flash=p.flash, rot=rot)

    # ---------------- HUD ----------------
    def draw_knife_icon(self, surf, c):
        pygame.draw.polygon(surf, (210, 216, 232), [(c[0] - 14, c[1] + 8), (c[0] + 14, c[1] - 14), (c[0] + 16, c[1] - 8), (c[0] - 8, c[1] + 12)])
        pygame.draw.polygon(surf, (255, 255, 255), [(c[0] - 14, c[1] + 8), (c[0] + 14, c[1] - 14), (c[0] + 4, c[1] + 2)])
        pygame.draw.line(surf, (120, 70, 40), (c[0] - 16, c[1] + 14), (c[0] - 8, c[1] + 6), 6)
        pygame.draw.line(surf, GOLD, (c[0] - 10, c[1] + 4), (c[0] - 4, c[1] + 10), 3)

    def draw_hud(self, surf, mouse):
        p = self.p
        t = self.t
        for i in range(START_HEALTH):
            full = i < p.health
            SP.draw_heart(surf, (34 + i * 36, 30), 26, (235, 50, 80) if full else (50, 50, 70),
                          (255, 210, 220) if full else (90, 90, 115))
        lab = self.f_small.render("LIVES", True, (170, 170, 190))
        surf.blit(lab, (14, 56))
        for i in range(START_LIVES):
            c = (90 + i * 26, 64)
            on = i < self.lives
            pygame.draw.circle(surf, (24, 24, 40) if on else (50, 50, 70), c, 10)
            pygame.draw.rect(surf, RED if on else (80, 80, 100), (c[0] - 10, c[1] - 6, 20, 5))
            pygame.draw.circle(surf, WHITE if on else (110, 110, 130), c, 10, 2)

        for i in range(len(STAR_POS)):
            SP.draw_star_icon(surf, (WIDTH - 100 + i * 32, 28), 12, self.got[i], t)
        SP.draw_skull_coin(surf, (WIDTH - 98, 66), 14)
        dc = self.f_med.render(f"x {self.save.get('deaths', 0)}", True, GOLD)
        surf.blit(dc, dc.get_rect(midleft=(WIDTH - 76, 66)))
        dl = self.f_small.render("DEATHS", True, (170, 170, 190))
        surf.blit(dl, dl.get_rect(midright=(WIDTH - 124, 66)))
        SP.draw_tk_coin(surf, (WIDTH - 98, 102), 14)
        mc = self.f_med.render(f"{self.money} Tk", True, (110, 240, 150))
        surf.blit(mc, mc.get_rect(midleft=(WIDTH - 76, 102)))

        tid = TL.TOOLS[self.tool]["id"]
        slots = [("J", "KNIFE", p.knife_cd / KNIFE_CD, None), ("H", "HIDE", 0.0, p.hide_e),
                 ("K", "PUNCH", p.punch_cd / PUNCH_CD, None), ("E", "TOOL", 0.0, None)]
        for i, (key, name, cd, energy) in enumerate(slots):
            r = pygame.Rect(0, 0, 62, 62)
            r.center = (int(WIDTH // 2 + (i - 1.5) * 86), HEIGHT - 52)
            pygame.draw.rect(surf, (22, 22, 40), r, border_radius=12)
            c = r.center
            if i == 0:
                self.draw_knife_icon(surf, c)
            elif i == 1:
                pygame.draw.arc(surf, (170, 220, 255), (c[0] - 18, c[1] - 16, 36, 30), 0.3, math.pi - 0.3, 4)
                pygame.draw.line(surf, (170, 220, 255), (c[0] - 16, c[1] + 8), (c[0] + 16, c[1] - 12), 3)
            elif i == 2:
                pygame.draw.rect(surf, (255, 215, 130), (c[0] - 14, c[1] - 8, 28, 22), border_radius=6)
                for k in range(4):
                    pygame.draw.circle(surf, (255, 235, 175), (c[0] - 10 + k * 7, c[1] - 8), 4)
            else:
                SP.draw_tool_icon(surf, tid, (c[0], c[1] - 2), 20, t)
            if cd > 0:
                ov = pygame.Surface((r.w, int(r.h * min(1, cd))), pygame.SRCALPHA)
                ov.fill((0, 0, 0, 160))
                surf.blit(ov, r.topleft)
            if energy is not None:
                pygame.draw.rect(surf, (40, 50, 70), (r.x + 6, r.bottom - 12, r.w - 12, 6), border_radius=3)
                col = (90, 220, 255) if not p.hide_lock else (200, 90, 90)
                pygame.draw.rect(surf, col, (r.x + 6, r.bottom - 12, int((r.w - 12) * energy), 6), border_radius=3)
            ready = cd <= 0 and (energy is None or not p.hide_lock)
            pygame.draw.rect(surf, rgb_color(t, offset=i * 0.3) if ready else (80, 80, 105), r, 3, border_radius=12)
            kl = self.f_small.render(key, True, WHITE)
            surf.blit(kl, kl.get_rect(center=(r.centerx, r.top - 10)))
        FX.draw_tool_select(surf, TL.TOOLS[self.tool], time.time() - self.tool_t0, t)
        tn = self.f_small.render(f"TOOL: {TL.TOOLS[self.tool]['name']}      Ctrl+Alt / TAB = all tools",
                                 True, (170, 175, 200))
        surf.blit(tn, tn.get_rect(midbottom=(WIDTH // 2, HEIGHT - 6)))

        if self.hint_i >= 0 and self.state == "play":
            txt = self.hints[self.hint_i][2]
            a = clamp(self.hint_t / 0.3, 0, 1)
            img = self.f_med.render(txt, True, WHITE)
            box = img.get_rect().inflate(36, 18)
            box.midtop = (WIDTH // 2, 100 - int((1 - a) * 12))
            bg = pygame.Surface(box.size, pygame.SRCALPHA)
            pygame.draw.rect(bg, (10, 10, 24, int(180 * a)), bg.get_rect(), border_radius=14)
            pygame.draw.rect(bg, (255, 200, 70, int(255 * a)), bg.get_rect(), 2, border_radius=14)
            surf.blit(bg, box.topleft)
            img.set_alpha(int(255 * a))
            surf.blit(img, img.get_rect(center=box.center))

        if self.toast_t > 0:
            a = clamp(min(self.toast_t, 0.4) / 0.4, 0, 1)
            img = self.f_big.render(self.toast, True, GOLD) if len(self.toast) < 14 else get_font(30).render(self.toast, True, GOLD)
            img.set_alpha(int(255 * a))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 180 - int((1 - a) * -10))))

    # ---------------- modal / overlays ----------------
    def draw_laptop(self, surf):
        """Laptop / terminal / pad: dhakna khola 3D animation, tarpor normal."""
        m = self.modal
        age = m.get("age", 9.0)
        if m.get("usb"):
            if age < FX.USB_TIME:
                FX.draw_usb_plug(surf, age / FX.USB_TIME, self.t)
                return
            age -= FX.USB_TIME
        k = age / FX.LID_TIME
        if k < 1.0:
            tmp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            self._draw_modal(tmp)
            base = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            base.fill((0, 0, 0, int(190 * min(1.0, k * 2))))
            surf.blit(base, (0, 0))
            FX.lid_glow(surf, k, self.t)
            surf.blit(FX.warp_lid(tmp, k), (0, 0))
            FX.draw_deck(surf, self.t, min(1.0, k * 2))
            return
        self._draw_modal(surf)
        if m.get("os") or m.get("pad") is None:
            FX.draw_deck(surf, self.t, 1.0)
        if self.autotype and m["done"] <= 0 and getattr(self, "auto_label", ""):
            FX.draw_autowriter(surf, self.auto_label, getattr(self, "auto_frac", 0.0), time.time())

    def _draw_modal(self, surf):
        m = self.modal
        if m.get("pad"):
            m["pad"].draw(surf)
            return
        if m.get("os"):
            m["os"].draw(surf)
            return
        lines = m["lines"]
        self._dim(surf, 190)
        body = pygame.Rect(130, 60, 700, 400)
        pygame.draw.rect(surf, (38, 40, 50), body.inflate(30, 30), border_radius=22)
        pygame.draw.rect(surf, (90, 94, 110), body.inflate(30, 30), 3, border_radius=22)
        pygame.draw.rect(surf, (4, 12, 8), body, border_radius=8)
        f = pygame.font.SysFont("couriernew,monospace", 24 if len(lines) > 1 else 32, bold=True)
        fs = pygame.font.SysFont("couriernew,monospace", 16, bold=True)
        surf.blit(fs.render(m["title"], True, (60, 200, 110)), (body.x + 18, body.y + 14))
        pygame.draw.line(surf, (30, 90, 56), (body.x + 14, body.y + 40), (body.right - 14, body.y + 40), 1)
        y = body.y + (70 if len(lines) > 1 else 120)
        for i, line in enumerate(lines):
            if i < m["li"]:
                surf.blit(f.render("OK ", True, (60, 255, 120)), (body.x + 18, y))
                surf.blit(f.render(line, True, (50, 160, 90)), (body.x + 70, y))
            elif i == m["li"] and m["done"] <= 0:
                surf.blit(f.render("> ", True, (255, 220, 90)), (body.x + 18, y))
                done = f.render(line[:m["ci"]], True, (230, 255, 235))
                rest = f.render(line[m["ci"]:], True, (110, 150, 120) if m["err"] <= 0 else (230, 70, 70))
                surf.blit(done, (body.x + 70, y))
                surf.blit(rest, (body.x + 70 + done.get_width(), y))
                if int(time.time() * 2) % 2 == 0:
                    pygame.draw.rect(surf, (230, 255, 235), (body.x + 70 + done.get_width(), y + 34, 14, 3))
            else:
                surf.blit(f.render("  " + line, True, (36, 60, 44)), (body.x + 52, y))
            y += 58
        total = sum(len(s_) for s_ in lines)
        typed = sum(len(lines[i]) for i in range(m["li"])) + (0 if m["li"] >= len(lines) else m["ci"])
        bar = pygame.Rect(body.x + 18, body.bottom - 66, body.w - 36, 14)
        pygame.draw.rect(surf, (14, 40, 28), bar, border_radius=7)
        pygame.draw.rect(surf, (60, 255, 120), (bar.x, bar.y, int(bar.w * typed / total), bar.h), border_radius=7)
        if m["done"] > 0:
            img = get_font(34).render("ACCESS GRANTED", True, (60, 255, 120))
            surf.blit(img, img.get_rect(center=(body.centerx, body.bottom - 28)))
        else:
            surf.blit(fs.render("Type the code exactly.   ESC = cancel", True, (120, 160, 130)), (body.x + 18, body.bottom - 36))

    def draw_rec_feed(self, surf):
        """LITE 3D - camera record (green night-vision feed)."""
        a = clamp(self.state_t / 0.3, 0, 1)
        self._dim(surf, int(180 * a))
        feed = pygame.Rect(190, 80, 580, 360)
        pygame.draw.rect(surf, (20, 22, 26), feed.inflate(24, 24), border_radius=14)
        fs = pygame.Surface(feed.size)
        SP.v_gradient(fs, fs.get_rect(), (10, 40, 22), (6, 22, 14))
        for gx in range(0, feed.w, 40):                              # 3D grid floor
            pygame.draw.line(fs, (14, 70, 36), (gx, 250), (feed.w // 2 + (gx - feed.w // 2) * 2.4, feed.h), 1)
        for gy in range(250, feed.h, 28):
            pygame.draw.line(fs, (14, 70, 36), (0, gy), (feed.w, gy), 1)
        pygame.draw.line(fs, (30, 130, 70), (0, 250), (feed.w, 250), 2)
        tmp = pygame.Surface((SP.TW, SP.TH), pygame.SRCALPHA)
        SP.draw_ninja(tmp, SP.OX, SP.OY, self.p.facing, self.t, "wave")
        big = pygame.transform.smoothscale(tmp, (SP.TW * 3, SP.TH * 3))
        big.fill((90, 255, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)
        fs.blit(big, big.get_rect(midbottom=(feed.w // 2, feed.h - 20)))
        for y in range(0, feed.h, 4):
            pygame.draw.line(fs, (0, 0, 0), (0, y), (feed.w, y))
        for _ in range(60):
            fs.set_at((random.randint(0, feed.w - 1), random.randint(0, feed.h - 1)), (120, 255, 160))
        surf.blit(fs, feed.topleft)
        pygame.draw.rect(surf, (60, 200, 110), feed, 3)
        f = pygame.font.SysFont("couriernew,monospace", 20, bold=True)
        if int(self.t * 2.5) % 2 == 0:
            pygame.draw.circle(surf, (255, 40, 40), (feed.x + 26, feed.y + 28), 9)
        surf.blit(f.render("REC", True, (255, 80, 80)), (feed.x + 42, feed.y + 17))
        surf.blit(f.render(f"CAM 0{self.rec_cam + 1}   LITE 3D", True, (150, 255, 190)), (feed.right - 230, feed.y + 17))
        surf.blit(f.render("SUBJECT RECORDED", True, (255, 220, 90)), (feed.x + 16, feed.bottom - 34))
        img = get_font(40).render("RECORDED!  POLICE ARE COMING", True, RED)
        sh = get_font(40).render("RECORDED!  POLICE ARE COMING", True, (0, 0, 0))
        surf.blit(sh, sh.get_rect(center=(WIDTH // 2 + 2, 482)))
        surf.blit(img, img.get_rect(center=(WIDTH // 2, 480)))

    def draw_jail(self, surf):
        k = clamp(self.state_t / 0.4, 0, 1)
        surf.fill((14, 14, 22))
        SP.v_gradient(surf, pygame.Rect(0, 0, WIDTH, HEIGHT), (34, 36, 46), (14, 14, 22))
        win = pygame.Rect(660, 70, 130, 100)
        pygame.draw.rect(surf, (12, 16, 40), win)
        pygame.draw.circle(surf, (230, 232, 210), (win.x + 90, win.y + 34), 14)
        pygame.draw.rect(surf, (80, 84, 96), win, 5)
        pygame.draw.rect(surf, (110, 90, 70), (120, 350, 220, 20), border_radius=4)           # bench
        SP.draw_ninja(surf, 230, 350, 1, self.t, "idle")
        pygame.draw.rect(surf, (28, 28, 38), (0, 440, WIDTH, 100))
        for bx in range(40, WIDTH, 74):                                                       # bars
            pygame.draw.rect(surf, (96, 100, 116), (bx, 0, 14, HEIGHT))
            pygame.draw.rect(surf, (170, 176, 196), (bx + 2, 0, 4, HEIGHT))
        pygame.draw.rect(surf, (60, 62, 74), (0, 120, WIDTH, 12))
        pygame.draw.rect(surf, (60, 62, 74), (0, 380, WIDTH, 12))
        box = pygame.Rect(0, 0, 640, 250)
        box.center = (WIDTH // 2, 262)
        bg = pygame.Surface(box.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (6, 8, 16, 226), bg.get_rect(), border_radius=18)
        pygame.draw.rect(bg, (230, 90, 90, 255), bg.get_rect(), 3, border_radius=18)
        surf.blit(bg, box.topleft)
        self._title(surf, "ARRESTED!", box.y + 40, RED)
        st = self.state_t
        if self.jail_paid:
            lines = [(f"BAIL PAID:  -{self.bail} Tk", (255, 220, 90)), (f"Money left:  {self.money} Tk", (110, 240, 150))]
            for i, (s_, c_) in enumerate(lines):
                img = self.f_med.render(s_, True, c_)
                surf.blit(img, img.get_rect(center=(WIDTH // 2, box.y + 100 + i * 34)))
            if st > 1.6:
                img = self.f_med.render("You are free.  DO IT  -  go to your DREAM PLACE!", True, WHITE)
                surf.blit(img, img.get_rect(center=(WIDTH // 2, box.y + 200)))
        else:
            img = self.f_med.render(f"No money for bail!  ({self.bail} Tk needed)", True, (255, 130, 130))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, box.y + 94)))
            days = int(clamp((st - 1.0) / 0.65, 0, JAIL_DAYS))
            for d in range(JAIL_DAYS):
                r = pygame.Rect(0, 0, 76, 62)
                r.center = (WIDTH // 2 + (d - 2) * 92, box.y + 150)
                pygame.draw.rect(surf, (230, 232, 240), r, border_radius=8)
                pygame.draw.rect(surf, (90, 94, 110), r, 3, border_radius=8)
                lab = self.f_small.render(f"DAY {d + 1}", True, (40, 40, 60))
                surf.blit(lab, lab.get_rect(midtop=(r.centerx, r.y + 6)))
                if d < days:
                    pygame.draw.line(surf, RED, (r.x + 10, r.y + 22), (r.right - 10, r.bottom - 8), 6)
                    pygame.draw.line(surf, RED, (r.x + 10, r.bottom - 8), (r.right - 10, r.y + 22), 6)
            if days >= JAIL_DAYS and st > 1.0 + JAIL_DAYS * 0.65 + 0.2:
                img = self.f_med.render("5 days served.  DO IT  -  go to your DREAM PLACE!", True, WHITE)
                surf.blit(img, img.get_rect(center=(WIDTH // 2, box.y + 214)))
        if k < 1:
            fade_overlay(surf, 1 - k)

    def menu(self, surf, labels, sel, mouse, top=215):
        rects = []
        for i, lab in enumerate(labels):
            r = pygame.Rect(0, 0, 320, 56)
            r.center = (WIDTH // 2, top + i * 72)
            hot = i == sel
            col = rgb_color(self.t, offset=i * 0.3)
            pygame.draw.rect(surf, col if hot else (34, 34, 58), r.inflate(16, 6) if hot else r, border_radius=16)
            pygame.draw.rect(surf, WHITE if hot else (95, 95, 125), r.inflate(16, 6) if hot else r, 3, border_radius=16)
            img = get_font(26).render(lab, True, (15, 15, 25) if hot else WHITE)
            surf.blit(img, img.get_rect(center=r.center))
            rects.append(r)
        return rects

    def draw_overlay(self, surf, mouse, sel):
        """Pause / game over / win - button rect list return kore."""
        if self.state == "play" and self.paused:
            self._dim(surf, 170)
            self._title(surf, "PAUSED", 120)
            rects = self.menu(surf, ["RESUME", "TUTORIAL", "RESTART", "EXIT TO LEVELS"], sel, mouse, top=190)
            lines = ["A D / Arrows - move      W / SPACE - jump      E - use tool",
                     "J - knife      H (hold) - hide      K - super punch      Ctrl+Alt / TAB - tools"]
            for i, l in enumerate(lines):
                img = self.f_small.render(l, True, (160, 160, 185))
                surf.blit(img, img.get_rect(center=(WIDTH // 2, 455 + i * 24)))
            return rects
        if self.state == "over":
            a = clamp(self.state_t / 0.6, 0, 1)
            self._dim(surf, int(200 * a))
            if a >= 1:
                self._title(surf, "GAME OVER", 110, RED)
                img = self.f_med.render(f"You ran out of lives.   Total deaths: {self.save.get('deaths', 0)}", True, WHITE)
                surf.blit(img, img.get_rect(center=(WIDTH // 2, 170)))
                return self.menu(surf, ["RESTART", "EXIT TO LEVELS"], sel, mouse, top=260)
            return []
        if self.state == "win" and self.state_t > 1.0:
            a = clamp((self.state_t - 1.0) / 0.5, 0, 1)
            self._dim(surf, int(200 * a))
            self._title(surf, self.win_title, 80, GOLD)
            n = sum(self.got)
            for i in range(len(STAR_POS)):
                k = clamp((self.state_t - 1.5 - i * 0.45) / 0.35, 0, 1)
                if k > 0:
                    SP.draw_star_icon(surf, (WIDTH // 2 + (i - 1) * 96, 180), 38 * (0.4 + 0.6 * k) + 6 * math.sin(k * 3.14),
                                      i < n, self.t, i < n)
            img = self.f_med.render(f"Stars: {n} / {len(STAR_POS)}      Deaths this run: {self.run_deaths}      Arrests: {self.arrests - 0}",
                                    True, WHITE)
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 258)))
            img = self.f_med.render(f"Loot: {self.money} Tk  (bonus +{self.won_loot} Tk)", True, (110, 240, 150))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 292)))
            img = get_font(28).render("DO IT.  MY DREAM PLACE!", True, (255, 230, 150))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 336)))
            if self.state_t > 1.5 + 0.45 * 3:
                return self.menu(surf, ["CONTINUE"], sel, mouse, top=405)
            return []
        return []

    def _dim(self, surf, a):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((4, 4, 12, a))
        surf.blit(ov, (0, 0))

    def _title(self, surf, text, y, color=WHITE):
        img = get_font(56).render(text, True, color)
        sh = get_font(56).render(text, True, (0, 0, 0))
        surf.blit(sh, sh.get_rect(center=(WIDTH // 2 + 3, y + 3)))
        surf.blit(img, img.get_rect(center=(WIDTH // 2, y)))

    def draw(self, surf, mouse, sel):
        if self.state == "jail3" and getattr(self, "jail_ui", None):
            self.jail_ui.draw(surf)
            return []
        if self.state == "jail":
            self.draw_jail(surf)
            return []
        off = (0, 0)
        if self.shake > 0:
            m = self.shake * 22
            off = (random.uniform(-m, m), random.uniform(-m, m))
        canvas = surf
        if off != (0, 0):
            canvas = pygame.Surface((WIDTH, HEIGHT))
        self.draw_world(canvas)
        self.draw_special(canvas)
        if off != (0, 0):
            surf.blit(canvas, (int(off[0]), int(off[1])))
        if self.red_flash > 0:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((200, 20, 40, int(110 * self.red_flash / 0.4)))
            surf.blit(ov, (0, 0))
        self.draw_hud(surf, mouse)
        self.draw_special_hud(surf)
        if self.god and self.state == "play":
            img = get_font(20).render("GOD MODE", True, (255, 220, 90))
            surf.blit(img, img.get_rect(midtop=(WIDTH // 2, 8)))
        if self.state == "rec":
            self.draw_rec_feed(surf)
        if self.state == "police" and self.state_t > 2.5:
            self._title(surf, "ARRESTED!", 200, RED)
        if self.modal:
            self.draw_laptop(surf)
        if self.state == "dying" and self.state_t > 1.0:
            fade_overlay(surf, (self.state_t - 1.0) / 0.4)
        if self.wheel:
            self.wheel_ui.draw(surf, self.t, self.wheel_sel, mouse)
        return self.draw_overlay(surf, mouse, sel)


# ------------------------------------------------------------------
# Intro cutscene : TV te boro diamond (shudhu prothom bar)
# ------------------------------------------------------------------
def play_intro(screen, clock):
    f_s = get_font(15)
    f_b = get_font(30)
    f_t = pygame.font.SysFont("couriernew,monospace", 22, bold=True)
    tv_rect = pygame.Rect(190, 36, 580, 380)
    said = set()
    t = 0.0
    news_lines = [(2.0, "THE STAR OF DAWN", (255, 235, 150), 28), (3.2, "the biggest diamond", (210, 225, 255), 20),
                  (4.4, "Value: 5,000,000 Tk", (110, 240, 150), 24), (5.8, "On display tonight in", (210, 225, 255), 20),
                  (6.8, "CITY BANK VAULT", (255, 120, 120), 28)]
    ticker = "   LIVE   *   CITY BANK TO SHOW THE STAR OF DAWN DIAMOND TONIGHT   *   SECURITY: GUARDS + CCTV + LASERS   *   "
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
        if t > 1.8 and "n" not in said:
            said.add("n")
            voice.say("Breaking news. The Star of Dawn diamond, worth five million taka, is on display tonight in the City Bank vault.")
        if t > 9.6 and "a" not in said:
            said.add("a")
            voice.say("That diamond. My dream place. Let's do it!")

        screen.fill((6, 6, 12))
        SP.v_gradient(screen, pygame.Rect(0, 0, WIDTH, HEIGHT), (10, 10, 20), (4, 4, 10))
        flick = 0.85 + 0.15 * math.sin(t * 17)
        gl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(6):
            pygame.draw.ellipse(gl, (90, 130, 255, int(14 * flick)), tv_rect.inflate(160 - i * 20, 140 - i * 16))
        screen.blit(gl, (0, 0))
        screen_r = SP.draw_tv_body(screen, tv_rect)
        sc = pygame.Surface(screen_r.size)
        if t < 1.4:                                                  # static
            sc.fill((20, 20, 24))
            for _ in range(900):
                c = random.randint(60, 255)
                sc.set_at((random.randint(0, sc.get_width() - 1), random.randint(0, sc.get_height() - 1)), (c, c, c))
        else:
            SP.v_gradient(sc, sc.get_rect(), (10, 20, 60), (28, 48, 110))
            pygame.draw.rect(sc, (200, 30, 40), (0, 0, sc.get_width(), 34))
            sc.blit(f_t.render("BREAKING NEWS   *   CITY BANK", True, WHITE), (14, 5))
            SP.draw_diamond(sc, (150, 170), 150 + 10 * math.sin(t * 2), t)
            for st_, txt, col, size in news_lines:
                if t >= st_:
                    n = int((t - st_) * 30)
                    img = get_font(size).render(txt[:n], True, col)
                    idx = news_lines.index((st_, txt, col, size))
                    sc.blit(img, (262, 70 + idx * 44))
            pygame.draw.rect(sc, (10, 10, 24), (0, sc.get_height() - 34, sc.get_width(), 34))
            off = int(t * 120) % (len(ticker) * 13)
            tk = f_t.render(ticker * 3, True, (255, 230, 120))
            sc.blit(tk, (-off, sc.get_height() - 28))
        screen.blit(sc, screen_r.topleft)
        SP.draw_tv_glass(screen, screen_r, t)
        # Abix (shamne boshe TV dekhche)
        tmp = pygame.Surface((SP.TW, SP.TH), pygame.SRCALPHA)
        SP.draw_ninja(tmp, SP.OX, SP.OY, 1, t, "idle")
        big = pygame.transform.smoothscale(tmp, (SP.TW * 2, SP.TH * 2))
        dark = pygame.Surface(big.get_size(), pygame.SRCALPHA)
        dark.fill((150, 160, 210, 255))
        big.blit(dark, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(big, big.get_rect(midbottom=(110, HEIGHT - 6)))
        if 9.6 <= t < 13.4:
            n = int((t - 9.6) * 24)
            SP.draw_speech(screen, "That diamond...\nMY DREAM PLACE!"[:n], (150, HEIGHT - 200), f_b, shake=1.5)
        if t > 12.6:
            k = clamp((t - 12.6) / 0.6, 0, 1)
            img = get_font(46).render("LEVEL 1  -  CITY BANK HEIST", True, GOLD)
            img.set_alpha(int(255 * k))
            screen.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT - 40)))
        if t > 2.0:
            img = f_s.render("ENTER = skip", True, (130, 130, 160))
            screen.blit(img, img.get_rect(bottomright=(WIDTH - 16, HEIGHT - 12)))
        fade_overlay(screen, 1 - t / 1.0)
        if t > 14.0:
            fade_overlay(screen, (t - 14.0) / 0.8)
            if t > 14.8:
                return
        pygame.display.flip()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
def run(screen, clock, save, save_fn):
    """Level 1 : Return {"won": bool, "stars": int}"""
    def intro():
        if not save.get("tv_seen"):
            play_intro(screen, clock)
            save["tv_seen"] = True
            save_fn()
    return run_level(screen, clock, save, save_fn, World, intro)


def run_level(screen, clock, save, save_fn, make_world, intro=None):
    """Shob level er common loop (menu, pause, tool wheel, laptop typing)."""
    voice.init()
    sound.play_music("level1", loops=-1)
    if intro:
        intro()
        sound.play_music("level1", loops=-1)

    world = make_world(save, save_fn)
    sel = 0
    fade = 0.0
    rects = []

    def leave():
        sound.stop_music(300)
        won = world.state == "win"
        if won:
            world.commit_progress()
            save["money"] = world.money
            save_fn()
        return {"won": won, "stars": sum(world.got) if won else 0}

    def do_action(label):
        nonlocal sel
        if label == "RESUME":
            world.paused = False
        elif label == "TUTORIAL":
            world.tut.open(save.get("settings", {}).get("control", "keyboard"))
            return None
        elif label in ("RESTART",):
            world.restart()
            sound.play_music("level1", loops=-1)
            sel = 0
            return None
        elif label in ("EXIT TO LEVELS", "CONTINUE"):
            return leave()
        return None

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.033)
        fade += dt
        mouse = pygame.mouse.get_pos()
        menu_open = (world.paused or world.state == "over"
                     or (world.state == "win" and world.state_t > 1.5 + 0.45 * 3))
        labels = []
        if world.paused:
            labels = ["RESUME", "TUTORIAL", "RESTART", "EXIT TO LEVELS"]
        elif world.state == "over":
            labels = ["RESTART", "EXIT TO LEVELS"]
        elif menu_open:
            labels = ["CONTINUE"]

        CT.set_ctx(world.wheel or menu_open or bool(world.modal) or world.tut.active or world.state == "jail3")
        for e in CT.filter(pygame.event.get()):
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if world.state == "jail3" and getattr(world, "jail_ui", None):
                world.jail_ui.event(e)
                continue
            if world.tut.active:                       # tutorial khola - shob event oikhane
                world.tut.event(e)
                continue
            if (e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION) and world.modal
                    and (world.modal.get("os") or world.modal.get("pad")) and world.state == "play" and not world.paused):
                world.modal_event(e)
                continue
            if e.type == pygame.KEYDOWN:
                mods = pygame.key.get_mods() | getattr(e, "mod", 0)
                playing = world.state == "play" and not world.paused
                # ---- laptop typing ----
                if world.modal and playing:
                    if e.key == pygame.K_ESCAPE:
                        world.close_modal()
                        sound.play("back")
                    else:
                        world.modal_event(e)
                    continue
                # ---- laptop hotkey: Ctrl+Alt+Tab (ba L), shudhu terminal er kache ----
                if playing and (e.key == pygame.K_l or (
                        e.key == pygame.K_TAB and mods & pygame.KMOD_CTRL and mods & pygame.KMOD_ALT)):
                    world.wheel = False
                    world.hotkey_laptop()
                    continue
                # ---- tool wheel ----
                if world.wheel:
                    if e.key in (pygame.K_ESCAPE, pygame.K_TAB) or (
                            e.key in (pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_LALT, pygame.K_RALT)
                            and mods & pygame.KMOD_CTRL and mods & pygame.KMOD_ALT):
                        world.wheel = False
                        sound.play("back")
                    elif e.key in (pygame.K_LEFT, pygame.K_UP, pygame.K_a, pygame.K_w):
                        world.wheel_sel = cycle_tool(world.wheel_sel, -1)
                        sound.play("hover")
                    elif e.key in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_d, pygame.K_s):
                        world.wheel_sel = cycle_tool(world.wheel_sel, 1)
                        sound.play("hover")
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                        world.tool = world.wheel_sel
                        world.wheel = False
                        sound.play("click")
                    continue
                if menu_open and labels:
                    if e.key in (pygame.K_UP, pygame.K_w):
                        sel = (sel - 1) % len(labels)
                        sound.play("hover")
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        sel = (sel + 1) % len(labels)
                        sound.play("hover")
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        sound.play("click")
                        res = do_action(labels[min(sel, len(labels) - 1)])
                        if res:
                            return res
                        continue
                if e.key == pygame.K_ESCAPE:
                    if world.state == "play":
                        world.paused = not world.paused
                        sel = 0
                        sound.play("back")
                    elif world.state in ("over", "win") and menu_open:
                        return leave()
                    continue
                if playing:
                    ctrl_alt = (e.key in (pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_LALT, pygame.K_RALT)
                                and mods & pygame.KMOD_CTRL and mods & pygame.KMOD_ALT)
                    if ctrl_alt or e.key == pygame.K_TAB:
                        world.wheel, world.wheel_sel = True, world.tool
                        sound.play("pop")
                    elif e.key in (pygame.K_w, pygame.K_UP, pygame.K_SPACE):
                        world.press_jump()
                    elif e.key in (pygame.K_j, pygame.K_x):
                        world.press_knife()
                    elif e.key in (pygame.K_k, pygame.K_f):
                        world.press_punch()
                    elif e.key == pygame.K_e:
                        world.use_tool()
                    elif e.key == pygame.K_t:
                        world.press_star()
                    elif e.key == pygame.K_c:
                        world.toggle_autotype()
                    elif e.key == pygame.K_q:
                        world.press_electric()
                    elif pygame.K_1 <= e.key <= pygame.K_9:
                        world.tool = TL.UNLOCKED[e.key - pygame.K_1]
                        sound.play("hover")
                    elif e.key == pygame.K_0:
                        world.tool = TL.UNLOCKED[9]
                        sound.play("hover")
            if e.type == pygame.MOUSEWHEEL and world.state == "play" and not world.paused and not world.modal:
                d = -1 if e.y > 0 else 1
                if world.wheel:
                    world.wheel_sel = cycle_tool(world.wheel_sel, d)
                else:
                    world.tool = cycle_tool(world.tool, d)
                sound.play("hover")
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                pos = getattr(e, "pos", mouse)
                if world.wheel:
                    i = world.wheel_ui.index_at(pos)
                    if i is not None and TL.TOOLS[i]["id"]:
                        world.tool = i
                        world.wheel = False
                        sound.play("click")
                elif menu_open:
                    for i, r in enumerate(rects):
                        if i < len(labels) and r.collidepoint(pos):
                            sound.play("click")
                            res = do_action(labels[i])
                            if res:
                                return res
                            break

        for i, r in enumerate(rects):
            if menu_open and r.collidepoint(mouse) and sel != i:
                sel = i
                sound.play("hover")

        world.tick_meta(dt)
        world.update(dt, pygame.key.get_pressed())
        world.tut.update(dt)
        rects = world.draw(screen, mouse, sel)
        world.tut.draw(screen)
        if fade < 0.5:
            fade_overlay(screen, 1 - fade / 0.5)
        pygame.display.flip()
