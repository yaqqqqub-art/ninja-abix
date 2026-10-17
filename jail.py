"""
jail.py - JAIL e gele 3 ta OPTION  (level 14, 15 + 3D level)

  1) PAY 10000 Tk      -> shathe shathe chhere dey (taka thakle)
  2) WAIT 1 MIN        -> 60 sec dariye thako, tarpor chhere dey
  3) BREAK OUT         -> 3 ta CELL BAR + 2 ta WINDOW bhango.
        BREAK button chapo (SPACE / ENTER / click / touch) jokhon dagh ta shobuj jaygay ashe:
           GOOD   (shobuj)   =  boro bhanga  (+55)
           NORMAL (holud)    =  chhoto bhanga (+28)
           BAD    (lal)      =  kom hoy (-30) + GUARD shune phele.   3 bar BAD = guard dhore ->  WAIT 1 MIN
        3 bar + 2 window sob bhangle ninja palay!

Use:
    ui = JailUI(money=1234, pay_cost=10000)
    ui.event(e) ; ui.update(dt) ; ui.draw(surf)
    ui.result -> None | "free"       ui.paid -> koto taka dilo
"""
import math
import random

import pygame

import sound
import sprites as SP
from animation import WIDTH, HEIGHT, get_font

PAY_COST = 10000
WAIT_TIME = 60.0

STAGES = [("CELL BAR 1 / 3", "bar"), ("CELL BAR 2 / 3", "bar"), ("CELL BAR 3 / 3", "bar"),
          ("WINDOW 1 / 2", "window"), ("WINDOW 2 / 2", "window")]
GOOD, NORMAL, BAD = "GOOD", "NORMAL", "BAD"
GAIN = {GOOD: 55.0, NORMAL: 28.0, BAD: -30.0}
STRIKES_MAX = 3


def _snd(name, v=1.0):
    try:
        sound.play(name, v)
    except Exception:
        pass


def judge(pos, good_w=0.10, normal_w=0.26):
    """pos 0..1 (bar er majhkhane 0.5).  Return GOOD | NORMAL | BAD."""
    d = abs(pos - 0.5)
    if d <= good_w / 2:
        return GOOD
    if d <= normal_w / 2:
        return NORMAL
    return BAD


