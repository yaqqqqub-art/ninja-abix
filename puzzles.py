"""
puzzles.py - Abix Ninja er notun puzzle gulo.

  WireGame   - "Wire Connecting": 3-4 ta tar thik port / node e jukto korte hobe.
               Laptop er WIRE CONNECT app e khelte hoy. Sob tar thik hole terminal UNLOCK.
  Keypad     - CODE LOCK er number pad (door e E chaple khole).
  PageSpot   - level e porte thaka "PAGE" (kagoj). Nile code ta collect hoye jay.
               Collect kora code gulo Keypad er bam pashe ar laptop er Documents/pages.txt e dekha jay.
  code_for   - ekta key theke sobsomoy ek-i 4 digit code banay (page ar door er code mile jay).

MASTER KEYCARD ar CODE LOCK e kaj kore na - shudhu code type korte hobe.
"""
import math
import random

import pygame

import sound
from animation import WIDTH, HEIGHT, WHITE, GOLD, get_font


def code_for(key):
    """Protita key er jonno ekta fixed 4-digit code (restart korleo ek-i thake)."""
    return str(random.Random("abix-code-" + str(key)).randint(1000, 9999))


# ------------------------------------------------------------------
# Wire Connecting
# ------------------------------------------------------------------
WIRE_COLORS = [("RED", (235, 70, 70)), ("BLUE", (70, 140, 250)), ("GREEN", (80, 200, 110)),
               ("YELLOW", (245, 200, 60)), ("PURPLE", (190, 100, 240))]


class WireGame:
    """Logic only (drawing laptop.py te). Bam pashe tar er mukh (source), dan pashe port (node)."""

    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.reset()

    def reset(self, count=None):
        n = count or self.rng.choice((3, 4))
        self.cols = self.rng.sample(range(len(WIRE_COLORS)), n)      # bam pasher rong (upor theke niche)
        right = self.cols[:]
        self.rng.shuffle(right)
        if right == self.cols and n > 1:                              # kokhono shuru theke thik thakbe na
            right = right[1:] + right[:1]
        self.right = right                                            # dan pasher port er rong
        self.link = {}                                                # bam i -> dan j  (thik connect hoyeche)
        self.sel = None                                               # ekhon dhora tar (bam index)
        self.cursor = (0, 0)
        self.shake = 0.0
        self.flash = 0.0
        self.msg = "Connect every wire to the port of the SAME color"
        self.solved = False
        self.solved_t = 0.0
        self.tries = 0

    @property
    def n(self):
        return len(self.cols)

    def color(self, color_idx):
        return WIRE_COLORS[color_idx][1]

    def name(self, color_idx):
        return WIRE_COLORS[color_idx][0]

    def connect(self, i, j):
        """bam i ke dan j te jukto koro. Return: 'ok' | 'wrong' | 'used' | 'done'."""
        if self.solved:
            return "done"
        if i in self.link or j in self.link.values():
            return "used"
        if self.cols[i] == self.right[j]:
            self.link[i] = j
            self.sel = None
            self.flash = 0.35
            if len(self.link) == self.n:
                self.solved = True
                self.msg = "ALL WIRES CONNECTED  -  ACCESS GRANTED"
            else:
                self.msg = f"{len(self.link)}/{self.n} connected"
            return "ok"
        self.tries += 1
        self.sel = None
        self.shake = 0.4
        self.msg = "WRONG PORT  -  short circuit! try again"
        return "wrong"

    def update(self, dt):
        self.shake = max(0.0, self.shake - dt)
        self.flash = max(0.0, self.flash - dt)
        if self.solved:
            self.solved_t += dt


