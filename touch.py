"""
touch.py - MOBILE TOUCH controls  (V12: aro SHOTHIK + RGB + animation)
(Settings > CONTROL MODE > MOBILE)

On-screen buttons, multi-touch (walk + jump + attack ekshathe):
  LEFT / RIGHT   walk (thumb na tule slide kora jay)        JUMP  = SPACE (dhore rakhle uchu lafay)
  KNIFE = J      PUNCH = K        STAR = T
  HIDE  = H (hold)                USE  = E
  TOOLS = TAB (tool wheel)        LAPTOP = L
  CODE  = C (code writer, green ON / red OFF)             ZAP = Q (electric)
  KEY   = phone keyboard on/off   REC = screen recorder   PAUSE = ESC

V12 e ki bodlalo:
  * Button boro, gulo alada (overlap nei) - ekta button chaple onno button chape na.
  * Hit test:  kache jei button sob cheye kache (normalised distance) sei pay - angul ektu bahire porleo kaj kore.
  * JUMP ekhon HOLD:  chepe rakhle uchu lafay, chhere dile chhoto lafay (keyboard er moto).
  * Finger / mouse dedupe thik kora - ek chape duibar kaj korbe na.
  * RGB rainbow ring (shob button), press e ripple + pop animation, jump button breathing glow.
  * RGB on/off:  TOUCH.rgb = False
Also works with a mouse on PC (click the buttons) so you can test it.
Android: this mode is chosen automatically the first time.
"""
import colorsys
import math
import os
import time

import pygame

W, H = 960, 540
ANDROID = "ANDROID_ARGUMENT" in os.environ
HIT_PAD = 16          # button er baire eto pixel porleo dhorbe

# id, label, centre, radius, key(s), mode  (hold | tap | toggle | kbd | rec), colour
_BTNS = [
    ("left",   "<",      (92, 448),  60, (pygame.K_LEFT, pygame.K_a),  "hold",   (70, 130, 255)),
    ("right",  ">",      (262, 448), 60, (pygame.K_RIGHT, pygame.K_d), "hold",   (70, 130, 255)),
    ("jump",   "JUMP",   (866, 430), 66, (pygame.K_SPACE,),            "hold",   (80, 220, 120)),
    ("knife",  "KNIFE",  (722, 490), 44, (pygame.K_j,),                "tap",    (255, 110, 90)),
    ("punch",  "PUNCH",  (740, 392), 44, (pygame.K_k,),                "tap",    (255, 170, 60)),
    ("star",   "STAR",   (882, 306), 38, (pygame.K_t,),                "tap",    (255, 220, 90)),
    ("hide",   "HIDE",   (608, 496), 38, (pygame.K_h,),                "hold",   (170, 120, 255)),
    ("use",    "USE",    (608, 410), 38, (pygame.K_e,),                "tap",    (90, 220, 230)),
    ("tools",  "TOOLS",  (500, 496), 36, (pygame.K_TAB,),              "tap",    (255, 140, 200)),
    ("zap",    "ZAP",    (500, 410), 34, (pygame.K_q,),                "tap",    (120, 200, 255)),
    ("laptop", "LAPTOP", (50, 48),   32, (pygame.K_l,),                "tap",    (150, 160, 255)),
    ("code",   "CODE",   (128, 48),  32, (pygame.K_c,),                "toggle", (110, 255, 150)),
    ("kbd",    "KEY",    (206, 48),  32, (),                           "kbd",    (230, 230, 120)),
    ("rec",    "REC",    (284, 48),  32, (),                           "rec",    (255, 80, 90)),
    ("pause",  "II",     (910, 48),  32, (pygame.K_ESCAPE,),           "tap",    (220, 220, 230)),
]
_BY_ID = {b[0]: b for b in _BTNS}
_UI_BTNS = ("pause", "kbd", "rec")      # menus/pause/tool wheel: only these show


def _key(k, down, uni=""):
    return pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=k, mod=0,
                              unicode=uni if down else "", scancode=0)


