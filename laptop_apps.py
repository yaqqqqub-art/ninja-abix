"""
laptop_apps.py - v9 update: laptop (ABIX OS 11) er notun app gulo.

  ABIX STORE  - free download store. Ekhane theke CALCULATOR ar NODEPAD download koro.
                Download hole app Desktop / Start menu / Taskbar e chole ashe (save file e thake).
  CALCULATOR  - mouse click ba keyboard (0-9 + - * / ( ) . Enter Backspace C).
  NODEPAD     - node style note board: "+ Node" diye note-node banao, drag kore sajao,
                "Link" diye duto node jora lagao, type kore lekho.

LaptopOS ei class ke inherit kore (class LaptopOS(ExtraApps)).
"""
import math
import re

import pygame

import sound

STORE_APPS = {
    "calc": {"name": "Calculator", "size": "1.2 MB",
             "desc": ["Add, subtract, multiply, divide.", "Mouse or keyboard."]},
    "nodepad": {"name": "NodePad", "size": "2.4 MB",
                "desc": ["Node style notes.", "Drag, link and type."]},
}

CALC_KEYS = [["C", "(", ")", "<"],
             ["7", "8", "9", "/"],
             ["4", "5", "6", "*"],
             ["1", "2", "3", "-"],
             ["0", ".", "=", "+"]]

NODE_W, NODE_H = 132, 58
MAX_NODES = 30
DL_TIME = 2.4            # download koto second nebe


