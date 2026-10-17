"""
bust3d.py - "BUSTED!"  3D ARREST ANIMATION  (Level 11 : ELITE POLICE).

Ninja 3 bar dhora porle (CATCH BAR 3 bar bhorle) elite police ninja ke handcuff pore JAIL e niye jay.
Eta sotti 3D:  camera ghure ghure (orbit) dekhay, perspective e floor / wall / jail cell / bar aka hoy,
police ar ninja "billboard" hishabe 3D te hete jay, cell er lohar dorja (3D te) khule bondho hoy.

Use:
    b = Bust3D(cop_facing)
    b.update(dt)          # b.done == True hole shesh
    b.draw(surf)
"""
import math
import random

import pygame

import police
import sound
import sprites as SP
from animation import WIDTH, HEIGHT, get_font

NEAR = 40.0
FOCAL = 640.0
HORIZON = HEIGHT * 0.50
DURATION = 10.4

# ---- timeline (seconds) ----
T_WALK_END = 5.2          # ninja ar police cell er shamne
T_DOOR_OPEN = (5.0, 5.9)
T_ENTER = (5.9, 7.2)      # ninja cell e dhoke
T_DOOR_SHUT = (7.4, 8.3)
T_CLANG = 8.3

CELL_X0, CELL_X1 = 760.0, 960.0
WALL_Z = 520.0
CELL_BACK_Z = 780.0
WALK_Z = 200.0
WALL_H = 330.0


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def ease(k):
    k = clamp(k, 0.0, 1.0)
    return k * k * (3 - 2 * k)


def seg(t, a, b):
    """t, [a,b] er moddhe 0..1"""
    return clamp((t - a) / (b - a), 0.0, 1.0)


def mix(c1, c2, k):
    k = clamp(k, 0.0, 1.0)
    return (int(c1[0] + (c2[0] - c1[0]) * k), int(c1[1] + (c2[1] - c1[1]) * k), int(c1[2] + (c2[2] - c1[2]) * k))


FOG = (6, 8, 18)


def fog(col, zc, far=2300.0):
    return mix(col, FOG, zc / far)


# ------------------------------------------------------------------
# tiny 3D camera
# ------------------------------------------------------------------
class Cam3D:
    def __init__(self):
        self.x = self.y = self.z = 0.0
        self.yaw = 0.0
        self.shake = (0.0, 0.0)

    def look(self, tx, ty, tz, ang, dist, height):
        """target (tx,ty,tz) er chardike ang (radian) kone, dist doore theke, height uchute theke dekhe."""
        self.x = tx + math.sin(ang) * dist
        self.z = tz - math.cos(ang) * dist
        self.y = height
        self.yaw = ang

    def to_cam(self, x, y, z):
        dx, dz = x - self.x, z - self.z
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        xr = dx * c + dz * s                 # right
        zf = -dx * s + dz * c                # forward
        return (xr, y - self.y, zf)

    def to_screen(self, p):
        xr, yr, zf = p
        k = FOCAL / zf
        return (WIDTH / 2 + xr * k + self.shake[0], HORIZON - yr * k + self.shake[1])

    def proj(self, x, y, z):
        """(sx, sy, scale) ba None (camera er pichone)"""
        p = self.to_cam(x, y, z)
        if p[2] < NEAR:
            return None
        sx, sy = self.to_screen(p)
        return sx, sy, FOCAL / p[2]

    def depth(self, x, y, z):
        return self.to_cam(x, y, z)[2]


def clip_near(pts):
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        ina, inb = a[2] >= NEAR, b[2] >= NEAR
        if ina:
            out.append(a)
        if ina != inb:
            t = (NEAR - a[2]) / (b[2] - a[2])
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, NEAR))
    return out


def poly(surf, cam, pts3, col, width=0, shade=True):
    """3D polygon (world coords) ankhe.  Camera er pichoner ongsho clip kore."""
    cp = [cam.to_cam(*p) for p in pts3]
    cp = clip_near(cp)
    if len(cp) < 3:
        return
    zc = sum(p[2] for p in cp) / len(cp)
    c = fog(col, zc) if shade else col
    sp = [cam.to_screen(p) for p in cp]
    xs = [q[0] for q in sp]
    if max(xs) < -50 or min(xs) > WIDTH + 50:
        return
    try:
        pygame.draw.polygon(surf, c, sp, width)
    except (ValueError, TypeError):
        pass