def rainbow(h, s=0.78, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return int(r * 255), int(g * 255), int(b * 255)


class Touch:
    def __init__(self):
        self.enabled = False
        self.ui = False
        self._held = set()
        self.ptr = {}            # pointer id -> button id
        self.code_on = False
        self.kbd_on = False
        self.rgb = True          # RGB rainbow ring
        self._last_touch = {}    # button id -> time of last finger press (dedupe emulated mouse)
        self._disc = {}
        self._scale = {}
        self._ripples = []       # [bid, t0]
        self._flash = {}         # bid -> time (tap flash)
        self._t0 = 0.0
        self._fonts = {}
        self._installed = False
        self._orig_flip = None
        self._glow = None

    # controls.py:  TOUCH.held  (set of keys)
    @property
    def held(self):
        return self._held

    @held.setter
    def held(self, v):
        self._held = set(v)

    # ---------- setup ----------
    def set_enabled(self, on):
        self.enabled = on
        self._held = set()
        self.ptr = {}
        self._t0 = 0.0
        if on and not self._installed:
            self._orig_flip = pygame.display.flip
            pygame.display.flip = self._flip
            self._installed = True
        if not on:
            self._kbd(False)

    def _kbd(self, on):
        self.kbd_on = on
        try:
            (pygame.key.start_text_input if on else pygame.key.stop_text_input)()
        except Exception:
            pass

    # ---------- geometry ----------
    def _visible(self):
        return [b for b in _BTNS if (not self.ui or b[0] in _UI_BTNS)]

    def _hit(self, x, y):
        """Je button er kendro sob cheye kache (radius er sapekkhe) sei button.  Angul ektu bahire porleo dhore."""
        best, bd = None, 1e9
        for b in self._visible():
            cx, cy = b[2]
            d = math.hypot(x - cx, y - cy)
            if d <= b[3] + HIT_PAD:
                k = d / b[3]
                if k < bd:
                    best, bd = b, k
        return best

    # ---------- events ----------
    def process(self, events):
        out = []
        for e in events:
            t = e.type
            if t == pygame.FINGERDOWN:
                self._press(("f", e.finger_id), e.x * W, e.y * H, out, True)
            elif t == pygame.FINGERUP:
                self._release(("f", e.finger_id), out)
            elif t == pygame.FINGERMOTION:
                self._move(("f", e.finger_id), e.x * W, e.y * H, out)
            elif t in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                b = self._hit(*e.pos)
                emulated = getattr(e, "touch", False)
                if t == pygame.MOUSEBUTTONDOWN and e.button == 1 and b:
                    if not emulated and time.time() - self._last_touch.get(b[0], 0) > 0.4:
                        self._press(("m", 0), e.pos[0], e.pos[1], out, False)
                    continue                      # tap on a button never reaches the game as a click
                if t == pygame.MOUSEBUTTONUP and e.button == 1:
                    if ("m", 0) in self.ptr:
                        self._release(("m", 0), out)
                        continue
                    if b or (emulated and self.ptr):
                        continue
                if t == pygame.MOUSEMOTION and ("m", 0) in self.ptr:
                    self._move(("m", 0), e.pos[0], e.pos[1], out)
                    continue
                out.append(e)
            elif t == pygame.TEXTINPUT and ANDROID:
                for ch in e.text:
                    out.append(_key(ord(ch), True, ch))
                    out.append(_key(ord(ch), False))
            else:
                out.append(e)
        return out

    def _press(self, pid, x, y, out, finger):
        b = self._hit(x, y)
        if not b:
            return
        if pid in self.ptr:                       # ek angul = ek button
            self._release(pid, out)
        self.ptr[pid] = b[0]
        if finger:
            self._last_touch[b[0]] = time.time()
        bid, keys, mode = b[0], b[4], b[5]
        self._ripples.append([bid, time.time()])
        del self._ripples[:-8]
        if mode == "hold":
            self._held |= set(keys)
            out.append(_key(keys[0], True))
        elif mode == "tap":
            self._flash[bid] = time.time()
            out.append(_key(keys[0], True))
            out.append(_key(keys[0], False))
        elif mode == "toggle":
            self.code_on = not self.code_on
            out.append(_key(keys[0], True))
            out.append(_key(keys[0], False))
        elif mode == "kbd":
            self._kbd(not self.kbd_on)
        elif mode == "rec":
            self._flash[bid] = time.time()
            try:
                import recorder
                recorder.toggle()
            except Exception:
                pass

    def _release(self, pid, out):
        bid = self.ptr.pop(pid, None)
        if bid is None:
            return
        b = _BY_ID[bid]
        if b[5] == "hold":
            if not any(v == bid for v in self.ptr.values()):
                self._held -= set(b[4])
            out.append(_key(b[4][0], False))

    def _move(self, pid, x, y, out):
        """Slide from LEFT to RIGHT without lifting the thumb."""
        old = self.ptr.get(pid)
        if old not in ("left", "right"):
            return
        b = self._hit(x, y)
        if b and b[0] in ("left", "right") and b[0] != old:
            self._release(pid, out)
            self._press(pid, x, y, out, False)

    # ---------- drawing ----------
    def _flip(self):
        try:
            self.draw(pygame.display.get_surface())
        except Exception:
            pass
        self._orig_flip()

    def _f(self, size):
        f = self._fonts.get(size)
        if f is None:
            f = self._fonts[size] = pygame.font.SysFont(None, size, bold=True)
        return f

    def _disc_sprite(self, b, lit, col):
        """Button er vitor + label (rong na bodlale cache)."""
        key = (b[0], lit, col, self.code_on if b[0] == "code" else None, self.kbd_on if b[0] == "kbd" else None)
        s = self._disc.get(key)
        if s:
            return s
        r = b[3]
        s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        c = (r + 2, r + 2)
        pygame.draw.circle(s, (12, 14, 26, 170 if lit else 120), c, r)          # dark glass
        pygame.draw.circle(s, (*col, 120 if lit else 46), c, r - 3)            # colour tint
        pygame.draw.circle(s, (255, 255, 255, 60 if lit else 28), (c[0] - r // 4, c[1] - r // 3), max(4, r // 3))
        label = b[1]
        if b[0] == "code":
            small = self._f(22)
            t1 = small.render("CODE", True, (255, 255, 255))
            t2 = small.render("ON" if self.code_on else "OFF", True, col)
            s.blit(t1, t1.get_rect(center=(c[0], c[1] - 7)))
            s.blit(t2, t2.get_rect(center=(c[0], c[1] + 11)))
        elif b[0] in ("left", "right"):
            txt = self._f(84).render(label, True, (255, 255, 255))
            s.blit(txt, txt.get_rect(center=c))
        else:
            size = 30 if len(label) <= 4 else (26 if len(label) <= 5 else 21)
            if r >= 60:
                size += 6
            txt = self._f(size).render(label, True, (255, 255, 255))
            s.blit(txt, txt.get_rect(center=c))
        self._disc[key] = s
        return s

    def _scratch(self, size):
        if self._glow is None or self._glow.get_width() < size:
            self._glow = pygame.Surface((size, size), pygame.SRCALPHA)
        return self._glow

    def draw(self, surf):
        if surf is None:
            return
        pressed = set(self.ptr.values())
        now = time.time()
        if not self._t0:
            self._t0 = now
        rec_on = False
        try:
            import recorder
            rec_on = recorder.is_recording()
        except Exception:
            pass
        # ripples (press animation)
        alive = []
        for rp in self._ripples:
            k = (now - rp[1]) / 0.45
            if k < 1.0:
                alive.append(rp)
                b = _BY_ID[rp[0]]
                if self.ui and rp[0] not in _UI_BTNS:
                    continue
                rr = int(b[3] * (1.0 + 0.55 * k))
                sc = self._scratch(2 * rr + 8)
                sc.fill((0, 0, 0, 0))
                col = rainbow(now * 0.5 + b[2][0] / 960.0) if self.rgb else b[6]
                pygame.draw.circle(sc, (*col, int(170 * (1 - k))), (rr + 4, rr + 4), rr, 4)
                surf.blit(sc, (b[2][0] - rr - 4, b[2][1] - rr - 4), (0, 0, 2 * rr + 8, 2 * rr + 8))
        self._ripples = alive

        for i, b in enumerate(self._visible()):
            bid = b[0]
            k0 = min(1.0, max(0.0, (now - self._t0 - i * 0.05) / 0.38))
            appear = 1 - (1 - k0) ** 3 * (1 + 1.6 * (1 - k0))          # pop-in with a little overshoot
            is_down = bid in pressed or (now - self._flash.get(bid, 0) < 0.14)
            target = 0.88 if is_down else 1.0
            sc = self._scale.get(bid, 1.0)
            sc += (target - sc) * 0.45
            self._scale[bid] = sc
            sc *= max(0.0, appear)
            if sc < 0.02:
                continue
            base = b[6]
            if bid == "code":
                base = (90, 255, 140) if self.code_on else (255, 90, 90)
            lit = is_down or (bid == "code" and self.code_on) or (bid == "kbd" and self.kbd_on) \
                or (bid == "rec" and rec_on)
            if bid == "jump" or (bid == "rec" and rec_on):
                sc *= 1.0 + 0.035 * math.sin(now * 4.2)              # breathing
            if bid == "code" and self.code_on:
                sc *= 1.0 + 0.05 * math.sin(now * 5)
            disc = self._disc_sprite(b, lit, base)
            if abs(sc - 1.0) > 0.01:
                disc = pygame.transform.rotozoom(disc, 0, sc)
            cx, cy = b[2]
            r = int(b[3] * sc)
            rect = pygame.Rect(0, 0, max(2, r * 2), max(2, r * 2))
            rect.center = b[2]
            if self.rgb:                                              # RGB rainbow glow + ring
                phase = now * (0.9 if lit else 0.35) + cx / 1200.0 + cy / 900.0
                glow_r = r + 10
                g = self._scratch(2 * glow_r + 8)
                g.fill((0, 0, 0, 0))
                pygame.draw.circle(g, (*rainbow(phase), 70 if lit else 34), (glow_r + 4, glow_r + 4), glow_r)
                surf.blit(g, (cx - glow_r - 4, cy - glow_r - 4), (0, 0, 2 * glow_r + 8, 2 * glow_r + 8))
                surf.blit(disc, disc.get_rect(center=b[2]))
                segs = 20
                th = 5 if lit else 3
                for k in range(segs):
                    a0 = k * (2 * math.pi / segs)
                    a1 = a0 + (2 * math.pi / segs) + 0.04
                    pygame.draw.arc(surf, rainbow(phase + k / segs, 0.85, 1.0), rect, a0, a1, th)
            else:
                surf.blit(disc, disc.get_rect(center=b[2]))
                pygame.draw.circle(surf, base, b[2], r, 4 if lit else 3)
            if bid == "rec" and rec_on and int(now * 2) % 2 == 0:
                pygame.draw.circle(surf, (255, 40, 50), (cx + r - 6, cy - r + 6), 6)


TOUCH = Touch()
