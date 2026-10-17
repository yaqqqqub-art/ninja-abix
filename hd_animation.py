"""
hd_animation.py - HD ANIMATION pack  (V12)

Shob kichu pure pygame (extra install lage na).  Chobi gulo 2x boro kore ake, tarpor smoothscale kore = anti-aliased / HD.
Cache kora, tai mobile e o halka.

  GOD MODE animation (ELITE police er samne):
     draw_god_shield()   hex-grid dome + rim glow + upor-nichu sweep line + rotating halo
     spawn_block()       samne theke mar dile:  expanding ring + hex shards + flash + "GOD MODE" stamp (RGB split)
  Mar khele:
     spawn_hit()         red spark + slash line + glow (big=True hole shockwave)
     spawn_ko()          stars ring + dust + "DOWN!" stamp
  Extra:
     draw_siren()        police light cone (lal/nil)
     rgb_text()          rainbow outline text (banner e)
     glow()              smooth radial glow (cache)

Use (police.py te kora ache):
     hd = hd_animation.get(world)      # per-world manager
     hd.update(dt) ;  hd.draw(surf, cam)
"""
import math
import random

import pygame

from animation import get_font

GOLD = (255, 214, 90)


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------
def _clamp(v, a=0.0, b=1.0):
    return a if v < a else (b if v > b else v)


def ease_out(k):
    k = _clamp(k)
    return 1 - (1 - k) ** 3


def ease_back(k):
    """0 -> 1 with overshoot (pop)."""
    k = _clamp(k)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (k - 1) ** 3 + c1 * (k - 1) ** 2


def hsv(h, s=0.8, v=1.0):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


_cache = {}


def glow(surf, pos, r, col, alpha=120, power=2.0):
    """Smooth radial glow (cache kora, alpha gradient)."""
    r = int(max(2, r))
    key = ("glow", r, col, int(alpha), power)
    s = _cache.get(key)
    if s is None:
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        steps = min(r, 36)
        for i in range(steps, 0, -1):
            k = i / steps
            rad = int(r * k)
            a = int(alpha * (1 - k) ** power) if power else int(alpha)
            pygame.draw.circle(s, (*col, a), (r, r), rad)
        _cache[key] = s
        if len(_cache) > 400:
            _cache.clear()
    surf.blit(s, (int(pos[0] - r), int(pos[1] - r)), special_flags=pygame.BLEND_RGBA_ADD)


# ------------------------------------------------------------------
# GOD MODE shield  (hex dome, right-facing base, flip for left)
# ------------------------------------------------------------------
SW, SH = 86, 128           # shield size (ninja dike mukh kore thakle dan dike)


def _hex_pts(cx, cy, r):
    return [(cx + r * math.cos(math.pi / 3 * i), cy + r * math.sin(math.pi / 3 * i)) for i in range(6)]


