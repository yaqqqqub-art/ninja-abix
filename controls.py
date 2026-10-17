"""
controls.py - Controller (gamepad) support. Settings > CONTROL MODE > CONTROLLER chalu korle kaj kore.

Level/menu loop e:    for e in controls.filter(pygame.event.get()):  ...
Controller er button ke ei module keyboard key e bodle dey, tai level er code bodlate hoy na.

GAME (khelar somoy)                         UI (menu / pause / tool wheel)
  Left stick / D-pad   = chola                 stick / D-pad = upor-niche-bam-dan
  RB     = jump (SPACE)                        A = select (ENTER)
  X      = knife (J)                           B = back (ESC)
  Y      = super punch (K)                     START = ESC
  B      = hide (H, dhore rakho)
  A      = ninja star (T)  - kinle
  LB     = use tool (E)
  BACK   = tool wheel (TAB)
  START  = pause (ESC)
  L3     = laptop (L)
  R3     = mini code writer on/off (C)
  LT     = electric (Q)
(Xbox layout. Onno controller e button number alada hote pare.)
"""
import time

import pygame

from touch import TOUCH

DEAD = 0.5
BTN_A, BTN_B, BTN_X, BTN_Y, BTN_LB, BTN_RB, BTN_BACK, BTN_START, BTN_L3, BTN_R3 = range(10)

GAME_MAP = {BTN_A: pygame.K_t, BTN_X: pygame.K_j, BTN_Y: pygame.K_k, BTN_LB: pygame.K_e, BTN_RB: pygame.K_SPACE,
            BTN_BACK: pygame.K_TAB, BTN_START: pygame.K_ESCAPE, BTN_L3: pygame.K_l, BTN_R3: pygame.K_c}
UI_MAP = {BTN_A: pygame.K_RETURN, BTN_B: pygame.K_ESCAPE, BTN_START: pygame.K_ESCAPE, BTN_Y: pygame.K_e,
          BTN_BACK: pygame.K_TAB, BTN_X: pygame.K_RETURN, BTN_RB: pygame.K_RETURN}


class _Keys:
    """pygame.key.get_pressed() er moto, kintu controller er dhora key o 'pressed' dhore."""

    def __init__(self, real, held):
        self.real, self.held = real, held

    def __getitem__(self, k):
        return bool(self.real[k]) or (k in self.held)


class Controls:
    def __init__(self):
        self.enabled = False
        self.joy = None
        self.ctx = "game"                # "game" | "ui"  (level loop prottek frame e set kore)
        self.held = set()
        self.dirs = {}                   # direction -> next repeat time
        self.lt_down = False
        self._last_scan = 0.0
        self._real_get_pressed = pygame.key.get_pressed
        self._installed = False

    # ---------- setup ----------
    def set_mode(self, mode):
        TOUCH.set_enabled(mode == "touch")
        self.enabled = (mode in ("controller", "touch"))
        if self.enabled:
            self.scan(force=True)
            if not self._installed:
                pygame.key.get_pressed = lambda: _Keys(self._real_get_pressed(), (self.held | TOUCH.held) if self.enabled else ())
                self._installed = True
        else:
            self.held = set()

    def scan(self, force=False):
        now = time.time()
        if not force and now - self._last_scan < 2.0:
            return
        self._last_scan = now
        try:
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self.joy = pygame.joystick.Joystick(0)
                try:
                    self.joy.init()
                except Exception:
                    pass
            else:
                self.joy = None
        except Exception:
            self.joy = None

    def connected(self):
        self.scan()
        return self.joy is not None

    # ---------- per frame ----------
    def filter(self, events):
        """Event list ne, controller er button gulo keyboard event e bodle sathe jure return kore."""
        events = list(events)
        if not self.enabled:
            return events
        if TOUCH.enabled:
            TOUCH.ui = self.ctx == "ui"
            return TOUCH.process(events)
        self.scan()
        if self.joy is None:
            self.held = set()
            return events
        out = list(events)
        ui = self.ctx == "ui"
        mp = UI_MAP if ui else GAME_MAP
        for e in events:
            if e.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
                b = e.button
                down = e.type == pygame.JOYBUTTONDOWN
                if b == BTN_B and not ui:                       # hide = dhore rakho
                    out.append(self._key(pygame.K_h, down))
                    continue
                k = mp.get(b)
                if k is not None and down:
                    out.append(self._key(k, True))
        # ---- stick / d-pad ----
        try:
            ax = self.joy.get_axis(0)
            ay = self.joy.get_axis(1)
            hat = self.joy.get_hat(0) if self.joy.get_numhats() > 0 else (0, 0)
        except Exception:
            return out
        dx = -1 if (ax < -DEAD or hat[0] < 0) else (1 if (ax > DEAD or hat[0] > 0) else 0)
        dy = 1 if (ay > DEAD or hat[1] < 0) else (-1 if (ay < -DEAD or hat[1] > 0) else 0)   # +1 = niche
        held = set()
        if dx < 0:
            held |= {pygame.K_LEFT, pygame.K_a}
        if dx > 0:
            held |= {pygame.K_RIGHT, pygame.K_d}
        if dy > 0:
            held |= {pygame.K_DOWN, pygame.K_s}
        try:
            if self.joy.get_button(BTN_B) and not ui:
                held.add(pygame.K_h)
        except Exception:
            pass
        self.held = held
        now = time.time()
        for name, active, key in (("L", dx < 0, pygame.K_LEFT), ("R", dx > 0, pygame.K_RIGHT),
                                  ("D", dy > 0, pygame.K_DOWN), ("U", dy < 0, pygame.K_UP)):
            if not active:
                self.dirs.pop(name, None)
                continue
            nxt = self.dirs.get(name)
            if nxt is None:
                self.dirs[name] = now + 0.35
                fire = True
            elif now >= nxt:
                self.dirs[name] = now + 0.12
                fire = True
            else:
                fire = False
            # game er bhitore UP = lafano hoye jay, tai shudhu UI te
            if fire and (ui or name != "U"):
                out.append(self._key(key, True))
        # ---- LT = electric (Q) ----
        try:
            if self.joy.get_numaxes() >= 6:
                lt = self.joy.get_axis(4) > 0.5
                if lt and not self.lt_down and not ui:
                    out.append(self._key(pygame.K_q, True))
                self.lt_down = lt
        except Exception:
            pass
        return out

    @staticmethod
    def _key(k, down):
        return pygame.event.Event(pygame.KEYDOWN if down else pygame.KEYUP, key=k, mod=0,
                                  unicode="", scancode=0)


CTL = Controls()


def set_mode(mode):
    CTL.set_mode(mode)


def filter(events):          # noqa: A001  (builtin nam, kintu eta ei module er)
    return CTL.filter(events)


def set_ctx(ui):
    CTL.ctx = "ui" if ui else "game"


def connected():
    return CTL.connected()


def enabled():
    return CTL.enabled
