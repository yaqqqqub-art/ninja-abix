"""
animation.py - Abix Ninja er shob animation ekhane thake.
Intro ar game duita file-i ekhan theke animation import kore.
"""
import colorsys
import math
import random
import pygame

import lang

WIDTH, HEIGHT = 960, 540

BG = (8, 8, 18)
RED = (225, 40, 60)
DARK_RED = (120, 15, 30)
WHITE = (240, 240, 245)
GOLD = (255, 200, 70)
GRAY = (60, 60, 80)


def get_font(size, bold=True):
    return lang.font(size, bold)          # bhasha onujayi font (cache kora)


# ------------------------------------------------------------------
# Background: tara (stars)
# ------------------------------------------------------------------
class Starfield:
    def __init__(self, count=90):
        self.stars = [
            [random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
             random.uniform(0.2, 1.2), random.randint(1, 3)]
            for _ in range(count)
        ]

    def update(self):
        for s in self.stars:
            s[0] -= s[2]
            if s[0] < 0:
                s[0] = WIDTH
                s[1] = random.uniform(0, HEIGHT)

    def draw(self, surf, t):
        for x, y, speed, size in self.stars:
            tw = 130 + int(100 * abs(math.sin(t * 2 + x)))
            pygame.draw.circle(surf, (tw, tw, min(255, tw + 20)), (int(x), int(y)), size // 2 + 1)


# ------------------------------------------------------------------
# Particles: lal agun-er fulki
# ------------------------------------------------------------------
class Embers:
    def __init__(self, count=45):
        self.items = [self._new() for _ in range(count)]

    @staticmethod
    def _new():
        return {
            "x": random.uniform(0, WIDTH),
            "y": random.uniform(HEIGHT, HEIGHT + 120),
            "vy": random.uniform(0.6, 2.0),
            "r": random.uniform(1, 3),
            "ph": random.uniform(0, 6.28),
        }

    def update(self):
        for p in self.items:
            p["y"] -= p["vy"]
            if p["y"] < -10:
                p.update(self._new())

    def draw(self, surf, t):
        for p in self.items:
            x = p["x"] + math.sin(t * 2 + p["ph"]) * 12
            pygame.draw.circle(surf, (255, 90 + int(p["y"]) % 80, 40), (int(x), int(p["y"])), int(p["r"]))


# ------------------------------------------------------------------
# Shuriken (ghurte thaka ninja tara)
# ------------------------------------------------------------------
def draw_shuriken(surf, center, radius, angle, color=RED, hole_color=BG):
    cx, cy = center
    pts = []
    for i in range(8):
        a = angle + i * math.pi / 4
        r = radius if i % 2 == 0 else radius * 0.32
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, WHITE, pts, 2)
    pygame.draw.circle(surf, hole_color, (int(cx), int(cy)), int(radius * 0.14))
    pygame.draw.circle(surf, WHITE, (int(cx), int(cy)), int(radius * 0.14), 2)


# ------------------------------------------------------------------
# Abix Ninja LOGO (pygame diye banano)
# ------------------------------------------------------------------
_LOGO = {"img": None, "tried": False, "cache": {}}


def _logo_image():
    if not _LOGO["tried"]:
        _LOGO["tried"] = True
        try:
            import os
            import sys
            base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
            _LOGO["img"] = pygame.image.load(os.path.join(base, "assets", "logo_big.png")).convert_alpha()
        except Exception:
            _LOGO["img"] = None
    return _LOGO["img"]


def logo_available():
    return _logo_image() is not None


