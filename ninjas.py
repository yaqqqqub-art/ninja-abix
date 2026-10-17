"""
ninjas.py - 30 ta NINJA SKIN + NINJAS shop screen.

  #1  ABIX (classic)  = FREE
  #2                  = 300 diamond
  #3 theke            = 350, 400, 450 ... (economy.py te NINJA_FIRST_PRICE / NINJA_STEP bodlaleই dam bodlay)

Main menu te "NINJAS (N)" button.  Kena ninja select korle shob level e oi ninja dekha jabe.
"""
import pygame

import economy as EC
import sound
import sprites as SP
from animation import WIDTH, HEIGHT, WHITE, GOLD, get_font, rgb_color
from menus import _txt, draw_wallet, draw_diamond


def _mix(c, k):
    """k < 1 = aro dark, k > 1 = aro halka."""
    if k <= 1:
        return tuple(max(0, int(v * k)) for v in c)
    return tuple(min(255, int(v + (255 - v) * (k - 1))) for v in c)


def _skin(name, body, accent, deco=None, aura=None, cape=None, face=None, head=None):
    return {
        "name": name,
        "pal": {
            "body": body, "body2": _mix(body, 1.35), "dark": _mix(body, 0.65),
            "head": head or _mix(body, 0.8), "face": face or (238, 200, 160),
            "accent": accent, "bag": _mix(body, 1.25), "bag2": _mix(body, 1.6),
            "aura": aura, "deco": deco, "cape": cape,
        },
    }


SKINS = [
    {"name": "ABIX", "pal": None},                                                       # 1  FREE (classic)
    _skin("BLOOD MOON", (110, 20, 30), (255, 215, 215)),                                  # 2  300
    _skin("ICE NINJA", (60, 130, 190), (230, 250, 255), aura=(140, 220, 255)),            # 3
    _skin("FOREST GHOST", (30, 90, 50), (190, 255, 120)),                                 # 4
    _skin("GOLDEN DRAGON", (150, 110, 20), (255, 230, 120), deco="crown"),                # 5
    _skin("SHADOW CAT", (40, 40, 48), (255, 130, 200), deco="cat"),                       # 6
    _skin("THUNDER", (70, 60, 150), (255, 235, 80), aura=(255, 235, 90)),                 # 7
    _skin("SAKURA", (230, 140, 170), (255, 255, 255)),                                    # 8
    _skin("SAMURAI", (60, 60, 70), (230, 60, 50), deco="samurai"),                        # 9
    _skin("DESERT WIND", (170, 130, 70), (90, 60, 30), deco="hat"),                       # 10
    _skin("TOXIC", (60, 130, 30), (230, 255, 60), aura=(160, 255, 60)),                   # 11
    _skin("MIDNIGHT", (20, 30, 90), (120, 170, 255), cape=(30, 45, 120)),                 # 12
    _skin("ONI", (150, 40, 40), (255, 255, 255), deco="horns"),                           # 13
    _skin("SNOW BUNNY", (235, 235, 245), (255, 150, 180), deco="bunny"),                  # 14
    _skin("LAVA", (60, 20, 10), (255, 120, 20), deco="flame", aura=(255, 110, 20)),       # 15
    _skin("ROYAL PURPLE", (90, 40, 140), (255, 215, 90), deco="crown", cape=(120, 50, 170)),  # 16
    _skin("EMERALD", (20, 110, 90), (150, 255, 220), aura=(90, 255, 200)),                # 17
    _skin("ROSE GOLD", (180, 100, 100), (255, 230, 200)),                                 # 18
    _skin("GHOST", (210, 215, 230), (120, 130, 160), aura=(230, 240, 255)),               # 19
    _skin("SPIKE PUNK", (30, 30, 30), (255, 60, 200), deco="spike"),                      # 20
    _skin("SUN WARRIOR", (210, 120, 20), (255, 240, 150), deco="spike", aura=(255, 200, 60)),  # 21
    _skin("OCEAN", (20, 90, 140), (255, 255, 255), cape=(30, 120, 180)),                  # 22
    _skin("ANGEL", (240, 240, 250), (255, 215, 90), deco="halo", aura=(255, 245, 190)),   # 23
    _skin("CYBER", (15, 25, 35), (0, 255, 220), aura=(0, 255, 220)),                      # 24
    _skin("VAMPIRE", (25, 10, 20), (200, 20, 50), cape=(140, 10, 30)),                    # 25
    _skin("CANDY", (255, 150, 200), (120, 230, 255), deco="cat"),                         # 26
    _skin("TITAN STEEL", (110, 115, 130), (255, 200, 70), deco="samurai"),                # 27
    _skin("PHANTOM FLAME", (30, 10, 60), (200, 80, 255), deco="flame", aura=(190, 80, 255), cape=(70, 20, 120)),  # 28
    _skin("RAINBOW", (40, 40, 60), "rainbow", deco="halo", aura="rainbow"),               # 29
    _skin("ABIX KING", (30, 24, 10), (255, 200, 60), deco="crown", aura=(255, 210, 80), cape=(190, 25, 40)),  # 30
]
assert len(SKINS) == EC.NINJA_COUNT


