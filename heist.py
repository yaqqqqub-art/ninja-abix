"""
heist.py - Level 3, 4, 5, 6 er jonno common engine (HeistWorld) + reusable "feature" gulo.

Ekta level = HeistWorld er subclass:
    - LEVEL_W, LEDGES, STARS, CASH, GUARDS, CAMS, CHECKPOINTS, HINTS ... (data)
    - make_features()  -> feature list (door, terminal, laser, case, drone ...)
    - draw_background(surf, cam)  / draw_fx(surf, cam)
Feature = chhoto object jar nijer solid / update / draw / tool target ache.

Shob level e common:
    guard, dog, CCTV, EMP / DECOY / SMOKE tool, thermite (2 sec), code typing modal (shob pause),
    arrest -> bail 500 Tk / jail, checkpoint locker, 3 star, cash, TTS.
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
from level1 import Camera, Player, World, clamp, GROUND_Y, CEIL_Y, START_HEALTH
from level2 import Guard2, Dog, draw_safe, draw_ruby_crown
from animation import WIDTH, HEIGHT, WHITE, RED, GOLD, get_font, fade_overlay

SMOKE_TIME, SMOKE_CD, SMOKE_R = 3.5, 10.0, 170
EMP_TIME, EMP_CD = 5.0, 16.0
DECOY_TIME, DECOY_CD = 6.0, 10.0
MELT_TIME = 2.0


class K0(dict):
    """Kono key chapa nei."""
    def __missing__(self, k):
        return False


# ------------------------------------------------------------------
# Feature (base)
# ------------------------------------------------------------------
class Feature:
    def solids(self, w):
        return []

    def update(self, w, dt):
        pass

    def draw(self, w, surf, cam, t):
        pass

    def targets(self, w, add):
        """add(tool_id, distance, payload)"""

    def use(self, w, tid, payload):
        pass

    def modal_done(self, w, m):
        pass

    def interact(self, w):
        """E chaple (kono tool lage na) - jemon CODE LOCK keypad. True = E kaj korlo."""
        return False

    def melt_done(self, w, payload):
        pass

    def prompt(self, w, tid, payload):
        """((x, y), [line1, line2]) ba None"""
        return None

    def on_knife(self, w, reach):
        pass

    def on_punch(self, w):
        pass

    def on_respawn(self, w):
        pass


def draw_dashed(surf, a, b, col):
    d = math.hypot(b[0] - a[0], b[1] - a[1])
    if d < 1:
        return
    n = max(1, int(d // 14))
    for i in range(n):
        k0, k1 = i / n, (i + 0.55) / n
        pygame.draw.line(surf, col, (a[0] + (b[0] - a[0]) * k0, a[1] + (b[1] - a[1]) * k0),
                         (a[0] + (b[0] - a[0]) * k1, a[1] + (b[1] - a[1]) * k1), 2)


# ------------------------------------------------------------------
# Generic features
# ------------------------------------------------------------------
class DoorFeature(Feature):
    """kind: keycard (glass) | thermite (dhatur) | terminal (laptop / onno kichu diye khole)"""

    def __init__(self, x, kind, label="", name="door"):
        self.x, self.kind, self.label, self.name = x, kind, label, name
        self.opening = False
        self.open_k = 0.0
        self.melting = False

    @property
    def is_open(self):
        return self.open_k >= 0.6 or (self.opening and self.open_k >= 0.6)

    def open(self, w):
        self.opening = True
        if self.open_k <= 0:
            self.open_k = 0.001

    def solids(self, w):
        if self.open_k < 0.6:
            return [pygame.Rect(self.x - 12, CEIL_Y, 24, GROUND_Y - CEIL_Y)]
        return []

    def update(self, w, dt):
        if self.opening and self.open_k < 1.0:
            self.open_k = min(1.0, self.open_k + dt * (0.8 if self.kind == "thermite" else 1.6))

    def targets(self, w, add):
        if self.opening:
            return
        d = abs(w.p.x - self.x)
        if self.kind == "keycard" and d < 110:
            add("keycard", d, (self, None))
        elif self.kind == "thermite" and d < 120 and not self.melting:
            add("thermite", d, (self, None))

    def use(self, w, tid, payload):
        if tid == "keycard":
            self.open(w)
            sound.play("unlock")
            w.say("DOOR UNLOCKED")
        elif tid == "thermite":
            self.melting = True
            w.start_melt(self, None)

    def melt_done(self, w, payload):
        self.open(w)
        sound.play("unlock")
        w.say("DOOR MELTED")
        w.burst(self.x, GROUND_Y - 80, (255, 150, 40), 30, 260, 0.8, grav=300)

    def prompt(self, w, tid, payload):
        if tid == "keycard":
            return (self.x, GROUND_Y - 160), ["[E]  SCAN KEYCARD", "open door"]
        return (self.x, GROUND_Y - 130), ["[E]  MELT", "2 seconds"]

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if not (-80 < x < WIDTH + 80):
            return
        h = GROUND_Y - CEIL_Y
        if self.kind in ("keycard", "terminal", "code"):
            if self.open_k < 0.6:
                gs = pygame.Surface((22, h), pygame.SRCALPHA)
                gs.fill((130, 200, 255, 70))
                surf.blit(gs, (x - 11, CEIL_Y))
                pygame.draw.rect(surf, (190, 225, 250), (x - 11, CEIL_Y, 22, h), 3)
                pygame.draw.rect(surf, (30, 34, 44), (x + 14, GROUND_Y - 150, 12, 30), border_radius=3)
                pygame.draw.circle(surf, (255, 60, 60) if int(t * 2) % 2 else (120, 20, 20), (x + 20, GROUND_Y - 142), 3)
            else:
                pygame.draw.rect(surf, (190, 225, 250), (x - 11, CEIL_Y, 4, 50), 2)
                pygame.draw.rect(surf, (190, 225, 250), (x + 7, CEIL_Y, 4, 50), 2)
                pygame.draw.circle(surf, (60, 255, 130), (x + 20, GROUND_Y - 142), 3)
        else:
            pygame.draw.rect(surf, (14, 16, 22), (x - 20, CEIL_Y, 40, h))
            if self.open_k < 0.999:
                off = int(h * self.open_k)
                slab = pygame.Rect(x - 16, CEIL_Y - off, 32, h)
                for i in range(slab.w):
                    kk = i / slab.w
                    c = SP.lerp_color((70, 74, 88), (170, 176, 192), math.sin(kk * math.pi))
                    pygame.draw.line(surf, c, (slab.x + i, slab.y), (slab.x + i, slab.bottom))
                pygame.draw.rect(surf, (30, 32, 40), slab, 3)
                for yy in range(slab.y + 20, slab.bottom, 50):
                    pygame.draw.circle(surf, (30, 32, 40), (slab.x + 6, yy), 2)
                    pygame.draw.circle(surf, (30, 32, 40), (slab.right - 6, yy), 2)
                if self.melting:
                    SP.glow(surf, (x, GROUND_Y - 80), 50, (255, 140, 40), 70, 3)
        if self.label:
            f = get_font(14).render(self.label, True, (240, 90, 90))
            surf.blit(f, f.get_rect(center=(x, 90)))


class TerminalFeature(Feature):
    """LAPTOP diye code type korar terminal. effect(w) call hoy shesh hole."""

    def __init__(self, x, lines, title, effect, status_on=("SYSTEM", "LOCKED")):
        self.x, self.lines, self.title, self.effect = x, lines, title, effect
        self.done = False

    def targets(self, w, add):
        d = abs(w.p.x - self.x)
        if not self.done and d < 80:
            add("laptop", d, (self, None))
            if w.level_key() in FX.CUTTER_LEVELS:
                add("cutter", d, (self, None))             # WIRE CUTTER (Level 3, 4, 5, 6, 8, 9)

    def use(self, w, tid, payload):
        if tid == "cutter":
            w.open_cutter(self, self.title.replace("LAPTOP", "WIRE BOX"))
            return
        w.open_modal("feature", self.lines, None, self.title, os=True)
        w.modal["feature"] = self

    def modal_done(self, w, m):
        self.done = True
        sound.play("unlock")
        self.effect(w)

    def prompt(self, w, tid, payload):
        if tid == "cutter":
            return (self.x, GROUND_Y - 120), ["[E]  CUT WIRES", "WIRE CUTTER"]
        return (self.x, GROUND_Y - 120), ["[E]  USE LAPTOP", "type the code"]

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if -100 < x < WIDTH + 100:
            SP.draw_terminal(surf, x, GROUND_Y, "open" if self.done else "locked", t)


class CodeLockDoor(DoorFeature):
    """Glass door with a numeric CODE LOCK.
    Code ta level e kothao ekta PAGE (kagoj) e lekha - PageFeature(..., key) nile collect hoy.
    Door er kache E chaple keypad khole. MASTER KEYCARD e kaj kore NA."""

    def __init__(self, x, key, label="", name="door"):
        super().__init__(x, "code", label, name)
        self.key = key
        self.code = PZ.code_for(key)

    def targets(self, w, add):
        pass                                    # kono tool (keycard soho) e khole na

    def near(self, w):
        return not self.opening and self.open_k <= 0 and abs(w.p.x - self.x) < 110

    def interact(self, w):
        if not self.near(w):
            return False
        if TL.TOOLS[w.tool]["id"] == "keycard":
            sound.play("lock")
            w.say("CODE LOCK  -  the KEYCARD does not work here")
            return True
        w.open_pad(self, self.label or "DOOR", self.code)
        return True

    def modal_done(self, w, m):
        self.open(w)
        sound.play("unlock")
        w.say("CODE ACCEPTED  -  DOOR OPEN")

    def draw(self, w, surf, cam, t):
        super().draw(w, surf, cam, t)
        x = self.x - cam
        if not (-80 < x < WIDTH + 80) or self.open_k >= 0.6:
            return
        pad = pygame.Rect(x + 14, GROUND_Y - 178, 34, 52)
        pygame.draw.rect(surf, (24, 26, 36), pad, border_radius=5)
        pygame.draw.rect(surf, (120, 126, 150), pad, 2, border_radius=5)
        pygame.draw.rect(surf, (60, 230, 130) if int(t * 2) % 2 else (20, 90, 50), (pad.x + 5, pad.y + 5, 24, 8))
        for r_ in range(3):
            for c_ in range(3):
                pygame.draw.circle(surf, (170, 176, 200), (pad.x + 9 + c_ * 8, pad.y + 22 + r_ * 8), 2)
        if self.near(w):
            f = get_font(14).render("[E]  ENTER CODE", True, (255, 220, 100))
            surf.blit(f, f.get_rect(center=(x, GROUND_Y - 196)))


class PageFeature(Feature):
    """Level e porte thaka PAGE (kagoj). Kache gele nijei collect hoy, code ta CODE LOCK er keypad e dekha jay."""

    def __init__(self, x, key, label, y=None):
        self.x = x
        self.spot = PZ.PageSpot(x, key, label, y if y is not None else GROUND_Y - 48)

    def update(self, w, dt):
        self.spot.update(w)

    def draw(self, w, surf, cam, t):
        self.spot.draw(w, surf, cam, t)


class SafeFeature(Feature):
    def __init__(self, x, cash=300):
        self.x, self.cash = x, cash
        self.opened = False
        self.melting = False

    def solids(self, w):
        return [] if self.opened else [pygame.Rect(self.x - 35, GROUND_Y - 90, 70, 90)]

    def targets(self, w, add):
        d = abs(w.p.x - self.x)
        if not self.opened and not self.melting and d < 100:
            add("thermite", d, (self, None))

    def use(self, w, tid, payload):
        self.melting = True
        w.start_melt(self, None)

    def update(self, w, dt):
        if not self.opened and not self.melting and f"safe{self.x}" in w.bonus_prior:
            self.opened = True          # ager bar gola hoyechilo - khali safe

    def melt_done(self, w, payload):
        self.opened = True
        w.bonus_new.add(f"safe{self.x}")
        w.money += self.cash
        sound.play("cash")
        w.say(f"SAFE MELTED  +{self.cash} Tk")
        w.burst(self.x, GROUND_Y - 50, (255, 150, 40), 26, 240, 0.8, grav=300)

    def prompt(self, w, tid, payload):
        return (self.x, GROUND_Y - 120), ["[E]  MELT SAFE", "2 seconds"]

    def draw(self, w, surf, cam, t):
        draw_safe(surf, self.x, cam, "melted" if self.opened else "closed", t)


class LootFeature(Feature):
    """Main target (briefcase / scepter / drive / core). requires(w) true hole nite pare."""

    def __init__(self, x, name, draw_fn, requires=None, y=None):
        self.x, self.name, self.draw_fn = x, name, draw_fn
        self.requires = requires or (lambda w: True)
        self.y = y if y is not None else GROUND_Y - 62

    def update(self, w, dt):
        p = w.p
        if not w.loot and p.alive and self.requires(w) and abs(p.x - self.x) < 70 and p.y > GROUND_Y - 90:
            w.loot = True
            sound.play("star")
            w.burst(self.x, self.y, (255, 220, 120), 30, 260, 0.9, grav=120)
            w.say(f"{self.name} STOLEN!")
            voice.say(f"{self.name.lower()} stolen. Now get out!")

    def draw(self, w, surf, cam, t):
        if w.loot:
            return
        x = self.x - cam
        if -80 < x < WIDTH + 80:
            self.draw_fn(surf, (x, self.y), t)
            f = get_font(14).render(self.name, True, (255, 230, 150))
            surf.blit(f, f.get_rect(midtop=(x, GROUND_Y + 14)))


class CaseFeature(Feature):
    """Kach er showcase. Punch = jore bhange (sensor on thakle ALARM). LASER BREAKER code = nissobde."""

    def __init__(self, x, name, draw_fn, width=72, item_y=None):
        self.x, self.name, self.draw_fn, self.w_ = x, name, draw_fn, width
        self.open = False
        self.sensor_on = True
        self.item_y = item_y if item_y is not None else GROUND_Y - 78

    def solids(self, w):
        return [] if self.open else [pygame.Rect(self.x - self.w_ // 2, GROUND_Y - 170, self.w_, 170)]

    def targets(self, w, add):
        d = abs(w.p.x - self.x)
        if not self.open and d < 130:
            add("laser", d + 20, (self, None))

    def use(self, w, tid, payload):
        w.open_modal("feature", [TL.LASER_CODE], None, "LASER BREAKER  -  type the code")
        w.modal["feature"] = self

    def modal_done(self, w, m):
        self.open = True
        sound.play("laser")
        w.burst(self.x, GROUND_Y - 90, (180, 230, 255), 26, 200, 0.8, grav=100)
        w.say("GLASS CUT  -  silent")

    def on_punch(self, w):
        if not self.open and abs(w.p.x - self.x) < 110:
            self.open = True
            sound.play("hit")
            w.burst(self.x, GROUND_Y - 90, (180, 230, 255), 34, 300, 0.9, grav=500)
            if self.sensor_on:
                sound.play("alarm")
                w.alarm(self.x, "GLASS SMASHED  -  ALARM!")
            else:
                w.say("Glass broken (sensor off)")

    def prompt(self, w, tid, payload):
        return (self.x, GROUND_Y - 160), ["[E]  CUT GLASS", "type code (silent)"]

    def draw(self, w, surf, cam, t):
        x = self.x - cam
        if not (-120 < x < WIDTH + 120):
            return
        ped = pygame.Rect(0, 0, 60, 60)
        ped.midbottom = (x, GROUND_Y)
        SP.v_gradient(surf, ped, (90, 76, 104), (46, 38, 58))
        pygame.draw.rect(surf, (210, 170, 80), ped, 2)
        if not w.loot:
            self.draw_fn(surf, (x, self.item_y), t)
        if not self.open:
            r = pygame.Rect(0, 0, self.w_, 112)
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
        f = get_font(14).render(self.name, True, (255, 150, 170))
        surf.blit(f, f.get_rect(midtop=(x, GROUND_Y + 14)))

    def loot_ready(self, w):
        return self.open


class SweepGridFeature(Feature):
    """Upor-nich othanama kora laser grid (Level 2 er moto). zones = [(x0, x1, phase)]"""
    MID, AMP, SPEED = 330, 200, 1.15

    def __init__(self, zones, color=(255, 60, 70)):
        self.zones = zones
        self.state = ["on"] * len(zones)
        self.color = color

    def beam_y(self, w, i):
        if self.state[i] == "rewired":
            return GROUND_Y - 30
        return self.MID + self.AMP * math.sin(w.t * self.SPEED + self.zones[i][2])

    def dist(self, w, i):
        x0, x1, _ = self.zones[i]
        px = w.p.x
        return 0 if x0 <= px <= x1 else min(abs(px - x0), abs(px - x1))

    def targets(self, w, add):
        for i in range(len(self.zones)):
            d = self.dist(w, i)
            if self.state[i] == "on" and d < 150:
                add("laser", d, (self, i))
                add("rewirer", d, (self, i))

    def use(self, w, tid, payload):
        i = payload
        if tid == "laser":
            w.open_modal("feature", [TL.LASER_CODE], i, "LASER BREAKER  -  type the code")
            w.modal["feature"] = self
        else:
            self.state[i] = "rewired"
            sound.play("hack")
            w.say("REWIRED  -  lasers now kill guards")

    def modal_done(self, w, m):
        self.state[m["target"]] = "broken"
        sound.play("laser")
        x0, x1, _ = self.zones[m["target"]]
        w.burst((x0 + x1) / 2, GROUND_Y - 120, (255, 200, 90), 22, 240, 0.7, grav=260)
        w.say("LASER GRID DISABLED")

    def prompt(self, w, tid, payload):
        x0, x1, _ = self.zones[payload]
        if tid == "laser":
            return ((x0 + x1) / 2, GROUND_Y - 150), ["[E]  DISABLE LASER", "type code"]
        return ((x0 + x1) / 2, GROUND_Y - 150), ["[E]  REWIRE LASER", "guards will die"]

    def update(self, w, dt):
        p = w.p
        if w.systems_off():
            return
        pr = p.rect()
        for i, (x0, x1, _) in enumerate(self.zones):
            if self.state[i] == "broken":
                continue
            band = pygame.Rect(x0, int(self.beam_y(w, i)) - 5, x1 - x0, 10)
            if self.state[i] == "on":
                if pr.colliderect(band):
                    if p.inv <= 0:
                        w.alarm(p.x, "ALARM!  Laser touched", zap=True)
                    w.hurt_player(1 if p.x > (x0 + x1) / 2 else -1, "laser")
            else:
                for g in list(w.guards) + list(w.dogs):
                    if g.alive and g.rect().colliderect(band):
                        g.die(w)
                        sound.play("zap")
                        w.burst(g.x, GROUND_Y - 30, (200, 20, 30), 22, 240, 0.9)
                        w.floats.append({"x": g.x, "y": GROUND_Y - 90, "t": 1.2, "txt": "ZAPPED!", "c": (255, 100, 100)})

    def draw(self, w, surf, cam, t):
        for i, (x0, x1, _) in enumerate(self.zones):
            a, b = x0 - cam, x1 - cam
            if b < -40 or a > WIDTH + 40:
                continue
            for px in (a, b):
                pygame.draw.rect(surf, (54, 56, 66), (px - 8, CEIL_Y, 16, GROUND_Y - CEIL_Y))
                pygame.draw.rect(surf, (90, 94, 108), (px - 8, CEIL_Y, 4, GROUND_Y - CEIL_Y))
            if self.state[i] == "broken" or w.systems_off():
                for px in (a, b):
                    pygame.draw.circle(surf, (40, 10, 10), (px, CEIL_Y + 30), 4)
                continue
            by = min(self.beam_y(w, i), GROUND_Y - 6)
            col = self.color if self.state[i] == "on" else (70, 255, 140)
            for px in (a, b):
                pygame.draw.circle(surf, col, (px, int(by)), 6)
            SP.glow(surf, ((a + b) / 2, by), (b - a) * 0.5, col, 40, 3)
            pygame.draw.line(surf, col, (a, by), (b, by), 5)
            pygame.draw.line(surf, (255, 255, 255), (a, by), (b, by), 1)


# ------------------------------------------------------------------
# HeistWorld
# ------------------------------------------------------------------
class HeistWorld(World):
    LEVEL_W = 6000
    SPAWN_X = 200
    LEDGES = []
    STARS = []
    CASH = []
    CASH_VALUE = 100
    GUARDS = []                 # (x0, x1) ba (x0, x1, "kind")
    DOGS = []
    CAMS = []
    CHECKPOINTS = []
    HINTS = []
    BAIL = 500
    GOAL_X = 5900
    TARGET = "LOOT"
    REWARD = 800
    WIN_TITLE = "HEIST COMPLETE!"
    SPOT_LINES = L1.SPOT_LINES
    CHAT_LINES = L1.CHAT_LINES
    GROUND_SEGS = None          # None = shobtai mati, nahole [(x0, x1)] (gorto thakle)
    DARK = False

    @property
    def GOAL_TEXT(self):
        return f"Steal the {self.TARGET}, then reach the exit."

    def __init__(self, save, save_fn):
        super().__init__(save, save_fn)

    # ---------- level hooks ----------
    def preset_loot(self):
        self.loot = True                # loot ager bar nise - ar nei, shudhu bahire jao

    def make_features(self):
        return []

    def make_cams(self):
        return []

    def make_guard(self, spec):
        return Guard2(spec[0], spec[1], self)

    def draw_background(self, surf, cam):
        surf.fill((20, 20, 30))

    def draw_fx(self, surf, cam):
        pass

    def extra_update(self, dt):
        pass

    # ---------- state ----------
    def restart(self):
        super().restart()
        self.level_w = self.LEVEL_W
        self.ledges = list(self.LEDGES)
        self.hints = self.HINTS
        self.bail = self.BAIL
        self.win_title = self.WIN_TITLE
        self.p = Player(self.SPAWN_X)
        self.p.riding = None
        self.cam = clamp(self.p.x - WIDTH * 0.38, 0, self.LEVEL_W - WIDTH)
        self.guards = [self.make_guard(s) for s in self.GUARDS]
        for g in self.guards:
            g.spot_lines, g.chat_lines = self.SPOT_LINES, self.CHAT_LINES
        self.dogs = [Dog(a, b) for a, b in self.DOGS]
        self.cams = [Camera(x, ph) for x, ph in self.CAMS] + self.make_cams()
        self.got = [False] * len(self.STARS)
        self.cash_taken = [False] * len(self.CASH)
        self.cp_on = [False] * len(self.CHECKPOINTS)
        self.loot = False
        self.emp_t = 0.0
        self.power_t = 0.0
        self.extra_danger = 0.0
        self.cd = {"emp": 0.0, "decoy": 0.0, "smoke": 0.0}
        self.decoy = None
        self.smoke = None
        self.melt = None
        self.noises, self.noise_id = [], 0
        self.in_sarc = None
        self.warned_exit = False
        self.won_loot = 0
        self.tool = 0
        self.wheel_sel = 0
        self.features = self.make_features()
        self.movers = []
        self.after_restart()

    def after_restart(self):
        pass

    def respawn(self):
        p = Player(self.CHECKPOINTS[self.cp_idx] if self.cp_idx >= 0 else self.SPAWN_X)
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
        self.in_sarc = None
        self.power_t = 0.0
        self.extra_danger = 0.0
        for f in self.features:
            f.on_respawn(self)
        self.state, self.state_t = "play", 0.0
        self.cam = clamp(p.x - WIDTH * 0.38, 0, self.LEVEL_W - WIDTH)

    # ---------- helpers ----------
    def systems_off(self):
        return self.emp_t > 0 or self.power_t > 0

    def add_noise(self, x, kind):
        self.noise_id += 1
        self.noises.append({"x": x, "kind": kind, "t": 1.5, "id": self.noise_id})

    def noise_for(self, who, rng):
        best = None
        for n in self.noises:
            if abs(n["x"] - who.x) < rng and (best is None or n["id"] > best["id"]):
                best = n
        if best is not None and isinstance(who, Dog):
            if best["kind"] == "bark" or abs(best["x"] - who.x) < 3:
                return None
        return best

    def smoke_hides(self, p):
        if self.in_sarc is not None:
            return True
        return bool(self.smoke) and abs(p.x - self.smoke["x"]) < SMOKE_R

    def smoke_hides_at(self, x):
        return bool(self.smoke) and abs(x - self.smoke["x"]) < SMOKE_R

    def alarm(self, x, text, zap=False):
        sound.play("zap" if zap else "alarm")
        if zap:
            sound.play("alarm", 0.6)
        self.add_noise(x, "glass")
        for g in self.guards:
            if g.alive:
                g.alert = max(g.alert, 8.0)
        for d in self.dogs:
            if d.alive:
                d.alert = max(d.alert, 8.0)
        self.say(text)

    def start_melt(self, feat, payload):
        self.melt = {"feat": feat, "payload": payload, "t": 0.0}
        sound.play("laser")

    # ---------- geometry ----------
    def ground_ok(self, x):
        if self.GROUND_SEGS is None:
            return True
        return any(a <= x <= b for a, b in self.GROUND_SEGS)

    def solids(self):
        out = []
        if self.GROUND_SEGS is None:
            out.append(pygame.Rect(-200, GROUND_Y, self.LEVEL_W + 400, 400))
        else:
            for a, b in self.GROUND_SEGS:
                out.append(pygame.Rect(a, GROUND_Y, b - a, 400))
        for f in self.features:
            out.extend(f.solids(self))
        return out

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
        if p.vy >= 0:
            lo, hi = p.x - p.W / 2, p.x + p.W / 2
            for s in sol:
                if s.top >= GROUND_Y and hi > s.left and lo < s.right and prev <= GROUND_Y + 0.5 and p.y >= GROUND_Y:
                    p.y, p.vy, p.on_ground = GROUND_Y, 0.0, True
            for x0, x1, y in self.ledges:
                if hi > x0 and lo < x1 and prev <= y + 2 and p.y >= y:
                    p.y, p.vy, p.on_ground = y, 0.0, True
            for m in self.movers:
                x0, x1, y = m.rect_top()
                if hi > x0 and lo < x1 and prev <= m.prev_y + 6 and p.y >= y - 1:
                    p.y, p.vy, p.on_ground = y, 0.0, True
                    p.riding = m

    # ---------- tools ----------
    def targets(self):
        p = self.p
        best, out = {}, {}

        def add(tid, dist, payload):
            if tid not in best or dist < best[tid]:
                best[tid], out[tid] = dist, payload

        for i, c in enumerate(self.cams):
            d = abs(c.x - p.x)
            if not c.hacked and d < 280:
                add("hacker", d, ("cam", i))
        for f in self.features:
            f.targets(self, add)
        return out

    def finish_modal(self, m):
        if m["kind"] == "camera":
            super().finish_modal(m)
        elif m.get("feature") is not None:
            m["feature"].modal_done(self, m)

    def use_tool(self):
        if self.in_sarc is not None:
            self.leave_sarc()
            return
        p = self.p
        if not self.can_do() or not p.on_ground:
            return
        if self.interact():
            return
        tid = TL.TOOLS[self.tool]["id"]
        tg = self.targets()
        if tid in ("emp", "decoy", "smoke"):
            return self.use_instant(tid)
        if tid == "cutter" and self.level_key() not in FX.CUTTER_LEVELS:
            self.say("WIRE CUTTER works only in Level " + FX.CUTTER_TEXT)
            return
        if tid in tg:
            tv = tg[tid]
            if tid == "hacker" and tv[0] == "cam":
                self.open_modal("camera", [TL.CAM_CODE], tv[1], "CCTV HACK  -  LITE 3D  -  type the code")
            else:
                tv[0].use(self, tid, tv[1])
            return
        names = {"hacker": "HACKER", "laser": "LASER BREAKER", "laptop": "LAPTOP", "rewirer": "REWIRER PRO",
                 "keycard": "MASTER KEYCARD", "thermite": "VAULT THERMITE", "cutter": "WIRE CUTTER"}
        if tg:
            need = next(iter(tg))
            self.say(f"Need {names.get(need, need)}  -  press Ctrl+Alt")
        else:
            self.say("Nothing to use here")

    def interact(self):
        """E chaple tool chhara onno kichu (jemon CODE LOCK keypad, sarcophagus). Level override kore."""
        for f in self.features:
            if f.interact(self):
                return True
        return False

    def remote_terminal(self):
        """L chaple laptop kothao theke je LOCKED terminal ta hack kore (shobcheye kachher ta). Na thakle None.
        Terminal feature gulo ke 'kache ache' dhore targets() chalie dekhi - tai level er custom terminal o kaj kore."""
        p = self.p
        x0 = p.x
        found = []
        try:
            for f in self.features:
                fx = getattr(f, "x", None)
                if fx is None:
                    continue
                got = {}

                def add(tid, dist, payload, _g=got):
                    if tid == "laptop":
                        _g["v"] = payload
                p.x = fx
                f.targets(self, add)
                if "v" in got:
                    found.append((abs(fx - x0), got["v"]))
        finally:
            p.x = x0
        if not found:
            return None
        payload = min(found, key=lambda q: q[0])[1]
        return lambda: payload[0].use(self, "laptop", payload[1])

    def leave_sarc(self):
        self.in_sarc = None
        self.p.hidden = False
        sound.play("hide")

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
            x = clamp(p.x + p.facing * 380, 60, self.level_w - 60)
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

    # ---------- combat ----------
    def press_knife(self):
        p = self.p
        if not self.can_do() or p.knife_cd > 0:
            return
        p.knife_cd, p.knife_t = L1.KNIFE_CD, L1.KNIFE_T
        sound.play("stab", 0.8)
        reach = pygame.Rect(0, int(p.y - 70), L1.KNIFE_REACH + 14, 80)
        if p.facing > 0:
            reach.left = int(p.x - 6)
        else:
            reach.right = int(p.x + 6)
        for g in self.guards:
            if g.alive and reach.colliderect(g.rect()):
                if hasattr(g, "stab"):
                    g.stab(self, p)
                else:
                    g.die(self)
                    self.floats.append({"x": g.x, "y": GROUND_Y - 90, "t": 1.0, "txt": "KNIFE!", "c": (255, 120, 120)})
        for d in self.dogs:
            if d.alive and reach.colliderect(d.rect()):
                d.die(self)
        for c in self.cams:
            if hasattr(c, "slash") and c.slash(self, reach):
                self.floats.append({"x": c.x, "y": c.y - 20, "t": 1.0, "txt": "DRONE DOWN!", "c": (255, 200, 90)})
        for f in self.features:
            f.on_knife(self, reach)

    def do_punch(self):
        p = self.p
        p.punch_cd = L1.PUNCH_CD
        p.punch_fired = True
        sound.play("punch")
        self.shake = 0.35
        self.waves.append({"x": p.x, "y": p.y, "t": 0.0})
        for g in self.guards:
            if g.alive and abs(g.x - p.x) <= L1.PUNCH_RADIUS and abs(p.y - GROUND_Y) < 90:
                if hasattr(g, "punched"):
                    g.punched(self)
                else:
                    g.die(self)
        for d in self.dogs:
            if d.alive and abs(d.x - p.x) <= L1.PUNCH_RADIUS and abs(p.y - GROUND_Y) < 90:
                d.die(self)
        for c in self.cams:
            if hasattr(c, "slash") and abs(c.x - p.x) < L1.PUNCH_RADIUS:
                c.slash(self, None)
        for f in self.features:
            f.on_punch(self)
        for i in range(24):
            dd = random.choice((-1, 1))
            self.parts.append({"x": p.x + dd * random.uniform(10, 40), "y": p.y - 4, "vx": dd * random.uniform(60, 420),
                               "vy": -random.uniform(40, 200), "life": 0.6, "max": 0.6, "c": (225, 225, 235),
                               "r": random.randint(2, 4), "g": 600})

    # ---------- update ----------
    def update(self, dt, keys):
        if not self.paused and not self.wheel and not self.modal:
            for k in self.cd:
                self.cd[k] = max(0.0, self.cd[k] - dt)
            self.emp_t = max(0.0, self.emp_t - dt)
            self.power_t = max(0.0, self.power_t - dt)
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
        p = self.p
        # thermite channel
        if self.melt is not None:
            keys = K0()
            self.melt["t"] += dt
            p.vx = 0
            if self.melt["t"] >= MELT_TIME:
                m = self.melt
                self.melt = None
                m["feat"].melt_done(self, m["payload"])

        if self.in_sarc is not None:
            left = keys[pygame.K_a] or keys[pygame.K_LEFT]
            right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
            jump = keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]
            p.hidden, p.vx, p.vy = True, 0.0, 0.0
            if left or right or jump:
                self.leave_sarc()
        else:
            for m in self.movers:
                m.update(self, dt)
            p.riding = None
            self.player_physics(dt, keys)
            if p.riding is not None:
                p.x = clamp(p.x + p.riding.dx, 16, self.level_w - 16)
        if self.state != "play":
            return
        p = self.p
        for f in self.features:
            f.update(self, dt)
        if self.state != "play":
            return
        if p.y > HEIGHT + 90:
            self.kill("fell")
            return

        for i, cx in enumerate(self.CHECKPOINTS):
            if not self.cp_on[i] and abs(p.x - cx) < 46 and p.y > GROUND_Y - 90:
                self.cp_on[i] = True
                self.cp_idx = i
                p.health = START_HEALTH
                sound.play("checkpoint")
                self.burst(cx, GROUND_Y - 50, (90, 235, 255), 16, 200, 0.8, grav=-80)
                self.say("CHECKPOINT SAVED  -  health refilled")
        for i, (sx, sy) in enumerate(self.STARS):
            if not self.got[i] and math.hypot(p.x - sx, (p.y - 28) - sy) < 34:
                self.got[i] = True
                sound.play("star")
                self.burst(sx, sy, GOLD, 18, 220, 0.8, grav=120)
                self.say(f"STAR {sum(self.got)} / {len(self.STARS)}")
        for i, (cx, cy) in enumerate(self.CASH):
            if not self.cash_taken[i] and abs(p.x - cx) < 30 and abs((p.y - 20) - cy) < 40:
                self.cash_taken[i] = True
                self.money += self.CASH_VALUE
                sound.play("cash")
                self.burst(cx, cy, (120, 255, 150), 12, 160, 0.6, grav=120)
                self.floats.append({"x": cx, "y": cy - 20, "t": 1.0, "txt": f"+{self.CASH_VALUE} Tk", "c": (120, 255, 150)})

        for b in self.bullets:
            b["x"] += b["vx"] * dt
            b["life"] -= dt
            if not p.hidden and p.alive and p.rect().inflate(6, 4).collidepoint(b["x"], b["y"]):
                b["life"] = 0
                self.hurt_player(1 if b["vx"] > 0 else -1, b.get("cause", "shot"))
                if self.state != "play":
                    return
        self.bullets = [b for b in self.bullets if b["life"] > 0 and -100 < b["x"] < self.level_w + 100]
        for g in self.guards:
            g.update(dt * self.guard_dt(), p, self)
        for d in self.dogs:
            d.update(dt * self.guard_dt(), p, self)
        if self.state != "play":
            return

        pts = [(p.x, p.y - 30), (p.x, p.y - 8), (p.x, p.y - 50)]
        for i, c in enumerate(self.cams):
            seen = (not self.systems_off() and not p.hidden and p.alive and not self.smoke_hides(p)
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

        self.extra_update(dt)
        if self.state != "play":
            return

        self.prompt = None
        tid = TL.TOOLS[self.tool]["id"]
        tg = self.targets()
        if self.can_do() and tid not in ("emp", "decoy", "smoke") and self.in_sarc is None:
            if tid in tg:
                self.prompt = (tid, tg[tid], True)
            elif tg:
                need = next(iter(tg))
                self.prompt = (need, tg[need], False)

        if p.x > self.GOAL_X - 70 and p.alive:
            if self.loot:
                self.state, self.state_t = "win", 0.0
                p.vx = 0
                p.hidden = False
                self.won_loot = 0 if self.looted_before else self.REWARD
                self.money += self.won_loot
                sound.stop_music(500)
                sound.play("win")
                self.burst(self.GOAL_X, GROUND_Y - 90, (255, 220, 120), 44, 320, 1.2, grav=160, r=4)
            elif not self.warned_exit:
                self.warned_exit = True
                self.say(f"Take the {self.TARGET} first!")
        if p.x < self.GOAL_X - 220:
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
        self.cam = clamp(self.cam, 0, self.level_w - WIDTH)

    # ---------- draw ----------
    def draw_world(self, surf):
        cam = int(self.cam)
        t = self.t
        self.draw_background(surf, cam)
        for f in self.features:
            f.draw(self, surf, cam, t)
        for x0, x1, y in self.ledges:
            if x1 - cam > -20 and x0 - cam < WIDTH + 20:
                SP.draw_ledge(surf, x0 - cam, x1 - cam, y)
        for m in self.movers:
            m.draw(surf, cam)
        for i, cx in enumerate(self.CHECKPOINTS):
            SP.draw_locker(surf, cx - cam, GROUND_Y, self.cp_on[i], t)
        for c in self.cams:
            saved = c.hacked
            c.hacked = saved or self.systems_off()
            c.draw(surf, cam, t)
            c.hacked = saved
        for i, (sx, sy) in enumerate(self.STARS):
            if not self.got[i]:
                SP.draw_star_icon(surf, (sx - cam, sy + math.sin(t * 3 + i) * 5), 15, True, t, True)
        for i, (cx, cy) in enumerate(self.CASH):
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
        if self.in_sarc is None:
            self.draw_player(surf, cam)
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
        self.draw_fx(surf, cam)
        self.draw_prompt_h(surf, cam)
        if self.emp_t > 0:
            a = int(150 * clamp(min(self.emp_t, 0.5) / 0.5, 0, 1) * (0.88 + 0.12 * math.sin(t * 30)))
            dk = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dk.fill((2, 4, 14, a))
            surf.blit(dk, (0, 0))
            img = self.f_small.render(f"EMP  {self.emp_t:.1f}s", True, (120, 210, 255))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 150)))

    def draw_prompt(self, surf, cam):
        pass

    def draw_prompt_h(self, surf, cam):
        p = self.p
        if self.state != "play":
            return
        dmax = max([c.danger for c in self.cams] + [self.extra_danger])
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
        if self.in_sarc is not None:
            img = self.f_small.render("HIDDEN  -  press E / move to come out", True, (200, 220, 255))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 150)))
            return
        if not self.prompt:
            return
        kind, payload, ok = self.prompt
        if kind == "hacker" and payload[0] == "cam":
            c = self.cams[payload[1]]
            lx, ly = c.lens(self.t)
            tgt = (lx, ly)
            lines = ["[E]  HACK CAMERA", "LITE 3D  -  type code"]
        else:
            res = payload[0].prompt(self, kind, payload[1])
            if not res:
                return
            tgt, lines = res
        tl = TL.tool_by_id(kind)["name"]
        keyn = next((t_["key"] for t_ in TL.TOOLS if t_["id"] == kind), "?")
        col = (120, 255, 190) if ok else (150, 150, 170)
        if not ok:
            lines = [f"Select {tl}", f"Ctrl+Alt  or  key {keyn}"]
        draw_dashed(surf, (p.x - cam, p.y - 50), (tgt[0] - cam, tgt[1]), col)
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

    def draw_player(self, surf, cam):
        if self.melt is not None and self.state == "play":
            p = self.p
            SP.draw_ninja(surf, p.x - cam, p.y, p.facing, self.t, "type", 0.0, 255)
            return
        super().draw_player(surf, cam)

    def draw_hud(self, surf, mouse):
        super().draw_hud(surf, mouse)
        if self.loot:
            f = get_font(15).render("LOOT SECURED  -  ESCAPE!", True, (255, 230, 150))
            surf.blit(f, f.get_rect(topright=(WIDTH - 14, 124)))
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
        if self.power_t > 0:
            img = get_font(26).render(f"POWER OFF  {self.power_t:.0f}s", True, (255, 200, 90))
            surf.blit(img, img.get_rect(center=(WIDTH // 2, 150)))


# ------------------------------------------------------------------
# Light overlay (dark level gulor jonno)
# ------------------------------------------------------------------
def light_overlay(surf, alpha, lights, tint=(2, 4, 12)):
    """lights: [("circle", (x, y), r, strength) | ("poly", [pts], strength)]  (screen coordinates)"""
    dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark.fill(tint + (alpha,))
    cut = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for L in lights:
        if L[0] == "circle":
            _, (x, y), r, s = L
            for i in range(6):
                rr = int(r * (1 - i * 0.14))
                pygame.draw.circle(cut, (255, 255, 255, int(s * alpha / 6)), (int(x), int(y)), rr)
        else:
            _, pts, s = L
            pygame.draw.polygon(cut, (255, 255, 255, int(s * alpha * 0.85)), pts)
    dark.blit(cut, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
    surf.blit(dark, (0, 0))


# ------------------------------------------------------------------
# Title card + runner
# ------------------------------------------------------------------
def play_title(screen, clock, title, lines, back_fn, icon_fn, say):
    t = 0.0
    f = get_font(50)
    f2 = get_font(22)
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
            voice.say(say)
        back_fn(screen, t * 40)
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((4, 4, 12, 200))
        screen.blit(dim, (0, 0))
        a = clamp(t / 0.6, 0, 1)
        img = f.render(title, True, GOLD)
        img.set_alpha(int(255 * a))
        screen.blit(img, img.get_rect(center=(WIDTH // 2, 170)))
        icon_fn(screen, (WIDTH // 2, 290), t)
        for i, ln in enumerate(lines):
            im = f2.render(ln, True, (210, 215, 235))
            im.set_alpha(int(255 * clamp((t - 0.8 - i * 0.4) / 0.5, 0, 1)))
            screen.blit(im, im.get_rect(center=(WIDTH // 2, 385 + i * 32)))
        im = get_font(15).render("ENTER = start", True, (130, 130, 160))
        screen.blit(im, im.get_rect(bottomright=(WIDTH - 16, HEIGHT - 12)))
        fade_overlay(screen, 1 - t / 0.6)
        if t > 5.0:
            return
        pygame.display.flip()


def run_heist(screen, clock, save, save_fn, world_cls, title, lines, back_fn, icon_fn, say):
    return L1.run_level(screen, clock, save, save_fn, world_cls,
                        lambda: play_title(screen, clock, title, lines, back_fn, icon_fn, say))


# ------------------------------------------------------------------
# Background helpers
# ------------------------------------------------------------------
class Tiled:
    """painter(surf, rnd) diye ekta tile ankhe, tarpor scroll kore repeat kore."""

    def __init__(self, tile_w, painter, seed=3, height=GROUND_Y, parallax=1.0):
        self.tw, self.par = tile_w, parallax
        self.surf = pygame.Surface((tile_w, height))
        painter(self.surf, random.Random(seed))

    def draw(self, surf, cam):
        off = int(cam * self.par) % self.tw
        x = -off
        while x < WIDTH:
            surf.blit(self.surf, (x, 0))
            x += self.tw


def draw_floor(surf, cam, top, bottom, line, stripe=None, seg=None, tile=80):
    r = pygame.Rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y)
    SP.v_gradient(surf, r, top, bottom)
    pygame.draw.line(surf, line, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
    if stripe:
        off = int(cam) % tile
        for x in range(-off, WIDTH, tile):
            pygame.draw.line(surf, stripe, (x, GROUND_Y + 3), (x - 24, HEIGHT), 1)


class Mover:
    """Chalonto platform (crane cargo). path: horizontal ba vertical. top = surface y."""

    def __init__(self, cx, y, w, axis="x", rng=140, speed=0.9, phase=0.0, color=(190, 90, 40)):
        self.cx0, self.y0, self.w, self.axis, self.rng, self.speed, self.phase = cx, y, w, axis, rng, speed, phase
        self.color = color
        self.cx, self.y = cx, y
        self.prev_y, self.dx = y, 0.0
        self.t = 0.0

    def update(self, w, dt):
        self.t += dt
        s = math.sin(self.t * self.speed + self.phase) * self.rng
        ox = self.cx
        self.prev_y = self.y
        if self.axis == "x":
            self.cx, self.y = self.cx0 + s, self.y0
        else:
            self.cx, self.y = self.cx0, self.y0 + s
        self.dx = self.cx - ox

    def rect_top(self):
        return (self.cx - self.w / 2, self.cx + self.w / 2, self.y)

    def draw(self, surf, cam):
        x = self.cx - cam
        if not (-200 < x < WIDTH + 200):
            return
        r = pygame.Rect(0, 0, int(self.w), 34)
        r.midtop = (x, self.y)
        pygame.draw.line(surf, (60, 60, 66), (x - self.w / 2 + 8, CEIL_Y - 10), (r.x + 8, r.y), 2)
        pygame.draw.line(surf, (60, 60, 66), (x + self.w / 2 - 8, CEIL_Y - 10), (r.right - 8, r.y), 2)
        SP.v_gradient(surf, r, self.color, SP.lerp_color(self.color, (0, 0, 0), 0.45))
        pygame.draw.rect(surf, (20, 20, 24), r, 2)
        for i in range(1, int(self.w // 22)):
            pygame.draw.line(surf, (20, 20, 24), (r.x + i * 22, r.y + 3), (r.x + i * 22, r.bottom - 3), 1)