def draw_logo(surf, center, t, scale=1.0, appear=1.0):
    """ABIX NINJA logo (photo). Photo na pele ager moto shuriken-ninja ankhe."""
    img = _logo_image()
    if img is None:
        return _draw_logo_old(surf, center, t, scale, appear)
    cx, cy = center
    s = scale * (0.2 + 0.8 * min(1.0, appear))
    size = max(8, int(300 * s))
    key = size // 2 * 2
    pic = _LOGO["cache"].get(key)
    if pic is None:
        pic = pygame.transform.smoothscale(img, (key, int(key * img.get_height() / img.get_width())))
        _LOGO["cache"][key] = pic
    pic = pic.copy()
    pic.set_alpha(int(255 * min(1.0, appear * 1.4)))
    bob = math.sin(t * 2.0) * 3 * scale
    surf.blit(pic, pic.get_rect(center=(int(cx), int(cy + bob))))


def _draw_logo_old(surf, center, t, scale=1.0, appear=1.0):
    """appear: 0..1, logo dhire dhire boro hoye ashe."""
    cx, cy = center
    s = scale * (0.2 + 0.8 * min(1.0, appear))
    # ghurte thaka duita shuriken
    draw_shuriken(surf, (cx, cy), 110 * s, t * 1.5, RED)
    draw_shuriken(surf, (cx, cy), 85 * s, -t * 2.2, DARK_RED)

    # glow ring
    glow = 70 * s + math.sin(t * 4) * 3
    pygame.draw.circle(surf, GOLD, (int(cx), int(cy)), int(glow), 3)

    # ninja mukh
    face_r = int(58 * s)
    pygame.draw.circle(surf, (18, 18, 28), (cx, cy), face_r)
    pygame.draw.circle(surf, WHITE, (cx, cy), face_r, 3)

    # headband
    band = pygame.Rect(0, 0, int(face_r * 2), int(face_r * 0.55))
    band.center = (cx, cy - int(face_r * 0.05))
    pygame.draw.rect(surf, RED, band)
    # headband-er tail
    tail_w = math.sin(t * 5) * 6 * s
    pygame.draw.polygon(surf, RED, [
        (cx + face_r, cy - 6 * s), (cx + face_r + 28 * s, cy - 20 * s + tail_w),
        (cx + face_r + 18 * s, cy + 2 * s), (cx + face_r + 34 * s, cy + 14 * s + tail_w),
        (cx + face_r, cy + 10 * s)])

    # chokh (blink kore)
    blink = 1.0 if (int(t * 1.2) % 4 != 0 or (t * 1.2) % 1 > 0.15) else 0.15
    ew, eh = int(16 * s), max(2, int(9 * s * blink))
    for dx in (-18, 18):
        eye = pygame.Rect(0, 0, ew, eh)
        eye.center = (cx + int(dx * s), cy - int(face_r * 0.05))
        pygame.draw.ellipse(surf, WHITE, eye)
        if blink > 0.5:
            pygame.draw.circle(surf, (0, 0, 0), eye.center, max(1, int(3 * s)))

    # "A" letter nicher dike
    f = get_font(max(10, int(22 * s)))
    a = f.render("A", True, GOLD)
    surf.blit(a, a.get_rect(center=(cx, cy + int(face_r * 0.55))))


# ------------------------------------------------------------------
# Fade in/out text
# ------------------------------------------------------------------
class FadeText:
    def __init__(self, text, size, color, center, start=0.0, fade=1.0, glow=None):
        self.font = get_font(size)
        self.base = self.font.render(text, True, color)
        self.glow = self.font.render(text, True, glow) if glow else None
        self.center = center
        self.start = start
        self.fade = fade

    def draw(self, surf, t, global_alpha=1.0):
        a = max(0.0, min(1.0, (t - self.start) / self.fade)) * global_alpha
        if a <= 0:
            return
        # nich theke ule asha slide effect
        offset = int((1 - a) * 25)
        x, y = self.center
        if self.glow:
            g = self.glow.copy()
            g.set_alpha(int(110 * a))
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                surf.blit(g, g.get_rect(center=(x + dx, y + offset + dy)))
        img = self.base.copy()
        img.set_alpha(int(255 * a))
        surf.blit(img, img.get_rect(center=(x, y + offset)))