class ExtraApps:
    # ------------------------------------------------------------------
    # state
    # ------------------------------------------------------------------
    def init_extra(self):
        cfg = self.cfg
        if not isinstance(cfg.get("installed"), list):
            cfg["installed"] = []
        if not isinstance(cfg.get("nodes"), list):
            cfg["nodes"] = []
        if not isinstance(cfg.get("links"), list):
            cfg["links"] = []
        self.dl = {}                                    # wid -> download progress 0..1
        self.calc = {"expr": "", "res": "", "done": False}
        self.nd = {"sel": None, "link": False, "from": None, "origin": (0, 0), "msg": ""}

    def installed(self, wid):
        return wid in self.cfg.get("installed", [])

    def update_extra(self, dt):
        for wid in list(self.dl):
            self.dl[wid] += dt / DL_TIME
            if self.dl[wid] >= 1.0:
                del self.dl[wid]
                if wid not in self.cfg["installed"]:
                    self.cfg["installed"].append(wid)
                self.toast(STORE_APPS[wid]["name"] + " downloaded  -  find it on your Desktop")
                sound.play("unlock", 0.5)
                self.persist()

    # ------------------------------------------------------------------
    # ABIX STORE
    # ------------------------------------------------------------------
    def store_download(self, wid, pos=None):
        if wid in self.dl or self.installed(wid):
            return
        self.dl[wid] = 0.0
        sound.play("hack", 0.5)

    def draw_store(self, surf, r, mouse):
        pygame.draw.rect(surf, (248, 249, 253), r)
        self.txt(surf, "ABIX STORE", (r.x + 16, r.y + 10), 22, (40, 46, 70), True)
        self.txt(surf, "Free downloads.  New apps appear on your Desktop, Start menu and Taskbar.",
                 (r.x + 16, r.y + 40), 12, (110, 116, 134))
        cw = (r.w - 16 * 3) // 2
        for i, wid in enumerate(STORE_APPS):
            info = STORE_APPS[wid]
            c = pygame.Rect(r.x + 16 + i * (cw + 16), r.y + 72, cw, r.h - 96)
            pygame.draw.rect(surf, (255, 255, 255), c, border_radius=12)
            pygame.draw.rect(surf, (210, 214, 228), c, 1, border_radius=12)
            self.app_icon(surf, wid, pygame.Rect(c.x + 16, c.y + 16, 56, 56))
            self.txt(surf, info["name"], (c.x + 86, c.y + 20), 18, (40, 46, 70), True)
            self.txt(surf, info["size"] + "   -   FREE", (c.x + 86, c.y + 44), 12, (110, 116, 134))
            for k, line in enumerate(info["desc"]):
                self.txt(surf, line, (c.x + 16, c.y + 90 + k * 18), 13, (70, 76, 96))
            b = pygame.Rect(c.x + 16, c.bottom - 50, c.w - 32, 34)
            if self.installed(wid):
                self.button(surf, b, "Open", lambda p, w=wid: self.open_win(w), mouse, (60, 170, 110))
            elif wid in self.dl:
                pygame.draw.rect(surf, (222, 226, 238), b, border_radius=8)
                pygame.draw.rect(surf, self.accent, (b.x, b.y, int(b.w * self.dl[wid]), b.h), border_radius=8)
                self.txt(surf, f"Downloading...  {int(self.dl[wid] * 100)}%", b.center, 13, (30, 34, 46), True,
                         anchor="center")
            else:
                self.button(surf, b, "Download", lambda p, w=wid: self.store_download(w), mouse)

    # ------------------------------------------------------------------
    # CALCULATOR
    # ------------------------------------------------------------------
    def calc_eval(self):
        c = self.calc
        ex = c["expr"].strip()
        if not ex:
            return
        if "**" in ex or not re.fullmatch(r"[0-9+\-*/(). %]+", ex):
            c["res"] = "Error"
            c["done"] = True
            return
        try:
            v = eval(ex, {"__builtins__": {}}, {})
            if isinstance(v, float):
                v = round(v, 10)
                if v == int(v) and abs(v) < 1e15:
                    v = int(v)
            c["res"] = str(v)[:18]
        except ZeroDivisionError:
            c["res"] = "Cannot divide by 0"
        except Exception:
            c["res"] = "Error"
        c["done"] = True
        sound.play("key", 0.4)

    def calc_press(self, ch, pos=None):
        c = self.calc
        if ch == "C":
            c["expr"], c["res"], c["done"] = "", "", False
        elif ch == "<":
            c["expr"] = c["expr"][:-1]
        elif ch == "=":
            self.calc_eval()
            return
        else:
            if c["done"]:
                # natija dekhar por: operator dile natija theke chalabe, onno kichu dile notun
                if ch in "+-*/" and c["res"] not in ("Error", "Cannot divide by 0", ""):
                    c["expr"] = c["res"]
                else:
                    c["expr"] = ""
                c["res"], c["done"] = "", False
            if len(c["expr"]) < 36:
                c["expr"] += ch
        sound.play("key", 0.3)

    def key_calc(self, e):
        if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.calc_press("=")
        elif e.key == pygame.K_BACKSPACE:
            self.calc_press("<")
        else:
            ch = getattr(e, "unicode", "")
            if ch in ("x", "X"):
                ch = "*"
            if ch in ("c", "C"):
                self.calc_press("C")
            elif ch and ch in "0123456789+-*/().":
                self.calc_press(ch)
            elif ch == "=":
                self.calc_press("=")

    def draw_calc(self, surf, r, mouse):
        pygame.draw.rect(surf, (236, 239, 247), r)
        disp = pygame.Rect(r.x + 8, r.y + 8, r.w - 16, 70)
        pygame.draw.rect(surf, (28, 32, 46), disp, border_radius=8)
        c = self.calc
        self.txt(surf, c["expr"][-30:] or "0", (disp.right - 10, disp.y + 8), 16, (160, 170, 195), mono=True,
                 anchor="topright")
        self.txt(surf, c["res"] if c["done"] else "", (disp.right - 10, disp.y + 32), 28, (255, 255, 255), True,
                 anchor="topright")
        gx, gy = r.x + 8, disp.bottom + 8
        gap = 6
        bw = (r.w - 16 - gap * 3) // 4
        bh = (r.bottom - 8 - gy - gap * 4) // 5
        for ri, row in enumerate(CALC_KEYS):
            for ci, ch in enumerate(row):
                b = pygame.Rect(gx + ci * (bw + gap), gy + ri * (bh + gap), bw, bh)
                if ch == "=":
                    col = self.accent
                elif ch in "+-*/":
                    col = (96, 106, 140)
                elif ch in "C(<)":
                    col = (150, 110, 110) if ch in "C<" else (120, 128, 150)
                else:
                    col = (70, 78, 104)
                self.button(surf, b, ch, lambda p, k=ch: self.calc_press(k), mouse, col, size=18)

    # ------------------------------------------------------------------
    # NODEPAD
    # ------------------------------------------------------------------
    def nd_new_id(self):
        return max([n["id"] for n in self.cfg["nodes"]] + [0]) + 1

    def nd_node(self, nid):
        for n in self.cfg["nodes"]:
            if n["id"] == nid:
                return n
        return None

    def nd_add(self, pos=None):
        if len(self.cfg["nodes"]) >= MAX_NODES:
            self.nd["msg"] = "Too many nodes (max %d)" % MAX_NODES
            return
        k = len(self.cfg["nodes"])
        nid = self.nd_new_id()
        self.cfg["nodes"].append({"id": nid, "x": 20 + (k % 5) * 40, "y": 16 + (k % 5) * 36, "t": f"Node {nid}"})
        self.nd["sel"] = nid
        sound.play("pop", 0.5)
        self.persist()

    def nd_delete(self, pos=None):
        sel = self.nd["sel"]
        if sel is None:
            return
        self.cfg["nodes"] = [n for n in self.cfg["nodes"] if n["id"] != sel]
        self.cfg["links"] = [l for l in self.cfg["links"] if sel not in l]
        self.nd["sel"] = None
        self.nd["from"] = None
        sound.play("back", 0.5)
        self.persist()

    def nd_clear(self, pos=None):
        self.cfg["nodes"], self.cfg["links"] = [], []
        self.nd.update(sel=None, **{"from": None})
        self.persist()

    def nd_toggle_link(self, pos=None):
        self.nd["link"] = not self.nd["link"]
        self.nd["from"] = None
        sound.play("click", 0.4)

    def nd_click_node(self, nid, pos):
        nd = self.nd
        n = self.nd_node(nid)
        if n is None:
            return
        nd["sel"] = nid
        if nd["link"]:
            a = nd["from"]
            if a is None:
                nd["from"] = nid
            elif a != nid:
                pair = sorted((a, nid))
                if pair in [sorted(l) for l in self.cfg["links"]]:
                    self.cfg["links"] = [l for l in self.cfg["links"] if sorted(l) != pair]    # abar click = link muche
                else:
                    self.cfg["links"].append(pair)
                nd["from"] = None
                sound.play("hack", 0.5)
                self.persist()
            return
        ox, oy = nd["origin"]
        self.drag = ("node", nid, pos[0] - (ox + n["x"]), pos[1] - (oy + n["y"]))

    def nd_drag(self, pos, d):
        n = self.nd_node(d[1])
        if n is None:
            return
        ox, oy = self.nd["origin"]
        cw, ch = self.nd.get("size", (560, 260))
        n["x"] = int(max(0, min(pos[0] - d[2] - ox, cw - NODE_W)))
        n["y"] = int(max(0, min(pos[1] - d[3] - oy, ch - NODE_H)))

    def key_nodepad(self, e):
        nd = self.nd
        n = self.nd_node(nd["sel"]) if nd["sel"] is not None else None
        if n is None:
            return
        if e.key == pygame.K_BACKSPACE:
            n["t"] = n["t"][:-1]
        elif e.key == pygame.K_DELETE:
            self.nd_delete()
        elif getattr(e, "unicode", "") and e.unicode.isprintable() and len(n["t"]) < 28:
            n["t"] += e.unicode
            sound.play("key", 0.3)

    def draw_nodepad(self, surf, r, mouse):
        nd = self.nd
        self.button(surf, (r.x + 8, r.y + 6, 84, 26), "+ Node", self.nd_add, mouse)
        self.button(surf, (r.x + 98, r.y + 6, 78, 26), "Link: ON" if nd["link"] else "Link", self.nd_toggle_link,
                    mouse, (90, 170, 110) if nd["link"] else (120, 130, 150))
        self.button(surf, (r.x + 182, r.y + 6, 74, 26), "Delete", self.nd_delete, mouse, (200, 90, 90),
                    enabled=nd["sel"] is not None)
        self.button(surf, (r.x + 262, r.y + 6, 64, 26), "Clear", self.nd_clear, mouse, (140, 140, 150))
        hint = nd["msg"] or ("Link mode: click two nodes (click again = unlink)" if nd["link"]
                             else "Click a node, then type.  Drag to move.")
        self.txt(surf, hint, (r.right - 10, r.y + 12), 12, (110, 116, 134), anchor="topright")
        area = pygame.Rect(r.x + 8, r.y + 40, r.w - 16, r.h - 48)
        nd["origin"] = (area.x, area.y)
        nd["size"] = (area.w, area.h)
        pygame.draw.rect(surf, (252, 253, 255), area, border_radius=6)
        pygame.draw.rect(surf, (200, 205, 218), area, 1, border_radius=6)
        for gx in range(area.x + 20, area.right, 28):                       # halka dot grid
            for gy in range(area.y + 14, area.bottom, 28):
                surf.set_at((gx, gy), (210, 214, 226))
        self.hit(area, lambda p: nd.update(sel=None, **{"from": None}))
        for a, b in self.cfg["links"]:
            na, nb = self.nd_node(a), self.nd_node(b)
            if na and nb:
                pa = (area.x + na["x"] + NODE_W // 2, area.y + na["y"] + NODE_H // 2)
                pb = (area.x + nb["x"] + NODE_W // 2, area.y + nb["y"] + NODE_H // 2)
                pygame.draw.line(surf, self.accent, pa, pb, 3)
        if not self.cfg["nodes"]:
            self.txt(surf, "Empty board.  Press  + Node", area.center, 16, (150, 156, 175), anchor="center")
        clip = surf.get_clip()
        surf.set_clip(area)
        for n in self.cfg["nodes"]:
            nr = pygame.Rect(area.x + n["x"], area.y + n["y"], NODE_W, NODE_H)
            sel = n["id"] == nd["sel"]
            pygame.draw.rect(surf, (255, 246, 200) if not sel else (255, 238, 160), nr, border_radius=10)
            pygame.draw.rect(surf, self.accent if sel else (190, 170, 110), nr, 3 if sel else 2, border_radius=10)
            if nd["from"] == n["id"]:
                pygame.draw.rect(surf, (90, 200, 120), nr.inflate(8, 8), 3, border_radius=12)
            pygame.draw.circle(surf, self.accent, (nr.x, nr.centery), 5)
            pygame.draw.circle(surf, self.accent, (nr.right, nr.centery), 5)
            t = n["t"]
            cur = "|" if sel and int(self.t * 2) % 2 == 0 else ""
            self.txt(surf, t[:14], (nr.x + 10, nr.y + 12), 14, (50, 46, 30), True)
            self.txt(surf, t[14:] + cur, (nr.x + 10, nr.y + 32), 14, (50, 46, 30), True)
            self.hit(nr, lambda p, i=n["id"]: self.nd_click_node(i, p))
        surf.set_clip(clip)

    # ------------------------------------------------------------------
    # icons (laptop.app_icon e jukto hoy)
    # ------------------------------------------------------------------
    def icon_extra(self, surf, wid, rect, col):
        c = rect.center
        u = rect.w / 44.0
        W = (255, 255, 255)
        if wid == "calc":
            pygame.draw.rect(surf, W, (c[0] - 12 * u, c[1] - 15 * u, 24 * u, 30 * u), border_radius=max(2, int(3 * u)))
            pygame.draw.rect(surf, col, (c[0] - 9 * u, c[1] - 12 * u, 18 * u, 7 * u), border_radius=2)
            for i in range(3):
                for j in range(3):
                    pygame.draw.circle(surf, col, (int(c[0] - 6 * u + i * 6 * u), int(c[1] + 1 * u + j * 6 * u)),
                                       max(1, int(1.8 * u)))
        elif wid == "nodepad":
            pts = [(c[0] - 12 * u, c[1] + 8 * u), (c[0], c[1] - 9 * u), (c[0] + 12 * u, c[1] + 8 * u)]
            pygame.draw.lines(surf, W, False, pts, max(2, int(2.5 * u)))
            for p in pts:
                pygame.draw.circle(surf, W, (int(p[0]), int(p[1])), max(3, int(5 * u)))
        elif wid == "store":
            pygame.draw.rect(surf, W, (c[0] - 14 * u, c[1] - 6 * u, 28 * u, 20 * u), border_radius=max(2, int(3 * u)))
            pygame.draw.arc(surf, W, (c[0] - 8 * u, c[1] - 16 * u, 16 * u, 18 * u), 0, math.pi, max(2, int(2.5 * u)))
            pygame.draw.polygon(surf, col, [(c[0] - 4 * u, c[1] + 1 * u), (c[0] + 4 * u, c[1] + 1 * u),
                                            (c[0], c[1] + 8 * u)])
