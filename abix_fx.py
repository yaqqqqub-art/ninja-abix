"""
abix_fx.py  -  ABIX NINJA PRO ULTRA v3  (notun feature gulo ek jaygay)

  * Tutorial          - prothom bar game khulle ashe, pore main menu / pause theke abar dekha jay.
                        Je CONTROL (keyboard / controller) select kora, tar lekha dekhay.
  * WireCutGame       - WIRE CUTTER tool er mini game (Level 3, 4, 5, 6, 8, 9 er terminal e).
  * warp_lid / draw_deck - laptop / terminal er 3D "dhakna khola" animation.
  * draw_tool_select  - tool select korle animation (ring + icon + naam).
  * draw_autowriter   - AUTO CODE WRITER chalu thakle upore likhar animation.
"""
import math
import random

import pygame

import sound
import sprites as SP
from animation import WIDTH, HEIGHT, WHITE, GOLD, get_font, rgb_color

CUTTER_LEVELS = ("level3", "level4", "level5", "level6", "level8", "level9")   # WIRE CUTTER shudhu ei level gulo te kaj kore
CUTTER_TEXT = "Level 3, 4, 5, 6, 8 and 9"
# v9: Level 4 = GREEN wire, Level 6 = RED wire, Level 8 = BLUE wire (ei rong er tar ta MAIN LINE, shobar shesh e katte hoy)
CUTTER_THEME = {"level4": "GREEN", "level6": "RED", "level8": "BLUE"}