class JailUI:
    def __init__(self, money, pay_cost=PAY_COST, wait_time=WAIT_TIME, seed=None):
        self.money = int(money)
        self.pay_cost = pay_cost
        self.wait_time = wait_time
        self.rnd = random.Random(seed)
        self.mode = "menu"            # menu | wait | break | caught | out
        self.sel = 0
        self.t = 0.0
        self.mode_t = 0.0
        self.result = None
        self.paid = 0
        self.toast, self.toast_t = "", 0.0
        # wait
        self.wait_left = wait_time
        # break
        self.stage = 0
        self.prog = 0.0
        self.marker = 0.0             # 0..1 (pingpong)
        self.speed = 0.9
        self.strikes = 0
        self.last = None              # (GOOD|NORMAL|BAD, time)
        self.guard_look = 0.0         # guard ghure takale > 0
        self.lock = 0.0
        self.break_rect = pygame.Rect(WIDTH // 2 - 110, 440, 220, 64)
        self.opt_rects = [pygame.Rect(80 + i * 270, 262, 250, 170) for i in range(3)]
        self.can_break = True
        self.shake = 0.0
        self.escape_t = 0.0
        self.guard_x = 700.0
        self.guard_dir = -1

    # ------------------------------------------------------------ logic
    def say(self, s):
        self.toast, self.toast_t = s, 1.6

    def choose(self, i):
        if i == 0:
            if self.money >= self.pay_cost:
                self.money -= self.pay_cost
                self.paid = self.pay_cost
                self.mode, self.mode_t = "out", 0.0
                _snd("unlock")
            else:
                self.say(f"Not enough money!  ({self.pay_cost} Tk needed)")
                _snd("back")
        elif i == 1:
            self.mode, self.mode_t = "wait", 0.0
            self.wait_left = self.wait_time
            _snd("click")
        else:
            if not self.can_break:
                self.say("Guard is watching - you can't break out now!")
                _snd("back")
                return
            self.mode, self.mode_t = "break", 0.0
            self.stage, self.prog, self.strikes = 0, 0.0, 0
            self.marker, self.speed, self.last = 0.0, 0.9, None
            _snd("click")

    def press_break(self):
        """BREAK button.  Return judge result ba None."""
        if self.mode != "break" or self.lock > 0:
            return None
        res = judge(self.marker_pos())
        self.last = (res, 0.0)
        self.prog = max(0.0, self.prog + GAIN[res])
        if res == BAD:
            self.strikes += 1
            self.guard_look = 1.4
            self.lock = 0.5
            self.shake = 0.3
            _snd("alarm", 0.5)
            if self.strikes >= STRIKES_MAX:
                self.mode, self.mode_t = "caught", 0.0
                self.can_break = False
                _snd("jail")
                return res
        else:
            self.shake = 0.18 if res == NORMAL else 0.3
            _snd("punch" if res == GOOD else "hit", 0.8)
        if self.prog >= 100.0:
            self.prog = 0.0
            self.stage += 1
            _snd("unlock")
            if self.stage >= len(STAGES):
                self.mode, self.mode_t = "escape", 0.0
            else:
                self.speed = 0.9 + self.stage * 0.18          # aro tez
        return res

    def marker_pos(self):
        return 0.5 - 0.5 * math.cos(self.marker * math.pi)   # 0..1, majhe 0.5

    # ------------------------------------------------------------ events
    def event(self, e):
        if self.mode == "menu":
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    self.sel = (self.sel - 1) % 3
                    _snd("hover")
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.sel = (self.sel + 1) % 3
                    _snd("hover")
                elif e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.choose(e.key - pygame.K_1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.choose(self.sel)
            elif e.type == pygame.MOUSEMOTION:
                for i, r in enumerate(self.opt_rects):
                    if r.collidepoint(e.pos) and self.sel != i:
                        self.sel = i
                        _snd("hover")
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(self.opt_rects):
                    if r.collidepoint(e.pos):
                        self.sel = i
                        self.choose(i)
        elif self.mode == "break":
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e, pygame.K_k):
                self.press_break()
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                self.press_break()          # jekhane chaple i BREAK (phone e shohoj)
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.mode, self.mode_t = "menu", 0.0
        elif self.mode == "wait":
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pass                          # 1 min dariye thakte hobe

    # ------------------------------------------------------------ update
    def update(self, dt):
        self.t += dt
        self.mode_t += dt
        self.toast_t = max(0.0, self.toast_t - dt)
        self.shake = max(0.0, self.shake - dt)
        self.lock = max(0.0, self.lock - dt)
        self.guard_look = max(0.0, self.guard_look - dt)
        if self.last:
            self.last = (self.last[0], self.last[1] + dt)
        # guard cell er bairer hnete beray
        self.guard_x += self.guard_dir * 38 * dt
        if self.guard_x < 560:
            self.guard_dir = 1
        if self.guard_x > 860:
            self.guard_dir = -1
        if self.mode == "wait":
            self.wait_left -= dt
            if self.wait_left <= 0:
                self.mode, self.mode_t = "out", 0.0
                _snd("unlock")
        elif self.mode == "break":
            self.marker += dt * self.speed
        elif self.mode == "caught":
            if self.mode_t > 2.4:
                self.mode, self.mode_t = "wait", 0.0
                self.wait_left = self.wait_time
        elif self.mode == "escape":
            if self.mode_t > 2.6:
                self.result = "free"
        elif self.mode == "out":
            if self.mode_t > 1.8:
                self.result = "free"

    # ------------------------------------------------------------ draw
    def _txt(self, surf, s, size, col, pos, center=True, shadow=True):
        img = get_font(size).render(s, True, col)
        r = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
        if shadow:
            sh = get_font(size).render(s, True, (0, 0, 0))
            surf.blit(sh, sh.get_rect(center=(pos[0] + 2, pos[1] + 2)) if center else (r.x + 2, r.y + 2))
        surf.blit(img, r)

    def _cell(self, surf, bars_broken=0, windows_broken=0, ninja_x=240, anim="idle"):
        SP.v_gradient(surf, pygame.Rect(0, 0, WIDTH, HEIGHT), (34, 36, 46), (12, 12, 20))
        # window (2 ta)
        for i in range(2):
            win = pygame.Rect(560 + i * 190, 60, 130, 100)
            broken = i < windows_broken
            pygame.draw.rect(surf, (10, 14, 38) if not broken else (40, 70, 130), win)
            pygame.draw.circle(surf, (230, 232, 210), (win.x + 90, win.y + 34), 14)
            pygame.draw.rect(surf, (80, 84, 96), win, 5)
            if not broken:
                for k in range(1, 4):
                    pygame.draw.line(surf, (130, 134, 150), (win.x + k * 32, win.y), (win.x + k * 32, win.bottom), 4)
            else:
                for k in range(5):
                    a = k * 1.3
                    pygame.draw.line(surf, (200, 230, 255), win.center,
                                     (win.centerx + math.cos(a) * 60, win.centery + math.sin(a) * 50), 2)
        pygame.draw.rect(surf, (110, 90, 70), (110, 360, 200, 18), border_radius=4)       # bench
        SP.draw_ninja(surf, ninja_x, 360, 1, self.t, anim)
        pygame.draw.rect(surf, (28, 28, 38), (0, 440, WIDTH, 100))
        # 3 ta cell bar group (protita 4 ta rod)
        for g in range(3):
            gx = 70 + g * 280
            broken = g < bars_broken
            for k in range(4):
                bx = gx + k * 56
                if broken and k in (1, 2):
                    continue                                        # bhanga - faka
                pygame.draw.rect(surf, (96, 100, 116), (bx, 0, 14, 440))
                pygame.draw.rect(surf, (170, 176, 196), (bx + 2, 0, 4, 440))
        pygame.draw.rect(surf, (60, 62, 74), (0, 120, WIDTH, 12))
        pygame.draw.rect(surf, (60, 62, 74), (0, 380, WIDTH, 12))

    def _guard(self, surf):
        facing = -1 if self.guard_dir < 0 else 1
        if self.guard_look > 0:
            facing = -1                                               # cell er dike ghure
        SP.draw_guard(surf, int(self.guard_x), 440, facing, self.t, "walk" if self.guard_look <= 0 else "aim", 0.7)
        if self.guard_look > 0:
            self._txt(surf, "WHAT WAS THAT?!", 20, (255, 120, 110), (int(self.guard_x), 270))

    def draw(self, surf):
        ox = oy = 0
        if self.shake > 0:
            ox, oy = random.uniform(-6, 6), random.uniform(-6, 6)
        canvas = surf
        if ox or oy:
            canvas = pygame.Surface((WIDTH, HEIGHT))
        m = self.mode
        if m == "menu":
            self._cell(canvas)
            self._guard(canvas)
            self._draw_menu(canvas)
        elif m == "wait":
            self._cell(canvas)
            self._guard(canvas)
            self._draw_wait(canvas)
        elif m == "break":
            bars = min(3, self.stage)
            wins = max(0, self.stage - 3)
            self._cell(canvas, bars, wins, anim="idle")
            self._guard(canvas)
            self._draw_break(canvas)
        elif m == "caught":
            self._cell(canvas)
            self._guard(canvas)
            dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim.fill((120, 0, 0, 90))
            canvas.blit(dim, (0, 0))
            self._txt(canvas, "GUARD CAUGHT YOU!", 54, (255, 90, 90), (WIDTH // 2, 200))
            self._txt(canvas, "Back to the cell  -  wait 1 MINUTE", 24, (255, 230, 230), (WIDTH // 2, 260))
        elif m == "escape":
            self._cell(canvas, 3, 2, ninja_x=240 + int(min(1.0, self.mode_t / 1.8) * 560), anim="walk")
            self._txt(canvas, "ESCAPED!", 64, (110, 255, 150), (WIDTH // 2, 200))
            self._txt(canvas, "You broke out of jail!", 24, (255, 255, 255), (WIDTH // 2, 262))
        elif m == "out":
            self._cell(canvas, 0, 0)
            if self.paid:
                self._txt(canvas, f"BAIL PAID:  -{self.paid} Tk", 40, (255, 220, 90), (WIDTH // 2, 200))
                self._txt(canvas, f"Money left:  {self.money} Tk", 28, (110, 240, 150), (WIDTH // 2, 252))
            else:
                self._txt(canvas, "1 MINUTE SERVED", 40, (230, 235, 255), (WIDTH // 2, 200))
            self._txt(canvas, "You are free.", 26, (255, 255, 255), (WIDTH // 2, 310))
        if canvas is not surf:
            surf.blit(canvas, (ox, oy))

    def _panel(self, surf, rect, border=(230, 90, 90), alpha=226):
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (6, 8, 16, alpha), bg.get_rect(), border_radius=16)
        pygame.draw.rect(bg, border + (255,), bg.get_rect(), 3, border_radius=16)
        surf.blit(bg, rect.topleft)

    def _draw_menu(self, surf):
        self._txt(surf, "ARRESTED!", 58, (255, 80, 90), (WIDTH // 2, 70))
        self._txt(surf, "Choose how to get out of JAIL", 24, (230, 235, 255), (WIDTH // 2, 130))
        can_pay = self.money >= self.pay_cost
        items = [("1  PAY BAIL", f"{self.pay_cost} Tk", f"You have {self.money} Tk",
                  (255, 220, 90) if can_pay else (130, 120, 90)),
                 ("2  WAIT", "1 MINUTE", "Do nothing - free for nothing", (120, 200, 255)),
                 ("3  BREAK OUT", "3 BARS + 2 WINDOWS", "Hit BREAK at the right time", (110, 255, 150)
                  if self.can_break else (110, 130, 120))]
        for i, (a, b, c, col) in enumerate(items):
            r = self.opt_rects[i]
            sel = i == self.sel
            rr = r.inflate(14, 14) if sel else r
            self._panel(surf, rr, border=col if sel else (96, 100, 130), alpha=235)
            self._txt(surf, a, 24, col, (rr.centerx, rr.y + 34))
            self._txt(surf, b, 26 if i != 2 else 20, (255, 255, 255), (rr.centerx, rr.y + 82))
            self._txt(surf, c, 15, (180, 188, 215), (rr.centerx, rr.y + 126))
        self._txt(surf, "LEFT / RIGHT + ENTER  (ba 1, 2, 3  ba tap)", 15, (150, 155, 180), (WIDTH // 2, 470))
        if self.toast_t > 0:
            self._txt(surf, self.toast, 24, (255, 130, 110), (WIDTH // 2, 505))

    def _draw_wait(self, surf):
        box = pygame.Rect(0, 0, 560, 170)
        box.center = (WIDTH // 2, 250)
        self._panel(surf, box, border=(120, 200, 255))
        self._txt(surf, "SERVING TIME", 30, (120, 200, 255), (WIDTH // 2, box.y + 38))
        left = max(0.0, self.wait_left)
        self._txt(surf, f"{int(left) // 60}:{int(left) % 60:02d}", 62, (255, 255, 255), (WIDTH // 2, box.y + 100))
        k = 1 - left / self.wait_time
        bar = pygame.Rect(box.x + 40, box.bottom - 26, box.w - 80, 10)
        pygame.draw.rect(surf, (40, 50, 80), bar, border_radius=5)
        pygame.draw.rect(surf, (120, 200, 255), (bar.x, bar.y, int(bar.w * k), bar.h), border_radius=5)

    def _draw_break(self, surf):
        label = STAGES[min(self.stage, len(STAGES) - 1)][0]
        self._txt(surf, "BREAK OUT!", 40, (110, 255, 150), (WIDTH // 2, 46))
        self._txt(surf, label, 24, (255, 255, 255), (WIDTH // 2, 86))
        # strikes
        for i in range(STRIKES_MAX):
            col = (255, 70, 70) if i < self.strikes else (70, 70, 90)
            pygame.draw.circle(surf, col, (60 + i * 30, 50), 11)
            pygame.draw.circle(surf, (230, 230, 240), (60 + i * 30, 50), 11, 2)
        self._txt(surf, "GUARD ALERT", 13, (190, 190, 210), (90, 76))
        # progress
        pr = pygame.Rect(WIDTH // 2 - 240, 380, 480, 18)
        pygame.draw.rect(surf, (30, 34, 52), pr, border_radius=9)
        pygame.draw.rect(surf, (110, 255, 150), (pr.x, pr.y, int(pr.w * min(1.0, self.prog / 100.0)), pr.h), border_radius=9)
        pygame.draw.rect(surf, (200, 210, 235), pr, 2, border_radius=9)
        # timing bar
        tb = pygame.Rect(WIDTH // 2 - 240, 410, 480, 22)
        pygame.draw.rect(surf, (200, 60, 60), tb, border_radius=6)
        nw = int(tb.w * 0.26)
        nr = pygame.Rect(0, tb.y, nw, tb.h)
        nr.centerx = tb.centerx
        pygame.draw.rect(surf, (240, 200, 70), nr)
        gw = int(tb.w * 0.10)
        gr = pygame.Rect(0, tb.y, gw, tb.h)
        gr.centerx = tb.centerx
        pygame.draw.rect(surf, (90, 240, 130), gr)
        pygame.draw.rect(surf, (240, 240, 250), tb, 2, border_radius=6)
        mx = tb.x + int(tb.w * self.marker_pos())
        pygame.draw.rect(surf, (255, 255, 255), (mx - 3, tb.y - 8, 6, tb.h + 16), border_radius=3)
        self._txt(surf, "BAD", 12, (255, 255, 255), (tb.x + 24, tb.centery), shadow=False)
        self._txt(surf, "NORMAL", 12, (30, 30, 30), (nr.x + 28, tb.centery), shadow=False)
        self._txt(surf, "GOOD", 12, (20, 40, 20), (gr.centerx, tb.centery), shadow=False)
        self._txt(surf, "BAD", 12, (255, 255, 255), (tb.right - 24, tb.centery), shadow=False)
        # BREAK button
        r = self.break_rect
        r.midtop = (WIDTH // 2, 452)
        down = self.lock > 0
        pygame.draw.rect(surf, (60, 60, 70) if down else (230, 70, 70), r, border_radius=16)
        pygame.draw.rect(surf, (255, 255, 255), r, 3, border_radius=16)
        self._txt(surf, "BREAK!", 34, (255, 255, 255), r.center)
        if self.last and self.last[1] < 1.0:
            res = self.last[0]
            col = {GOOD: (90, 240, 130), NORMAL: (240, 200, 70), BAD: (255, 80, 80)}[res]
            self._txt(surf, res + "!", 44, col, (WIDTH // 2, 330 - int(self.last[1] * 30)))
        self._txt(surf, "SPACE / ENTER / tap  =  BREAK", 14, (150, 155, 180), (WIDTH - 140, 520))
