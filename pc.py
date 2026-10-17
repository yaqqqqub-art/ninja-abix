"""
pc.py - Tomar nijer GAMING PC (main menu theke).

  - Laptop er moto on hoy (boot, desktop, taskbar, Start menu, File Manager, Notepad, Settings...)
  - kintu PYTHON, AI, DETAIL AI, WIRE CONNECT app NEI - eigulo shudhu laptop e.
  - BROWSER (Google) chaple tomar asol PC browser e google.com khole.
  - NINJA RUN: ekta chhoto game (SPACE / W / click = laf).
  - Secret code:  143babyi<3u  ba  /godsummon  jekhanei (Notepad, Search...) likhle GOD MODE toggle hoy.
"""
import random
import types

import pygame

import laptop as LP
import lang
import sound

HIDDEN = ("py", "wire", "ai", "detail")

# "game" app ke laptop er table e boshai (shudhu PC er vis() e dekhay)
LP.NAME["game"] = "Ninja Run"
LP.COL["game"] = (235, 90, 70)
LP.SIZES["game"] = (640, 380)
LP.TITLES["game"] = "Ninja Run"

W, H, GROUND = 632, 340, 286          # game er virtual size (window er bhitor)


class GamingPC(LP.LaptopOS):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.g = {"state": "ready", "y": 0.0, "vy": 0.0, "obs": [], "speed": 280.0, "score": 0.0,
                  "spawn": 1.0, "best": int(self.cfg.get("run_best", 0)), "t": 0.0}

    # ---------- app list: game ta shudhu PC te ----------
    def vis(self, lst):
        base = super().vis(lst)
        if "game" not in base and lst in (LP.DESK, LP.TASKBAR, LP.START_TILES):
            base.insert(min(len(base), 4 if lst is not LP.TASKBAR else len(base)), "game")
        return base

    # ---------- Ninja Run ----------
    def run_jump(self, pos=None):
        g = self.g
        if g["state"] in ("ready", "over"):
            g.update(state="run", y=0.0, vy=0.0, obs=[], speed=280.0, score=0.0, spawn=1.0, t=0.0)
            sound.play("pop", 0.5)
        elif g["y"] <= 0.0:
            g["vy"] = 720.0
            sound.play("jump", 0.6)

    def key_game(self, e):
        if e.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
            self.run_jump()

    def step_game(self, dt):
        g = self.g
        if g["state"] != "run":
            return
        g["t"] += dt
        g["vy"] -= 1900.0 * dt
        g["y"] = max(0.0, g["y"] + g["vy"] * dt)
        if g["y"] == 0.0 and g["vy"] < 0:
            g["vy"] = 0.0
        g["speed"] = 280.0 + g["t"] * 9
        g["score"] += dt * 12
        g["spawn"] -= dt
        if g["spawn"] <= 0:
            g["obs"].append({"x": float(W + 20), "w": random.choice((22, 30, 40)), "h": random.choice((28, 40, 52))})
            g["spawn"] = random.uniform(0.85, 1.7) * (280.0 / g["speed"]) ** 0.5
        for o in g["obs"]:
            o["x"] -= g["speed"] * dt
        g["obs"] = [o for o in g["obs"] if o["x"] > -60]
        me = pygame.Rect(80, int(GROUND - 40 - g["y"]), 24, 40)
        for o in g["obs"]:
            if me.colliderect(pygame.Rect(int(o["x"]), GROUND - o["h"], o["w"], o["h"])):
                g["state"] = "over"
                sound.play("die", 0.7)
                best = max(g["best"], int(g["score"]))
                if best != g["best"]:
                    g["best"] = best
                    self.cfg["run_best"] = best
                    self.persist()
                break

    def update(self, dt):
        super().update(dt)
        w = self.wins.get("game")
        if w and w.get("open") and not w.get("min"):
            self.step_game(dt)
        elif self.g["state"] == "run":
            self.g["state"] = "over"

    def draw_game(self, surf, r, mouse):
        g = self.g
        pygame.draw.rect(surf, (18, 20, 34), r)
        for i in range(24):                                                  # tara
            x = r.x + (i * 97 + int(g["t"] * 20)) % r.w
            pygame.draw.circle(surf, (120, 125, 170), (x, r.y + 20 + (i * 53) % 150), 1)
        gy = r.y + GROUND
        pygame.draw.rect(surf, (40, 44, 70), (r.x, gy, r.w, r.bottom - gy))
        pygame.draw.line(surf, (110, 118, 160), (r.x, gy), (r.right, gy), 3)
        # ninja
        nx, ny = r.x + 80, int(gy - 40 - g["y"])
        pygame.draw.rect(surf, (26, 26, 40), (nx, ny + 8, 24, 32), border_radius=6)
        pygame.draw.circle(surf, (26, 26, 40), (nx + 12, ny + 8), 11)
        pygame.draw.rect(surf, (238, 200, 160), (nx + 5, ny + 4, 16, 6))
        pygame.draw.rect(surf, (225, 40, 60), (nx, ny - 1, 24, 4))
        if g["state"] == "run":
            pygame.draw.polygon(surf, (225, 40, 60), [(nx, ny), (nx - 14, ny - 3 + int(g["t"] * 40) % 5), (nx - 6, ny + 4)])
        for o in g["obs"]:                                                   # shapla / kata
            ox = r.x + int(o["x"])
            pts = [(ox, gy), (ox + o["w"] / 2, gy - o["h"]), (ox + o["w"], gy)]
            pygame.draw.polygon(surf, (200, 205, 225), pts)
            pygame.draw.polygon(surf, (110, 118, 160), pts, 2)
        self.txt(surf, f"{lang.tr('pc_score')}  {int(g['score'])}", (r.x + 14, r.y + 10), 18, (235, 240, 255), True)
        self.txt(surf, f"{lang.tr('pc_best')}  {g['best']}", (r.right - 14, r.y + 10), 16, (255, 215, 110), True, anchor="topright")
        if g["state"] == "ready":
            self.txt(surf, lang.tr("pc_game"), (r.centerx, r.y + 110), 34, (255, 255, 255), True, anchor="center")
            self.txt(surf, lang.tr("pc_tip"), (r.centerx, r.y + 150), 16, (170, 178, 210), anchor="center")
        elif g["state"] == "over":
            self.txt(surf, lang.tr("pc_over"), (r.centerx, r.y + 130), 26, (255, 120, 110), True, anchor="center")
        self.hit(r, self.run_jump)


def make_pc(save, save_fn):
    """PC ta banay. god code likhle save["god"] toggle hoy (level shuru hole GOD MODE chalu thake)."""
    world = types.SimpleNamespace(save=save, save_fn=save_fn)

    def god():
        save["god"] = not save.get("god", False)
        save_fn()
        return save["god"]

    info = lambda: {"scan": "gaming PC - no level is running", "goal": "Relax, play Ninja Run.",
                    "hint": "Open Ninja Run from the desktop.", "brief": "Goal: relax"}
    return GamingPC(lang.tr("pc_title"), [], info, god, lambda: None, world=world, free=True, hidden=HIDDEN)
