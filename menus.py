"""
menus.py - Main menu er notun screen gulo:
  SettingsScreen  - Language / Control mode / Volume / About / Privacy Policy
  SpecialScreen   - Special Tools (9 slot) + Currency Exchange (Tk -> Dollar / Diamond)

Mouse, keyboard (arrow + Enter) ar controller (stick + A) - tinte-i chole.
"""
import math

import pygame

import controls
import economy as EC
import lang
import sound
import voice
from animation import WIDTH, HEIGHT, WHITE, RED, GOLD, get_font, rgb_color, draw_shuriken


def apply_settings(save):
    """Save kora Settings ke game e lagao (bhasha, controller mode, volume)."""
    st = save["settings"]
    lang.set_lang(st["lang"])
    try:
        voice.set_language(st["lang"])
    except Exception:
        pass
    controls.set_mode(st["control"])
    try:
        sound.set_master(save.get("laptop", {}).get("volume", 0.8))
    except Exception:
        pass


def _chip(surf, rect, text, active, focus, t, size=18):
    hov = rect.collidepoint(pygame.mouse.get_pos())
    if active:
        col = rgb_color(t, offset=rect.x * 0.002)
        pygame.draw.rect(surf, col, rect, border_radius=12)
        tc = (15, 15, 25)
    else:
        pygame.draw.rect(surf, (52, 56, 84) if (hov or focus) else (30, 32, 52), rect, border_radius=12)
        tc = WHITE
    pygame.draw.rect(surf, (255, 230, 120) if focus else ((200, 205, 230) if active else (96, 102, 138)), rect,
                     4 if focus else 2, border_radius=12)
    img = get_font(size).render(text, True, tc)
    surf.blit(img, img.get_rect(center=rect.center))


def _txt(surf, text, pos, size=16, col=WHITE, bold=False, center=False, right=False):
    img = get_font(size, bold).render(text, True, col)
    r = img.get_rect()
    if center:
        r.center = pos
    elif right:
        r.midright = pos
    else:
        r.topleft = pos
    surf.blit(img, r)
    return r


# ------------------------------------------------------------------
# Icons
# ------------------------------------------------------------------
def draw_diamond(surf, c, r, col=(110, 230, 255)):
    x, y = c
    pts = [(x, y - r), (x + r * 0.85, y - r * 0.2), (x, y + r), (x - r * 0.85, y - r * 0.2)]
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, WHITE, pts, 2)
    pygame.draw.line(surf, WHITE, (x - r * 0.85, y - r * 0.2), (x + r * 0.85, y - r * 0.2), 2)


def draw_coin(surf, c, r, col, label):
    pygame.draw.circle(surf, col, (int(c[0]), int(c[1])), r)
    pygame.draw.circle(surf, WHITE, (int(c[0]), int(c[1])), r, 2)
    _txt(surf, label, c, max(10, int(r * 1.1)), (20, 20, 30), True, center=True)


def draw_special_icon(surf, tid, c, r, t):
    x, y = c
    if tid == "star":
        draw_shuriken(surf, c, r, t * 2, (210, 215, 235), (24, 26, 40))
    elif tid == "code":
        _txt(surf, "</>", c, int(r * 0.9), (110, 230, 255), True, center=True)
        pygame.draw.rect(surf, (110, 230, 255), (x - r, y - r * 0.6, r * 2, r * 1.2), 2, border_radius=6)
    elif tid == "electric":
        pts = [(x + r * 0.15, y - r), (x - r * 0.55, y + r * 0.1), (x - r * 0.05, y + r * 0.1),
               (x - r * 0.2, y + r), (x + r * 0.55, y - r * 0.2), (x + r * 0.05, y - r * 0.2)]
        pygame.draw.polygon(surf, (255, 225, 70) if int(t * 6) % 2 else (255, 255, 160), pts)
        pygame.draw.polygon(surf, (255, 150, 30), pts, 2)