# ------------------------------------------------------------------
# Loading bar
# ------------------------------------------------------------------
class LoadingBar:
    def __init__(self, center, width=520, height=26):
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center
        self.font = get_font(18)

    def draw(self, surf, progress, t, alpha=1.0):
        progress = max(0.0, min(1.0, progress))
        pygame.draw.rect(surf, GRAY, self.rect, border_radius=14)
        fill = self.rect.copy()
        fill.width = int(self.rect.width * progress)
        if fill.width > 6:
            pygame.draw.rect(surf, RED, fill, border_radius=14)
            # chalachol shine
            sx = fill.x + int((t * 220) % max(1, fill.width))
            pygame.draw.rect(surf, (255, 150, 160), (sx, fill.y + 4, 10, fill.height - 8), border_radius=5)
        pygame.draw.rect(surf, WHITE, self.rect, 2, border_radius=14)

        dots = "." * (int(t * 3) % 4)
        label = self.font.render(f"Loading{dots}  {int(progress * 100)}%", True, WHITE)
        surf.blit(label, label.get_rect(center=(self.rect.centerx, self.rect.bottom + 28)))


# ------------------------------------------------------------------
# Screen fade (black overlay)
# ------------------------------------------------------------------
def fade_overlay(surf, alpha):
    """alpha 0..1 (1 = pura kalo)."""
    if alpha <= 0:
        return
    ov = pygame.Surface((WIDTH, HEIGHT))
    ov.fill((0, 0, 0))
    ov.set_alpha(int(255 * min(1.0, alpha)))
    surf.blit(ov, (0, 0))