# ------------------------------------------------------------------
# easing
# ------------------------------------------------------------------
def ease_out_cubic(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_out_back(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


# ------------------------------------------------------------------
# 3D laptop lid  (dhakna khola)
# ------------------------------------------------------------------
LID_TIME = 0.75


def warp_lid(src, k):
    """src = full screen size (SRCALPHA) surface.  k 0..1  -> dhakna kotota khola.
    Niche (hinge) e pura chaura, upore choto (perspective).  Return: surface (screen size)."""
    k = max(0.0, min(1.0, k))
    out = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    e = ease_out_back(k) if k < 1 else 1.0
    e = max(0.02, min(1.04, e))
    hinge = HEIGHT - 6
    top = hinge - int(hinge * min(1.0, e))
    h = hinge - top
    if h < 2:
        return out
    step = 3
    top_w = 0.50 + 0.50 * min(1.0, e)               # upore kom chaura
    for y in range(0, h, step):
        u = y / float(h)                             # 0 = upor, 1 = hinge
        wd = int(WIDTH * (top_w + (1.0 - top_w) * u))
        sy = int(u * (HEIGHT - step))
        strip = src.subsurface((0, sy, WIDTH, step))
        if wd < 4:
            continue
        sc = pygame.transform.scale(strip, (wd, step))
        out.blit(sc, ((WIDTH - wd) // 2, top + y))
    # dhakna er chhaya (shesh e shob alo hoye jay)
    if k < 1:
        sh = pygame.Surface((WIDTH, h), pygame.SRCALPHA)
        sh.fill((0, 0, 0, int(150 * (1 - k))))
        out.blit(sh, (0, top))
    return out


def draw_deck(surf, t, k=1.0):
    """Laptop er niche er 'keyboard deck' (3D slab).  k = kotota dekha jabe."""
    a = int(255 * max(0.0, min(1.0, k)))
    deck = pygame.Surface((WIDTH, 30), pygame.SRCALPHA)
    pts = [(40, 0), (WIDTH - 40, 0), (WIDTH - 4, 30), (4, 30)]
    pygame.draw.polygon(deck, (58, 62, 76, a), pts)
    pygame.draw.polygon(deck, (130, 136, 156, a), pts, 2)
    pygame.draw.line(deck, (190, 196, 214, a), (60, 2), (WIDTH - 60, 2), 2)
    for i in range(18):                              # keyboard dot
        x = 90 + i * 44
        pygame.draw.rect(deck, (30, 32, 42, a), (x, 12, 28, 6), border_radius=2)
    pygame.draw.rect(deck, (36, 38, 50, a), (WIDTH // 2 - 50, 21, 100, 6), border_radius=3)
    surf.blit(deck, (0, HEIGHT - 30))


def lid_glow(surf, k, t):
    """Khola'r somoy screen theke alo."""
    if k >= 1:
        return
    g = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(g, (90, 170, 255, int(70 * k)), (WIDTH // 2 - 380, HEIGHT - 160, 760, 150))
    surf.blit(g, (0, 0))



# ------------------------------------------------------------------
# v9: USB plug 3D animation  (terminal er shamne gele: USB lagay, tarpor laptop on hoy)
# ------------------------------------------------------------------
USB_TIME = 2.3


def _ease_io(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _box3d(surf, x, y, w, h, dx, dy, front, top, side, edge=(8, 10, 16)):
    """Oblique 3D box: samne (front), upor (top), dan pash (side)."""
    t_pts = [(x, y), (x + dx, y - dy), (x + w + dx, y - dy), (x + w, y)]
    s_pts = [(x + w, y), (x + w + dx, y - dy), (x + w + dx, y + h - dy), (x + w, y + h)]
    pygame.draw.polygon(surf, top, t_pts)
    pygame.draw.polygon(surf, side, s_pts)
    pygame.draw.rect(surf, front, (x, y, w, h))
    pygame.draw.polygon(surf, edge, t_pts, 2)
    pygame.draw.polygon(surf, edge, s_pts, 2)
    pygame.draw.rect(surf, edge, (x, y, w, h), 2)
    return s_pts


def draw_usb_plug(surf, k, t):
    """k 0..1.  Terminal er port e USB stick ashe, dhuke jay, LED sobuj hoy, 'ABIX OS booting'."""
    k = max(0.0, min(1.0, k))
    dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, int(205 * min(1.0, k * 5))))
    surf.blit(dim, (0, 0))
    appear = ease_out_cubic(k / 0.18)
    cx, cy = WIDTH // 2, HEIGHT // 2 + 10
    fw, fh, dx, dy = 300, 230, 56, 44
    fx = cx - 240 + int((1 - appear) * -40)
    fy = cy - 110
    # chhaya
    sh = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, int(120 * appear)), (fx - 10, 10, fw + dx + 40, 50))
    surf.blit(sh, (0, fy + fh + 6))
    plugged = k >= 0.66
    scr_col = (60, 255, 140) if plugged else (255, 70, 70)
    side = _box3d(surf, fx, fy, fw, fh, dx, dy, (44, 48, 62), (86, 92, 114), (28, 30, 40))
    # screen
    scr = pygame.Rect(fx + 18, fy + 18, fw - 36, fh - 78)
    pygame.draw.rect(surf, (4, 12, 10), scr, border_radius=6)
    pygame.draw.rect(surf, scr_col, scr, 2, border_radius=6)
    f = get_font(22)
    lab = f.render("USB OK" if plugged else "LOCKED", True, scr_col)
    surf.blit(lab, lab.get_rect(center=(scr.centerx, scr.y + 30)))
    if plugged:
        for i in range(4):
            g = pygame.font.SysFont("couriernew,monospace", 12, bold=True).render(
                ["> mount /dev/usb0", "> abix.os --boot", "> link terminal", "> ready"][i], True, (90, 230, 150))
            if k > 0.7 + i * 0.05:
                surf.blit(g, (scr.x + 12, scr.y + 56 + i * 16))
    else:
        pd = pygame.Rect(0, 0, 26, 20)
        pd.center = (scr.centerx, scr.y + 86)
        pygame.draw.rect(surf, (255, 90, 90), pd, border_radius=4)
        pygame.draw.arc(surf, (255, 90, 90), (pd.x + 3, pd.y - 16, 20, 26), 0, math.pi, 4)
    # buttons / LED
    pygame.draw.circle(surf, scr_col if (plugged or int(t * 3) % 2) else (90, 20, 20), (fx + 30, fy + fh - 28), 7)
    for i in range(5):
        pygame.draw.rect(surf, (28, 30, 40), (fx + 70 + i * 40, fy + fh - 38, 30, 18), border_radius=3)
    # port (dan pashe)
    px = (side[0][0] + side[2][0]) // 2
    py = (side[0][1] + side[2][1]) // 2 + 34
    near = _ease_io((k - 0.40) / 0.2)
    if near > 0:
        SP_glow = pygame.Surface((90, 70), pygame.SRCALPHA)
        pygame.draw.ellipse(SP_glow, (80, 200, 255, int(110 * near)), SP_glow.get_rect())
        surf.blit(SP_glow, (px - 45, py - 35))
    pygame.draw.polygon(surf, (6, 8, 12), [(px - 6, py - 12), (px + 14, py - 17), (px + 14, py + 6), (px - 6, py + 11)])
    pygame.draw.polygon(surf, (120, 130, 160), [(px - 6, py - 12), (px + 14, py - 17), (px + 14, py + 6), (px - 6, py + 11)], 2)
    # USB stick
    fly = ease_out_cubic((k - 0.10) / 0.45)
    ins = _ease_io((k - 0.58) / 0.10)
    gap = 36 + (1 - fly) * 430 - ins * 44
    tip_x = px + 8 + gap
    tip_y = py - 2 + (1 - fly) * -120 + math.sin(t * 7) * 4 * (1 - ins) * (1 if fly > 0.05 else 0)
    if k > 0.1:
        # connector (metal)
        _box3d(surf, int(tip_x), int(tip_y - 11), 36, 22, 9, 7, (190, 196, 210), (226, 230, 240), (130, 136, 152))
        pygame.draw.rect(surf, (60, 66, 84), (int(tip_x + 8), int(tip_y - 3), 6, 6))
        pygame.draw.rect(surf, (60, 66, 84), (int(tip_x + 20), int(tip_y - 3), 6, 6))
        # body
        bx = int(tip_x + 36)
        _box3d(surf, bx, int(tip_y - 17), 96, 34, 11, 9, (36, 40, 52), (70, 130, 220), (22, 26, 36))
        pygame.draw.rect(surf, (70, 140, 250), (bx + 8, int(tip_y - 17), 56, 6))
        lt = f"ABIX"
        surf.blit(get_font(13).render(lt, True, (235, 240, 255)), (bx + 12, int(tip_y - 6)))
        pygame.draw.circle(surf, (255, 255, 255), (bx + 84, int(tip_y)), 5, 2)
        led_on = plugged and int(t * 8) % 2 == 0
        pygame.draw.circle(surf, (90, 255, 150) if led_on else (30, 60, 40), (bx + 70, int(tip_y)), 3)
    # sparks masha lagar somoy
    if 0.62 <= k <= 0.74:
        r = random.Random(int(k * 100))
        for _ in range(14):
            ang = r.uniform(-1.2, 1.2) + math.pi
            dist = r.uniform(6, 34) * (k - 0.62) / 0.12
            pygame.draw.circle(surf, (255, 230, 120), (int(px + math.cos(ang) * dist), int(py + math.sin(ang) * dist)), 2)
    # text + bar
    if k < 0.58:
        msg = "INSERTING USB" + "." * (1 + int(t * 4) % 3)
        mc = (255, 220, 120)
    elif k < 0.76:
        msg = "USB DETECTED"
        mc = (120, 255, 170)
    else:
        msg = "ABIX OS 11  -  POWERING ON" + "." * (1 + int(t * 4) % 3)
        mc = (150, 215, 255)
    img = get_font(22).render(msg, True, mc)
    surf.blit(img, img.get_rect(center=(WIDTH // 2, 58)))
    bar = pygame.Rect(WIDTH // 2 - 130, 84, 260, 8)
    pygame.draw.rect(surf, (20, 28, 40), bar, border_radius=4)
    pygame.draw.rect(surf, mc, (bar.x, bar.y, int(bar.w * k), bar.h), border_radius=4)

# ------------------------------------------------------------------
# Tool select animation
# ------------------------------------------------------------------
TOOL_ANIM_T = 0.9


def draw_tool_select(surf, tool, age, t):
    """tool = TOOLS er dict.  age = koto second age select hoyeche (0..TOOL_ANIM_T)."""
    if age < 0 or age > TOOL_ANIM_T:
        return
    k = age / TOOL_ANIM_T
    cx, cy = WIDTH // 2, HEIGHT - 235
    a = int(255 * (1 - ease_out_cubic(max(0.0, (k - 0.55) / 0.45))))
    # 3 ta ring bere jay
    for i in range(3):
        kk = max(0.0, k * 1.25 - i * 0.14)
        if 0 < kk < 1:
            rr = 20 + 90 * ease_out_cubic(kk)
            col = rgb_color(t, offset=i * 0.2)
            ring = pygame.Surface((int(rr * 2) + 8, int(rr * 2) + 8), pygame.SRCALPHA)
            pygame.draw.circle(ring, (*col, int(200 * (1 - kk))), ring.get_rect().center, int(rr), 3)
            surf.blit(ring, ring.get_rect(center=(cx, cy)))
    # spark
    rnd = random.Random(int(tool.get("key", "1") or 1) * 7)
    for i in range(14):
        ang = rnd.random() * math.tau
        dist = 30 + 85 * ease_out_cubic(k) * (0.6 + 0.4 * rnd.random())
        px, py = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist
        pygame.draw.circle(surf, (255, 235, 150), (int(px), int(py)), max(1, int(4 * (1 - k))))
    # icon (zoom-in with bounce)
    sc = 0.4 + 0.9 * ease_out_back(min(1.0, k / 0.45))
    box = pygame.Surface((160, 160), pygame.SRCALPHA)
    pygame.draw.circle(box, (22, 24, 40, 230), (80, 80), 62)
    pygame.draw.circle(box, (*rgb_color(t), 255), (80, 80), 62, 4)
    SP.draw_tool_icon(box, tool["id"], (80, 80), 36, t)
    box = pygame.transform.smoothscale(box, (max(2, int(160 * sc)), max(2, int(160 * sc))))
    box.set_alpha(a)
    surf.blit(box, box.get_rect(center=(cx, cy)))
    # naam
    f = get_font(24).render(tool["name"], True, GOLD)
    f.set_alpha(a)
    surf.blit(f, f.get_rect(center=(cx, cy + 82 - int(8 * (1 - ease_out_cubic(k * 2))))))


# ------------------------------------------------------------------
# AUTO CODE WRITER banner (upore)
# ------------------------------------------------------------------
def draw_autowriter(surf, label, frac, t):
    box = pygame.Rect(0, 0, 440, 46)
    box.midtop = (WIDTH // 2, 6)
    bg = pygame.Surface(box.size, pygame.SRCALPHA)
    pygame.draw.rect(bg, (8, 22, 14, 225), bg.get_rect(), border_radius=12)
    pygame.draw.rect(bg, (60, 255, 140, 255), bg.get_rect(), 2, border_radius=12)
    surf.blit(bg, box.topleft)
    # ghost haat (keyboard e tip-tip)
    for i in range(4):
        hx = box.x + 22 + i * 9
        hy = box.y + 22 + int(math.sin(t * 22 + i * 1.7) * 5)
        pygame.draw.rect(surf, (90, 255, 160), (hx, hy, 6, 10), border_radius=2)
    f = get_font(14).render("AUTO CODE WRITER", True, (120, 255, 170))
    surf.blit(f, (box.x + 70, box.y + 6))
    dots = "." * (1 + int(t * 4) % 3)
    f2 = pygame.font.SysFont("couriernew,monospace", 13, bold=True).render(label + dots, True, (200, 255, 215))
    surf.blit(f2, (box.x + 70, box.y + 24))
    bar = pygame.Rect(box.right - 90, box.centery - 5, 76, 10)
    pygame.draw.rect(surf, (14, 40, 28), bar, border_radius=5)
    pygame.draw.rect(surf, (60, 255, 140), (bar.x, bar.y, int(bar.w * max(0.0, min(1.0, frac))), bar.h), border_radius=5)


# ------------------------------------------------------------------
# WIRE CUTTER mini game
# ------------------------------------------------------------------
CUT_COLORS = [("RED", (235, 70, 70)), ("BLUE", (70, 140, 250)), ("GREEN", (80, 200, 110)),
              ("YELLOW", (245, 200, 60)), ("PURPLE", (190, 100, 240))]


class WireCutGame:
    """Modal 'pad' (event/update/draw).  Note e lekha rong er ordere tar kato.
    Bhul tar kate = short circuit (bhul hole notun kore shuru, kono mrittu nei)."""

    def __init__(self, title, done_fn=None, rng=None, theme=None):
        self.theme = theme            # "GREEN" / "RED" / "BLUE"  (Level 4 / 6 / 8)  ba None
        self.title = title
        self.done_fn = done_fn
        self.rng = rng or random.Random()
        self.t = 0.0
        self.ok = False
        self.ok_t = 0.0
        self.err = 0.0
        self.wrong = 0
        self.sparks = []
        self.reset()

    def reset(self):
        names = [c[0] for c in CUT_COLORS]
        if self.theme in names:
            # THEME level: 3 ta tar. MAIN LINE (theme rong) shobar SHESH e katte hobe, baki duto age (jekono order)
            ti = names.index(self.theme)
            others = self.rng.sample([i for i in range(len(CUT_COLORS)) if i != ti], 2)
            self.cols = [ti] + others
            self.rng.shuffle(self.cols)                                  # upor theke niche tar
            main = self.cols.index(ti)
            rest = [i for i in range(3) if i != main]
            self.rng.shuffle(rest)
            self.order = rest + [main]
        else:
            n = self.rng.choice((3, 4))
            self.cols = self.rng.sample(range(len(CUT_COLORS)), n)      # upor theke niche tar
            self.order = self.rng.sample(range(n), n)                    # kon tar kon number e kata
        n = len(self.cols)
        self.cut = [False] * n
        self.step = 0
        self.msg = "Cut the wires in the order shown on the note"

    BOX = pygame.Rect(WIDTH // 2 - 300, 130, 300, 260)

    def wire_rect(self, i):
        n = len(self.cols)
        b = self.BOX
        step = (b.h - 90) / max(1, n - 1)
        return pygame.Rect(b.x + 20, int(b.y + 50 + i * step), b.w - 40, 22)

    def press(self, i):
        if self.ok or self.err > 0 or self.cut[i]:
            return
        want = self.order[self.step]
        if i == want:
            self.cut[i] = True
            self.step += 1
            r = self.wire_rect(i)
            for _ in range(22):
                self.sparks.append([r.centerx, r.centery, random.uniform(-190, 190), random.uniform(-230, 60),
                                    random.uniform(0.3, 0.7)])
            sound.play("zap", 0.7)
            if self.step >= len(self.cols):
                self.ok = True
                self.msg = "ALL WIRES CUT  -  ACCESS GRANTED"
                sound.play("unlock")
                if self.done_fn:
                    self.done_fn()
            else:
                self.msg = f"{self.step}/{len(self.cols)} cut"
        else:
            self.err = 0.9
            self.wrong += 1
            self.msg = "WRONG WIRE  -  short circuit!"
            sound.play("lock")

    def event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 1) == 1:
            pos = getattr(e, "pos", (0, 0))
            for i in range(len(self.cols)):
                if self.wire_rect(i).inflate(0, 22).collidepoint(pos):
                    self.press(i)
                    break
        elif e.type == pygame.KEYDOWN and pygame.K_1 <= e.key <= pygame.K_5:
            i = e.key - pygame.K_1
            if i < len(self.cols):
                self.press(i)

    def update(self, dt):
        self.t += dt
        if self.err > 0:
            self.err = max(0.0, self.err - dt)
            if self.err == 0.0:
                self.reset()
        if self.ok:
            self.ok_t += dt
        for s in self.sparks:
            s[0] += s[2] * dt
            s[1] += s[3] * dt
            s[3] += 520 * dt
            s[4] -= dt
        self.sparks = [s for s in self.sparks if s[4] > 0]

    def draw(self, surf, mouse=None):
        mouse = mouse or pygame.mouse.get_pos()
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 190))
        surf.blit(dim, (0, 0))
        panel = pygame.Rect(WIDTH // 2 - 330, 40, 660, 460)
        edge = (230, 70, 70) if self.err > 0 else ((60, 220, 120) if self.ok else (110, 116, 140))
        pygame.draw.rect(surf, (28, 30, 40), panel, border_radius=20)
        pygame.draw.rect(surf, edge, panel, 4, border_radius=20)
        if self.theme in [c[0] for c in CUT_COLORS]:
            tcol = dict(CUT_COLORS)[self.theme]
            pygame.draw.rect(surf, tcol, panel.inflate(-8, -8), 3, border_radius=16)
        h = get_font(22).render("WIRE CUTTER" + (f"  -  {self.theme} WIRE" if self.theme else ""), True, GOLD)
        surf.blit(h, h.get_rect(center=(panel.centerx, panel.y + 30)))
        sub = get_font(13, bold=False).render(self.title, True, (190, 196, 215))
        surf.blit(sub, sub.get_rect(center=(panel.centerx, panel.y + 56)))
        # note (kon order e katbe)
        note = pygame.Rect(panel.right - 190, panel.y + 90, 170, 250)
        pygame.draw.rect(surf, (244, 238, 214), note, border_radius=6)
        pygame.draw.rect(surf, (150, 130, 90), note, 3, border_radius=6)
        t = get_font(14).render("CUT ORDER", True, (110, 40, 40))
        surf.blit(t, t.get_rect(center=(note.centerx, note.y + 20)))
        for s, idx in enumerate(self.order):
            nm, col = CUT_COLORS[self.cols[idx]]
            y = note.y + 48 + s * 46
            done = s < self.step
            pygame.draw.circle(surf, col, (note.x + 30, y), 13)
            pygame.draw.circle(surf, (60, 50, 30), (note.x + 30, y), 13, 2)
            lab = get_font(18).render(f"{s + 1}. {nm}", True, (90, 150, 90) if done else (90, 80, 60))
            surf.blit(lab, (note.x + 54, y - 10))
            if done:
                pygame.draw.line(surf, (60, 160, 90), (note.x + 54, y), (note.right - 12, y), 3)
        # wire box
        box = self.BOX
        pygame.draw.rect(surf, (46, 52, 70), box, border_radius=10)
        pygame.draw.rect(surf, (96, 104, 130), box, 3, border_radius=10)
        shake = int(math.sin(self.t * 70) * 5) if self.err > 0 else 0
        n = len(self.cols)
        for i in range(n):
            r = self.wire_rect(i)
            r.x += shake
            nm, col = CUT_COLORS[self.cols[i]]
            hov = r.inflate(0, 22).collidepoint(mouse) and not self.cut[i]
            if self.cut[i]:
                gap = 30
                pygame.draw.rect(surf, col, (r.x, r.y, r.w // 2 - gap // 2, r.h), border_radius=8)
                pygame.draw.rect(surf, col, (r.centerx + gap // 2, r.y, r.w // 2 - gap // 2, r.h), border_radius=8)
                pygame.draw.circle(surf, (255, 230, 120), (r.centerx - gap // 2, r.centery), 5)
                pygame.draw.circle(surf, (255, 230, 120), (r.centerx + gap // 2, r.centery), 5)
            else:
                pygame.draw.rect(surf, (0, 0, 0), r.inflate(6, 6), border_radius=10)
                pygame.draw.rect(surf, col, r, border_radius=8)
                pygame.draw.rect(surf, tuple(min(255, v + 90) for v in col), (r.x + 6, r.y + 4, r.w - 12, 5), border_radius=3)
                if hov:
                    pygame.draw.rect(surf, WHITE, r.inflate(10, 10), 3, border_radius=12)
                    SP.draw_tool_icon(surf, "cutter", (r.centerx, r.centery - 30), 18, self.t)
            lab = get_font(14).render(f"[{i + 1}] {nm}", True, col)
            surf.blit(lab, (r.x - 2, r.y - 22))
        for s in self.sparks:
            pygame.draw.circle(surf, (255, 225, 110), (int(s[0]), int(s[1])), max(1, int(4 * s[4] + 1)))
        mc = (90, 255, 150) if self.ok else ((240, 90, 90) if self.err > 0 else (170, 180, 205))
        m = get_font(16).render(self.msg, True, mc)
        surf.blit(m, m.get_rect(center=(panel.centerx, panel.bottom - 70)))
        k = get_font(13, bold=False).render(
            ("MAIN LINE = " + self.theme + " wire: cut it LAST.   " if self.theme else "") +
            "Click a wire (or press its number).  ESC = close", True, (130, 136, 160))
        surf.blit(k, k.get_rect(center=(panel.centerx, panel.bottom - 28)))


# ------------------------------------------------------------------
# TUTORIAL
# ------------------------------------------------------------------
# (key-caps, text)  -  keyboard
KB_PAGES = [
    ("MOVE & FIGHT", [
        (["A", "D"], "Move left / right   (or arrow keys)"),
        (["W"], "Jump   (or UP / SPACE)"),
        (["J"], "Throw knife"),
        (["K"], "Super punch"),
        (["H"], "Hide  (hold)  - guards cannot see you"),
    ]),
    ("TOOLS & LAPTOP", [
        (["1", "..", "0"], "Select a tool   (0 = WIRE CUTTER)"),
        (["TAB"], "Open the TOOL WHEEL  (Ctrl+Alt or mouse wheel too)"),
        (["E"], "Use the selected tool near a target"),
        (["L"], "Open the LAPTOP at a terminal - WIRE CONNECT or Python"),
        (["ESC"], "Pause   -   you can open this tutorial there"),
    ]),
    ("SPECIAL & WIRE CUTTER", [
        (["T"], "Ninja star   (buy in SPECIAL TOOLS)"),
        (["C"], "AUTO CODE WRITER on / off  - types codes for you"),
        (["Q"], "Electric  - freezes guards"),
        (["0"], "WIRE CUTTER - Level 3, 4, 5, 6, 8, 9 terminals: cut the wires in order"),
        (["CLICK"], "Laptop & wire boxes work with the mouse"),
    ]),
]
PAD_PAGES = [
    ("MOVE & FIGHT", [
        (["L-STICK"], "Move   (D-pad too)"),
        (["RB"], "Jump"),
        (["X"], "Throw knife"),
        (["Y"], "Super punch"),
        (["B"], "Hide  (hold)"),
    ]),
    ("TOOLS & LAPTOP", [
        (["BACK"], "TOOL WHEEL  (stick = move, A = pick)"),
        (["LB"], "Use the selected tool"),
        (["L3"], "Open the LAPTOP at a terminal"),
        (["START"], "Pause   -   open this tutorial there"),
        (["A"], "Select in menus"),
    ]),
    ("SPECIAL & WIRE CUTTER", [
        (["A"], "Ninja star   (if you bought it)"),
        (["R3"], "AUTO CODE WRITER on / off"),
        (["LT"], "Electric"),
        (["LB"], "WIRE CUTTER at terminals in Level 3, 4, 5, 6, 8, 9"),
        (["STICK"], "Move the mouse-cursor-like pointer in menus"),
    ]),
]


class Tutorial:
    """open(mode) -> active.  event(e) / update(dt) / draw(surf)."""

    def __init__(self):
        self.active = False
        self.mode = "keyboard"
        self.page = 0
        self.t = 0.0
        self.tabs = {}
        self.btn = {}

    def open(self, mode="keyboard"):
        self.active = True
        self.mode = mode if mode in ("keyboard", "controller") else "keyboard"
        self.page = 0
        self.t = 0.0
        sound.play("pop")

    def pages(self):
        return PAD_PAGES if self.mode == "controller" else KB_PAGES

    def close(self):
        self.active = False
        sound.play("back")

    def next(self):
        if self.page >= len(self.pages()) - 1:
            self.close()
        else:
            self.page += 1
            self.t = 0.0
            sound.play("click")

    def prev(self):
        if self.page > 0:
            self.page -= 1
            self.t = 0.0
            sound.play("hover")

    def event(self, e):
        if not self.active:
            return False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.close()
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHT, pygame.K_d, pygame.K_KP_ENTER):
                self.next()
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self.prev()
            elif e.key in (pygame.K_TAB, pygame.K_c):
                self.mode = "controller" if self.mode == "keyboard" else "keyboard"
                sound.play("hover")
        elif e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 1) == 1:
            pos = getattr(e, "pos", (0, 0))
            for name, r in self.tabs.items():
                if r.collidepoint(pos):
                    self.mode = name
                    sound.play("click")
                    return True
            for name, r in self.btn.items():
                if r.collidepoint(pos):
                    {"next": self.next, "back": self.prev, "skip": self.close}[name]()
                    return True
        return True

    def update(self, dt):
        self.t += dt

    def _cap(self, surf, label, x, y, t, wide=None):
        f = get_font(18 if len(label) < 4 else 14)
        img = f.render(label, True, (240, 244, 255))
        w = wide or max(44, img.get_width() + 22)
        r = pygame.Rect(x, y, w, 44)
        press = max(0.0, math.sin(t * 3.2 + x * 0.02)) ** 8
        r2 = r.move(0, int(4 * press))
        pygame.draw.rect(surf, (12, 14, 24), r.move(0, 5), border_radius=10)
        if self.mode == "controller":
            pygame.draw.rect(surf, (40, 44, 70), r2, border_radius=22)
            pygame.draw.rect(surf, rgb_color(t, offset=x * 0.002), r2, 3, border_radius=22)
        else:
            pygame.draw.rect(surf, (52, 56, 84), r2, border_radius=10)
            pygame.draw.rect(surf, rgb_color(t, offset=x * 0.002), r2, 3, border_radius=10)
        surf.blit(img, img.get_rect(center=r2.center))
        return w

    def draw(self, surf):
        if not self.active:
            return
        t = self.t
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((4, 6, 16, 235))
        surf.blit(dim, (0, 0))
        ent = ease_out_cubic(t / 0.4)
        title = get_font(40).render("HOW TO PLAY", True, WHITE)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 40 - int((1 - ent) * 30))))
        # tabs
        self.tabs = {}
        for i, (name, lab) in enumerate((("keyboard", "KEYBOARD"), ("controller", "CONTROLLER"))):
            r = pygame.Rect(0, 0, 190, 40)
            r.center = (WIDTH // 2 - 100 + i * 200, 90)
            on = self.mode == name
            pygame.draw.rect(surf, rgb_color(t, offset=i * 0.3) if on else (34, 36, 58), r, border_radius=12)
            pygame.draw.rect(surf, WHITE if on else (95, 95, 125), r, 3, border_radius=12)
            img = get_font(20).render(lab, True, (15, 15, 25) if on else WHITE)
            surf.blit(img, img.get_rect(center=r.center))
            self.tabs[name] = r
        name, rows = self.pages()[self.page]
        ph = get_font(28).render(f"{self.page + 1}/{len(self.pages())}   {name}", True, GOLD)
        surf.blit(ph, ph.get_rect(center=(WIDTH // 2, 144)))
        y0 = 172
        for i, (caps, text) in enumerate(rows):
            k = ease_out_cubic((t - 0.15 - i * 0.09) / 0.35)
            if k <= 0:
                continue
            y = y0 + i * 54
            row = pygame.Surface((WIDTH, 56), pygame.SRCALPHA)
            x = 120
            for c in caps:
                if c == "..":
                    d = get_font(22).render("..", True, (150, 156, 180))
                    row.blit(d, (x, 8))
                    x += 36
                else:
                    x += self._cap(row, c, x, 4, t) + 8
            tx = max(x + 18, 330)
            img = get_font(19).render(text, True, (215, 220, 240))
            row.blit(img, (tx, 12))
            row.set_alpha(int(255 * k))
            surf.blit(row, (int((1 - k) * 60), y))
        # button
        self.btn = {}
        last = self.page >= len(self.pages()) - 1
        for name_, lab, cx in (("back", "BACK", WIDTH // 2 - 220), ("skip", "SKIP", WIDTH // 2),
                               ("next", "DONE" if last else "NEXT", WIDTH // 2 + 220)):
            r = pygame.Rect(0, 0, 170, 44)
            r.center = (cx, HEIGHT - 44)
            if name_ == "back" and self.page == 0:
                continue
            hot = r.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(surf, rgb_color(t, offset=cx * 0.002) if hot or name_ == "next" else (34, 34, 58), r, border_radius=14)
            pygame.draw.rect(surf, WHITE if hot else (95, 95, 125), r, 3, border_radius=14)
            img = get_font(22).render(lab, True, (15, 15, 25) if hot or name_ == "next" else WHITE)
            surf.blit(img, img.get_rect(center=r.center))
            self.btn[name_] = r
        h = get_font(14, bold=False).render("TAB = switch keyboard / controller      ENTER = next      ESC = close",
                                            True, (140, 146, 170))
        surf.blit(h, h.get_rect(center=(WIDTH // 2, HEIGHT - 84)))
