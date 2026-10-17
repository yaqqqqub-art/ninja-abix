"""
sprites.py - Bank heist game er shob character ar jinish ankar code (pygame diye, kono image lage na).

Character gulo "unit" e ankha (pa = 0, matha = -120), tarpor scale (s) diye chhoto/boro kora hoy.
Shob character dan dike mukh kore ankhe, facing = -1 hole ulte dey.
Shading (alo-chhaya) diye jothasombhob "real" dekhano hoyeche.
"""
import math
import random
import pygame

S = 0.52                      # Abix scale
TW, TH = 130, 110             # character temp surface
OX, OY = 65, 96               # temp surface e pa er jaygay

RED = (225, 40, 60)
GOLD = (255, 200, 70)
WHITE = (240, 240, 245)
DARK = (20, 20, 34)


def _font(size):
    return pygame.font.SysFont("arialblack,arial,verdana", size, bold=True)


def lerp_color(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ------------------------------------------------------------------
# chhoto helper
# ------------------------------------------------------------------
def glow(surf, c, r, color, alpha=70, steps=4):
    size = int(r * 2) + 4
    g = pygame.Surface((size, size), pygame.SRCALPHA)
    for i in range(steps, 0, -1):
        pygame.draw.circle(g, (*color, int(alpha * (steps - i + 1) / steps)),
                           (size // 2, size // 2), max(1, int(r * i / steps)))
    surf.blit(g, g.get_rect(center=(int(c[0]), int(c[1]))))


def v_gradient(surf, rect, top, bottom):
    rect = pygame.Rect(rect)
    for i in range(rect.h):
        pygame.draw.line(surf, lerp_color(top, bottom, i / max(1, rect.h - 1)),
                         (rect.x, rect.y + i), (rect.right - 1, rect.y + i))


def star_points(cx, cy, r, rot=-math.pi / 2, inner=0.45):
    pts = []
    for i in range(10):
        a = rot + i * math.pi / 5
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    return pts


def draw_star_icon(surf, c, r, filled=True, t=0.0, with_glow=False):
    """Jomano 'star' (gold) - HUD, level tile, ar level e."""
    if with_glow:
        glow(surf, c, r * 2.2, GOLD, 60 + int(30 * math.sin(t * 4)))
    rot = -math.pi / 2 + (math.sin(t * 3) * 0.12 if with_glow else 0)
    pts = star_points(c[0], c[1], r, rot)
    if filled:
        pygame.draw.polygon(surf, GOLD, pts)
        pygame.draw.polygon(surf, (255, 245, 200), pts, max(1, int(r * 0.15)))
    else:
        pygame.draw.polygon(surf, (28, 28, 44), pts)
        pygame.draw.polygon(surf, (95, 95, 120), pts, max(1, int(r * 0.15)))


def draw_heart(surf, c, size, color=(235, 50, 80), outline=(255, 210, 220)):
    x, y = c
    r = size * 0.28
    pygame.draw.circle(surf, color, (int(x - r), int(y - r * 0.4)), int(r) + 1)
    pygame.draw.circle(surf, color, (int(x + r), int(y - r * 0.4)), int(r) + 1)
    pygame.draw.polygon(surf, color, [(x - size * 0.52, y - r * 0.1), (x + size * 0.52, y - r * 0.1),
                                       (x, y + size * 0.55)])
    if outline:
        pygame.draw.lines(surf, outline, False, [(x - size * 0.5, y + r * 0.1), (x, y + size * 0.55),
                                                 (x + size * 0.5, y + r * 0.1)], 2)


def draw_skull_coin(surf, c, r=15):
    """Mrittur count er coin."""
    pygame.draw.circle(surf, GOLD, (int(c[0]), int(c[1])), r)
    pygame.draw.circle(surf, (190, 130, 20), (int(c[0]), int(c[1])), r, 3)
    sk = int(r * 0.52)
    pygame.draw.circle(surf, (30, 24, 20), (int(c[0]), int(c[1] - r * 0.1)), sk)
    pygame.draw.rect(surf, (30, 24, 20), pygame.Rect(c[0] - sk * 0.55, c[1] + sk * 0.3, sk * 1.1, sk * 0.9))
    for dx in (-0.42, 0.42):
        pygame.draw.circle(surf, GOLD, (int(c[0] + dx * sk), int(c[1] - r * 0.12)), max(1, int(sk * 0.3)))


def draw_tk_coin(surf, c, r=15):
    """Taka (Tk) coin - wallet."""
    pygame.draw.circle(surf, (60, 190, 90), (int(c[0]), int(c[1])), r)
    pygame.draw.circle(surf, (20, 120, 50), (int(c[0]), int(c[1])), r, 3)
    f = _font(max(8, int(r * 0.9)))
    img = f.render("Tk", True, (10, 50, 20))
    surf.blit(img, img.get_rect(center=(int(c[0]), int(c[1]))))


def _finish(surf, tmp, x, feet_y, facing, alpha, flash=0.0, rot=0.0):
    if flash > 0:
        tmp.fill((int(130 * min(1, flash * 5)),) * 3 + (0,), special_flags=pygame.BLEND_RGB_ADD)
    if facing < 0:
        tmp = pygame.transform.flip(tmp, True, False)
    if alpha < 255:
        tmp.set_alpha(int(alpha))
    if rot:
        tmp = pygame.transform.rotate(tmp, rot)
        surf.blit(tmp, tmp.get_rect(center=(int(x), int(feet_y - 30))))
    else:
        surf.blit(tmp, (int(x) - OX, int(feet_y) - OY))


# ------------------------------------------------------------------
# Abix (chor / ninja)
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# NINJA SKIN (ninjas.py theke set hoy).  Default = ager Abix.
# ------------------------------------------------------------------
DEFAULT_PAL = {"body": (30, 30, 50), "body2": (48, 48, 74), "dark": (20, 20, 34), "head": (24, 24, 40),
               "face": (238, 200, 160), "accent": RED, "bag": (58, 58, 72), "bag2": (88, 88, 104),
               "aura": None, "deco": None, "cape": None}
SKIN = dict(DEFAULT_PAL)


def _rainbow(t, off=0.0):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb((t * 0.35 + off) % 1.0, 0.85, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))


def set_skin(pal):
    """Game er shob jaygay (level, preview) ei ninja skin bebohar hobe."""
    SKIN.clear()
    SKIN.update(DEFAULT_PAL)
    if pal:
        SKIN.update(pal)


def _draw_deco(tmp, kind, U, s, acc):
    """Matha r upore choto sajh (crown, horns, hat ...)."""
    def poly(col, pts):
        pygame.draw.polygon(tmp, col, pts)
    gold, gold_d = (255, 210, 80), (200, 150, 40)
    if kind == "crown":
        poly(gold, [U(-14, -117), U(-14, -131), U(-7, -122), U(0, -134), U(7, -122), U(14, -131), U(14, -117)])
        poly(gold_d, [U(-14, -117), U(14, -117), U(14, -113), U(-14, -113)])
    elif kind == "horns":
        poly((235, 235, 225), [U(-14, -114), U(-22, -138), U(-6, -118)])
        poly((235, 235, 225), [U(14, -114), U(22, -138), U(6, -118)])
    elif kind == "hat":
        poly((214, 176, 100), [U(-34, -112), U(34, -112), U(0, -142)])
        pygame.draw.line(tmp, (150, 110, 50), U(-34, -112), U(34, -112), max(1, int(3 * s)))
    elif kind == "spike":
        for dx in (-12, 0, 12):
            poly(acc, [U(dx - 6, -116), U(dx, -138 + abs(dx) * 0.4), U(dx + 6, -116)])
    elif kind == "halo":
        r = pygame.Rect(0, 0, max(6, int(34 * s)), max(3, int(10 * s)))
        r.center = U(0, -132)
        pygame.draw.ellipse(tmp, gold, r, max(1, int(3 * s)))
    elif kind == "cat":
        poly((30, 30, 40), [U(-16, -114), U(-17, -134), U(-4, -118)])
        poly((30, 30, 40), [U(16, -114), U(17, -134), U(4, -118)])
        poly(acc, [U(-14, -118), U(-15, -128), U(-8, -119)])
        poly(acc, [U(14, -118), U(15, -128), U(8, -119)])
    elif kind == "samurai":
        poly((50, 50, 64), [U(-20, -112), U(20, -112), U(14, -128), U(-14, -128)])
        poly(gold, [U(0, -126), U(-14, -142), U(-4, -128)])
        poly(gold, [U(0, -126), U(14, -142), U(4, -128)])
    elif kind == "bunny":
        poly((245, 245, 250), [U(-12, -114), U(-17, -146), U(-6, -146), U(-4, -116)])
        poly((245, 245, 250), [U(12, -114), U(17, -146), U(6, -146), U(4, -116)])
        poly((255, 170, 190), [U(-11, -118), U(-14, -140), U(-8, -140), U(-6, -118)])
    elif kind == "flame":
        poly((255, 120, 30), [U(-12, -116), U(-6, -140), U(0, -122), U(6, -146), U(12, -116)])
        poly((255, 220, 90), [U(-6, -116), U(0, -134), U(6, -116)])


def draw_ninja(surf, x, feet_y, facing=1, t=0.0, anim="idle", ap=0.0, alpha=255, s=S, flash=0.0, rot=0.0, pal=None):
    """
    anim: idle | run | air (ap = -1 uporey .. +1 niche) | stab (ap 0..1) | punch (ap 0..1)
          hide | dead | wave | type (laptop e)
    """
    tmp = pygame.Surface((TW, TH), pygame.SRCALPHA)
    ox, oy = OX, OY

    def P(dx, dy):
        return (ox + dx * s, oy + dy * s)

    pal = pal or SKIN
    body_c, dark_c = pal["body"], pal["dark"]
    acc = pal["accent"]
    if acc == "rainbow":
        acc = _rainbow(t)
    lw = max(2, int(10 * s))
    aw = max(2, int(8 * s))

    if anim == "dead":
        pygame.draw.ellipse(tmp, body_c, pygame.Rect(*P(-48, -26), 96 * s, 26 * s))
        pygame.draw.circle(tmp, pal["head"], (int(P(-44, -16)[0]), int(P(-44, -16)[1])), max(4, int(15 * s)))
        pygame.draw.rect(tmp, acc, pygame.Rect(*P(-58, -26), 28 * s, 6 * s))
        for dx in (-6, 6):
            c = P(-44 + dx, -17)
            pygame.draw.line(tmp, WHITE, (c[0] - 2, c[1] - 2), (c[0] + 2, c[1] + 2), 1)
            pygame.draw.line(tmp, WHITE, (c[0] - 2, c[1] + 2), (c[0] + 2, c[1] - 2), 1)
        _finish(surf, tmp, x, feet_y, facing, alpha, flash)
        return

    ph = t * 12
    crouch = 0.0
    lean = bob = 0.0
    fl, fr = (-9, -2), (9, -2)
    hl, hr = (-24, -50), (24, -50)
    bag = True

    if anim == "idle":
        bob = math.sin(t * 3) * 1.4
    elif anim == "run":
        sn, cs = math.sin(ph), math.cos(ph)
        fl = (-8 - sn * 15, -2 - max(0, cs) * 13)
        fr = (8 + sn * 15, -2 - max(0, -cs) * 13)
        hl = (-20 + sn * 12, -54)
        hr = (22 - sn * 12, -54)
        lean, bob = 6, -abs(cs) * 2.5
    elif anim == "air":
        up = ap < 0
        fl = (-12, -14)
        fr = (12, -26) if up else (11, -6)
        hl = (-30, -98 if up else -66)
        hr = (30, -102 if up else -66)
    elif anim == "stab":
        ext = math.sin(min(1.0, ap) * math.pi)
        hr = (22 + 30 * ext, -66)
        hl = (-20, -48)
        lean = 7 * ext
        fl, fr = (-12, -2), (14, -2)
    elif anim == "punch":
        if ap < 0.7:                       # haat upore, nich hoy
            crouch = 0.6 * ap / 0.7
            hr = (20, -124 + 30 * crouch)
            hl = (-20, -118 + 30 * crouch)
        else:                              # mati te ghusi
            crouch = 1.0
            hr = (24, -6)
            hl = (-8, -6)
            pygame.draw.line(tmp, (255, 220, 120), P(40, -4), P(60, -12), 2)
            pygame.draw.line(tmp, (255, 220, 120), P(40, -4), P(62, 0), 2)
    elif anim == "hide":
        crouch = 1.3
        hl = (-12, -26)
        hr = (12, -26)
        bag = False
    elif anim == "wave":
        hl = (-26, -96 + math.sin(t * 9) * 12)
        hr = (26, -96 - math.sin(t * 9) * 12)
        bob = math.sin(t * 6) * 1.5
    elif anim == "type":
        hl = (18, -44 + math.sin(t * 22) * 3)
        hr = (24, -44 - math.sin(t * 22) * 3)
        lean = 3

    drop = crouch * 24
    ux, uy = lean, bob + drop
    sy = 1 - 0.16 * min(1.0, crouch)

    def U(dx, dy):
        return P(dx + ux, dy + uy)

    # pither tuli (loot bag)
    if bag:
        bag_r = pygame.Rect(0, 0, int(26 * s), int(34 * s))
        bag_r.center = U(-19, -58)
        pygame.draw.ellipse(tmp, pal["bag"], bag_r)
        pygame.draw.ellipse(tmp, pal["bag2"], bag_r.inflate(-int(10 * s), -int(14 * s)))
        pygame.draw.line(tmp, (30, 30, 40), U(-12, -82), U(8, -46), max(1, int(3 * s)))

    # cape (pichone)
    if pal.get("cape") and anim != "hide":
        cw = math.sin(t * 8) * 5 + (10 if anim == "run" else 0)
        pygame.draw.polygon(tmp, pal["cape"], [U(-14, -86), U(-14, -46), U(-46 - cw, -28), U(-34 - cw * 0.5, -78)])

    # pa
    if crouch > 0:
        fl = (-16 - crouch * 4, -2)
        fr = (16 + crouch * 4, -2)
    pygame.draw.line(tmp, dark_c, U(-7, -40 + drop * 0.1), P(*fl), lw)
    pygame.draw.line(tmp, dark_c, U(7, -40 + drop * 0.1), P(*fr), lw)

    # torso + belt
    torso = pygame.Rect(0, 0, max(4, int(36 * s)), max(4, int(46 * s * sy)))
    torso.center = U(0, -62)
    pygame.draw.ellipse(tmp, body_c, torso)
    pygame.draw.ellipse(tmp, pal["body2"], torso.inflate(-int(torso.w * 0.5), -int(torso.h * 0.3)).move(int(torso.w * 0.12), 0))
    belt = pygame.Rect(0, 0, max(4, int(38 * s)), max(2, int(7 * s)))
    belt.center = U(0, -50)
    pygame.draw.rect(tmp, acc, belt)

    # haat
    if anim != "hide":
        pygame.draw.line(tmp, body_c, U(-16, -74), P(hl[0] + ux, hl[1] + bob), aw)
        pygame.draw.line(tmp, body_c, U(16, -74), P(hr[0] + ux, hr[1] + bob), aw)

    # matha
    hc = U(0, -100)
    pygame.draw.circle(tmp, pal["head"], (int(hc[0]), int(hc[1])), max(4, int(19 * s)))
    slit = pygame.Rect(0, 0, max(4, int(28 * s)), max(2, int(11 * s)))
    slit.center = U(2, -99)
    pygame.draw.rect(tmp, pal["face"], slit, border_radius=3)
    for ex in (-3, 9):
        ec = U(ex, -99)
        pygame.draw.circle(tmp, WHITE, (int(ec[0]), int(ec[1])), max(2, int(3.2 * s)))
        pygame.draw.circle(tmp, (0, 0, 0), (int(ec[0] + 1), int(ec[1])), max(1, int(1.6 * s)))

    # headband + tail
    band = pygame.Rect(0, 0, max(4, int(40 * s)), max(2, int(7 * s)))
    band.center = U(0, -108)
    pygame.draw.rect(tmp, acc, band)
    wave = math.sin(t * 9) * 5 + (8 if anim == "run" else 0)
    pygame.draw.polygon(tmp, acc, [U(-19, -110), U(-19, -104), U(-44, -96 + wave),
                                   U(-36, -106 + wave * 0.6), U(-47, -114 + wave)])
    if pal.get("deco"):
        _draw_deco(tmp, pal["deco"], U, s, acc)

    # chhuri (knife)
    if anim == "stab":
        hx, hy = P(hr[0] + ux, hr[1] + bob)
        blade = [(hx, hy - 2.5 * s * 2), (hx + 30 * s * 1.6, hy), (hx, hy + 2.5 * s * 2)]
        pygame.draw.polygon(tmp, (214, 220, 232), blade)
        pygame.draw.line(tmp, WHITE, (hx, hy - 1), (hx + 28 * s * 1.6, hy), 1)
        pygame.draw.line(tmp, (30, 24, 20), (hx - 6 * s, hy), (hx, hy), max(2, int(5 * s)))
        if 0.15 < ap < 0.7:                                  # slash
            sl = pygame.Surface((TW, TH), pygame.SRCALPHA)
            pygame.draw.arc(sl, (255, 255, 255, 150), pygame.Rect(hx - 18, hy - 26, 60, 52), -1.0, 1.0, 3)
            tmp.blit(sl, (0, 0))

    if pal.get("aura") and alpha > 60 and not rot:
        ac = _rainbow(t, 0.5) if pal["aura"] == "rainbow" else pal["aura"]
        glow(surf, (x, feet_y - 32), 40 + 3 * math.sin(t * 5), ac, int(60 * alpha / 255), 4)
    _finish(surf, tmp, x, feet_y, facing, alpha, flash, rot)


# ------------------------------------------------------------------
# Guard (asol manusher moto, hate gun)
# ------------------------------------------------------------------
def draw_guard(surf, x, feet_y, facing=1, t=0.0, anim="walk", ap=0.0, flash=0.0, alpha=255, s=0.62, pal=None):
    """anim: idle | walk | aim (ap 0..1) | shoot | recover | dead"""
    tmp = pygame.Surface((TW, TH), pygame.SRCALPHA)
    ox, oy = OX, OY

    def P(dx, dy):
        return (ox + dx * s, oy + dy * s)

    def I(pt):
        return (int(pt[0]), int(pt[1]))

    skin, skin_d = (228, 182, 144), (182, 134, 102)
    shirt, shirt_d, shirt_l = (72, 102, 160), (46, 70, 120), (110, 144, 202)
    pants, pants_l = (32, 36, 60), (58, 64, 98)
    dark = (14, 14, 22)
    navy, navy_l = (28, 38, 74), (50, 64, 112)
    gun_c, gun_l = (28, 30, 36), (110, 114, 128)
    if pal:                                   # police er pOshak (rong bodlano)
        shirt, shirt_d, shirt_l = pal.get("shirt", shirt), pal.get("shirt_d", shirt_d), pal.get("shirt_l", shirt_l)
        pants, pants_l = pal.get("pants", pants), pal.get("pants_l", pants_l)
        navy, navy_l = pal.get("navy", navy), pal.get("navy_l", navy_l)

    if anim == "dead":
        pygame.draw.ellipse(tmp, pants, pygame.Rect(*P(6, -22), 62 * s, 20 * s))
        pygame.draw.ellipse(tmp, shirt_d, pygame.Rect(*P(-42, -30), 62 * s, 28 * s))
        pygame.draw.ellipse(tmp, shirt, pygame.Rect(*P(-40, -30), 58 * s, 18 * s))
        pygame.draw.circle(tmp, skin, I(P(-50, -20)), max(4, int(12 * s)))
        pygame.draw.ellipse(tmp, navy, pygame.Rect(*P(-66, -34), 26 * s, 12 * s))
        for dx in (-5, 5):
            c = P(-50 + dx, -22)
            pygame.draw.line(tmp, dark, (c[0] - 2, c[1] - 2), (c[0] + 2, c[1] + 2), 1)
            pygame.draw.line(tmp, dark, (c[0] - 2, c[1] + 2), (c[0] + 2, c[1] - 2), 1)
        pygame.draw.line(tmp, gun_c, P(30, -6), P(54, -8), max(3, int(7 * s)))
        _finish(surf, tmp, x, feet_y, facing, alpha, flash)
        return

    ph = t * (6 if anim == "walk" else 10)
    sn, cs = math.sin(ph), math.cos(ph)
    bob = 0.0
    lean = 0.0
    fl, fr = (-8, -2), (8, -2)
    if anim == "walk":
        fl = (-8 - sn * 12, -2 - max(0, cs) * 9)
        fr = (8 + sn * 12, -2 - max(0, -cs) * 9)
        bob = -abs(cs) * 1.5
    elif anim == "idle":
        bob = math.sin(t * 2.4) * 0.8
    elif anim in ("aim", "shoot"):
        fl, fr = (-12, -2), (13, -2)
        lean = 3

    def U(dx, dy):
        return P(dx + lean, dy + bob)

    # --- pa (pant + juta)
    lw = max(3, int(13 * s))
    for hip, ft in (((-7, -42), fl), ((7, -42), fr)):
        pygame.draw.line(tmp, pants, U(*hip), P(*ft), lw)
        pygame.draw.line(tmp, pants_l, U(hip[0] + 2, hip[1]), P(ft[0] + 2, ft[1] - 2), max(1, int(3 * s)))
        pygame.draw.ellipse(tmp, dark, pygame.Rect(P(ft[0] - 3, ft[1] - 6)[0], P(ft[0] - 3, ft[1] - 6)[1],
                                                   18 * s, 9 * s))

    # --- gun-er haat (age ankhi, kintu shesh e boshabo) -> ekhane hater position hishab
    if anim == "aim":
        e = min(1.0, ap)
        H = (22 + 20 * e, -58 - 22 * e)
        th = math.radians(60 * (1 - e) - 2)
    elif anim == "shoot":
        H = (38, -79)
        th = math.radians(-3)
    elif anim == "recover":
        H = (34, -70)
        th = math.radians(26)
    else:
        H = (21, -58)
        th = math.radians(62)
    gd = (math.cos(th), math.sin(th))

    # --- pichoner haat
    bh = (-19 - (sn * 4 if anim == "walk" else 0), -58) if anim in ("walk", "idle", "recover") else (H[0] - 8, H[1] + 6)
    pygame.draw.line(tmp, shirt_d, U(-15, -84), U(*bh), max(3, int(9 * s)))
    pygame.draw.circle(tmp, skin_d, I(U(*bh)), max(2, int(4.5 * s)))

    # --- torso
    pygame.draw.polygon(tmp, shirt, [U(-18, -88), U(18, -88), U(22, -40), U(-22, -40)])
    pygame.draw.polygon(tmp, shirt_d, [U(-18, -88), U(-4, -88), U(-6, -40), U(-22, -40)])
    pygame.draw.polygon(tmp, shirt_l, [U(9, -88), U(18, -88), U(22, -40), U(14, -40)])
    pygame.draw.polygon(tmp, WHITE, [U(-5, -88), U(5, -88), U(0, -78)])                     # collar
    pygame.draw.polygon(tmp, navy, [U(-1.5, -80), U(2, -80), U(3, -58), U(0, -55), U(-3, -58)])  # tie
    pygame.draw.circle(tmp, GOLD, I(U(10, -74)), max(2, int(3.4 * s)))                          # badge
    for dx in (-18, 14):                                                                         # epaulet
        pygame.draw.rect(tmp, navy_l, pygame.Rect(*U(dx, -89), 8 * s, 4 * s))
    pygame.draw.rect(tmp, dark, pygame.Rect(*U(-23, -48), 46 * s, 8 * s))                    # belt
    pygame.draw.rect(tmp, GOLD, pygame.Rect(*U(-3, -48), 6 * s, 8 * s))
    pygame.draw.rect(tmp, (22, 22, 30), pygame.Rect(*U(-22, -46), 10 * s, 18 * s), border_radius=2)  # holster

    # --- matha
    hc = U(2, -102)
    pygame.draw.rect(tmp, skin_d, pygame.Rect(*U(-3, -92), 10 * s, 8 * s))                      # gola
    pygame.draw.circle(tmp, skin_d, I(hc), max(4, int(14 * s)))
    pygame.draw.circle(tmp, skin, I((hc[0] + 1.5 * s, hc[1] - 0.8 * s)), max(3, int(12 * s)))
    pygame.draw.polygon(tmp, dark, [U(-12, -106), U(-8, -94), U(-14, -94)])                    # chul
    pygame.draw.ellipse(tmp, navy, pygame.Rect(*U(-13, -121), 30 * s, 18 * s))               # cap
    pygame.draw.ellipse(tmp, navy_l, pygame.Rect(*U(-6, -120), 14 * s, 6 * s))
    pygame.draw.polygon(tmp, (18, 22, 44), [U(6, -110), U(23, -108), U(23, -105), U(6, -106)])   # cap brim
    pygame.draw.circle(tmp, GOLD, I(U(5, -113)), max(1, int(2.6 * s)))
    ec = U(9, -102)
    pygame.draw.circle(tmp, WHITE, I(ec), max(2, int(3.3 * s)))
    pygame.draw.circle(tmp, dark, I((ec[0] + 1, ec[1])), max(1, int(1.7 * s)))
    pygame.draw.line(tmp, dark, U(5, -107), U(13, -104.5), max(1, int(2.6 * s)))                # bhru
    pygame.draw.polygon(tmp, skin_d, [U(13, -101), U(17, -96), U(12, -96)])                     # nak
    pygame.draw.rect(tmp, (44, 32, 28), pygame.Rect(*U(8, -95), 9 * s, 2.6 * s))                # goph
    pygame.draw.line(tmp, (120, 60, 56), U(9, -92), U(15, -92), 1)

    # --- samner haat + gun (shobar upore)
    sh = U(15, -84)
    hp = U(*H)
    pygame.draw.line(tmp, shirt, sh, hp, max(3, int(10 * s)))
    pygame.draw.line(tmp, shirt_l, (sh[0] + 1, sh[1] - 1), (hp[0] + 1, hp[1] - 1), max(1, int(3 * s)))
    # gun
    tip = (hp[0] + gd[0] * 26 * s, hp[1] + gd[1] * 26 * s)
    pygame.draw.line(tmp, gun_c, hp, tip, max(3, int(8 * s)))
    pygame.draw.line(tmp, gun_l, (hp[0], hp[1] - 1), (tip[0], tip[1] - 1), max(1, int(2.4 * s)))
    grip = (hp[0] - gd[1] * -5 * s, hp[1] + 7 * s)
    pygame.draw.line(tmp, gun_c, (hp[0] + 2 * s, hp[1]), grip, max(3, int(6 * s)))
    pygame.draw.circle(tmp, skin, I(hp), max(2, int(4.6 * s)))
    if anim == "shoot":                                           # muzzle flash
        fx, fy = tip
        fl_pts = [(fx, fy), (fx + 12 * s * 1.5, fy - 7 * s * 1.5), (fx + 22 * s * 1.5, fy),
                  (fx + 12 * s * 1.5, fy + 7 * s * 1.5)]
        pygame.draw.polygon(tmp, (255, 200, 80), fl_pts)
        pygame.draw.polygon(tmp, (255, 255, 230), [(fx, fy), (fx + 8 * s * 1.5, fy - 3), (fx + 14 * s * 1.5, fy),
                                                   (fx + 8 * s * 1.5, fy + 3)])

    _finish(surf, tmp, x, feet_y, facing, alpha, flash)


def draw_bullet(surf, x, y, direction):
    glow(surf, (x, y), 12, (255, 200, 90), 70, 3)
    pygame.draw.line(surf, (255, 235, 170), (x - 22 * direction, y), (x, y), 3)
    pygame.draw.circle(surf, (255, 255, 235), (int(x), int(y)), 3)


# ------------------------------------------------------------------
# CCTV camera
# ------------------------------------------------------------------
def draw_cctv(surf, x, y, ang_deg, active, t, danger=0.0):
    """x,y = ceiling mount. ang_deg: 90 = sojasuji niche."""
    pygame.draw.rect(surf, (54, 56, 66), (x - 16, y - 8, 32, 8), border_radius=2)
    pygame.draw.line(surf, (92, 96, 110), (x, y), (x, y + 10), 7)
    a = math.radians(ang_deg)
    d = (math.cos(a), math.sin(a))
    n = (-d[1], d[0])
    p0 = (x, y + 12)
    back, front = -10, 34
    w0, w1 = 10, 8

    def q(l, w):
        return (p0[0] + d[0] * l + n[0] * w, p0[1] + d[1] * l + n[1] * w)

    body = (200, 204, 214) if active else (98, 100, 108)
    shade = (140, 144, 158) if active else (64, 66, 74)
    pygame.draw.polygon(surf, shade, [q(back, -w0), q(front, -w1), q(front, w1), q(back, w0)])
    pygame.draw.polygon(surf, body, [q(back, -w0), q(front, -w1), q(front, 0), q(back, 0)])
    pygame.draw.polygon(surf, (40, 42, 50), [q(back, -w0), q(front, -w1), q(front, w1), q(back, w0)], 2)
    lens = q(front + 3, 0)
    pygame.draw.circle(surf, (18, 20, 26), (int(lens[0]), int(lens[1])), 8)
    pygame.draw.circle(surf, (40, 70, 130) if active else (36, 38, 46), (int(lens[0]), int(lens[1])), 5)
    if active:
        pygame.draw.circle(surf, (190, 220, 255), (int(lens[0] - 1), int(lens[1] - 2)), 2)
        led = q(back + 4, -w0 - 1)
        on = (int(t * 3) % 2 == 0) or danger > 0.5
        col = (255, 40, 40) if on else (90, 20, 20)
        if on:
            glow(surf, led, 12, (255, 40, 40), 90, 3)
        pygame.draw.circle(surf, col, (int(led[0]), int(led[1])), 3)
    else:
        c = q(10, 0)
        pygame.draw.line(surf, (150, 60, 60), (c[0] - 4, c[1] - 4), (c[0] + 4, c[1] + 4), 2)
        pygame.draw.line(surf, (150, 60, 60), (c[0] - 4, c[1] + 4), (c[0] + 4, c[1] - 4), 2)
    return lens


# ------------------------------------------------------------------
# Laser
# ------------------------------------------------------------------
def draw_laser(surf, x, top, floor, broken, t):
    for y, up in ((top, True), (floor, False)):
        r = pygame.Rect(0, 0, 30, 16)
        r.midtop = (x, y) if up else (x, y - 16)
        v_gradient(surf, r, (110, 114, 128), (52, 54, 64))
        pygame.draw.rect(surf, (30, 32, 40), r, 2, border_radius=3)
        pygame.draw.circle(surf, (40, 10, 10) if broken else (255, 50, 50), (x, r.centery), 3)
    if broken:
        for i in range(3):
            sx = x + math.sin(t * 9 + i * 2) * 6
            sy = top + 40 + ((t * 120 + i * 90) % (floor - top - 80))
            pygame.draw.circle(surf, (255, 200, 90), (int(sx), int(sy)), 2)
        return
    a = 70 + int(40 * math.sin(t * 20))
    g = pygame.Surface((46, floor - top - 32), pygame.SRCALPHA)
    pygame.draw.rect(g, (255, 30, 40, 40), g.get_rect(), border_radius=20)
    pygame.draw.rect(g, (255, 60, 70, a), g.get_rect().inflate(-26, 0), border_radius=10)
    surf.blit(g, (x - 23, top + 16))
    pygame.draw.line(surf, (255, 190, 190), (x, top + 16), (x, floor - 16), 2)
    pygame.draw.line(surf, (255, 40, 50), (x - 3, top + 16), (x - 3, floor - 16), 2)
    pygame.draw.line(surf, (255, 40, 50), (x + 3, top + 16), (x + 3, floor - 16), 2)
    for i in range(6):                                          # chalte thaka alo-bindu
        sy = top + 16 + ((t * 160 + i * 60) % (floor - top - 32))
        pygame.draw.circle(surf, (255, 230, 230), (x, int(sy)), 2)


# ------------------------------------------------------------------
# Terminal / vault / diamond / cash
# ------------------------------------------------------------------
def draw_terminal(surf, x, ground_y, state, t):
    desk = pygame.Rect(0, 0, 84, 40)
    desk.midbottom = (x, ground_y)
    v_gradient(surf, desk, (96, 70, 44), (58, 40, 26))
    pygame.draw.rect(surf, (140, 106, 66), (desk.x - 3, desk.y - 4, desk.w + 6, 6), border_radius=2)
    mon = pygame.Rect(0, 0, 46, 34)
    mon.midbottom = (x, desk.y - 6)
    pygame.draw.rect(surf, (34, 36, 44), mon.inflate(8, 8), border_radius=4)
    pygame.draw.rect(surf, (6, 14, 10), mon)
    pygame.draw.rect(surf, (80, 84, 96), (x - 6, desk.y - 7, 12, 5))
    col = (60, 255, 120) if state == "open" else (255, 80, 80)
    f = pygame.font.SysFont("couriernew,monospace", 9, bold=True)
    lines = ["ACCESS", "GRANTED"] if state == "open" else ["VAULT", "LOCKED", "_" if int(t * 2) % 2 else " "]
    for i, ln in enumerate(lines):
        surf.blit(f.render(ln, True, col), (mon.x + 5, mon.y + 4 + i * 10))
    glow(surf, mon.center, 46, col, 40, 3)


def draw_vault_door(surf, x, ground_y, ceil_y, openness, t):
    h = ground_y - ceil_y
    pygame.draw.rect(surf, (16, 18, 24), (x - 30, ceil_y, 60, h))
    rv = (28, 30, 38)
    for i in range(0, h, 26):
        pygame.draw.circle(surf, rv, (x - 26, ceil_y + 10 + i), 2)
        pygame.draw.circle(surf, rv, (x + 26, ceil_y + 10 + i), 2)
    if openness >= 0.999:
        return
    off = int(h * openness)
    slab = pygame.Rect(x - 22, ceil_y - off, 44, h)
    for i in range(slab.w):
        k = i / slab.w
        c = lerp_color((84, 90, 104), (190, 196, 210), math.sin(k * math.pi))
        pygame.draw.line(surf, c, (slab.x + i, slab.y), (slab.x + i, slab.bottom))
    pygame.draw.rect(surf, (36, 38, 46), slab, 3)
    cy = slab.centery
    pygame.draw.circle(surf, (60, 64, 76), (x, cy), 18)
    pygame.draw.circle(surf, (150, 156, 170), (x, cy), 18, 3)
    ang = openness * 720 + 20
    for k in range(4):
        a = math.radians(ang + k * 90)
        pygame.draw.line(surf, (200, 206, 220), (x, cy), (x + math.cos(a) * 16, cy + math.sin(a) * 16), 3)
    pygame.draw.circle(surf, GOLD, (x, cy), 4)
    pygame.draw.rect(surf, (40, 200, 90) if openness > 0 else (220, 50, 50), (x - 4, slab.y + 14, 8, 8))


def draw_diamond(surf, c, size, t):
    cx, cy = c
    w, h = size, size * 0.9
    top, gy = cy - h * 0.5, cy - h * 0.12
    tl, tr = (cx - w * 0.3, top), (cx + w * 0.3, top)
    gl, gr = (cx - w * 0.55, gy), (cx + w * 0.55, gy)
    g1, g2 = (cx - w * 0.2, gy), (cx + w * 0.2, gy)
    apx = (cx, cy + h * 0.55)
    tm = (cx, top)
    facets = [[tl, tm, g1, gl], [tm, tr, gr, g2], [tm, g2, g1], [gl, g1, apx], [g1, g2, apx], [g2, gr, apx]]
    glow(surf, c, size * 1.3, (150, 220, 255), 70 + int(25 * math.sin(t * 3)), 5)
    for i, f in enumerate(facets):
        k = 0.5 + 0.5 * math.sin(t * 2.2 + i * 1.3)
        col = lerp_color((70, 150, 225), (238, 252, 255), k * 0.85 + (0.15 if i < 3 else 0))
        pygame.draw.polygon(surf, col, f)
        pygame.draw.polygon(surf, (225, 245, 255), f, 1)
    for i in range(3):                                         # jholmol
        ph = (t * 1.3 + i * 0.37) % 1.0
        sx = cx + math.cos(i * 2.4) * w * 0.38
        sy = cy - h * 0.3 + math.sin(i * 1.7) * h * 0.3
        r = 2 + 7 * math.sin(ph * math.pi)
        pygame.draw.line(surf, WHITE, (sx - r, sy), (sx + r, sy), 2)
        pygame.draw.line(surf, WHITE, (sx, sy - r), (sx, sy + r), 2)


def draw_cash(surf, c, t):
    x, y = c
    y += math.sin(t * 3 + x * 0.01) * 2
    for k in range(3):
        r = pygame.Rect(0, 0, 28, 13)
        r.center = (x + (k - 1) * 3, y - k * 6)
        pygame.draw.rect(surf, (74, 168, 92), r, border_radius=2)
        pygame.draw.rect(surf, (36, 110, 56), r, 2, border_radius=2)
        pygame.draw.rect(surf, (230, 230, 210), (r.centerx - 3, r.y, 6, r.h))
    glow(surf, (x, y - 6), 26, (120, 255, 150), 36, 3)


def draw_locker(surf, x, ground_y, active, t):
    """Safe locker = checkpoint."""
    r = pygame.Rect(0, 0, 66, 92)
    r.midbottom = (x, ground_y + 2)
    if active:
        glow(surf, r.center, 90, (80, 255, 160), 50 + int(20 * math.sin(t * 4)), 5)
    v_gradient(surf, r, (150, 156, 170), (84, 88, 100))
    pygame.draw.rect(surf, (40, 44, 54), r, 3, border_radius=4)
    inner = r.inflate(-14, -14)
    pygame.draw.rect(surf, (104, 110, 124), inner, border_radius=3)
    pygame.draw.rect(surf, (60, 64, 76), inner, 2, border_radius=3)
    pygame.draw.circle(surf, (200, 204, 214), (inner.centerx - 8, inner.centery + 6), 12)
    pygame.draw.circle(surf, (70, 74, 86), (inner.centerx - 8, inner.centery + 6), 12, 2)
    for k in range(6):
        a = math.radians(k * 60 + 15)
        pygame.draw.line(surf, (70, 74, 86), (inner.centerx - 8, inner.centery + 6),
                         (inner.centerx - 8 + math.cos(a) * 11, inner.centery + 6 + math.sin(a) * 11), 1)
    pad = pygame.Rect(inner.right - 18, inner.top + 6, 12, 18)
    pygame.draw.rect(surf, (30, 34, 40), pad, border_radius=2)
    led = (60, 255, 130) if active else (255, 70, 70)
    pygame.draw.circle(surf, led, (pad.centerx, pad.y + 5), 3)
    for k in range(3):
        pygame.draw.rect(surf, (90, 96, 110), (pad.x + 2, pad.y + 10 + k * 3, 8, 2))
    pygame.draw.rect(surf, (200, 160, 60), (r.x + 4, r.bottom - 9, r.w - 8, 5))


def draw_ledge(surf, x0, x1, y):
    """Counter / shelf (uporey uthar jaygа)."""
    w = int(x1 - x0)
    top = pygame.Rect(int(x0), int(y), w, 7)
    pygame.draw.rect(surf, (168, 124, 76), top, border_radius=3)
    pygame.draw.rect(surf, (206, 164, 110), (top.x, top.y, top.w, 2), border_radius=2)
    front = pygame.Rect(int(x0) + 2, int(y) + 7, w - 4, 11)
    v_gradient(surf, front, (98, 66, 40), (56, 38, 24))
    pygame.draw.rect(surf, (214, 170, 70), (int(x0), int(y) + 6, w, 2))
    for i in range(int(w // 34)):
        pygame.draw.rect(surf, (70, 48, 30), (int(x0) + 10 + i * 34, int(y) + 10, 20, 5), 1)


# ------------------------------------------------------------------
# TV (intro) ar police gari
# ------------------------------------------------------------------
def draw_tv_body(surf, rect):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surf, (10, 10, 14), rect.move(8, 10), border_radius=24)
    v_gradient(surf, rect, (74, 66, 58), (34, 30, 26))
    pygame.draw.rect(surf, (20, 18, 16), rect, 4, border_radius=18)
    screen = rect.inflate(-44, -52)
    pygame.draw.rect(surf, (4, 4, 6), screen.inflate(10, 10), border_radius=16)
    return screen


def draw_tv_glass(surf, screen, t):
    sc = pygame.Surface(screen.size, pygame.SRCALPHA)
    for y in range(0, screen.h, 3):
        pygame.draw.line(sc, (0, 0, 0, 60), (0, y), (screen.w, y))
    pygame.draw.polygon(sc, (255, 255, 255, 26), [(0, 0), (screen.w * 0.55, 0), (screen.w * 0.15, screen.h), (0, screen.h)])
    for i in range(6):                                          # vignette
        pygame.draw.rect(sc, (0, 0, 0, 14), sc.get_rect().inflate(-i * 6, -i * 6), 6, border_radius=14)
    for _ in range(40):                                         # static noise
        x, y = random.randint(0, screen.w - 1), random.randint(0, screen.h - 1)
        c = random.randint(120, 255)
        sc.set_at((x, y), (c, c, c, 40))
    surf.blit(sc, screen.topleft)


def draw_police_car(surf, x, feet_y, facing, t):
    w, h = 200, 100
    tmp = pygame.Surface((w, h), pygame.SRCALPHA)
    base_y = h - 14
    pygame.draw.ellipse(tmp, (0, 0, 0, 90), (10, base_y - 2, w - 20, 12))
    body = [(8, base_y - 22), (30, base_y - 28), (60, base_y - 30), (78, base_y - 54), (140, base_y - 54),
            (160, base_y - 30), (190, base_y - 26), (194, base_y - 8), (8, base_y - 8)]
    pygame.draw.polygon(tmp, (238, 240, 248), body)
    pygame.draw.polygon(tmp, (30, 60, 150), [(8, base_y - 16), (194, base_y - 16), (194, base_y - 8), (8, base_y - 8)])
    pygame.draw.polygon(tmp, (255, 255, 255), [(8, base_y - 22), (30, base_y - 28), (60, base_y - 30), (190, base_y - 26),
                                               (194, base_y - 18), (8, base_y - 18)])
    pygame.draw.polygon(tmp, (30, 40, 70), body, 3)
    pygame.draw.polygon(tmp, (80, 120, 170), [(84, base_y - 50), (110, base_y - 50), (110, base_y - 32), (70, base_y - 32)])
    pygame.draw.polygon(tmp, (60, 100, 150), [(116, base_y - 50), (136, base_y - 50), (152, base_y - 32), (116, base_y - 32)])
    f = _font(10)
    tmp.blit(f.render("POLICE", True, (20, 40, 110)), (24, base_y - 24))
    for wx in (46, 150):
        pygame.draw.circle(tmp, (16, 16, 20), (wx, base_y - 4), 16)
        pygame.draw.circle(tmp, (150, 154, 166), (wx, base_y - 4), 8)
        pygame.draw.circle(tmp, (60, 64, 76), (wx, base_y - 4), 3)
    red_on = int(t * 6) % 2 == 0
    pygame.draw.rect(tmp, (255, 40, 50) if red_on else (90, 14, 20), (98, base_y - 62, 16, 8), border_radius=2)
    pygame.draw.rect(tmp, (50, 110, 255) if not red_on else (14, 30, 90), (114, base_y - 62, 16, 8), border_radius=2)
    if facing < 0:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (int(x) - w // 2, int(feet_y) - (h - 14) - 2))
    lx = x + (-16 if red_on else 16) * (1 if facing > 0 else -1)
    glow(surf, (lx, feet_y - 70), 70, (255, 50, 60) if red_on else (60, 120, 255), 70, 4)


# ------------------------------------------------------------------
# Tool icon (menu, Ctrl+Alt wheel)
# ------------------------------------------------------------------
def draw_tool_icon(surf, tool_id, c, r, t=0.0):
    cx, cy = int(c[0]), int(c[1])
    if tool_id == "laser":
        body = pygame.Rect(0, 0, int(r * 1.1), int(r * 0.55))
        body.center = (cx - int(r * 0.35), cy + int(r * 0.2))
        v_gradient(surf, body, (150, 156, 170), (80, 84, 96))
        pygame.draw.rect(surf, (30, 32, 40), body, 2, border_radius=5)
        pygame.draw.rect(surf, (255, 150, 40), (body.x + 6, body.y + 5, int(r * 0.3), 6), border_radius=2)
        pygame.draw.rect(surf, (60, 64, 76), (body.right - 6, body.y + 4, int(r * 0.25), body.h - 8), border_radius=3)
        by = body.centery
        glow(surf, (body.right + int(r * 0.45), by), r * 0.6, (255, 50, 60), 80, 3)
        pygame.draw.line(surf, (255, 70, 80), (body.right + 4, by), (cx + int(r * 0.9), by), 4)
        pygame.draw.line(surf, (255, 220, 220), (body.right + 4, by), (cx + int(r * 0.9), by), 1)
        for k in (-1, 1):
            pygame.draw.line(surf, WHITE, (cx + int(r * 0.55), cy - 10 * k - 8), (cx + int(r * 0.8), cy + 10 * k + 8), 2)
    elif tool_id == "hacker":
        pygame.draw.polygon(surf, (36, 38, 48), [(cx, cy - r * 0.95), (cx - r * 0.75, cy + r * 0.2), (cx - r * 0.5, cy + r * 0.8),
                                                 (cx + r * 0.5, cy + r * 0.8), (cx + r * 0.75, cy + r * 0.2)])
        pygame.draw.polygon(surf, (70, 74, 90), [(cx, cy - r * 0.95), (cx - r * 0.75, cy + r * 0.2), (cx - r * 0.5, cy + r * 0.8),
                                                 (cx + r * 0.5, cy + r * 0.8), (cx + r * 0.75, cy + r * 0.2)], 2)
        pygame.draw.ellipse(surf, (4, 6, 8), (cx - r * 0.42, cy - r * 0.45, r * 0.84, r * 0.95))
        for dx in (-0.2, 0.2):
            pygame.draw.ellipse(surf, (60, 255, 130), (cx + dx * r - 4, cy - r * 0.12, 9, 6))
        f = pygame.font.SysFont("couriernew,monospace", max(8, int(r * 0.2)), bold=True)
        s = "".join(random.Random(int(t * 4) + i).choice("01") for i in range(6))
        img = f.render(s, True, (60, 255, 130))
        surf.blit(img, img.get_rect(center=(cx, cy + r * 0.45)))
    elif tool_id == "laptop":
        scr = pygame.Rect(0, 0, int(r * 1.35), int(r * 0.9))
        scr.center = (cx, cy - int(r * 0.12))
        pygame.draw.rect(surf, (36, 38, 46), scr.inflate(8, 8), border_radius=5)
        pygame.draw.rect(surf, (6, 18, 12), scr)
        f = pygame.font.SysFont("couriernew,monospace", max(8, int(r * 0.3)), bold=True)
        surf.blit(f.render(">_" if int(t * 2) % 2 else "> ", True, (60, 255, 130)), (scr.x + 5, scr.y + 5))
        for k in range(3):
            pygame.draw.line(surf, (40, 160, 90), (scr.x + 6, scr.y + 24 + k * 7), (scr.right - 10 - k * 8, scr.y + 24 + k * 7), 2)
        pygame.draw.polygon(surf, (150, 154, 166), [(scr.x - 10, scr.bottom + 8), (scr.right + 10, scr.bottom + 8),
                                                    (scr.right + 18, scr.bottom + 16), (scr.x - 18, scr.bottom + 16)])
    elif tool_id == "emp":
        for k in range(3):
            rr = r * (0.35 + 0.28 * ((t * 1.4 + k / 3) % 1.0) * 2)
            pygame.draw.circle(surf, (90, 190, 255), (cx, cy), int(rr), 2)
        glow(surf, (cx, cy), r * 0.6, (90, 190, 255), 70, 3)
        pygame.draw.polygon(surf, (255, 240, 120), [(cx + r * 0.1, cy - r * 0.75), (cx - r * 0.4, cy + r * 0.1), (cx - r * 0.02, cy + r * 0.1),
                                                    (cx - r * 0.15, cy + r * 0.78), (cx + r * 0.42, cy - r * 0.15), (cx + r * 0.03, cy - r * 0.15)])
    elif tool_id == "decoy":
        pygame.draw.ellipse(surf, (70, 76, 96), (cx - r * 0.36, cy - r * 0.18, r * 0.72, r * 0.42))
        pygame.draw.ellipse(surf, (150, 156, 180), (cx - r * 0.36, cy - r * 0.18, r * 0.72, r * 0.42), 2)
        pygame.draw.circle(surf, (255, 90, 90), (cx, cy + int(r * 0.02)), max(2, int(r * 0.09)))
        for sx in (-1, 1):
            ax = cx + sx * r * 0.62
            pygame.draw.line(surf, (110, 116, 140), (cx + sx * r * 0.3, cy - r * 0.1), (ax, cy - r * 0.3), 3)
            w = r * 0.3 * (1 if int(t * 12) % 2 else 0.6)
            pygame.draw.line(surf, (220, 225, 240), (ax - w, cy - r * 0.3), (ax + w, cy - r * 0.3), 3)
        for k in range(3):
            pygame.draw.arc(surf, (255, 220, 90), (cx - r * (0.3 + 0.2 * k), cy + r * 0.2, r * (0.6 + 0.4 * k), r * 0.5), 3.6, 5.8, 2)
    elif tool_id == "rewirer":
        chip = pygame.Rect(0, 0, int(r * 0.9), int(r * 0.7))
        chip.center = (cx, cy)
        for k in range(4):
            pygame.draw.line(surf, (200, 200, 120), (chip.x + 6 + k * int(r * 0.22), chip.y - 6), (chip.x + 6 + k * int(r * 0.22), chip.y), 2)
            pygame.draw.line(surf, (200, 200, 120), (chip.x + 6 + k * int(r * 0.22), chip.bottom), (chip.x + 6 + k * int(r * 0.22), chip.bottom + 6), 2)
        pygame.draw.rect(surf, (30, 70, 50), chip, border_radius=4)
        pygame.draw.rect(surf, (60, 255, 130), chip, 2, border_radius=4)
        pygame.draw.line(surf, (255, 70, 70), (chip.x + 6, chip.centery), (chip.right - 6, chip.centery), 3)
        pygame.draw.line(surf, (60, 255, 130), (chip.x + 10, chip.centery + 8), (chip.right - 10, chip.centery - 8), 2)
        pygame.draw.circle(surf, (255, 70, 70), (cx, cy - int(r * 0.8)), max(3, int(r * 0.12)))
    elif tool_id == "smoke":
        for i, (dx, dy, rr) in enumerate(((-0.35, 0.1, 0.38), (0.3, 0.12, 0.34), (0.0, -0.2, 0.42), (-0.05, 0.3, 0.3))):
            g = 150 + i * 14
            pygame.draw.circle(surf, (g, g, g + 8), (int(cx + dx * r), int(cy + dy * r - math.sin(t * 2 + i) * 2)), int(rr * r))
        pygame.draw.circle(surf, (225, 228, 235), (int(cx - 0.1 * r), int(cy - 0.3 * r)), int(0.16 * r))
    elif tool_id == "thermite":
        can = pygame.Rect(0, 0, int(r * 0.6), int(r * 0.85))
        can.center = (cx - int(r * 0.3), cy + int(r * 0.1))
        v_gradient(surf, can, (150, 154, 166), (80, 84, 96))
        pygame.draw.rect(surf, (230, 90, 30), (can.x, can.y + can.h // 3, can.w, 7))
        glow(surf, (cx + r * 0.35, cy + r * 0.2), r * 0.7, (255, 140, 40), 90, 4)
        fl = [(cx + r * 0.35, cy - r * 0.6), (cx + r * 0.7, cy + r * 0.1), (cx + r * 0.55, cy + r * 0.6), (cx + r * 0.15, cy + r * 0.6), (cx + r * 0.0, cy + r * 0.1)]
        pygame.draw.polygon(surf, (255, 110, 30), fl)
        pygame.draw.polygon(surf, (255, 220, 90), [(cx + r * 0.35, cy - r * 0.1), (cx + r * 0.52, cy + r * 0.35), (cx + r * 0.2, cy + r * 0.45)])
    elif tool_id == "keycard":
        card = pygame.Rect(0, 0, int(r * 1.3), int(r * 0.85))
        card.center = (cx, cy)
        v_gradient(surf, card, (70, 120, 220), (36, 60, 140))
        pygame.draw.rect(surf, (200, 220, 255), card, 2, border_radius=6)
        pygame.draw.rect(surf, (230, 190, 70), (card.x + 8, card.y + 10, int(r * 0.3), int(r * 0.22)), border_radius=3)
        pygame.draw.rect(surf, (20, 24, 50), (card.x, card.bottom - 14, card.w, 8))
        for k in range(3):
            pygame.draw.arc(surf, (160, 255, 200), (card.right - 22 + k * 4, card.y + 6, 14, 14), -1.0, 1.0, 2)
    elif tool_id == "cutter":
        # WIRE CUTTER: duita lal hatol + tar + chhurir moto dhar
        for sgn, col in ((-1, (210, 60, 60)), (1, (190, 40, 40))):
            hx = cx + sgn * r * 0.28
            pygame.draw.line(surf, col, (hx + sgn * r * 0.2, cy + r * 0.85), (cx + sgn * r * 0.05, cy + r * 0.1), max(4, int(r * 0.2)))
            pygame.draw.line(surf, (235, 235, 245), (cx, cy + r * 0.05), (cx - sgn * r * 0.45, cy - r * 0.75), max(3, int(r * 0.16)))
            pygame.draw.line(surf, (110, 114, 130), (cx, cy + r * 0.05), (cx - sgn * r * 0.45, cy - r * 0.75), max(1, int(r * 0.05)))
        pygame.draw.circle(surf, (60, 64, 80), (cx, int(cy + r * 0.05)), max(3, int(r * 0.13)))
        pygame.draw.circle(surf, (255, 220, 90), (cx, int(cy + r * 0.05)), max(1, int(r * 0.06)))
        sp = 0.5 + 0.5 * math.sin(t * 6)
        pygame.draw.line(surf, (70, 160, 250), (cx - r * 0.95, cy - r * 0.1), (cx - r * 0.5, cy - r * 0.45), 3)
        pygame.draw.circle(surf, (255, 240, 120), (int(cx - r * 0.5), int(cy - r * 0.45)), max(2, int(r * 0.1 * (0.6 + sp))))
    else:                                                       # lock
        gray = (125, 125, 150)
        pygame.draw.arc(surf, gray, (cx - r * 0.3, cy - r * 0.62, r * 0.6, r * 0.9), 0, math.pi, 4)
        body = pygame.Rect(0, 0, int(r * 0.9), int(r * 0.65))
        body.center = (cx, cy + int(r * 0.18))
        pygame.draw.rect(surf, gray, body, border_radius=5)
        pygame.draw.circle(surf, (35, 35, 52), body.center, 5)


# ------------------------------------------------------------------
# K9 police dog
# ------------------------------------------------------------------
def draw_dog(surf, x, feet_y, facing=1, t=0.0, anim="idle", flash=0.0, alpha=255):
    """anim: idle | run | bark | dead"""
    tmp = pygame.Surface((120, 80), pygame.SRCALPHA)
    fur, fur_d, fur_l = (150, 100, 56), (96, 62, 34), (196, 144, 88)
    dark = (20, 16, 14)
    gy = 72
    if anim == "dead":
        pygame.draw.ellipse(tmp, fur_d, (20, gy - 20, 66, 20))
        pygame.draw.ellipse(tmp, fur, (22, gy - 22, 60, 16))
        pygame.draw.ellipse(tmp, fur, (74, gy - 22, 26, 16))
        pygame.draw.line(tmp, dark, (88, gy - 18), (92, gy - 14), 2)
        pygame.draw.line(tmp, dark, (92, gy - 18), (88, gy - 14), 2)
        out = tmp
    else:
        ph = t * (16 if anim == "run" else 3)
        bob = abs(math.sin(ph)) * 3 if anim == "run" else 0
        sn = math.sin(ph)
        by = gy - 30 - bob
        # legs
        for lx, sg in ((30, 1), (38, -1), (74, -1), (82, 1)):
            off = sn * 9 * sg if anim == "run" else 0
            pygame.draw.line(tmp, fur_d, (lx, by + 12), (lx + off, gy), 6)
            pygame.draw.circle(tmp, dark, (int(lx + off), gy), 3)
        # tail
        wag = math.sin(t * 14) * 6 if anim != "idle" else math.sin(t * 5) * 3
        pygame.draw.line(tmp, fur_d, (22, by + 2), (8, by - 14 + wag), 6)
        # body
        pygame.draw.ellipse(tmp, fur_d, (18, by - 4, 76, 30))
        pygame.draw.ellipse(tmp, fur, (18, by - 6, 76, 26))
        pygame.draw.ellipse(tmp, fur_l, (30, by - 5, 44, 10))
        pygame.draw.rect(tmp, (190, 40, 50), (82, by - 6, 7, 22), border_radius=2)     # collar
        # head
        hy = by - 12 - (4 if anim == "bark" else 0)
        pygame.draw.circle(tmp, fur, (98, hy + 6), 14)
        snout = (104, hy + 8, 18, 11) if anim != "bark" else (104, hy + 3, 18, 8)
        pygame.draw.ellipse(tmp, fur_l, snout)
        if anim == "bark":
            pygame.draw.ellipse(tmp, (150, 30, 40), (104, hy + 12, 18, 8))
            pygame.draw.polygon(tmp, WHITE, [(108, hy + 12), (111, hy + 17), (114, hy + 12)])
        pygame.draw.circle(tmp, dark, (121, hy + 8), 3)
        pygame.draw.polygon(tmp, fur_d, [(88, hy - 6), (96, hy - 16), (100, hy - 2)])
        pygame.draw.circle(tmp, (255, 255, 255), (102, hy + 3), 3)
        pygame.draw.circle(tmp, dark, (103, hy + 3), 1)
        out = tmp
    if flash > 0:
        out = out.copy()
        out.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGB_ADD)
    if facing < 0:
        out = pygame.transform.flip(out, True, False)
    if alpha < 255:
        out = out.copy()
        out.set_alpha(alpha)
    surf.blit(out, (int(x) - 60, int(feet_y) - gy))


# ------------------------------------------------------------------
# Kotha-r bubble
# ------------------------------------------------------------------
def draw_speech(surf, text, midbottom, font, color=(20, 20, 35), shake=0.0, tail=True, border=RED):
    lines = text.split("\n")
    imgs = [font.render(l, True, color) for l in lines]
    w = max(i.get_width() for i in imgs) + 30
    h = sum(i.get_height() for i in imgs) + 20
    ox = random.uniform(-shake, shake)
    box = pygame.Rect(0, 0, w, h)
    box.midbottom = (int(midbottom[0] + ox), int(midbottom[1]))
    pygame.draw.rect(surf, WHITE, box, border_radius=14)
    pygame.draw.rect(surf, border, box, 3, border_radius=14)
    if tail:
        tri = [(box.centerx - 10, box.bottom - 2), (box.centerx + 10, box.bottom - 2), (box.centerx, box.bottom + 16)]
        pygame.draw.polygon(surf, WHITE, tri)
        pygame.draw.lines(surf, border, False, tri, 3)
    y = box.top + 10
    for img in imgs:
        surf.blit(img, img.get_rect(midtop=(box.centerx, y)))
        y += img.get_height()
    return box