def draw_wallet(surf, save, y=34, x_right=WIDTH - 24, t=0.0):
    """Tk, Dollar ar Diamond - ek line e."""
    x = x_right
    for label, val, kind in (("diamond", save["diamonds"], "d"), ("dollar", save["dollars"], "$"), ("tk", save["money"], "tk")):
        s = f"{val}"
        r = _txt(surf, s, (x, y), 22, (235, 240, 255), True, right=True)
        ic = (r.left - 20, y)
        if kind == "d":
            draw_diamond(surf, ic, 11)
        elif kind == "$":
            draw_coin(surf, ic, 11, (90, 210, 120), "$")
        else:
            draw_coin(surf, ic, 11, (255, 200, 70), "Tk")
        x = ic[0] - 26 - 14


# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------
class SettingsScreen:
    def __init__(self):
        self.lang_rects = [pygame.Rect(40 + i * 178, 122, 166, 46) for i in range(5)]
        self.ctrl_rects = [pygame.Rect(40, 212, 150, 46), pygame.Rect(200, 212, 150, 46), pygame.Rect(360, 212, 150, 46)]
        self.vol_rect = pygame.Rect(40, 306, 440, 14)
        self.info_rects = [pygame.Rect(40, 352, 230, 46), pygame.Rect(280, 352, 290, 46)]
        self.sel = [0, 0]
        self.info = None
        self.dirty = False
        self.t = 0.0
        self.drag = False

    def open(self, save):
        self.save = save
        self.sel = [0, [lang.CODES.index(save["settings"]["lang"]), 0, 0, 0][0]]
        self.sel = [0, lang.CODES.index(save["settings"]["lang"])]
        self.info = None
        self.drag = False

    def rects_of(self, row):
        return [self.lang_rects, self.ctrl_rects, [self.vol_rect], self.info_rects][row]

    def set_lang(self, code):
        self.save["settings"]["lang"] = code
        apply_settings(self.save)
        sound.play("click")
        self.dirty = True

    def set_ctrl(self, mode):
        self.save["settings"]["control"] = mode
        apply_settings(self.save)
        sound.play("click")
        self.dirty = True

    def set_volume(self, v):
        v = max(0.0, min(1.0, v))
        self.save["laptop"]["volume"] = v
        sound.set_master(v)
        self.dirty = True

    def activate(self, row, col):
        if row == 0:
            self.set_lang(lang.CODES[col])
        elif row == 1:
            self.set_ctrl(("keyboard", "controller", "touch")[col])
        elif row == 3:
            self.info = ("about", "privacy")[col] if self.info != ("about", "privacy")[col] else None
            sound.play("pop")

    def event(self, e):
        s = self.save
        if e.type == pygame.KEYDOWN:
            r, c = self.sel
            if e.key == pygame.K_UP:
                r = (r - 1) % 4
            elif e.key == pygame.K_DOWN:
                r = (r + 1) % 4
            elif e.key == pygame.K_LEFT:
                if r == 2:
                    self.set_volume(s["laptop"]["volume"] - 0.1)
                else:
                    c -= 1
            elif e.key == pygame.K_RIGHT:
                if r == 2:
                    self.set_volume(s["laptop"]["volume"] + 0.1)
                else:
                    c += 1
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.activate(r, c)
            n = len(self.rects_of(r))
            c = max(0, min(n - 1, c))
            if (r, c) != tuple(self.sel):
                sound.play("hover", 0.5)
            self.sel = [r, c]
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            pos = e.pos
            for row in range(4):
                for col, rc in enumerate(self.rects_of(row)):
                    hit = rc.inflate(0, 24) if row == 2 else rc
                    if hit.collidepoint(pos):
                        self.sel = [row, col]
                        if row == 2:
                            self.drag = True
                            self.set_volume((pos[0] - self.vol_rect.x) / self.vol_rect.w)
                        else:
                            self.activate(row, col)
                        return
        elif e.type == pygame.MOUSEBUTTONUP:
            self.drag = False
        elif e.type == pygame.MOUSEMOTION and self.drag:
            self.set_volume((e.pos[0] - self.vol_rect.x) / self.vol_rect.w)

    def update(self, dt):
        self.t += dt

    def draw(self, surf, mouse):
        t = self.t
        st = self.save["settings"]
        _txt(surf, lang.tr("settings"), (40, 26), 40, WHITE, True)
        # language
        _txt(surf, lang.tr("language"), (40, 94), 18, GOLD, True)
        for i, (rc, (code, name)) in enumerate(zip(self.lang_rects, lang.LANGS)):
            _chip(surf, rc, name, st["lang"] == code, self.sel == [0, i], t)
        # control mode
        _txt(surf, lang.tr("control_mode"), (40, 184), 18, GOLD, True)
        for i, (rc, key) in enumerate(zip(self.ctrl_rects, ("keyboard", "controller", "touch"))):
            _chip(surf, rc, lang.tr(key), st["control"] == key, self.sel == [1, i], t)
        if st["control"] == "touch":
            _txt(surf, "On-screen buttons: walk, JUMP, KNIFE, PUNCH, STAR, HIDE, USE,", (40, 232 + 36), 15, (110, 240, 150))
            _txt(surf, "TOOLS, LAPTOP, CODE on/off, ZAP, KEY (phone keyboard), PAUSE", (40, 232 + 56), 15, (110, 240, 150))
        if st["control"] == "controller":
            ok = controls.connected()
            _txt(surf, lang.tr("ctrl_ok" if ok else "ctrl_none"), (510, 224), 15,
                 (110, 240, 150) if ok else (255, 150, 120))
            box = pygame.Rect(580, 270, 350, 250)
            pygame.draw.rect(surf, (20, 22, 38), box, border_radius=12)
            pygame.draw.rect(surf, (90, 96, 130), box, 2, border_radius=12)
            y = box.y + 12
            for k in ("c_move", "c_jump", "c_knife", "c_punch", "c_hide", "c_star", "c_use", "c_wheel", "c_pause",
                      "c_laptop", "c_special"):
                for ln in _wrap(lang.tr(k), 44):
                    _txt(surf, ln, (box.x + 12, y), 13, (205, 210, 230))
                    y += 17
                y += 2
        # volume
        v = self.save["laptop"]["volume"]
        _txt(surf, f"{lang.tr('volume')}   {int(v * 100)}%", (40, 276), 18, GOLD, True)
        pygame.draw.rect(surf, (40, 44, 68), self.vol_rect, border_radius=7)
        fill = self.vol_rect.copy()
        fill.w = max(6, int(self.vol_rect.w * v))
        pygame.draw.rect(surf, rgb_color(t), fill, border_radius=7)
        kx = self.vol_rect.x + int(self.vol_rect.w * v)
        pygame.draw.circle(surf, WHITE, (kx, self.vol_rect.centery), 12 if self.sel[0] == 2 else 10)
        if self.sel[0] == 2:
            pygame.draw.circle(surf, (255, 230, 120), (kx, self.vol_rect.centery), 15, 3)
        # about / privacy
        for i, (rc, key) in enumerate(zip(self.info_rects, ("about", "privacy"))):
            _chip(surf, rc, lang.tr(key), self.info == key, self.sel == [3, i], t, 16)
        if self.info:
            box = pygame.Rect(40, 414, 530, 110)
            pygame.draw.rect(surf, (20, 22, 38), box, border_radius=12)
            pygame.draw.rect(surf, (90, 96, 130), box, 2, border_radius=12)
            keys = ("about_1", "about_2", "about_3") if self.info == "about" else \
                ("priv_1", "priv_2", "priv_3", "priv_4", "priv_5")
            y = box.y + 10
            for k in keys:
                _txt(surf, lang.tr(k), (box.x + 14, y), 14 if self.info == "privacy" else 17, (210, 215, 235))
                y += 20 if self.info == "privacy" else 28
        _txt(surf, lang.tr("esc_back"), (WIDTH // 2, HEIGHT - 16), 14, (150, 150, 170), center=True)


def _wrap(text, width):
    """Shobdo bhenge line banay (CJK te akkhor dhore)."""
    if len(text) <= width:
        return [text]
    words, lines, cur = text.split(" "), [], ""
    if len(words) == 1:
        return [text[i:i + width] for i in range(0, len(text), width)]
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------
# Special Tools + Exchange
# ------------------------------------------------------------------
class SpecialScreen:
    def __init__(self):
        self.cards = [pygame.Rect(40 + (i % 3) * 136, 108 + (i // 3) * 136, 120, 120) for i in range(9)]
        self.buy_tk = pygame.Rect(470, 330, 215, 50)
        self.buy_dia = pygame.Rect(700, 330, 215, 50)
        self.ex_btn = pygame.Rect(470, 410, 445, 50)
        self.sel = 0
        self.pay_dia = False
        self.overlay = False
        self.ex_sel = 0
        self.ex_rects = [pygame.Rect(210 + (i % 2) * 280, 232 + (i // 2) * 80, 260, 62) for i in range(4)]
        self.toast = ("", 0.0)
        self.dirty = False
        self.t = 0.0

    def open(self, save):
        self.save = save
        self.sel, self.overlay, self.toast = 0, False, ("", 0.0)

    def back(self):
        """ESC: overlay khola thakle shudhu seta bondho. True = ESC khoy hoye geche."""
        if self.overlay:
            self.overlay = False
            sound.play("back")
            return True
        return False

    def say(self, key, ok=True):
        self.toast = (lang.tr(key), 2.0, ok)

    def buy(self, with_dia):
        item = EC.SPECIAL[self.sel]
        if not item["id"]:
            sound.play("lock")
            return
        res = EC.buy(self.save, item["id"], with_dia)
        if res == "ok":
            sound.play("unlock")
            self.say("bought")
            self.dirty = True
        elif res == "owned":
            sound.play("hover", 0.5)
            self.say("owned")
        else:
            sound.play("lock")
            self.say("need_more", False)

    def do_exchange(self, i):
        kind, n = (("dollar", 1), ("dollar", 10), ("diamond", 1), ("diamond", 5))[i]
        if EC.exchange(self.save, kind, n):
            sound.play("cash")
            self.say("exchanged")
            self.dirty = True
        else:
            sound.play("lock")
            self.say("need_more", False)

    def event(self, e):
        if e.type == pygame.KEYDOWN:
            if self.overlay:
                r, c = divmod(self.ex_sel, 2)
                if e.key == pygame.K_UP:
                    r = max(0, r - 1)
                elif e.key == pygame.K_DOWN:
                    r = min(1, r + 1)
                elif e.key == pygame.K_LEFT:
                    c = 0
                elif e.key == pygame.K_RIGHT:
                    c = 1
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    self.do_exchange(self.ex_sel)
                elif e.key == pygame.K_e:
                    self.overlay = False
                self.ex_sel = r * 2 + c
                return
            r, c = divmod(self.sel, 3)
            if e.key == pygame.K_UP:
                r = (r - 1) % 3
            elif e.key == pygame.K_DOWN:
                r = (r + 1) % 3
            elif e.key == pygame.K_LEFT:
                c = (c - 1) % 3
            elif e.key == pygame.K_RIGHT:
                c = (c + 1) % 3
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.buy(self.pay_dia)
            elif e.key == pygame.K_TAB:
                self.pay_dia = not self.pay_dia
                sound.play("hover", 0.5)
            elif e.key == pygame.K_e:
                self.overlay = True
                sound.play("pop")
            if r * 3 + c != self.sel:
                sound.play("hover", 0.5)
            self.sel = r * 3 + c
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            pos = e.pos
            if self.overlay:
                for i, rc in enumerate(self.ex_rects):
                    if rc.collidepoint(pos):
                        self.ex_sel = i
                        self.do_exchange(i)
                        return
                return
            for i, rc in enumerate(self.cards):
                if rc.collidepoint(pos):
                    self.sel = i
                    sound.play("click")
                    return
            if self.buy_tk.collidepoint(pos):
                self.buy(False)
            elif self.buy_dia.collidepoint(pos):
                self.buy(True)
            elif self.ex_btn.collidepoint(pos):
                self.overlay = True
                sound.play("pop")

    def update(self, dt):
        self.t += dt
        if self.toast[1] > 0:
            self.toast = (self.toast[0], self.toast[1] - dt, self.toast[2] if len(self.toast) > 2 else True)

    def draw(self, surf, mouse):
        t, save = self.t, self.save
        _txt(surf, lang.tr("sp_title"), (40, 26), 36, WHITE, True)
        draw_wallet(surf, save, 44, WIDTH - 24, t)
        for i, (rc, item) in enumerate(zip(self.cards, EC.SPECIAL)):
            owned = bool(item["id"] and save["special"].get(item["id"]))
            sel = (i == self.sel)
            pygame.draw.rect(surf, (28, 30, 50), rc, border_radius=16)
            col = rgb_color(t, offset=i * 0.07) if (sel and item["id"]) else ((90, 200, 130) if owned else (80, 84, 112))
            pygame.draw.rect(surf, col, rc, 5 if sel else 3, border_radius=16)
            if item["id"]:
                draw_special_icon(surf, item["id"], (rc.centerx, rc.centery - 8), 34, t)
                _txt(surf, lang.tr(item["name"]), (rc.centerx, rc.bottom - 16), 11, WHITE, True, center=True)
                if owned:
                    pygame.draw.circle(surf, (90, 220, 130), (rc.right - 16, rc.y + 16), 11)
                    pygame.draw.lines(surf, (15, 25, 15), False,
                                      [(rc.right - 22, rc.y + 16), (rc.right - 17, rc.y + 21), (rc.right - 10, rc.y + 11)], 3)
            else:
                _draw_lock(surf, (rc.centerx, rc.centery - 8))
                _txt(surf, f"{i + 1}", (rc.x + 10, rc.y + 6), 14, (130, 134, 160), True)
                _txt(surf, lang.tr("soon"), (rc.centerx, rc.bottom - 16), 10, (130, 134, 160), True, center=True)
        # detail
        panel = pygame.Rect(470, 108, 445, 265 - 0)
        pygame.draw.rect(surf, (20, 22, 38), panel, border_radius=16)
        pygame.draw.rect(surf, (90, 96, 130), panel, 3, border_radius=16)
        item = EC.SPECIAL[self.sel]
        if item["id"]:
            draw_special_icon(surf, item["id"], (panel.x + 58, panel.y + 62), 36, t)
            _txt(surf, lang.tr(item["name"]), (panel.x + 112, panel.y + 24), 26, GOLD, True)
            y = panel.y + 100
            for ln in lang.tr_lines(item["desc"]):
                _txt(surf, ln, (panel.x + 20, y), 16, (210, 215, 235))
                y += 26
            owned = save["special"].get(item["id"])
            _txt(surf, f"{item['price_tk']} Tk   =   {item['price_dia']}", (panel.x + 20, panel.y + 190), 20, (235, 240, 255), True)
            draw_diamond(surf, (panel.x + 20 + 196, panel.y + 201), 11)
            if owned:
                _txt(surf, lang.tr("owned"), (panel.right - 20, panel.y + 26), 20, (110, 240, 150), True, right=True)
            for rc, key, price, dia in ((self.buy_tk, "buy_tk", item["price_tk"], False),
                                        (self.buy_dia, "buy_dia", item["price_dia"], True)):
                can = not owned
                mode_on = (self.pay_dia == dia)
                pygame.draw.rect(surf, (36, 90, 60) if (can and mode_on) else (34, 36, 56), rc, border_radius=12)
                pygame.draw.rect(surf, (255, 230, 120) if mode_on else (96, 102, 138), rc, 3 if mode_on else 2, border_radius=12)
                _txt(surf, lang.tr(key), (rc.centerx, rc.centery - 10), 14, WHITE, True, center=True)
                _txt(surf, str(price), (rc.centerx, rc.centery + 12), 14, (200, 205, 230), False, center=True)
        else:
            _draw_lock(surf, (panel.centerx, panel.y + 90), 1.6)
            _txt(surf, lang.tr("soon"), (panel.centerx, panel.y + 170), 24, (150, 154, 180), True, center=True)
        # exchange button
        hov = self.ex_btn.collidepoint(mouse)
        pygame.draw.rect(surf, (60, 64, 100) if hov else (36, 38, 66), self.ex_btn, border_radius=12)
        pygame.draw.rect(surf, rgb_color(t), self.ex_btn, 3, border_radius=12)
        _txt(surf, "E   " + lang.tr("exchange"), self.ex_btn.center, 18, WHITE, True, center=True)
        _txt(surf, "TAB = " + (lang.tr("buy_dia") if not self.pay_dia else lang.tr("buy_tk")) + "     " + lang.tr("esc_back"),
             (WIDTH // 2, HEIGHT - 16), 13, (150, 150, 170), center=True)
        if self.toast[1] > 0:
            ok = self.toast[2] if len(self.toast) > 2 else True
            _txt(surf, self.toast[0], (WIDTH // 2, 500), 26, (110, 240, 150) if ok else (255, 130, 110), True, center=True)
        if self.overlay:
            self._draw_exchange(surf, mouse)

    def _draw_exchange(self, surf, mouse):
        t, save = self.t, self.save
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 190))
        surf.blit(dim, (0, 0))
        box = pygame.Rect(180, 110, 600, 330)
        pygame.draw.rect(surf, (22, 24, 42), box, border_radius=18)
        pygame.draw.rect(surf, rgb_color(t), box, 4, border_radius=18)
        _txt(surf, lang.tr("ex_title"), (box.centerx, box.y + 30), 28, GOLD, True, center=True)
        _txt(surf, lang.tr("ex_rate1"), (box.x + 40, box.y + 66), 17, (210, 215, 235))
        _txt(surf, lang.tr("ex_rate2"), (box.x + 330, box.y + 66), 17, (210, 215, 235))
        draw_wallet(surf, save, box.y + 110, box.right - 30, t)
        labels = (("+1", "$", EC.TK_PER_DOLLAR), ("+10", "$", EC.TK_PER_DOLLAR * 10),
                  ("+1", "d", EC.TK_PER_DIAMOND), ("+5", "d", EC.TK_PER_DIAMOND * 5))
        for i, (rc, (n, kind, cost)) in enumerate(zip(self.ex_rects, labels)):
            sel = (i == self.ex_sel)
            pygame.draw.rect(surf, (52, 56, 84) if (rc.collidepoint(mouse) or sel) else (32, 34, 56), rc, border_radius=12)
            pygame.draw.rect(surf, (255, 230, 120) if sel else (96, 102, 138), rc, 4 if sel else 2, border_radius=12)
            _txt(surf, n, (rc.x + 24, rc.centery), 24, WHITE, True, center=True)
            if kind == "d":
                draw_diamond(surf, (rc.x + 68, rc.centery), 14)
            else:
                draw_coin(surf, (rc.x + 68, rc.centery), 14, (90, 210, 120), "$")
            _txt(surf, f"{cost} Tk", (rc.right - 16, rc.centery), 20, (255, 215, 110), True, right=True)
        _txt(surf, "E / ESC", (box.centerx, box.bottom - 22), 14, (150, 154, 180), center=True)


def _draw_lock(surf, center, size=1.0):
    cx, cy = center
    gray = (125, 125, 150)
    pygame.draw.arc(surf, gray, (cx - int(9 * size), cy - int(19 * size), int(18 * size), int(32 * size)),
                    0, math.pi, max(2, int(3 * size)))
    body = pygame.Rect(0, 0, int(24 * size), int(18 * size))
    body.center = (cx, cy + int(6 * size))
    pygame.draw.rect(surf, gray, body, border_radius=4)
    pygame.draw.circle(surf, (35, 35, 52), body.center, max(2, int(3 * size)))