# ------------------------------------------------------------------
# Code lock keypad (modal)
# ------------------------------------------------------------------
class Keypad:
    KEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "C", "0", "<"]
    KW, KH, GAP = 76, 54, 10
    GRID_Y = 215

    def __init__(self, title, code, pages, done_fn=None):
        self.title = title
        self.code = code
        self.pages = pages                    # world.pages : {key: (label, code)}
        self.done_fn = done_fn
        self.entered = ""
        self.err = 0.0
        self.ok = False
        self.ok_t = 0.0
        self.wrong = 0
        self.rects = {}
        gx = WIDTH // 2 - (3 * self.KW + 2 * self.GAP) // 2
        for i, k in enumerate(self.KEYS):
            c, r = i % 3, i // 3
            self.rects[k] = pygame.Rect(gx + c * (self.KW + self.GAP), self.GRID_Y + r * (self.KH + self.GAP),
                                        self.KW, self.KH)

    def press(self, k):
        if self.ok or self.err > 0:
            return
        if k == "C":
            self.entered = ""
            sound.play("hover", 0.5)
        elif k == "<":
            self.entered = self.entered[:-1]
            sound.play("hover", 0.5)
        elif k.isdigit() and len(self.entered) < len(self.code):
            self.entered += k
            sound.play("key", 0.6)
            if len(self.entered) == len(self.code):
                self._check()

    def _check(self):
        if self.entered == self.code:
            self.ok = True
            sound.play("unlock")
            if self.done_fn:
                self.done_fn()
        else:
            self.err = 0.7
            self.wrong += 1
            sound.play("lock")

    def event(self, e):
        if e.type == pygame.KEYDOWN:
            ch = getattr(e, "unicode", "")
            if ch and ch.isdigit():
                self.press(ch)
            elif e.key == pygame.K_BACKSPACE:
                self.press("<")
        elif e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 1) == 1:
            pos = getattr(e, "pos", (0, 0))
            for k, r in self.rects.items():
                if r.collidepoint(pos):
                    self.press(k)
                    break

    def update(self, dt):
        if self.err > 0:
            self.err = max(0.0, self.err - dt)
            if self.err == 0.0:
                self.entered = ""
        if self.ok:
            self.ok_t += dt

    def draw(self, surf, mouse=None):
        mouse = mouse or pygame.mouse.get_pos()
        ticks = pygame.time.get_ticks() / 1000.0
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 190))
        surf.blit(dim, (0, 0))
        # ---- keypad panel ----
        panel = pygame.Rect(WIDTH // 2 - 175, 40, 350, 460)
        pygame.draw.rect(surf, (28, 30, 40), panel, border_radius=20)
        pygame.draw.rect(surf, (200, 70, 70) if self.err > 0 else ((60, 220, 120) if self.ok else (110, 116, 140)),
                         panel, 4, border_radius=20)
        t = get_font(20).render("CODE LOCK", True, GOLD)
        surf.blit(t, t.get_rect(center=(panel.centerx, panel.y + 30)))
        sub = get_font(13, bold=False).render(self.title, True, (190, 196, 215))
        surf.blit(sub, sub.get_rect(center=(panel.centerx, panel.y + 56)))
        # code slots
        n = len(self.code)
        sw, gap = 52, 10
        x0 = panel.centerx - (n * sw + (n - 1) * gap) // 2
        shake = int(math.sin(ticks * 60) * 6) if self.err > 0 else 0
        for i in range(n):
            r = pygame.Rect(x0 + i * (sw + gap) + shake, panel.y + 86, sw, 66)
            pygame.draw.rect(surf, (10, 14, 20), r, border_radius=8)
            col = (230, 70, 70) if self.err > 0 else ((90, 255, 150) if self.ok else (90, 150, 220))
            pygame.draw.rect(surf, col, r, 2, border_radius=8)
            if i < len(self.entered):
                d = get_font(36).render(self.entered[i], True, col)
                surf.blit(d, d.get_rect(center=r.center))
            elif i == len(self.entered) and not self.ok and int(ticks * 2) % 2 == 0:
                pygame.draw.rect(surf, (200, 210, 230), (r.centerx - 8, r.bottom - 14, 16, 3))
        # status line
        if self.ok:
            msg, mc = "ACCESS GRANTED", (90, 255, 150)
        elif self.err > 0:
            msg, mc = "WRONG CODE", (240, 90, 90)
        else:
            msg, mc = "Type the code (keyboard or click)", (150, 156, 180)
        m = get_font(15).render(msg, True, mc)
        surf.blit(m, m.get_rect(center=(panel.centerx, panel.y + 176)))
        # keys
        for k, r in self.rects.items():
            hov = r.collidepoint(mouse)
            base = (60, 66, 90) if hov else (44, 48, 68)
            pygame.draw.rect(surf, base, r, border_radius=10)
            pygame.draw.rect(surf, (110, 118, 150), r, 2, border_radius=10)
            lab = {"C": "CLR", "<": "DEL"}.get(k, k)
            li = get_font(22 if k.isdigit() else 16).render(lab, True, WHITE)
            surf.blit(li, li.get_rect(center=r.center))
        h = get_font(13, bold=False).render("ESC = close", True, (130, 136, 160))
        surf.blit(h, h.get_rect(center=(panel.centerx, panel.bottom - 16)))
        # ---- collected pages ----
        sheet = pygame.Rect(30, 110, 250, 300)
        pygame.draw.rect(surf, (244, 238, 214), sheet, border_radius=6)
        pygame.draw.rect(surf, (150, 130, 90), sheet, 3, border_radius=6)
        head = get_font(16).render("COLLECTED PAGES", True, (110, 40, 40))
        surf.blit(head, head.get_rect(center=(sheet.centerx, sheet.y + 24)))
        pygame.draw.line(surf, (190, 170, 130), (sheet.x + 14, sheet.y + 44), (sheet.right - 14, sheet.y + 44), 2)
        y = sheet.y + 58
        if not self.pages:
            for ln in ("No page yet.", "", "Search the level for a", "PAGE (white paper).", "It has the code."):
                s = get_font(14, bold=False).render(ln, True, (90, 80, 60))
                surf.blit(s, (sheet.x + 18, y))
                y += 22
        else:
            for label, code in list(self.pages.values())[:4]:
                s = get_font(12, bold=False).render(label, True, (90, 80, 60))
                surf.blit(s, (sheet.x + 18, y))
                c = get_font(30).render(code, True, (170, 30, 40))
                surf.blit(c, (sheet.x + 18, y + 18))
                y += 68


# ------------------------------------------------------------------
# PAGE (kagoj) - level e kuriye nite hoy
# ------------------------------------------------------------------
def draw_page_icon(surf, c, t, scale=1.0):
    x, y = c
    y += math.sin(t * 3) * 3
    for r, a in ((34, 40), (24, 70)):
        g = pygame.Surface((int(r * 2 * scale) + 4, int(r * 2 * scale) + 4), pygame.SRCALPHA)
        pygame.draw.circle(g, (255, 235, 150, a), g.get_rect().center, int(r * scale))
        surf.blit(g, g.get_rect(center=(int(x), int(y))))
    w, h = int(26 * scale), int(34 * scale)
    pts = [(x - w / 2, y - h / 2), (x + w / 2 - 6 * scale, y - h / 2), (x + w / 2, y - h / 2 + 6 * scale),
           (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)]
    pygame.draw.polygon(surf, (248, 244, 224), pts)
    pygame.draw.polygon(surf, (140, 120, 80), pts, 2)
    for i in range(3):
        yy = y - h / 2 + (12 + i * 7) * scale
        pygame.draw.line(surf, (150, 140, 110), (x - w / 2 + 4 * scale, yy), (x + w / 2 - 5 * scale, yy), 2)
    pygame.draw.circle(surf, (220, 60, 60), (int(x + w / 2 - 6 * scale), int(y + h / 2 - 6 * scale)), max(2, int(4 * scale)))


class PageSpot:
    """Ekta page. Kache gele nijei nao hoy. Code w.pages e jomay."""

    def __init__(self, x, key, label, y):
        self.x, self.key, self.label, self.y = x, key, label, y
        self.taken = False

    def update(self, w):
        p = w.p
        if self.taken or not p.alive:
            return
        if abs(p.x - self.x) < 55 and abs((p.y - 30) - self.y) < 110:
            self.taken = True
            code = code_for(self.key)
            w.pages[self.key] = (self.label, code)
            sound.play("star")
            sound.play("pop", 0.6)
            w.burst(self.x, self.y, (255, 235, 150), 22, 220, 0.8, grav=120)
            w.say(f"PAGE FOUND  -  {self.label}:  {code}")

    def draw(self, w, surf, cam, t):
        if self.taken:
            return
        x = self.x - cam
        if not (-60 < x < WIDTH + 60):
            return
        draw_page_icon(surf, (x, self.y), t)
        f = get_font(12).render("PAGE", True, (255, 240, 180))
        surf.blit(f, f.get_rect(midtop=(x, self.y + 26)))