# ------------------------------------------------------------------
# Coming Soon animation (game.py er jonno)
# ------------------------------------------------------------------
class ComingSoon:
    def __init__(self, heading="ABIX NINJA", emblem=None, emblem_y=150, sub="COMING SOON"):
        size = 68
        while size > 24 and get_font(size).size(heading)[0] > 860:
            size -= 4
        self.title = FadeText(heading, size, WHITE, (WIDTH // 2, 330), 0.3, 1.0, glow=RED)
        self.sub = FadeText(sub, 40, GOLD, (WIDTH // 2, 410), 1.2, 1.0)
        self.emblem = emblem          # function(surf, center, t) - jemon boss
        self.emblem_y = emblem_y
        self.hint = get_font(16)

    def draw(self, surf, t):
        if self.emblem:
            self.emblem(surf, (WIDTH // 2, self.emblem_y), t)
        else:
            draw_logo(surf, (WIDTH // 2, 150), t, scale=1.0, appear=min(1.0, t / 1.0))
        self.title.draw(surf, t)
        pulse = 0.75 + 0.25 * math.sin(t * 3)
        self.sub.draw(surf, t, pulse if t > 2.2 else 1.0)
        if t > 2.5:
            h = self.hint.render("Press ESC to go back", True, (150, 150, 170))
            surf.blit(h, h.get_rect(center=(WIDTH // 2, HEIGHT - 30)))


# ------------------------------------------------------------------
# Menu button (slide-in animation + optional RGB color)
# ------------------------------------------------------------------
def _ease_out_back(x):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def rgb_color(t, speed=0.35, sat=0.85, val=1.0, offset=0.0):
    r, g, b = colorsys.hsv_to_rgb((t * speed + offset) % 1.0, sat, val)
    return int(r * 255), int(g * 255), int(b * 255)


class MenuButton:
    """
    from_offset: button kon dik theke slide kore ashbe, jemon (0, -300) = upor theke,
    (0, 300) = niche theke, (0, 0) = jaygay thekei fade/pop in.
    rgb=True hole button er color ghurte thake (RGB).
    """
    def __init__(self, label, center, size=(320, 66), rgb=False,
                 start=0.0, from_offset=(0, 0), duration=0.9, rgb_offset=0.0):
        self.label = label
        self.center = center
        self.size = size
        self.rgb = rgb
        self.start = start
        self.from_offset = from_offset
        self.duration = duration
        self.rgb_offset = rgb_offset
        fs = 28
        while fs > 12 and get_font(fs).size(label)[0] > size[0] - 34:
            fs -= 2
        self.font = get_font(fs)
        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center

    def progress(self, t):
        return max(0.0, min(1.0, (t - self.start) / self.duration))

    def ready(self, t):
        return self.progress(t) >= 1.0

    def hovered(self, mouse, t):
        return self.ready(t) and self.rect.collidepoint(mouse)

    def draw(self, surf, t, mouse):
        p = self.progress(t)
        if p <= 0:
            return
        e = _ease_out_back(p)
        ox, oy = self.from_offset
        cx = self.center[0] + ox * (1 - e)
        cy = self.center[1] + oy * (1 - e)
        grow = 1.0
        if self.from_offset == (0, 0):
            grow = max(0.01, e)
        w, h = int(self.size[0] * grow), int(self.size[1] * grow)
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (int(cx), int(cy))
        self.rect.center = self.center  # click area fix thake

        hover = self.hovered(mouse, t)
        if hover:
            rect.inflate_ip(14, 6)

        if self.rgb:
            col = rgb_color(t, offset=self.rgb_offset)
            col2 = rgb_color(t, offset=self.rgb_offset + 0.25)
            # glow
            glow = pygame.Surface((rect.w + 40, rect.h + 40), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*col, 70), glow.get_rect(), border_radius=30)
            surf.blit(glow, glow.get_rect(center=rect.center))
            pygame.draw.rect(surf, col, rect, border_radius=18)
            pygame.draw.rect(surf, col2, rect, 4, border_radius=18)
            text_col = (15, 15, 25)
        else:
            fill = (55, 55, 90) if hover else (30, 30, 52)
            pygame.draw.rect(surf, fill, rect, border_radius=18)
            pygame.draw.rect(surf, RED if hover else WHITE, rect, 3, border_radius=18)
            text_col = WHITE

        txt = self.font.render(self.label, True, text_col)
        surf.blit(txt, txt.get_rect(center=rect.center))


# ------------------------------------------------------------------
# Level select: square level tile (1..20)
# ------------------------------------------------------------------
def _draw_lock(surf, center, size=1.0):
    cx, cy = center
    gray = (125, 125, 150)
    pygame.draw.arc(surf, gray, (cx - int(9 * size), cy - int(19 * size), int(18 * size), int(32 * size)),
                    0, math.pi, max(2, int(3 * size)))
    body = pygame.Rect(0, 0, int(24 * size), int(18 * size))
    body.center = (cx, cy + int(6 * size))
    pygame.draw.rect(surf, gray, body, border_radius=4)
    pygame.draw.circle(surf, (35, 35, 52), body.center, max(2, int(3 * size)))


class LevelTile:
    """state: 'locked' | 'current' (khelar jonno khola) | 'done' (shesh kora)"""

    def __init__(self, number, rect):
        self.number = number
        self.rect = pygame.Rect(rect)
        self.font = get_font(26)
        self.small = get_font(13)
        self.shake = 0.0

    def hovered(self, mouse, appear=1.0):
        return appear >= 1.0 and self.rect.collidepoint(mouse)

    def draw(self, surf, t, mouse, state, chapter, appear):
        if appear <= 0:
            return
        e = _ease_out_back(min(1.0, appear))
        r = pygame.Rect(0, 0, max(2, int(self.rect.w * e)), max(2, int(self.rect.h * e)))
        r.center = self.rect.center
        if self.shake > 0:
            r.x += int(math.sin(self.shake * 70) * 6 * (self.shake / 0.35))
        if self.hovered(mouse, appear):
            r.inflate_ip(8, 8)

        if state == "locked":
            pygame.draw.rect(surf, (28, 28, 44), r, border_radius=14)
            pygame.draw.rect(surf, (75, 75, 100), r, 3, border_radius=14)
            _draw_lock(surf, r.center, r.w / 66.0)
            return

        col = rgb_color(t, offset=self.number * 0.045)
        col2 = rgb_color(t, offset=self.number * 0.045 + 0.25)
        if state == "current":
            grow = 12 + int(4 * math.sin(t * 5))
            pygame.draw.rect(surf, col, r.inflate(grow, grow), 3, border_radius=18)
        pygame.draw.rect(surf, col, r, border_radius=14)
        pygame.draw.rect(surf, col2, r, 3, border_radius=14)
        txt = self.font.render(str(self.number), True, (15, 15, 25))
        surf.blit(txt, txt.get_rect(center=r.center))
        check_col = (15, 15, 25)
        if state == "done":
            pts = [(r.right - 24, r.bottom - 14), (r.right - 17, r.bottom - 7), (r.right - 6, r.bottom - 21)]
            pygame.draw.lines(surf, check_col, False, pts, 3)


# ------------------------------------------------------------------
# < > chapter button
# ------------------------------------------------------------------
class ArrowButton:
    def __init__(self, direction, center, size=54, rgb_offset=0.0):
        self.dir = direction          # -1 = <   +1 = >
        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = center
        self.rgb_offset = rgb_offset
        self.enabled = True

    def hovered(self, mouse):
        return self.enabled and self.rect.collidepoint(mouse)

    def draw(self, surf, t, mouse):
        r = self.rect.copy()
        if self.hovered(mouse):
            r.inflate_ip(8, 8)
        cx, cy = r.center
        d = self.dir
        pts = [(cx - d * 6, cy - 12), (cx + d * 6, cy), (cx - d * 6, cy + 12)]
        if self.enabled:
            col = rgb_color(t, offset=self.rgb_offset)
            col2 = rgb_color(t, offset=self.rgb_offset + 0.25)
            pygame.draw.rect(surf, col, r, border_radius=14)
            pygame.draw.rect(surf, col2, r, 3, border_radius=14)
            pygame.draw.lines(surf, (15, 15, 25), False, pts, 6)
        else:
            pygame.draw.rect(surf, (28, 28, 44), r, border_radius=14)
            pygame.draw.rect(surf, (70, 70, 95), r, 3, border_radius=14)
            pygame.draw.lines(surf, (85, 85, 110), False, pts, 6)


# ------------------------------------------------------------------
# Laf mara ninja + speech bubble: "Play me, don't die me!"
# ------------------------------------------------------------------
class JumpingNinja:
    def __init__(self, x, ground_y, scale=1.15, jump=90, period=1.7):
        self.x = x
        self.ground = ground_y
        self.s = scale
        self.jump = jump
        self.period = period
        self.font = get_font(22)

    def _pose(self, t):
        ph = (t % self.period) / self.period
        crouch = air = h = 0.0
        if ph < 0.16:                                   # noy hoye laf er jonno ready
            crouch = math.sin(math.pi * ph / 0.16)
        else:                                           # lafie uthche
            u = (ph - 0.16) / 0.84
            h = 4 * u * (1 - u) * self.jump * self.s
            air = math.sin(math.pi * u)
        return crouch, air, h

    def draw(self, surf, t):
        s = self.s
        crouch, air, h = self._pose(t)
        sx = 1 + 0.12 * crouch - 0.05 * air
        sy = 1 - 0.16 * crouch + 0.10 * air
        x, gy = self.x, self.ground
        body_c, dark_c = (30, 30, 50), (20, 20, 34)

        def P(dx, dy):
            return (x + dx * s * sx, gy + dy * s * sy - h)

        # shadow
        k = 1 - 0.45 * min(1.0, h / (self.jump * self.s))
        sw, sh = max(4, int(60 * s * k)), max(2, int(14 * s * k))
        shadow = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 110), shadow.get_rect())
        surf.blit(shadow, shadow.get_rect(center=(int(x), int(gy + 3))))

        # pithe talowar
        pygame.draw.line(surf, (170, 170, 190), P(-16, -36), P(16, -112), max(2, int(5 * s)))
        pygame.draw.line(surf, GOLD, P(14, -106), P(20, -120), max(2, int(6 * s)))

        # legs
        lw = max(2, int(10 * s))
        fl = P(-11 - 9 * air, -2 - 14 * air)
        fr = P(11 + 5 * air, -2 - 28 * air)
        pygame.draw.line(surf, dark_c, P(-7, -40), fl, lw)
        pygame.draw.line(surf, dark_c, P(7, -40), fr, lw)

        # torso + belt
        torso = pygame.Rect(0, 0, max(4, int(36 * s * sx)), max(4, int(46 * s * sy)))
        torso.center = P(0, -62)
        pygame.draw.ellipse(surf, body_c, torso)
        belt = pygame.Rect(0, 0, max(4, int(38 * s * sx)), max(2, int(7 * s)))
        belt.center = P(0, -50)
        pygame.draw.rect(surf, RED, belt)

        # arms (lafanor somoy upore)
        aw = max(2, int(8 * s))
        hl = P(-24 - 6 * air, -50 - 50 * air)
        hr = P(24 + 6 * air, -50 - 54 * air)
        pygame.draw.line(surf, body_c, P(-16, -74), hl, aw)
        pygame.draw.line(surf, body_c, P(16, -74), hr, aw)

        # head
        hc = P(0, -100)
        pygame.draw.circle(surf, (24, 24, 40), (int(hc[0]), int(hc[1])), max(4, int(19 * s)))
        slit = pygame.Rect(0, 0, max(4, int(28 * s * sx)), max(2, int(11 * s)))
        slit.center = P(0, -99)
        pygame.draw.rect(surf, (238, 200, 160), slit, border_radius=4)
        for ex in (-6, 6):
            ec = P(ex, -99)
            pygame.draw.circle(surf, WHITE, (int(ec[0]), int(ec[1])), max(2, int(3.2 * s)))
            pygame.draw.circle(surf, (0, 0, 0), (int(ec[0] + 1), int(ec[1])), max(1, int(1.6 * s)))

        # headband + udte thaka tail
        band = pygame.Rect(0, 0, max(4, int(40 * s * sx)), max(2, int(7 * s)))
        band.center = P(0, -108)
        pygame.draw.rect(surf, RED, band)
        wave = math.sin(t * 9) * 5
        pygame.draw.polygon(surf, RED, [P(-19, -110), P(-19, -104), P(-44, -96 + wave),
                                        P(-36, -106 + wave * 0.6), P(-47, -114 + wave)])

    def draw_bubble(self, surf, t):
        lines = ["Play me,", "don't die me!"]
        imgs = [self.font.render(l, True, (20, 20, 35)) for l in lines]
        w = max(i.get_width() for i in imgs) + 32
        hgt = sum(i.get_height() for i in imgs) + 22
        bob = math.sin(t * 3) * 4
        box = pygame.Rect(0, 0, w, hgt)
        box.midbottom = (int(self.x), int(self.ground - 270 + bob))
        pygame.draw.rect(surf, WHITE, box, border_radius=14)
        pygame.draw.rect(surf, RED, box, 3, border_radius=14)
        tri = [(box.centerx - 12, box.bottom - 2), (box.centerx + 12, box.bottom - 2), (box.centerx, box.bottom + 20)]
        pygame.draw.polygon(surf, WHITE, tri)
        pygame.draw.lines(surf, RED, False, tri, 3)
        y = box.top + 11
        for img in imgs:
            surf.blit(img, img.get_rect(midtop=(box.centerx, y)))
            y += img.get_height()