def line3(surf, cam, a, b, col, width=2, shade=True):
    pa, pb = cam.to_cam(*a), cam.to_cam(*b)
    cl = []
    if pa[2] >= NEAR and pb[2] >= NEAR:
        cl = [pa, pb]
    elif pa[2] >= NEAR:
        t = (NEAR - pa[2]) / (pb[2] - pa[2])
        cl = [pa, (pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t, NEAR)]
    elif pb[2] >= NEAR:
        t = (NEAR - pb[2]) / (pa[2] - pb[2])
        cl = [(pb[0] + (pa[0] - pb[0]) * t, pb[1] + (pa[1] - pb[1]) * t, NEAR), pb]
    if len(cl) < 2:
        return
    zc = (cl[0][2] + cl[1][2]) / 2
    c = fog(col, zc) if shade else col
    w = max(1, int(width * FOCAL / max(zc, NEAR)))
    pygame.draw.line(surf, c, cam.to_screen(cl[0]), cam.to_screen(cl[1]), min(w, 40))


# ------------------------------------------------------------------
# Scene
# ------------------------------------------------------------------
class Bust3D:
    def __init__(self, ninja_x=0.0, rounds=3):
        self.t = 0.0
        self.done = False
        self.cam = Cam3D()
        self.rounds = rounds
        self.clanged = False
        self.flash = 0.0
        self.rnd = random.Random(7)
        self.tmp = pygame.Surface((SP.TW, SP.TH), pygame.SRCALPHA)
        self.noise_t = 0.0
        self.posters = [(-380 + i * 230, self.rnd.randint(150, 210)) for i in range(6)]
        sound.play("siren", 0.7)
        sound.play("alarm", 0.5)

    # ---------- timeline ----------
    def door_angle(self):
        """0 = bondho, 1.8 rad = khola"""
        t = self.t
        if t < T_DOOR_OPEN[0]:
            return 0.0
        if t < T_DOOR_OPEN[1] + 0.01 or t < T_DOOR_SHUT[0]:
            return 1.85 * ease(seg(t, *T_DOOR_OPEN))
        return 1.85 * (1.0 - ease(seg(t, *T_DOOR_SHUT)))

    def ninja_pos(self):
        t = self.t
        walk = ease(seg(t, 0.15, T_WALK_END))
        x = -200 + (CELL_X0 + 100 + 200) * walk
        z = WALK_Z
        if t >= T_ENTER[0]:
            k = ease(seg(t, *T_ENTER))
            z = WALK_Z + (CELL_BACK_Z - 70 - WALK_Z) * k
            x = (CELL_X0 + 100) + 0
        else:
            x = min(x, CELL_X0 + 100)
        return x, z

    def cop_pos(self):
        t = self.t
        nx, _ = self.ninja_pos()
        if t < T_ENTER[0]:
            return nx - 78, WALK_Z - 6, 1
        if t < T_DOOR_SHUT[1] + 0.4:
            return CELL_X0 + 100 - 78, WALK_Z - 6, 1
        k = seg(t, T_DOOR_SHUT[1] + 0.4, DURATION)
        return CELL_X0 + 22 - 330 * k * k, WALK_Z - 6, -1

    def ninja_anim(self):
        t = self.t
        if t < T_ENTER[1]:
            moving = t < T_WALK_END or t >= T_ENTER[0]
            return "walk" if moving else "idle"
        return "idle"

    # ---------- update ----------
    def update(self, dt):
        self.t += dt
        self.flash = max(0.0, self.flash - dt)
        if self.t >= T_CLANG and not self.clanged:
            self.clanged = True
            self.flash = 0.35
            sound.play("lock", 1.0)
            sound.play("jail", 0.9)
        if self.t >= DURATION:
            self.done = True
        # camera
        t = self.t
        nx, nz = self.ninja_pos()
        cx, cz = self.cop_pos()[0], WALK_Z
        mid_x = (nx + cx) / 2
        tx = mid_x + 60
        tz = WALK_Z + (CELL_BACK_Z - WALK_Z) * 0.55 * ease(seg(t, T_ENTER[0] - 0.4, T_ENTER[1]))
        k = t / DURATION
        ang = -0.62 + 1.05 * k
        end = ease(seg(t, T_CLANG - 0.4, DURATION - 0.6))
        dist = (820 - 140 * ease(seg(t, 0, 6))) - 220 * end
        height = 190 - 60 * ease(seg(t, 0, 6)) - 30 * end
        if end > 0:
            tx = tx + (CELL_X0 + 100 - tx) * end
            ang = ang * (1 - 0.8 * end)
        self.cam.look(tx, 80.0, tz, ang, dist, height)
        if self.flash > 0:
            m = self.flash * 16
            self.cam.shake = (random.uniform(-m, m), random.uniform(-m, m))
        else:
            self.cam.shake = (math.sin(t * 9) * 1.2 if t < T_WALK_END else 0.0, 0.0)

    # ---------- billboards ----------
    def billboard(self, surf, who, x, y, z, facing, anim, t):
        cam = self.cam
        pr = cam.proj(x, y, z)
        if pr is None:
            return
        sx, sy, sc = pr
        tmp = self.tmp
        tmp.fill((0, 0, 0, 0))
        if who == "cop":
            SP.draw_guard(tmp, SP.OX, SP.OY, facing, t, anim, 0.0, pal=police.ELITE_PAL, s=0.72)
        else:
            SP.draw_ninja(tmp, SP.OX, SP.OY, facing, t, anim)
        k = sc * 2.15
        w, h = max(2, int(SP.TW * k)), max(2, int(SP.TH * k))
        img = pygame.transform.smoothscale(tmp, (w, h))
        zc = FOCAL / sc
        dark = clamp(zc / 2300.0, 0.0, 0.8)
        if dark > 0.05:
            img.fill((int(255 * (1 - dark)),) * 3 + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        # shadow
        shw = pygame.Surface((int(70 * k), max(2, int(14 * k))), pygame.SRCALPHA)
        pygame.draw.ellipse(shw, (0, 0, 0, 110), shw.get_rect())
        surf.blit(shw, shw.get_rect(center=(int(sx), int(sy))))
        surf.blit(img, (int(sx - SP.OX * k), int(sy - SP.OY * k)))
        if who == "ninja" and self.t < T_ENTER[1]:
            # handcuffs
            hx, hy = sx + facing * 20 * k, sy - 40 * k
            r = max(2, int(4 * k))
            pygame.draw.circle(surf, (210, 214, 230), (int(hx), int(hy)), r, 2)
            pygame.draw.circle(surf, (210, 214, 230), (int(hx + 7 * k), int(hy + 2 * k)), r, 2)
        if who == "cop":                                         # siren light on the cap
            on = int(t * 6) % 2 == 0
            col = (255, 50, 60) if on else (70, 120, 255)
            SP.glow(surf, (sx + 2 * k, sy - 128 * k * 0.9), max(6, int(16 * k)), col, 90, 3)
        return sx, sy, k

    # ---------- scenery ----------
    def draw_room(self, surf):
        cam = self.cam
        t = self.t
        # ceiling-dark backdrop
        surf.fill((8, 9, 18))
        # floor
        step = 120
        for ix in range(-9, 13):
            for iz in range(10):
                x0 = ix * step
                z1 = WALL_Z - iz * step
                z0 = z1 - step
                dark = (ix + iz) % 2 == 0
                col = (58, 62, 78) if dark else (46, 50, 64)
                poly(surf, cam, [(x0, 0, z0), (x0 + step, 0, z0), (x0 + step, 0, z1), (x0, 0, z1)], col)
        # back wall (cell opening bichhe)
        for xa, xb in ((-1000, CELL_X0), (CELL_X1, 1500)):
            poly(surf, cam, [(xa, 0, WALL_Z), (xb, 0, WALL_Z), (xb, WALL_H, WALL_Z), (xa, WALL_H, WALL_Z)], (84, 90, 112))
        poly(surf, cam, [(CELL_X0, 250, WALL_Z), (CELL_X1, 250, WALL_Z), (CELL_X1, WALL_H, WALL_Z), (CELL_X0, WALL_H, WALL_Z)], (70, 74, 96))
        # wall stripe + panel lines
        poly(surf, cam, [(-1000, 120, WALL_Z - 1), (1500, 120, WALL_Z - 1), (1500, 134, WALL_Z - 1), (-1000, 134, WALL_Z - 1)], (40, 60, 150))
        for xx in range(-1000, 1500, 150):
            line3(surf, cam, (xx, 0, WALL_Z - 1), (xx, WALL_H, WALL_Z - 1), (60, 66, 88), 1)
        # WANTED posters (ninja!)
        for px, ph in self.posters:
            if CELL_X0 - 60 < px < CELL_X1 + 60:
                continue
            poly(surf, cam, [(px, ph - 70, WALL_Z - 2), (px + 70, ph - 70, WALL_Z - 2), (px + 70, ph + 30, WALL_Z - 2), (px, ph + 30, WALL_Z - 2)], (214, 196, 150))
            poly(surf, cam, [(px + 20, ph - 40, WALL_Z - 3), (px + 50, ph - 40, WALL_Z - 3), (px + 50, ph - 8, WALL_Z - 3), (px + 20, ph - 8, WALL_Z - 3)], (30, 30, 44))
        # sign
        poly(surf, cam, [(CELL_X0 - 40, 280, WALL_Z - 3), (CELL_X1 + 40, 280, WALL_Z - 3), (CELL_X1 + 40, 322, WALL_Z - 3), (CELL_X0 - 40, 322, WALL_Z - 3)], (190, 40, 50))
        # ---- cell inside ----
        poly(surf, cam, [(CELL_X0, 0, CELL_BACK_Z), (CELL_X1, 0, CELL_BACK_Z), (CELL_X1, WALL_H, CELL_BACK_Z), (CELL_X0, WALL_H, CELL_BACK_Z)], (50, 54, 72))
        poly(surf, cam, [(CELL_X0, 0, WALL_Z), (CELL_X0, 0, CELL_BACK_Z), (CELL_X0, WALL_H, CELL_BACK_Z), (CELL_X0, WALL_H, WALL_Z)], (64, 68, 90))
        poly(surf, cam, [(CELL_X1, 0, WALL_Z), (CELL_X1, 0, CELL_BACK_Z), (CELL_X1, WALL_H, CELL_BACK_Z), (CELL_X1, WALL_H, WALL_Z)], (58, 62, 84))
        poly(surf, cam, [(CELL_X0, 0, WALL_Z), (CELL_X1, 0, WALL_Z), (CELL_X1, 0, CELL_BACK_Z), (CELL_X0, 0, CELL_BACK_Z)], (36, 38, 50))
        # bench
        poly(surf, cam, [(CELL_X0 + 10, 34, CELL_BACK_Z - 60), (CELL_X0 + 150, 34, CELL_BACK_Z - 60), (CELL_X0 + 150, 34, CELL_BACK_Z - 5), (CELL_X0 + 10, 34, CELL_BACK_Z - 5)], (120, 96, 70))
        poly(surf, cam, [(CELL_X0 + 10, 0, CELL_BACK_Z - 5), (CELL_X0 + 150, 0, CELL_BACK_Z - 5), (CELL_X0 + 150, 34, CELL_BACK_Z - 5), (CELL_X0 + 10, 34, CELL_BACK_Z - 5)], (90, 70, 50))
        # barred window + moon
        wx0, wx1, wy0, wy1 = CELL_X0 + 100, CELL_X0 + 170, 190, 270
        poly(surf, cam, [(wx0, wy0, CELL_BACK_Z - 1), (wx1, wy0, CELL_BACK_Z - 1), (wx1, wy1, CELL_BACK_Z - 1), (wx0, wy1, CELL_BACK_Z - 1)], (14, 20, 50), shade=False)
        for bx in range(int(wx0) + 12, int(wx1), 18):
            line3(surf, cam, (bx, wy0, CELL_BACK_Z - 2), (bx, wy1, CELL_BACK_Z - 2), (150, 154, 172), 2)
        # cell light (red/blue pulse bahire theke)
        # ---- ceiling lamps (corridor) ----
        for lx in range(-400, 1400, 400):
            line3(surf, cam, (lx, WALL_H + 60, WALL_Z - 120), (lx, WALL_H - 20, WALL_Z - 120), (60, 60, 70), 2)
            pr = cam.proj(lx, WALL_H - 26, WALL_Z - 120)
            if pr:
                SP.glow(surf, (pr[0], pr[1]), max(8, int(40 * pr[2])), (255, 240, 190), 55, 3)

    def draw_door(self, surf):
        cam = self.cam
        ang = self.door_angle()
        hx, hz = CELL_X0, WALL_Z
        c, s = math.cos(ang), math.sin(ang)
        # ang barle dorja camera r dike (z komar dike) khole
        def pt(u, y):
            return (hx + u * c, y, hz - u * s)
        w = CELL_X1 - CELL_X0
        flash = self.flash > 0
        col = (255, 255, 255) if flash else (176, 184, 206)
        for r_y in (6, 120, 244):
            line3(surf, cam, pt(0, r_y), pt(w, r_y), (110, 116, 138), 5)
        for i in range(0, 11):
            u = i * w / 10.0
            line3(surf, cam, pt(u, 0), pt(u, 250), col, 4)
        line3(surf, cam, pt(0, 0), pt(0, 250), (120, 126, 150), 7)
        line3(surf, cam, pt(w, 0), pt(w, 250), (120, 126, 150), 7)
        # frame
        line3(surf, cam, (CELL_X0, 0, WALL_Z), (CELL_X0, 250, WALL_Z), (130, 136, 160), 8)
        line3(surf, cam, (CELL_X1, 0, WALL_Z), (CELL_X1, 250, WALL_Z), (130, 136, 160), 8)
        line3(surf, cam, (CELL_X0, 250, WALL_Z), (CELL_X1, 250, WALL_Z), (130, 136, 160), 8)

    # ---------- draw ----------
    def draw(self, surf):
        t = self.t
        self.draw_room(surf)
        cam = self.cam
        items = []
        nx, nz = self.ninja_pos()
        cx, cz, cf = self.cop_pos()
        ninja_anim = self.ninja_anim()
        cop_anim = "walk" if (t < T_WALK_END or t > T_DOOR_SHUT[1] + 0.4) else "idle"
        items.append((cam.depth(nx, 0, nz), "ninja", (nx, 0, nz, 1, ninja_anim)))
        items.append((cam.depth(cx, 0, cz), "cop", (cx, 0, cz, cf, cop_anim)))
        items.append((cam.depth(CELL_X0 + 100, 0, WALL_Z), "door", None))
        items.sort(key=lambda it: -it[0])
        for _, kind, a in items:
            if kind == "door":
                self.draw_door(surf)
            else:
                x, y, z, f, an = a
                self.billboard(surf, kind, x, y, z, f, an, t * (1.9 if an == "walk" else 1.0))
        # police light wash (lal / nil)
        on = int(t * 4) % 2 == 0
        wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        wash.fill((255, 40, 60, 26) if on else (60, 110, 255, 26))
        surf.blit(wash, (0, 0))
        # vignette bars (cinematic)
        pygame.draw.rect(surf, (0, 0, 0), (0, 0, WIDTH, 44))
        pygame.draw.rect(surf, (0, 0, 0), (0, HEIGHT - 44, WIDTH, 44))
        # titles
        if t < 2.6:
            a = clamp(1.0 - max(0.0, t - 1.8) / 0.8, 0, 1)
            k = 1.0 + 0.25 * max(0.0, 1 - t * 3)
            big = get_font(int(58 * k), True).render("BUSTED!", True, (255, 70, 80))
            big.set_alpha(int(255 * a))
            surf.blit(big, big.get_rect(center=(WIDTH // 2, 120)))
            sub = get_font(22).render(f"ELITE POLICE caught you {self.rounds} times", True, (255, 230, 150))
            sub.set_alpha(int(255 * a))
            surf.blit(sub, sub.get_rect(center=(WIDTH // 2, 166)))
        elif T_WALK_END - 0.2 < t < T_ENTER[1] + 0.6:
            sub = get_font(24).render("Taking you to the holding cell...", True, (230, 235, 255))
            surf.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT - 70)))
        if t >= T_CLANG:
            a = clamp((t - T_CLANG) / 0.5, 0, 1)
            big = get_font(54, True).render("LOCKED UP!", True, (255, 80, 90))
            big.set_alpha(int(255 * a))
            surf.blit(big, big.get_rect(center=(WIDTH // 2, 120)))
        if self.flash > 0:
            fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fl.fill((255, 255, 255, int(190 * self.flash / 0.35)))
            surf.blit(fl, (0, 0))
        # fade in / out
        if t < 0.35:
            fo = pygame.Surface((WIDTH, HEIGHT))
            fo.fill((0, 0, 0))
            fo.set_alpha(int(255 * (1 - t / 0.35)))
            surf.blit(fo, (0, 0))
        if t > DURATION - 0.5:
            fo = pygame.Surface((WIDTH, HEIGHT))
            fo.fill((0, 0, 0))
            fo.set_alpha(int(255 * (t - (DURATION - 0.5)) / 0.5))
            surf.blit(fo, (0, 0))