def pal_of(i):
    return SKINS[i]["pal"]


def apply(save):
    """Select kora ninja ke game e lagao (level, preview shob jaygay)."""
    SP.set_skin(pal_of(save["ninja"]["sel"]))


_mini_cache = {}


def render(i, anim="idle", t=0.0):
    """Ekta ninja er chhobi (130x110 surface)."""
    surf = pygame.Surface((SP.TW, SP.TH), pygame.SRCALPHA)
    SP.draw_ninja(surf, SP.OX, SP.OY, 1, t, anim, 0.0, 255, pal=pal_of(i) or SP.DEFAULT_PAL)
    return surf


def mini(i):
    if i not in _mini_cache:
        _mini_cache[i] = pygame.transform.smoothscale(render(i, "idle", 0.0), (91, 77))
    return _mini_cache[i]


class NinjaScreen:
    COLS, ROWS, CARD, GAP = 6, 5, 70, 8

    def __init__(self):
        self.x0, self.y0 = 24, 92
        self.cards = [pygame.Rect(self.x0 + (i % self.COLS) * (self.CARD + self.GAP),
                                  self.y0 + (i // self.COLS) * (self.CARD + self.GAP), self.CARD, self.CARD)
                      for i in range(EC.NINJA_COUNT)]
        self.panel = pygame.Rect(516, 92, 420, 396)
        self.btn = pygame.Rect(540, 424, 372, 52)
        self.sel = 0
        self.anim_i = 0
        self.toast = ("", 0.0, True)
        self.dirty = False
        self.t = 0.0
        self.save = None

    def open(self, save):
        self.save = save
        self.sel = save["ninja"]["sel"]
        self.toast = ("", 0.0, True)

    def say(self, text, ok=True):
        self.toast = (text, 2.0, ok)

    def action(self):
        """Button: kena na thakle KINO, kena thakle SELECT."""
        sv, i = self.save, self.sel
        if i in sv["ninja"]["owned"]:
            EC.select_ninja(sv, i)
            apply(sv)
            sound.play("unlock", 0.7)
            self.say(SKINS[i]["name"] + "  EQUIPPED")
            self.dirty = True
            return
        res = EC.buy_ninja(sv, i)
        if res == "ok":
            EC.select_ninja(sv, i)
            apply(sv)
            sound.play("unlock")
            self.say("BOUGHT!  " + SKINS[i]["name"])
            self.dirty = True
        else:
            sound.play("lock")
            self.say("Not enough diamonds", False)

    def event(self, e):
        if e.type == pygame.KEYDOWN:
            r, c = divmod(self.sel, self.COLS)
            if e.key == pygame.K_LEFT:
                c = (c - 1) % self.COLS
            elif e.key == pygame.K_RIGHT:
                c = (c + 1) % self.COLS
            elif e.key == pygame.K_UP:
                r = (r - 1) % self.ROWS
            elif e.key == pygame.K_DOWN:
                r = (r + 1) % self.ROWS
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.action()
                return
            elif e.key == pygame.K_TAB:
                self.anim_i = (self.anim_i + 1) % 3
            if r * self.COLS + c != self.sel:
                sound.play("hover", 0.5)
            self.sel = r * self.COLS + c
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            pos = e.pos
            for i, rc in enumerate(self.cards):
                if rc.collidepoint(pos):
                    self.sel = i
                    sound.play("click")
                    return
            if self.btn.collidepoint(pos):
                self.action()
            elif self.panel.collidepoint(pos):
                self.anim_i = (self.anim_i + 1) % 3

    def update(self, dt):
        self.t += dt
        if self.toast[1] > 0:
            self.toast = (self.toast[0], self.toast[1] - dt, self.toast[2])

    def draw(self, surf, mouse):
        t, sv = self.t, self.save
        owned = sv["ninja"]["owned"]
        equipped = sv["ninja"]["sel"]
        _txt(surf, "NINJAS", (24, 26), 36, WHITE, True)
        _txt(surf, "%d / %d" % (len(owned), EC.NINJA_COUNT), (200, 38), 20, (170, 175, 200), True)
        draw_wallet(surf, sv, 44, WIDTH - 24, t)
        # ---- grid ----
        for i, rc in enumerate(self.cards):
            have = i in owned
            focus = (i == self.sel)
            pygame.draw.rect(surf, (28, 30, 50), rc, border_radius=12)
            if i == equipped:
                col, w = (110, 240, 150), 4
            elif focus:
                col, w = rgb_color(t, offset=i * 0.05), 4
            else:
                col, w = ((90, 200, 130) if have else (80, 84, 112)), 2
            pygame.draw.rect(surf, col, rc, w, border_radius=12)
            img = mini(i)
            if not have:
                img = img.copy()
                img.fill((70, 70, 90, 255), special_flags=pygame.BLEND_RGBA_MULT)
            surf.blit(img, img.get_rect(center=(rc.centerx, rc.centery + 2)))
            _txt(surf, str(i + 1), (rc.x + 6, rc.y + 3), 11, (150, 154, 180), True)
            if not have:
                _txt(surf, str(EC.ninja_price(i)), (rc.right - 6, rc.bottom - 14), 11, (150, 235, 255), True, right=True)
        # ---- detail ----
        pygame.draw.rect(surf, (20, 22, 38), self.panel, border_radius=16)
        pygame.draw.rect(surf, (90, 96, 130), self.panel, 3, border_radius=16)
        i = self.sel
        have = i in owned
        anim = ("idle", "run", "wave")[self.anim_i]
        big = pygame.transform.scale(render(i, anim, t), (SP.TW * 2, SP.TH * 2))
        surf.blit(big, big.get_rect(center=(self.panel.centerx, self.panel.y + 140)))
        _txt(surf, "#%d  %s" % (i + 1, SKINS[i]["name"]), (self.panel.centerx, self.panel.y + 266), 28, GOLD, True, center=True)
        if have:
            _txt(surf, "EQUIPPED" if i == equipped else "OWNED", (self.panel.centerx, self.panel.y + 302), 20,
                 (110, 240, 150), True, center=True)
        elif i == 0:
            _txt(surf, "FREE", (self.panel.centerx, self.panel.y + 302), 22, (110, 240, 150), True, center=True)
        else:
            price = EC.ninja_price(i)
            r = _txt(surf, str(price), (self.panel.centerx - 4, self.panel.y + 302), 24, (235, 240, 255), True, center=True)
            draw_diamond(surf, (r.right + 20, r.centery), 12)
        # ---- button ----
        if have:
            label, bg, ln = ("EQUIPPED" if i == equipped else "SELECT"), (36, 90, 60), (110, 240, 150)
        else:
            price = EC.ninja_price(i)
            can = sv["diamonds"] >= price
            label, bg, ln = "BUY  %d" % price, ((36, 90, 60) if can else (60, 40, 50)), ((255, 230, 120) if can else (150, 90, 90))
        hov = self.btn.collidepoint(mouse)
        pygame.draw.rect(surf, _mix(bg, 1.3) if hov else bg, self.btn, border_radius=12)
        pygame.draw.rect(surf, ln, self.btn, 3, border_radius=12)
        _txt(surf, label, self.btn.center, 22, WHITE, True, center=True)
        _txt(surf, "ARROWS = choose    ENTER = buy / select    TAB = pose    ESC = back",
             (WIDTH // 2, HEIGHT - 16), 13, (150, 150, 170), center=True)
        if self.toast[1] > 0:
            _txt(surf, self.toast[0], (WIDTH // 2, HEIGHT - 44), 24, (110, 240, 150) if self.toast[2] else (255, 130, 110),
                 True, center=True)