def _shield_layers():
    """-> (base, mask). 2x supersample -> smoothscale (HD edge)."""
    c = _cache.get("shield_layers")
    if c:
        return c
    k = 2
    w, h = SW * k, SH * k
    base = pygame.Surface((w, h), pygame.SRCALPHA)
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    ell = pygame.Rect(-w, 0, 2 * w, h)
    # soft fill gradient (left edge strong -> right edge faded)
    for i in range(w):
        a = int(70 * (1 - i / w) + 14)
        pygame.draw.line(base, (255, 215, 100, a), (i, 0), (i, h))
    m2 = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(m2, (255, 255, 255, 255), ell)
    base.blit(m2, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)                 # ellipse shape e kete nao
    pygame.draw.ellipse(mask, (255, 255, 255, 255), ell)
    # hex grid inside
    hexl = pygame.Surface((w, h), pygame.SRCALPHA)
    r = 17 * k
    dx, dy = r * 1.5, r * math.sqrt(3)
    for col in range(-1, int(w / dx) + 2):
        for row in range(-1, int(h / dy) + 2):
            cx = col * dx
            cy = row * dy + (dy / 2 if col % 2 else 0)
            pygame.draw.polygon(hexl, (255, 236, 160, 90), _hex_pts(cx, cy, r - 2), 2)
    hexl.blit(m2, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    base.blit(hexl, (0, 0))
    # bright rim
    pygame.draw.ellipse(base, (255, 240, 170, 235), ell, 6 * k // 2)
    pygame.draw.ellipse(base, (255, 255, 255, 120), ell.inflate(-10 * k, -10 * k), 2)
    base = pygame.transform.smoothscale(base, (SW, SH))
    mask = pygame.transform.smoothscale(mask, (SW, SH))
    _cache["shield_layers"] = (base, mask)
    return base, mask


def draw_god_shield(surf, x, gy, facing, t, flash=0.0, stagger=False):
    """x = cop er x (screen), gy = ground y.  facing = +1 dan / -1 bam.  flash 0..1 = mar thekano muhurto."""
    base, mask = _shield_layers()
    pulse = 0.72 + 0.18 * math.sin(t * 4.5)
    layer = base.copy()
    # sweep line (upor theke nichu)
    sweep = pygame.Surface((SW, SH), pygame.SRCALPHA)
    yy = int((t * 90) % (SH + 40)) - 20
    for dy, a in ((-3, 40), (-2, 90), (-1, 160), (0, 230), (1, 160), (2, 90), (3, 40)):
        pygame.draw.line(sweep, (255, 250, 200, a), (0, yy + dy), (SW, yy + dy))
    sweep.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    layer.blit(sweep, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    a = _clamp(pulse + flash * 0.9, 0.0, 1.0)
    if stagger:
        a *= 0.35                                  # mar khele shield durbol
    layer.set_alpha(int(255 * a))
    if flash > 0:
        glow(surf, (x + facing * 34, gy - 62), 70, (255, 224, 120), int(150 * flash), 2.0)
    top = gy - SH + 14
    if facing >= 0:
        surf.blit(layer, (int(x + 12), int(top)))
    else:
        surf.blit(pygame.transform.flip(layer, True, False), (int(x - 12 - SW), int(top)))


def draw_halo(surf, x, y, t, col=GOLD, r=15):
    """Matha r upor ghurte thaka halo (3 ta dot + ring)."""
    rect = pygame.Rect(0, 0, r * 2, int(r * 0.7))
    rect.center = (int(x), int(y))
    pygame.draw.ellipse(surf, col, rect, 2)
    for i in range(3):
        a = t * 3.2 + i * 2.094
        px, py = x + math.cos(a) * r, y + math.sin(a) * r * 0.35
        glow(surf, (px, py), 7, col, 140, 1.5)
        pygame.draw.circle(surf, (255, 255, 235), (int(px), int(py)), 2)


# ------------------------------------------------------------------
# Siren cone
# ------------------------------------------------------------------
def draw_siren(surf, x, y, t, facing=1):
    on = int(t * 6) % 2 == 0
    col = (255, 50, 70) if on else (70, 130, 255)
    glow(surf, (x, y), 34, col, 150, 2.0)
    pts = [(x, y), (x + facing * 150, y - 44), (x + facing * 150, y + 40)]
    cone = pygame.Surface((160, 100), pygame.SRCALPHA)
    ox, oy = (0 if facing > 0 else 160), 50
    pp = [(ox, oy), (ox + facing * 150, oy - 44), (ox + facing * 150, oy + 40)]
    pygame.draw.polygon(cone, (*col, 26), pp)
    surf.blit(cone, (int(x - ox), int(y - oy)), special_flags=pygame.BLEND_RGBA_ADD)
    pygame.draw.circle(surf, col, (int(x), int(y)), 4)
    del pts


# ------------------------------------------------------------------
# Rainbow text
# ------------------------------------------------------------------
def rgb_text(surf, text, center, size, t, alpha=255, bold=True):
    f = get_font(size, bold)
    base = f.render(text, True, (255, 255, 255))
    for k, (dx, dy) in enumerate(((-2, 0), (2, 0), (0, -2), (0, 2))):
        o = f.render(text, True, hsv(t * 0.6 + k * 0.25, 0.9, 1.0))
        o.set_alpha(alpha)
        surf.blit(o, o.get_rect(center=(center[0] + dx, center[1] + dy)))
    base.set_alpha(alpha)
    surf.blit(base, base.get_rect(center=center))


# ------------------------------------------------------------------
# Effects manager (world space)
# ------------------------------------------------------------------
class _Fx:
    __slots__ = ("kind", "x", "y", "t", "life", "d")

    def __init__(self, kind, x, y, life, **d):
        self.kind, self.x, self.y, self.t, self.life, self.d = kind, x, y, 0.0, life, d


class Manager:
    def __init__(self):
        self.fx = []
        self.shake = 0.0

    # ----- spawners -----
    def block(self, x, y, facing):
        """GOD MODE:  samne theke mar thekano."""
        self.fx.append(_Fx("ring", x + facing * 30, y, 0.55, col=(255, 224, 120), r1=78, w=5))
        self.fx.append(_Fx("ring", x + facing * 30, y, 0.4, col=(255, 255, 255), r1=48, w=3))
        self.fx.append(_Fx("flash", x + facing * 30, y, 0.3, col=(255, 224, 120), r=90))
        for _ in range(12):
            a = random.uniform(-1.1, 1.1) + (0 if facing > 0 else math.pi)
            sp = random.uniform(160, 340)
            self.fx.append(_Fx("shard", x + facing * 26, y + random.uniform(-26, 26), random.uniform(0.45, 0.8),
                               vx=math.cos(a) * sp, vy=math.sin(a) * sp - 60, rot=random.uniform(0, 6.28),
                               vr=random.uniform(-9, 9), s=random.uniform(5, 10)))
        self.fx.append(_Fx("stamp", x, y - 96, 1.0, text="GOD MODE", sub="hit from BEHIND",
                           col=(255, 224, 120)))

    def hit(self, x, y, big=False):
        n = 18 if big else 10
        for _ in range(n):
            a = random.uniform(0, 6.28)
            sp = random.uniform(120, 360 if big else 260)
            self.fx.append(_Fx("spark", x, y, random.uniform(0.3, 0.6), vx=math.cos(a) * sp, vy=math.sin(a) * sp - 80,
                               col=random.choice(((255, 70, 80), (255, 140, 90), (255, 230, 160)))))
        ang = random.uniform(-0.6, 0.6)
        self.fx.append(_Fx("slash", x, y, 0.22, ang=ang, ln=90 if big else 64))
        self.fx.append(_Fx("flash", x, y, 0.22, col=(255, 90, 100), r=70 if big else 48))
        if big:
            self.fx.append(_Fx("ring", x, y, 0.45, col=(255, 160, 100), r1=90, w=6))
            self.shake = max(self.shake, 0.25)

    def ko(self, x, y):
        self.fx.append(_Fx("ring", x, y + 20, 0.7, col=(150, 190, 255), r1=100, w=5))
        for i in range(6):
            self.fx.append(_Fx("star", x, y - 30, 1.4, a0=i * 1.047, rr=26))
        for _ in range(10):
            self.fx.append(_Fx("spark", x + random.uniform(-20, 20), y + 40, random.uniform(0.5, 0.9),
                               vx=random.uniform(-90, 90), vy=random.uniform(-120, -20), col=(190, 190, 200)))
        self.fx.append(_Fx("stamp", x, y - 90, 1.1, text="DOWN!", sub="", col=(150, 190, 255)))

    # ----- update / draw -----
    def update(self, dt):
        self.shake = max(0.0, self.shake - dt)
        for f in self.fx:
            f.t += dt
            d = f.d
            if f.kind in ("shard", "spark"):
                f.x += d["vx"] * dt
                f.y += d["vy"] * dt
                d["vy"] += 620 * dt
                if f.kind == "shard":
                    d["rot"] += d["vr"] * dt
        self.fx = [f for f in self.fx if f.t < f.life]

    def draw(self, surf, cam):
        for f in self.fx:
            k = f.t / f.life
            x, y = f.x - cam, f.y
            d = f.d
            if f.kind == "ring":
                r = int(12 + (d["r1"] - 12) * ease_out(k))
                s = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (*d["col"], int(230 * (1 - k))), (4, 4 + int(r * 0.15), r * 2, int(r * 1.7)),
                                    max(1, int(d["w"] * (1 - k * 0.6))))
                surf.blit(s, (int(x - r - 4), int(y - r - 4)))
            elif f.kind == "flash":
                glow(surf, (x, y), d["r"] * (0.6 + 0.6 * k), d["col"], int(220 * (1 - k)), 2.0)
            elif f.kind == "shard":
                pts = [(x + math.cos(d["rot"] + i * 1.571) * d["s"] * (1.0 if i % 2 == 0 else 0.5),
                        y + math.sin(d["rot"] + i * 1.571) * d["s"] * (1.0 if i % 2 == 0 else 0.5)) for i in range(4)]
                pygame.draw.polygon(surf, (255, 232, 150), pts)
                pygame.draw.polygon(surf, (255, 255, 255), pts, 1)
            elif f.kind == "spark":
                x2, y2 = x - d["vx"] * 0.03, y - d["vy"] * 0.03
                pygame.draw.line(surf, d["col"], (x, y), (x2, y2), max(1, int(3 * (1 - k))))
            elif f.kind == "slash":
                ln = d["ln"] * ease_out(k * 2)
                w = max(1, int(7 * (1 - k)))
                ca, sa = math.cos(d["ang"] + 0.8), math.sin(d["ang"] + 0.8)
                pygame.draw.line(surf, (255, 255, 255), (x - ca * ln / 2, y - sa * ln / 2), (x + ca * ln / 2, y + sa * ln / 2), w)
            elif f.kind == "star":
                a = d["a0"] + f.t * 6
                px, py = x + math.cos(a) * d["rr"], y + math.sin(a) * d["rr"] * 0.35
                glow(surf, (px, py), 9, (255, 235, 110), int(200 * (1 - k)), 1.5)
                pygame.draw.circle(surf, (255, 240, 130), (int(px), int(py)), 3)
            elif f.kind == "stamp":
                sc = ease_back(k * 4) if k < 0.25 else 1.0
                alpha = 255 if k < 0.7 else int(255 * (1 - (k - 0.7) / 0.3))
                fy = y - 20 * ease_out(k)
                fnt = get_font(max(8, int(30 * sc)), True)
                off = 3 * (1 - k)
                for col, dx in (((255, 60, 90), -off), ((70, 230, 255), off)):        # RGB split
                    img = fnt.render(d["text"], True, col)
                    img.set_alpha(int(alpha * 0.75))
                    surf.blit(img, img.get_rect(center=(x + dx, fy)))
                img = fnt.render(d["text"], True, d["col"])
                img.set_alpha(alpha)
                surf.blit(img, img.get_rect(center=(x, fy)))
                if d.get("sub"):
                    sub = get_font(15, True).render(d["sub"], True, (255, 255, 255))
                    sub.set_alpha(alpha)
                    surf.blit(sub, sub.get_rect(center=(x, fy + 24)))


def get(world):
    m = getattr(world, "_hd", None)
    if m is None:
        m = world._hd = Manager()
    return m
