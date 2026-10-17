"""
level10.py - Chapter 1 / Level 10 : THE GOVERNOR'S CITADEL  (CHAPTER 1 BOSS).
main_game.py theke:  level10.run(screen, clock, save, save_fn)

Lokkho: fortress citadel theke "CITADEL MASTER CIPHER" churi kore helipad er helicopter e palao.  (Chapter 2 unlock!)

Challenge:
  - SEARCHLIGHT:  tower er alo te porle turret continuous goli kore.  Power box e HACKER (key 2) diye
    /CAMERA01099 type korle searchlight off.  EMP = 5 sec off.  H / SMOKE diye lukano jay.
  - DUAL DOOR:  Terminal A (power off, 18 sec)  ->  Terminal B (blast door override) 18 sec er moddhe.
    Dutoy LAPTOP (Python app e  unlock).
  - COMMANDER STEELE (mini-boss) + 2 CYBER-K9:  shamne theke knife kaj kore na.
        * REWIRER PRO (key 6) diye laser grid rewire koro, Steele ke grid er opor dik e dhukiye maro
        * Super Punch (K)  = boro damage
        * EMP blackout (key 4): Steele stun, tokhon knife kaj kore
        * pichon theke knife
  - Cipher vault: VAULT THERMITE (key 8).  Tarpor helipad.
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
from level2 import Guard2, Dog, draw_helicopter
from level5 import ShieldGuard, DualTerminal
from animation import WIDTH, HEIGHT, get_font
import heist as H
from heist import (HeistWorld, Feature, DoorFeature, LootFeature, SweepGridFeature, Tiled, draw_floor)

LEVEL_W = 7100
GOAL = 6900
POWER_TIME = 18.0
DOOR_X = 5020
IN_END = 6650                    # er pore abar bairer (helipad)


# ------------------------------------------------------------------
# Drawings
# ------------------------------------------------------------------
def draw_cipher(surf, c, t):
    x, y = c
    y += math.sin(t * 3) * 3
    SP.glow(surf, (x, y), 58, (255, 200, 80), 100, 4)
    pygame.draw.circle(surf, (40, 30, 10), (int(x), int(y)), 24)
    pygame.draw.circle(surf, (255, 205, 80), (int(x), int(y)), 24, 4)
    pygame.draw.circle(surf, (255, 205, 80), (int(x), int(y)), 14, 2)
    for k in range(12):
        a = t * 1.5 + k * math.tau / 12
        pygame.draw.line(surf, (255, 235, 150), (x + math.cos(a) * 14, y + math.sin(a) * 14),
                         (x + math.cos(a) * 22, y + math.sin(a) * 22), 2)
    pygame.draw.circle(surf, (255, 255, 200), (int(x), int(y)), 5)


def outdoor_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (8, 10, 22), (30, 34, 54))
    for _ in range(5):
        pygame.draw.ellipse(s, (16, 18, 34), (rnd.randint(-40, w), rnd.randint(20, 140), rnd.randint(180, 320), 60))
    # fortress wall with battlements
    pygame.draw.rect(s, (30, 32, 44), (0, 200, w, GROUND_Y - 200))
    for x in range(0, w, 60):
        pygame.draw.rect(s, (30, 32, 44), (x, 176, 36, 28))
    for x in range(0, w, 90):
        pygame.draw.rect(s, (44, 46, 62), (x, 210, 3, GROUND_Y - 214))
    for ty in range(240, GROUND_Y, 50):
        pygame.draw.line(s, (44, 46, 62), (0, ty), (w, ty), 1)
    # arrow slits (glow)
    for x in range(50, w, 180):
        pygame.draw.rect(s, (200, 150, 70), (x, 250, 6, 26))
    # distant towers
    for x in (120, 400):
        pygame.draw.rect(s, (22, 24, 36), (x, 90, 60, 130))
        pygame.draw.polygon(s, (22, 24, 36), [(x - 8, 92), (x + 68, 92), (x + 30, 50)])
        pygame.draw.rect(s, (230, 200, 90), (x + 24, 120, 10, 16))


def indoor_wall(s, rnd):
    w, h = s.get_size()
    SP.v_gradient(s, s.get_rect(), (30, 22, 34), (14, 10, 20))
    pygame.draw.rect(s, (10, 6, 14), (0, 0, w, 38))
    pygame.draw.rect(s, (200, 40, 50), (0, 38, w, 4))
    for i in range(3):                                           # monitors
        r = pygame.Rect(40 + i * 170, 100, 150, 100)
        pygame.draw.rect(s, (40, 40, 52), r.inflate(10, 10), border_radius=6)
        pygame.draw.rect(s, (6, 14, 12), r)
        for k in range(8):
            pygame.draw.line(s, (60, 220, 130), (r.x + 8, r.y + 10 + k * 11), (r.x + 8 + rnd.randint(30, 130), r.y + 10 + k * 11), 2)
    pygame.draw.rect(s, (28, 24, 36), (60, 240, 420, 120))      # war table
    pygame.draw.rect(s, (120, 40, 40), (60, 240, 420, 120), 3)
    for _ in range(14):
        pygame.draw.circle(s, rnd.choice(((230, 60, 60), (60, 200, 240))), (rnd.randint(80, 460), rnd.randint(256, 346)), 4)
    pygame.draw.polygon(s, (170, 30, 40), [(w - 120, 90), (w - 40, 90), (w - 80, 220)])      # banner


def draw_helipad(surf, x, t):
    pad = pygame.Rect(0, 0, 220, 14)
    pad.midbottom = (x, GROUND_Y)
    pygame.draw.rect(surf, (60, 64, 76), pad)
    pygame.draw.rect(surf, (230, 200, 40), pad, 2)
    f = get_font(22, ).render("H", True, (230, 200, 40))
    surf.blit(f, f.get_rect(center=(x, GROUND_Y - 6)))
    draw_helicopter(surf, x + 10, GROUND_Y - 24 + math.sin(t * 3) * 3, t)
    lab = get_font(15).render("EXTRACTION HELICOPTER", True, (80, 255, 150))
    surf.blit(lab, lab.get_rect(center=(x, GROUND_Y - 150)))


# ------------------------------------------------------------------
# Searchlight + power box
# ------------------------------------------------------------------
class Searchlight(Feature):
    RANGE, HALF, FIRE = 560, 0.26, 0.55

    def __init__(self, x, phase=0.0):
        self.x, self.ph = x, phase
        self.y = 120
        self.off = False
        self.lock = 0.0
        self.fire_t = 0.0
        self.tracer = 0.0
        self.target = None

    def ang(self, t):
        return math.pi / 2 + 0.62 * math.sin(t * 0.75 + self.ph)

    def active(self, w):
        return not self.off and not w.systems_off()

    def in_beam(self, w):
        p = w.p
        if not p.alive or p.hidden or w.smoke_hides(p):
            return False
        vx, vy = p.x - self.x, (p.y - 30) - self.y
        d = math.hypot(vx, vy)
        if d > self.RANGE or d < 5:
            return False
        diff = (math.atan2(vy, vx) - self.ang(w.t) + math.pi) % math.tau - math.pi
        return abs(diff) <= self.HALF

    def update(self, w, dt):
        self.tracer = max(0.0, self.tracer - dt)
        if not self.active(w):
            self.lock = 0.0
            return
        if self.in_beam(w):
            self.lock = min(1.0, self.lock + dt * 3)
            self.fire_t -= dt
            if self.fire_t <= 0 and w.state == "play":
                self.fire_t = self.FIRE
                self.tracer = 0.12
                self.target = (w.p.x, w.p.y - 30)
                sound.play("gunshot", 0.7)
                w.hurt_player(1 if w.p.x > self.x else -1, "turret")
        else:
            self.lock = max(0.0, self.lock - dt * 2)
            self.fire_t = min(self.fire_t, 0.3)

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if x < -300 or x > WIDTH + 300:
            return
        # tower
        pygame.draw.polygon(surf, (28, 30, 40), [(x - 26, GROUND_Y), (x - 12, self.y + 20), (x + 12, self.y + 20), (x + 26, GROUND_Y)])
        for k in range(6):
            yy = self.y + 40 + k * 55
            pygame.draw.line(surf, (60, 64, 80), (x - 20 + k * 2, yy), (x + 20 - k * 2, yy + 30), 2)
        pygame.draw.rect(surf, (50, 54, 68), (x - 22, self.y, 44, 24), border_radius=6)
        a = self.ang(t)
        if self.active(w):
            col = SP.lerp_color((255, 245, 190), (255, 60, 50), self.lock)
            pts = [(x, self.y + 12)]
            for k in (-self.HALF, -self.HALF / 2, 0, self.HALF / 2, self.HALF):
                pts.append((x + math.cos(a + k) * self.RANGE, self.y + 12 + math.sin(a + k) * self.RANGE))
            xs, ys = [q[0] for q in pts], [q[1] for q in pts]
            bx, by = int(min(xs)), int(min(ys))
            cs = pygame.Surface((int(max(xs)) - bx + 4, int(max(ys)) - by + 4), pygame.SRCALPHA)
            pygame.draw.polygon(cs, col + (46 + int(60 * self.lock),), [(q[0] - bx, q[1] - by) for q in pts])
            surf.blit(cs, (bx, by))
            pygame.draw.circle(surf, col, (int(x), self.y + 12), 9)
            SP.glow(surf, (x, self.y + 12), 40, col, 60, 3)
        else:
            pygame.draw.circle(surf, (70, 70, 80), (int(x), self.y + 12), 9)
        if self.tracer > 0 and self.target:
            pygame.draw.line(surf, (255, 220, 120), (x, self.y + 12), (self.target[0] - cam, self.target[1]), 2)


class PowerBox(Feature):
    def __init__(self, x, light):
        self.x, self.light = x, light
        self.done = False

    def targets(self, w, add):
        d = abs(w.p.x - self.x)
        if not self.done and d < 90:
            add("hacker", d, (self, None))

    def use(self, w, tid, payload):
        w.open_modal("feature", [TL.CAM_CODE], None, "SEARCHLIGHT POWER BOX  -  type the code")
        w.modal["feature"] = self

    def modal_done(self, w, m):
        self.done = True
        self.light.off = True
        sound.play("hack")
        w.burst(self.x, GROUND_Y - 50, (90, 255, 200), 20, 200, 0.7, grav=100)
        w.say("SEARCHLIGHT POWER CUT")

    def prompt(self, w, tid, payload):
        return (self.x, GROUND_Y - 100), ["[E]  HACK POWER BOX", "type /CAMERA01099"]

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if not (-60 < x < WIDTH + 60):
            return
        r = pygame.Rect(0, 0, 46, 60)
        r.midbottom = (x, GROUND_Y)
        SP.v_gradient(surf, r, (70, 76, 90), (36, 40, 52))
        pygame.draw.rect(surf, (20, 22, 30), r, 3, border_radius=4)
        col = (80, 255, 150) if self.done else ((255, 70, 70) if int(t * 2) % 2 else (130, 30, 30))
        pygame.draw.circle(surf, col, (int(x), r.y + 14), 5)
        pygame.draw.line(surf, (230, 200, 60), (x - 14, r.y + 34), (x + 14, r.y + 34), 3)
        f = get_font(12).render("POWER BOX", True, (200, 210, 230))
        surf.blit(f, f.get_rect(midbottom=(x, r.y - 4)))


class DualTerminal18(DualTerminal):
    def modal_done(self, w, m):
        sound.play("unlock")
        if self.which == "A":
            w.power_t = POWER_TIME
            w.say(f"CITADEL POWER OFF  -  reach TERMINAL B in {int(POWER_TIME)} s!")
        else:
            if w.power_t <= 0:
                w.say("Too slow!  Power is back - redo TERMINAL A")
                return
            self.done = True
            self.door.open(w)
            w.say("BLAST DOOR OVERRIDDEN")
            w.shake = 0.5


# ------------------------------------------------------------------
# Commander Steele + cyber K9
# ------------------------------------------------------------------
class CyberDog(Dog):
    SMELL, PATROL, CHASE = 300, 90, 260

    def draw(self, surf, cam, t):
        super().draw(surf, cam, t)
        if self.alive:
            x = self.x - cam
            if -80 < x < WIDTH + 80:
                SP.glow(surf, (x + self.facing * 18, GROUND_Y - 24), 18, (80, 200, 255), 110, 3)
                f = get_font(11).render("CYBER-K9", True, (120, 210, 255))
                surf.blit(f, f.get_rect(midbottom=(x, GROUND_Y - 40)))


class Steele(Guard2):
    HW, HH = 44, 78
    HP = 6
    SIGHT = 560

    def reset(self):
        super().reset()
        self.hp = self.HP
        self.stun = 0.0
        self.engaged = False
        self.fire_cd = 1.0
        self.burst = 0
        self.burst_t = 0.0
        self.hit_t = 0.0
        self.intro = False

    def front(self, p):
        return (p.x - self.x) * self.facing > 0

    def hurt(self, w, dmg, txt):
        self.hp -= dmg
        self.hit_t = 0.4
        sound.play("hit")
        w.burst(self.x, GROUND_Y - 50, (200, 30, 40), 12, 170, 0.6)
        w.floats.append({"x": self.x, "y": GROUND_Y - 120, "t": 0.9, "txt": txt, "c": (255, 220, 120)})
        if self.hp <= 0:
            self.die(w)
            w.floats.append({"x": self.x, "y": GROUND_Y - 140, "t": 1.6, "txt": "COMMANDER STEELE DOWN!", "c": (255, 120, 120)})
            voice.say("Commander Steele is down")
            w.say("COMMANDER STEELE DEFEATED")

    def stab(self, w, p):
        if self.stun > 0:
            self.hurt(w, 2, "STUNNED HIT -2")
        elif self.front(p):
            sound.play("hit")
            w.burst(self.x + self.facing * 26, GROUND_Y - 50, (190, 200, 220), 12, 220, 0.5, grav=0)
            w.floats.append({"x": self.x, "y": GROUND_Y - 120, "t": 0.9, "txt": "ARMOR!  immune from front", "c": (160, 220, 255)})
            self.engaged, self.alert = True, max(self.alert, 8.0)
        else:
            self.hurt(w, 2, "BACKSTAB -2")

    def punched(self, w):
        self.hurt(w, 3, "SUPER PUNCH -3")
        self.engaged, self.alert = True, max(self.alert, 8.0)

    def die(self, world):
        if not self.alive:
            return
        self.hp = 0
        super().die(world)

    def update(self, dt, p, world):
        self.hit_t = max(0.0, self.hit_t - dt)
        if not self.alive:
            super().update(dt, p, world)
            return
        self.anim_t += dt
        self.bubble_t = max(0.0, self.bubble_t - dt)
        self.excl = max(0.0, self.excl - dt)
        self.alert = max(0.0, self.alert - dt)
        if world.emp_t > 0:
            self.stun = max(self.stun, world.emp_t)
        self.stun = max(0.0, self.stun - dt)
        if self.stun > 0:
            self.burst = 0
            return
        dx = p.x - self.x
        see = self.sees(p)
        if not self.intro and abs(dx) < 650 and p.alive:
            self.intro = True
            self.say(world, "You will not leave my citadel, thief!")
        if see and not self.engaged:
            self.engaged = True
            self.excl = 0.8
            sound.play("alert", 0.8)
        if not p.alive or p.hidden or world.smoke_hides(p):
            if self.engaged and not see:
                self.alert = max(0.0, self.alert)
                if self.alert <= 0:
                    self.engaged = False
        if self.engaged and p.alive:
            self.facing = 1 if dx > 0 else -1
            if abs(dx) > 250:
                self.x += self.facing * 96 * dt
            self.fire_cd -= dt
            if self.burst > 0:
                self.burst_t -= dt
                if self.burst_t <= 0:
                    self.burst -= 1
                    self.burst_t = 0.11
                    world.bullets.append({"x": self.x + self.facing * 40, "y": GROUND_Y - 44, "vx": self.facing * 780.0,
                                          "life": 1.2, "cause": "assault rifle"})
                    sound.play("gunshot", 0.6)
            elif self.fire_cd <= 0 and abs(dx) < 620:
                self.burst, self.burst_t, self.fire_cd = 3, 0.0, 1.9
            if not see and self.alert <= 0:
                self.engaged = False
        else:
            self.facing = self.facing or 1
            self.x += self.facing * 55 * dt
            if self.x >= self.x1:
                self.x, self.facing = self.x1, -1
            elif self.x <= self.x0:
                self.x, self.facing = self.x0, 1

    def draw(self, surf, cam, t):
        x = self.x - cam
        if x < -140 or x > WIDTH + 140:
            return
        if not self.alive:
            alpha = clamp(255 - (self.dead_t - 1.6) * 160, 0, 255)
            if alpha > 0:
                SP.draw_guard(surf, x, GROUND_Y, self.facing, t, "dead", alpha=alpha, s=0.8)
            return
        anim = "idle" if self.stun > 0 else ("aim" if self.burst > 0 or self.engaged else "walk")
        SP.draw_guard(surf, x, GROUND_Y, self.facing, self.anim_t, anim, 1.0 if anim == "aim" else 0.0, s=0.8)
        # armor plates
        pygame.draw.rect(surf, (60, 64, 80), (x - 24, GROUND_Y - 78, 48, 34), border_radius=8)
        pygame.draw.rect(surf, (200, 50, 50), (x - 24, GROUND_Y - 78, 48, 34), 3, border_radius=8)
        pygame.draw.rect(surf, (200, 50, 50), (x - 10, GROUND_Y - 100, 20, 8), border_radius=3)
        if self.hit_t > 0:
            SP.glow(surf, (x, GROUND_Y - 50), 50, (255, 90, 90), 90, 3)
        if self.stun > 0:
            f = get_font(18).render("STUNNED", True, (140, 210, 255))
            surf.blit(f, f.get_rect(midbottom=(x, GROUND_Y - 104)))
            for k in range(4):
                a = t * 8 + k * 1.57
                pygame.draw.line(surf, (160, 220, 255), (x + math.cos(a) * 14, GROUND_Y - 112), (x + math.cos(a) * 24, GROUND_Y - 118 + math.sin(a) * 6), 2)
        if self.excl > 0:
            f = get_font(30).render("!", True, (255, 60, 60))
            surf.blit(f, f.get_rect(center=(x, GROUND_Y - 120)))
        if self.bubble_t > 0:
            SP.draw_speech(surf, self.bubble, (x, GROUND_Y - 130), get_font(16), shake=0.0)


# ------------------------------------------------------------------
# Level data
# ------------------------------------------------------------------
LEDGES = [(850, 990, 350),
          (2850, 2960, 365), (3010, 3120, 290), (3170, 3290, 215),
          (4500, 4600, 360), (4650, 4750, 285)]
STARS = [(920, 312), (3230, 177), (4700, 247)]
CASH = [(450, GROUND_Y - 12), (1000, GROUND_Y - 12), (1700, GROUND_Y - 12), (2300, GROUND_Y - 12),
        (2900, 350), (3200, 200), (3500, GROUND_Y - 12), (4200, GROUND_Y - 12),
        (5200, GROUND_Y - 12), (6050, GROUND_Y - 12)]
GUARDS = [(500, 800), (1600, 1900), (2000, 2300), (3000, 3350), (4100, 4400, "s")]
DOGS = [(1600, 1900), (3400, 3700)]
CAMS = [(900, 0.0), (2200, 1.7), (3300, 3.0), (4500, 4.4)]
CHECKPOINTS = [1400, 2600, 4000, 5200, 6100]
HINTS = [
    (0, 420, "THE GOVERNOR'S CITADEL  -  steal the CITADEL MASTER CIPHER"),
    (700, 1050, "SEARCHLIGHT:  in the beam = turret fire.  Hack the POWER BOX (key 2, /CAMERA01099)"),
    (1900, 2450, "Next tower's power box ahead  -  or hide (H) / SMOKE / EMP"),
    (4200, 4350, "DUAL DOOR:  TERMINAL A (power off 18 s)  then TERMINAL B"),
    (4350, 4850, "Run to TERMINAL B!  Cameras, lasers, lights are OFF now"),
    (5030, 5300, "COMMANDER STEELE ahead!  Knife is useless from the FRONT"),
    (5300, 5600, "Rewire the laser grid (key 6) and bait him in,  or K = Super Punch,  or EMP then stab"),
    (6100, 6250, "Cipher vault:  key 8 VAULT THERMITE"),
    (6400, 6850, "Take the CIPHER and run to the HELICOPTER!"),
]
SPOT_LINES = ["Intruder in the citadel!", "Sound the alarm!", "Kill the thief!"]
CHAT_LINES = ["The Governor sees everything.", "Searchlights are live.", "Nobody leaves the citadel.",
              "I have CCTV footage in this fortress."]


class World10(HeistWorld):
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
    TARGET = "CITADEL MASTER CIPHER"
    REWARD = 4000
    BAIL = 800
    WIN_TITLE = "CHAPTER 1 COMPLETE!"
    SPOT_LINES = SPOT_LINES
    CHAT_LINES = CHAT_LINES

    def __init__(self, save, save_fn):
        self.bg_out = Tiled(600, outdoor_wall, seed=61)
        self.bg_in = Tiled(600, indoor_wall, seed=62)
        self.rain = [(random.random() * WIDTH, random.random() * HEIGHT, random.uniform(0.7, 1.4)) for _ in range(120)]
        self.flash = 0.0
        super().__init__(save, save_fn)

    def make_guard(self, spec):
        if len(spec) == 3:
            return ShieldGuard(spec[0], spec[1], self)
        return Guard2(spec[0], spec[1], self)

    def restart(self):
        super().restart()
        self.boss = Steele(5300, 5900, self)
        self.boss.spot_lines, self.boss.chat_lines = SPOT_LINES, CHAT_LINES
        self.guards.append(self.boss)
        self.dogs.extend([CyberDog(5250, 5650), CyberDog(5550, 5900)])

    def make_features(self):
        door = DoorFeature(DOOR_X, "blast", "BLAST DOOR")
        self.door = door
        lights = [Searchlight(1300, 0.0), Searchlight(2700, 2.0), Searchlight(3800, 4.0)]
        feats = list(lights)
        for lt, bx in zip(lights, (1050, 2450, 3550)):
            feats.append(PowerBox(bx, lt))
        feats += [DualTerminal18(4350, "A", door), DualTerminal18(4850, "B", door), door,
                  SweepGridFeature([(5620, 5760, 0.0)]),
                  DoorFeature(6200, "thermite", "CIPHER VAULT"),
                  LootFeature(6350, "CITADEL MASTER CIPHER", draw_cipher)]
        return feats

    def extra_update(self, dt):
        self.flash = max(0.0, self.flash - dt)
        if random.random() < dt * 0.12:
            self.flash = 0.25
            sound.play("whoosh", 0.2)
        for i, (rx, ry, sp) in enumerate(self.rain):
            ry += 640 * sp * dt
            rx -= 100 * sp * dt
            if ry > HEIGHT:
                ry, rx = -10, random.random() * (WIDTH + 100)
            self.rain[i] = (rx % WIDTH, ry, sp)

    def draw_background(self, surf, cam):
        self.bg_out.draw(surf, cam)
        split = DOOR_X - cam
        send = IN_END - cam
        if split < WIDTH and send > 0:
            clip = surf.get_clip()
            surf.set_clip(pygame.Rect(max(0, int(split)), 0, max(0, int(min(send, WIDTH) - max(0, split))), HEIGHT))
            self.bg_in.draw(surf, cam)
            surf.set_clip(clip)
        hx = GOAL - cam
        if -200 < hx < WIDTH + 200:
            draw_helipad(surf, hx, self.t)
        draw_floor(surf, cam, (36, 38, 52), (14, 16, 26), (120, 124, 150), stripe=(50, 54, 70), tile=90)
        if split < WIDTH and send > 0:
            clip = surf.get_clip()
            surf.set_clip(pygame.Rect(max(0, int(split)), GROUND_Y, max(0, int(min(send, WIDTH) - max(0, split))), HEIGHT - GROUND_Y))
            SP.v_gradient(surf, pygame.Rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y), (60, 30, 40), (20, 10, 18))
            pygame.draw.line(surf, (200, 50, 60), (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
            surf.set_clip(clip)

    def draw_fx(self, surf, cam):
        # storm
        tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        a0, a1 = DOOR_X - cam, IN_END - cam

        def outdoors(px):
            return px < a0 or px > a1
        tint.fill((4, 8, 26, 80))
        if a1 > 0 and a0 < WIDTH:
            tint.fill((0, 0, 0, 0), (max(0, int(a0)), 0, max(0, int(min(a1, WIDTH) - max(0, a0))), HEIGHT))
        surf.blit(tint, (0, 0))
        for rx, ry, sp in self.rain:
            if outdoors(rx):
                pygame.draw.line(surf, (150, 180, 220), (rx, ry), (rx + 5 * sp, ry + 14 * sp), 1)
        if self.flash > 0:
            fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fl.fill((220, 230, 255, int(150 * self.flash / 0.25)))
            if a1 > 0 and a0 < WIDTH:
                fl.fill((0, 0, 0, 0), (max(0, int(a0)), 0, max(0, int(min(a1, WIDTH) - max(0, a0))), HEIGHT))
            surf.blit(fl, (0, 0))
        b = self.boss
        if b.alive and abs(b.x - self.p.x) < 900 and self.state == "play":
            r = pygame.Rect(0, 0, 360, 14)
            r.midtop = (WIDTH // 2, 100)
            pygame.draw.rect(surf, (30, 16, 20), r.inflate(6, 6), border_radius=8)
            pygame.draw.rect(surf, (210, 50, 60), (r.x, r.y, int(r.w * b.hp / b.HP), r.h), border_radius=6)
            f = get_font(15).render("COMMANDER STEELE", True, (255, 200, 200))
            surf.blit(f, f.get_rect(midbottom=(r.centerx, r.y - 4)))
        if self.power_t > 0:
            k = self.power_t / POWER_TIME
            r = pygame.Rect(0, 0, 300, 12)
            r.center = (WIDTH // 2, 190)
            pygame.draw.rect(surf, (30, 30, 20), r.inflate(4, 4), border_radius=6)
            pygame.draw.rect(surf, (255, 200, 80) if k > 0.3 else (255, 70, 70), (r.x, r.y, int(r.w * k), r.h), border_radius=5)
            img = self.f_small.render("GO TO TERMINAL B", True, (255, 220, 120))
            surf.blit(img, img.get_rect(midbottom=(WIDTH // 2, r.y - 6)))


def run(screen, clock, save, save_fn):
    """Return: {"won": bool, "stars": int}"""
    cache = {}

    def back(s, off):
        s.fill((8, 10, 22))
        cache.setdefault("t", Tiled(600, outdoor_wall, seed=61)).draw(s, off)
        draw_floor(s, off, (36, 38, 52), (14, 16, 26), (120, 124, 150))

    return H.run_heist(screen, clock, save, save_fn, World10, "THE GOVERNOR'S CITADEL",
                       ["CHAPTER 1 BOSS  -  steal the CITADEL MASTER CIPHER.",
                        "Searchlights, dual-hack blast door, Commander Steele.",
                        "Reach the helicopter on the helipad."],
                       back, lambda s, c, t: draw_cipher(s, c, t),
                       "The Governor's Citadel. Chapter one boss. Steal the citadel master cipher.")
