"""
laptop.py - ABIX OS 11: laptop er Windows 11 style screen.

Laptop kholar niyom: jekhane khushi  L  chaplei laptop khule jay  (ba Ctrl+Alt+Tab).
v9: L chaple laptop kothao khole, kintu terminal ta khulte hole terminal er SHAMNE jete hobe.
Terminal er shamne gele USB lagano 3D animation hoy, tarpor laptop on hoy.
Terminal er kache na thakle WIRE CONNECT / 'unlock all' kichu korbe na - "no terminal found" dekhabe.

NOTUN (v9):  ABIX STORE -> CALCULATOR ar NODEPAD download koro (Desktop / Start / Taskbar e ashe).

Taskbar (majhkhane frosted glass):  Start, Search, File Manager, Browser, Notepad, Settings,
Task Manager, Detail AI, Python.   (Abix AI Start menu / desktop e ache.)

  WIRE CONNECT - 3-4 ta tar thik port / node e jukto korle terminal khule jay.
  PYTHON        - hidden terminal: "unlock" likhle terminal khule jay.
  ABIX AI       - jeta khushi jiggesh koro.
  DETAIL AI     - live level scan (guard, camera, dog, star, cash ...).
  FILE MANAGER  - Documents / System_Hacks / Security_Logs, notun .txt file banano.
  NOTEPAD       - lekho, Ctrl+S dile save (game save file e thake).
  BROWSER       - sotti PC browser e google.com khole (game cholte thake).
  TASK MANAGER  - CPU / RAM / threads, alert process "End task" kora.
  SETTINGS      - display, sound slider, firewall, theme color.

Window: title bar e drag, minimize (-), close (x).  ESC ba Start > power = laptop bondho.
Laptop cholar somoy pura game pause thake (level1.World modal).
"""
import math
import os
import random
import re
import threading
import time
import webbrowser
from collections import deque

import pygame

import sound
from laptop_apps import ExtraApps, STORE_APPS
import tools as TL
import puzzles as PZ
from animation import WIDTH, HEIGHT

_FONTS = {}


def font(size, bold=False, mono=False):
    k = (size, bold, mono)
    if k not in _FONTS:
        names = "consolas,couriernew,dejavusansmono,monospace" if mono else "segoeui,arial,dejavusans,sans"
        _FONTS[k] = pygame.font.SysFont(names, size, bold=bold)
    return _FONTS[k]


def wrap(text, fnt, width):
    out = []
    for para in str(text).split("\n"):
        words, cur = para.split(" "), ""
        for w in words:
            tr = (cur + " " + w).strip()
            if fnt.size(tr)[0] <= width:
                cur = tr
            else:
                if cur:
                    out.append(cur)
                cur = w
        out.append(cur)
    return out


# ------------------------------------------------------------------
# AI brain (offline, rule based)
# ------------------------------------------------------------------
CONTROLS = ("A/D = move,  W/SPACE = jump,  J = knife,  H = hide,  K = super punch (4 s cooldown),  "
            "E = use selected tool / CODE LOCK keypad,  1-9 or Ctrl+Alt / TAB = tool wheel,  ESC = pause,  "
            "L (or Ctrl+Alt+Tab) = open the LAPTOP  (to unlock a terminal you must stand at it).")

TOOL_HELP = {
    "laser": "LASER BREAKER (key 1): stand near a laser grid or glass case, press E and type /TKDIAMONDLASER.",
    "hacker": "HACKER (key 2): stand near a CCTV camera / drone / sniper scope, press E and type /CAMERA01099.",
    "laptop": "LAPTOP: walk up to a locked terminal and press L (or E) - a USB is plugged in and the laptop powers on in 3D. Far from a terminal it only says NO TERMINAL FOUND. "
              "Open WIRE CONNECT and join 3-4 wires to the ports of the same color (or open PYTHON and type: unlock).",
    "emp": "EMP DISRUPTOR (key 4): press E - cameras, lasers, drones, turrets and snipers go dead for 5 s (16 s recharge).",
    "decoy": "DECOY DRONE (key 5): throws a noisy drone ahead of you. Guards and dogs go to investigate it (10 s recharge). "
             "Great for turning shield guards around.",
    "rewirer": "REWIRER PRO (key 6): near a laser grid / pressure plate / turret: short-circuit it. "
               "Rewired lasers and turrets kill GUARDS instead of you.",
    "smoke": "SMOKE BOMB (key 7): cloud for 3.5 s. Guards, cameras, snipers and dog scent cannot see you inside it. "
             "Blinds shield guards, so you can stab them from the front.",
    "thermite": "VAULT THERMITE (key 8): near a safe / reinforced door, press E: 2 second channel melts it.",
    "keycard": "MASTER KEYCARD (key 9): it does NOT work on CODE LOCKS any more. Find the PAGE (white paper) with the code "
               "in the level and type the code on the door's keypad (press E at the door).",
}


def tool_key_of(word):
    for tid, kws in (("laser", ("laser", "breaker")), ("hacker", ("hacker",)), ("laptop", ("laptop",)),
                     ("emp", ("emp", "disrupt")), ("decoy", ("decoy", "drone")), ("rewirer", ("rewire",)),
                     ("smoke", ("smoke",)), ("thermite", ("thermite", "melt")), ("keycard", ("keycard", "key card", "master"))):
        if any(k in word for k in kws):
            return tid
    return None


def ai_answer(q, info, detailed=False):
    s = q.strip().lower()
    if not s:
        return "Ask me anything about the heist."
    scan = ""
    if detailed and info:
        scan = ("LIVE SCAN  -  " + info.get("scan", "") + "\n")
    if "godsummon" in s or re.search(r"\bgod\b|cheat|secret", s):
        return "I have no records about that."
    if any(k in s for k in ("scan", "status", "intel", "report", "situation")):
        return scan or ("Open DETAIL AI for a full live scan. " + (info.get("brief", "") if info else ""))
    body = None
    if any(k in s for k in ("camera", "cctv", "rec ", "recording", "hack")) and "laptop" not in s:
        body = ("CCTV cameras record you in night-vision (LITE 3D). If a camera fills its REC bar, police arrive. "
                "Counter: select HACKER (key 2), stand near it, press E and type /CAMERA01099. "
                "Everything is paused while you type. EMP or SMOKE also blinds cameras.")
    elif "laser" in s and "grid" not in s or "tkdiamond" in s:
        body = TOOL_HELP["laser"] + "  EMP also switches lasers off for 5 s, REWIRER makes them kill guards."
    elif any(k in s for k in ("wire", "wiring", " port", "node")):
        body = ("WIRE CONNECT app: 3 or 4 wires on the left, ports on the right in a different order. Drag each wire "
                "(or click the wire, then the port) to the port of the SAME color. A wrong port = short circuit, try again. "
                "When all wires are connected the terminal UNLOCKS.")
    elif any(k in s for k in ("page", "code lock", "keypad", "door code", "keycard", "key card")) and "tool" not in s:
        body = ("Locked doors now have a CODE LOCK. The MASTER KEYCARD does not work on them. Look around the level for a PAGE "
                "(a white paper with a red dot) - walk over it to collect the 4-digit code. Then press E at the door and type "
                "the code on the keypad. Collected codes are also saved in Documents/pages.txt on this laptop.")
    elif any(k in s for k in ("unlock", "python", "terminal", "password", "pass code")) or ("code" in s and "laptop" in s):
        body = ("Walk up to the locked terminal and press L. A USB plugs in and the laptop turns on. Then open WIRE CONNECT and join "
                "the wires to the matching ports, or open the PYTHON app and type:  unlock   (unlock() or unlock all also work). "
                "Press ENTER. That's all.")
    elif any(k in s for k in ("notepad", "file manager", "files", "browser", "chrome", "settings", "task manager", "taskmanager")):
        body = ("The laptop is a mini Windows: FILE MANAGER keeps notes in Documents / System_Hacks / Security_Logs, "
                "NOTEPAD saves text with Ctrl+S, BROWSER opens google.com in your real browser, "
                "TASK MANAGER shows CPU/RAM and can End Task alert processes (25 s cooldown), "
                "SETTINGS has volume, firewall and theme colors.")
    elif any(k in s for k in ("open laptop", "hotkey", "ctrl+alt", "how to open", "terminal")):
        body = ("Press L (or Ctrl+Alt+Tab) to open the laptop. To unlock a terminal you must stand in front of it - far away the laptop says NO TERMINAL FOUND.")
    elif "code" in s:
        body = ("Codes:  CCTV hack = /CAMERA01099   |   lasers & glass = /TKDIAMONDLASER   |   "
                "laptop terminals = WIRE CONNECT app (or  unlock  in PYTHON)   |   door CODE LOCKS = collect the PAGE.")
    else:
        tid = tool_key_of(s)
        if tid and any(k in s for k in ("how", "what", "use", "tool", "key", "do", "work", "?")) or tid:
            if tid:
                body = TOOL_HELP[tid]
        if body is None and "tool" in s:
            body = "TOOLS:  " + "   ".join(f"{t['key']} {t['name']}" for t in TL.TOOLS)
        elif body is None and any(k in s for k in ("control", "move", "jump", "button", "keys", "how to play", "play")):
            body = CONTROLS
        elif body is None and any(k in s for k in ("guard", "enemy", "enemies", "soldier")):
            body = ("Guards patrol and shoot when they SEE you. J (knife) from behind or the front kills normal guards. "
                    "BOUNCERS need 2 hits or K. RIOT-SHIELD guards block frontal hits - go behind, use SMOKE or DECOY. "
                    "Dead bodies and noises make other guards investigate.")
        elif body is None and any(k in s for k in ("dog", "k9")):
            body = ("K9 dogs smell you even when you hide with H. Use SMOKE BOMB (key 7), a sarcophagus (museum), "
                    "or kill them with J / K. Their bite hurts.")
        elif body is None and "sniper" in s:
            body = "Snipers charge a red line, then shoot. Keep MOVING (the dot lags behind), hide with H, use SMOKE, EMP or hack their scope."
        elif body is None and "drone" in s:
            body = "Patrol drones have a downward spotlight. Jump and slash with J, EMP them, or hack them."
        elif body is None and "turret" in s:
            body = "Ceiling turrets charge a line then fire. REWIRER PRO makes them shoot guards for good; EMP disables them for 5 s."
        elif body is None and any(k in s for k in ("star", "collect")):
            body = "Each level has 3 hidden gold STARS on high ledges. Jump up the ledge chains to reach them."
        elif body is None and any(k in s for k in ("cash", "money", "tk", "reward")):
            body = "Cash drops give +100 Tk. Money is saved only when you win the level. Safes melted with THERMITE give bonus cash."
        elif body is None and any(k in s for k in ("checkpoint", "locker", "save")):
            body = "Walk into a safe LOCKER to set a checkpoint and refill health."
        elif body is None and any(k in s for k in ("police", "arrest", "bail", "jail")):
            body = ("If a camera records you, police arrest you. Pay bail (500 Tk or more) and keep playing, "
                    "or serve jail time if you cannot pay.")
        elif body is None and any(k in s for k in ("hide", "hiding")):
            body = "Press H to hide in shadows (guards can't see you, but dogs smell you). You cannot act while hidden."
        elif body is None and any(k in s for k in ("goal", "objective", "loot", "target", "exit", "win", "steal", "mission")):
            body = (info.get("goal", "Steal the loot and reach the exit.") if info else "Steal the loot and reach the exit.")
        elif body is None and any(k in s for k in ("hint", "help", "next", "what now", "where", "stuck", "tip", "level")):
            body = (info.get("hint", "") if info else "") or "Keep moving right, watch the hints at the top of the screen."
        elif body is None and any(k in s for k in ("who", "name", "hello", "hi ", "hey")) or s in ("hi", "hello", "hey"):
            body = "I'm ABIX AI, your heist assistant. Ask me about codes, tools, guards, this level - anything."
    if body is None:
        body = ("I can explain: codes, the 9 tools, controls, guards, dogs, cameras, lasers, stars, cash, police/bail, "
                "or this level's goal and next step. Try: 'what is the camera code?'")
    return scan + body



# ------------------------------------------------------------------
# Laptop OS  (ABIX OS 11)
# ------------------------------------------------------------------
THEMES = {"Blue": (60, 140, 250), "Purple": (150, 100, 240), "Green": (50, 190, 120),
          "Crimson": (225, 70, 90), "Orange": (240, 150, 50)}

APPS = [("files", "File Manager", (238, 184, 50)),
        ("browser", "Browser", (60, 150, 90)),
        ("notes", "Notepad", (80, 160, 225)),
        ("settings", "Settings", (110, 122, 145)),
        ("tasks", "Task Manager", (55, 115, 200)),
        ("detail", "Detail AI", (40, 170, 150)),
        ("py", "Python", (70, 130, 200)),
        ("wire", "Wire Connect", (230, 120, 60)),
        ("search", "Search", (95, 100, 125)),
        ("store", "Abix Store", (250, 140, 60)),
        ("calc", "Calculator", (70, 90, 130)),
        ("nodepad", "NodePad", (150, 100, 230)),
        ("ai", "Abix AI", (150, 90, 230))]
NAME = {a[0]: a[1] for a in APPS}
COL = {a[0]: a[2] for a in APPS}
TASKBAR = ["search", "files", "browser", "notes", "store", "calc", "nodepad", "settings", "tasks", "detail", "py", "wire"]
START_TILES = ["files", "browser", "notes", "store", "calc", "nodepad", "settings", "tasks", "detail", "py", "wire", "ai"]
DESK = ["files", "browser", "notes", "store", "tasks", "py", "wire", "detail", "ai", "settings", "calc", "nodepad"]
SIZES = {"wire": (640, 380), "py": (640, 320), "ai": (600, 320), "detail": (600, 320), "files": (650, 350),
         "notes": (600, 350), "tasks": (660, 350), "settings": (620, 340), "search": (480, 320),
         "store": (560, 330), "calc": (300, 392), "nodepad": (640, 380)}
TITLES = {"wire": "Wire Connect  -  security panel", "py": "Python 3.12  -  abix_terminal.py", "ai": "Abix AI", "detail": "Detail AI  -  live level scan",
          "files": "File Manager", "notes": "Notepad", "tasks": "Task Manager", "settings": "Settings",
          "search": "Search", "store": "Abix Store  -  free downloads", "calc": "Calculator", "nodepad": "NodePad"}
DARK_APPS = ("py",)
TASKBAR_H = 44

FOLDERS = ["Documents", "System_Hacks", "Security_Logs"]
LOGS = ("Security_Logs/security.log", "Security_Logs/access.log")
DEFAULT_FILES = {
    "Documents/welcome.txt": ("Welcome to ABIX OS 11.\n\nThis is your own notebook.\n"
                              "Open Notepad, write anything, press Ctrl+S to save.\n"
                              "Files stay saved even after you close the game."),
    "System_Hacks/readme.txt": ("HACK TOOLKIT\n\n- PYTHON app   : the terminal. Type your code there.\n"
                                "- DETAIL AI    : live scan of this level.\n"
                                "- ABIX AI      : ask anything about the heist.\n"
                                "- TASK MANAGER : End Task on alert processes."),
}

MAX_LINE = 66          # notepad: ekta line e max char
MAX_LINES = 400


def frost(surf, rect, tint=(26, 30, 44), alpha=150):
    """Frosted glass: niche ja ache tar blur + halka rong."""
    rect = pygame.Rect(rect).clip(surf.get_rect())
    if rect.w < 4 or rect.h < 4:
        return
    sub = surf.subsurface(rect).copy()
    small = pygame.transform.smoothscale(sub, (max(1, rect.w // 8), max(1, rect.h // 8)))
    blur = pygame.transform.smoothscale(small, rect.size)
    ov = pygame.Surface(rect.size, pygame.SRCALPHA)
    ov.fill(tint + (alpha,))
    blur.blit(ov, (0, 0))
    surf.blit(blur, rect.topleft)


def proc_mem_mb():
    """Ei game process er RAM (MB). psutil -> resource -> estimate."""
    try:
        import psutil
        return psutil.Process().memory_info().rss / 1048576.0
    except Exception:
        pass
    try:
        import resource
        kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return kb / 1024.0 if kb < 10 ** 8 else kb / 1048576.0
    except Exception:
        return 180.0


class LaptopOS(ExtraApps):
    def __init__(self, title, accept, info_fn, god_fn, done_fn, world=None, free=False, hidden=()):
        self.title = title
        self.hidden = set(hidden)     # PC te Python / AI app thake na
        self.secret = ""              # shesh lekha akkhor (secret code er jonno)
        self.free = free              # true = kono locked terminal nei (shudhu laptop)
        self.wire = PZ.WireGame()
        self.wire_ports = {}
        self.accept = [a.lower() for a in accept if a]
        self.info_fn, self.god_fn, self.done_fn = info_fn, god_fn, done_fn
        self.world = world
        sv = getattr(world, "save", None)
        self.save = sv if isinstance(sv, dict) else {}
        self.save_fn = getattr(world, "save_fn", None)
        cfg = self.save.setdefault("laptop", {})
        cfg.setdefault("files", {})
        cfg.setdefault("deleted", [])
        cfg.setdefault("theme", "Blue")
        cfg.setdefault("volume", sound.get_master())
        cfg.setdefault("firewall", True)
        self.cfg = cfg
        if cfg["theme"] not in THEMES:
            cfg["theme"] = "Blue"
        sound.set_master(cfg["volume"])
        self.init_extra()

        self.t = 0.0
        self.boot = 0.0
        self.key_flash = 0.0          # AUTO CODE WRITER likhle input line jole
        self.wire_fx = []             # wire connect er sparks [x, y, vx, vy, life, color]
        self.scr = pygame.Rect(66, 26, 828, 484)
        self.wins = {}            # id -> {"open","min","x","y"}
        self.order = []           # z-order (last = top)
        self.focus = None
        self.start = False
        self.done = False
        self.want_close = False
        self.prog = 0
        self.hot = []             # [(rect, fn)]  -  protita frame e notun kore banano click zone
        self.drag = None
        self.toasts = []          # [[text, time_left]]
        self.browser_t = 0.0
        self.fps = 60.0
        self.cpu, self.cpu_hist, self.mem_hist = 0.0, deque([0.0] * 60, maxlen=60), deque([0.0] * 60, maxlen=60)
        self._sa, self._cpu0, self._wall0 = 0.0, time.process_time(), time.perf_counter()
        self.mem = proc_mem_mb()
        self.wall = None
        self.wall_theme = None

        self.py_lines = ["Python 3.12.4 (abix-os)  [MSC v.1940 64 bit]",
                         f"Terminal: {title}",
                         "STATUS: NO LOCKED TERMINAL" if free else "STATUS: LOCKED",
                         "Type your code and press ENTER.  (help for hints)", ""]
        self.py_in = ""
        self.chat = {"ai": [("ai", "Hi, I'm ABIX AI. Ask me anything about the heist - codes, tools, guards, this level.")],
                     "detail": [("ai", "DETAIL AI online. I scan the level live. Ask: 'scan', 'what next', 'how do I unlock the terminal?'")]}
        self.chat_in = {"ai": "", "detail": ""}
        self.pending = {}         # id -> (timer, text)
        self.hist = []
        self.hist_i = 0
        # file manager / notepad / search / task manager / settings state
        self.fm = {"folder": "Documents", "sel": None, "new_in": None, "msg": "", "last": ("", -9.0)}
        self.np = {"path": None, "lines": [""], "r": 0, "c": 0, "top": 0, "dirty": False, "ro": False,
                   "name_in": None, "msg": ""}
        self.sr_in = ""
        self.tm = {"sel": None, "msg": ""}
        self.st = {"tab": "Display"}
        if "py" not in self.hidden:
            self.open_win("py")
        if not free and "wire" not in self.hidden:
            self.open_win("wire")      # wire puzzle shamne

    # ------------------------------------------------------------------
    @property
    def accent(self):
        return THEMES.get(self.cfg.get("theme"), THEMES["Blue"])

    def persist(self):
        if self.save_fn:
            try:
                self.save_fn()
            except Exception:
                pass

    def toast(self, text):
        self.toasts.append([text, 3.0])
        self.toasts = self.toasts[-3:]

    def hit(self, rect, fn):
        self.hot.append((pygame.Rect(rect), fn))

    # ------------------------------------------------------------------
    # virtual file system  (save["laptop"] e thake)
    # ------------------------------------------------------------------
    def fs_files(self):
        files = {p: t for p, t in DEFAULT_FILES.items() if p not in self.cfg["deleted"]}
        files.update(self.cfg["files"])
        pg = getattr(self.world, "pages", None)
        if pg:
            files["Documents/pages.txt"] = ("COLLECTED PAGES  (door code locks)\n\n"
                                            + "\n".join(f"- {lab}:  {code}" for lab, code in pg.values()))
        return files

    def fs_list(self, folder):
        names = {p.split("/", 1)[1] for p in self.fs_files() if p.startswith(folder + "/")}
        if folder == "Security_Logs":
            names |= {p.split("/", 1)[1] for p in LOGS}
        return sorted(names, key=str.lower)

    def fs_read(self, path):
        if path in LOGS:
            return self.make_log(path)
        return self.fs_files().get(path, "")

    def fs_write(self, path, text):
        if path in LOGS:
            return False
        self.cfg["files"][path] = text
        if path in self.cfg["deleted"]:
            self.cfg["deleted"].remove(path)
        self.persist()
        return True

    def fs_delete(self, path):
        if path in LOGS:
            return False
        self.cfg["files"].pop(path, None)
        if path in DEFAULT_FILES and path not in self.cfg["deleted"]:
            self.cfg["deleted"].append(path)
        self.persist()
        return True

    def make_log(self, path):
        info = self.info_fn() if self.info_fn else {}
        if not isinstance(info, dict):
            info = {}
        w = self.world
        now = time.strftime("%H:%M:%S")
        if path.endswith("security.log"):
            out = ["== SECURITY LOG ==", f"terminal : {self.title}", f"time     : {now}", "",
                   "[SCAN] " + str(info.get("scan", "n/a")),
                   f"[INFO] deaths this run : {getattr(w, 'run_deaths', 0)}",
                   f"[INFO] arrests this run: {getattr(w, 'arrests', 0)}"]
            alerts = w.os_alerts() if w is not None and hasattr(w, "os_alerts") else []
            if alerts:
                out += [f"[ALERT] {n} - {d}" for n, d, _ in alerts]
            else:
                out.append("[ OK ] no alert process is running")
            return "\n".join(out)
        return "\n".join(["== ACCESS LOG ==", f"[{now}] ABIX OS 11 booted",
                          f"[{now}] firewall: {'ACTIVE' if self.cfg['firewall'] else 'DISABLED'}",
                          f"[{now}] terminal status: {'UNLOCKED' if self.done else 'LOCKED'}",
                          f"[{now}] user: Ninja"])

    # ------------------------------------------------------------------
    # windows
    # ------------------------------------------------------------------
    def win_rect(self, wid):
        w = self.wins[wid]
        sw, sh = SIZES[wid]
        return pygame.Rect(w["x"], w["y"], sw, sh)

    def open_win(self, wid):
        if wid == "browser":
            self.launch_browser()
            return
        if wid in STORE_APPS and not self.installed(wid):
            self.toast(STORE_APPS[wid]["name"] + " is not installed  -  download it from Abix Store")
            wid = "store"
        w = self.wins.get(wid)
        if w is None:
            sw, sh = SIZES[wid]
            n = len(self.wins) % 4
            x = self.scr.centerx - sw // 2 + (n - 1) * 24
            y = self.scr.centery - 26 - sh // 2 + (n - 1) * 18
            x = max(self.scr.x + 4, min(x, self.scr.right - sw - 4))
            y = max(self.scr.y + 4, min(y, self.scr.bottom - TASKBAR_H - sh - 4))
            w = self.wins[wid] = {"open": False, "min": False, "x": x, "y": y}
        w["open"], w["min"] = True, False
        if wid in self.order:
            self.order.remove(wid)
        self.order.append(wid)
        self.focus = wid
        self.start = False
        sound.play("pop", 0.5)

    def close_win(self, wid):
        if wid in self.wins:
            self.wins[wid]["open"] = False
        if wid in self.order:
            self.order.remove(wid)
        self.focus = self.order[-1] if self.order else None
        sound.play("back", 0.5)

    def min_win(self, wid):
        self.wins[wid]["min"] = True
        if wid in self.order:
            self.order.remove(wid)
        self.focus = self.order[-1] if self.order else None
        sound.play("hover", 0.5)

    def raise_win(self, wid):
        self.focus = wid
        if wid in self.order:
            self.order.remove(wid)
        self.order.append(wid)
        self.start = False

    def begin_drag(self, wid, pos):
        self.raise_win(wid)
        r = self.win_rect(wid)
        self.drag = ("win", wid, pos[0] - r.x, pos[1] - r.y)

    def launch_browser(self):
        """Sotti PC browser e google.com. Alada thread - game kokhono atke ba crash kore na."""
        def _go():
            try:
                webbrowser.open("https://www.google.com")
            except Exception:
                pass
        threading.Thread(target=_go, daemon=True).start()
        self.browser_t = 2.5
        self.start = False
        self.toast("Opening your web browser...  (the game keeps running)")
        sound.play("pop", 0.5)

    def toggle_start(self, pos=None):
        self.start = not self.start
        sound.play("click", 0.5)

    def shutdown(self):
        """Laptop bondho howar somoy: Notepad er unsaved file (nam thakle) auto-save."""
        np = self.np
        if np["dirty"] and np["path"] and not np["ro"]:
            self.fs_write(np["path"], "\n".join(np["lines"]))
            np["dirty"] = False
        self.persist()

    # ------------------------------------------------------------------
    # events
    # ------------------------------------------------------------------
    def event(self, e):
        if self.done or self.boot < 1.8:
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.click(e.pos)
        elif e.type == pygame.MOUSEMOTION:
            self.motion(e.pos)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.release(e.pos)
        elif e.type == pygame.KEYDOWN:
            self.key(e)

    def click(self, pos):
        for rect, fn in reversed(self.hot):
            if rect.collidepoint(pos):
                if fn:
                    fn(pos)
                return

    def motion(self, pos):
        d = self.drag
        if not d:
            return
        if d[0] == "win":
            _, wid, dx, dy = d
            sw, sh = SIZES[wid]
            w = self.wins[wid]
            w["x"] = max(self.scr.x - sw + 80, min(pos[0] - dx, self.scr.right - 80))
            w["y"] = max(self.scr.y, min(pos[1] - dy, self.scr.bottom - TASKBAR_H - 34))
        elif d[0] == "vol":
            self.set_volume_from(pos[0], d[1])
        elif d[0] == "node":
            self.nd_drag(pos, d)

    def release(self, pos):
        d, self.drag = self.drag, None
        if d and d[0] == "vol":
            sound.play("pop", 0.6)
            self.persist()
        elif d and d[0] == "node":
            self.persist()
        elif d and d[0] == "wire":
            for j, pr in self.wire_ports.items():
                if pr.collidepoint(pos):
                    self.wire_try(d[1], j)
                    break

    def set_volume_from(self, x, track):
        v = (x - track.x) / max(1, track.w)
        v = max(0.0, min(1.0, v))
        self.cfg["volume"] = round(v, 2)
        sound.set_master(v)

    def vis(self, lst):
        """Hidden app bad diye list."""
        return [w for w in lst if w not in self.hidden and (w not in STORE_APPS or self.installed(w))
                and not (w == "store" and "store" in self.hidden)]

    def secret_code(self, e):
        """Jekhanei (notepad, search, python, chat...) 143babyi<3u likhle GOD MODE toggle hoy.
        PC te (Python nei) /godsummon likhleo hoy."""
        ch = getattr(e, "unicode", "")
        if not ch or not ch.isprintable():
            return
        self.secret = (self.secret + ch)[-24:].lower()
        hit = self.secret.endswith("143babyi<3u") or ("py" in self.hidden and self.secret.endswith("/godsummon"))
        if hit and self.god_fn:
            self.secret = ""
            on = self.god_fn()
            self.toast("GOD MODE " + ("ON" if on else "OFF"))
            sound.play("star")

    def key(self, e):
        self.secret_code(e)
        if self.start and e.key == pygame.K_RETURN:
            self.start = False
        wid = self.focus
        if wid is None:
            return
        fn = getattr(self, "key_" + wid, None)
        if fn:
            fn(e)

    # ---------- python ----------
    def key_py(self, e):
        if e.key == pygame.K_RETURN:
            self.run_py(self.py_in)
            self.py_in = ""
        elif e.key == pygame.K_BACKSPACE:
            self.py_in = self.py_in[:-1]
        elif e.key == pygame.K_UP and self.hist:
            self.hist_i = (self.hist_i - 1) % len(self.hist)
            self.py_in = self.hist[self.hist_i]
        elif getattr(e, "unicode", "") and e.unicode.isprintable() and len(self.py_in) < 60:
            self.py_in += e.unicode
            sound.play("key", 0.35)

    # ---------- AI chats ----------
    def key_chat(self, wid, e):
        if e.key == pygame.K_RETURN:
            q = self.chat_in[wid].strip()
            if q:
                self.chat[wid].append(("me", q))
                self.chat_in[wid] = ""
                info = self.info_fn() if self.info_fn else {}
                if not isinstance(info, dict):
                    info = {}
                self.pending[wid] = (0.55 + random.random() * 0.4, ai_answer(q, info, detailed=(wid == "detail")))
                sound.play("beep", 0.3)
        elif e.key == pygame.K_BACKSPACE:
            self.chat_in[wid] = self.chat_in[wid][:-1]
        elif getattr(e, "unicode", "") and e.unicode.isprintable() and len(self.chat_in[wid]) < 80:
            self.chat_in[wid] += e.unicode
            sound.play("key", 0.35)

    def key_ai(self, e):
        self.key_chat("ai", e)

    def key_detail(self, e):
        self.key_chat("detail", e)

    # ---------- search ----------
    def key_search(self, e):
        if e.key == pygame.K_RETURN:
            res = self.search_results()
            if res:
                res[0][2](None)
        elif e.key == pygame.K_BACKSPACE:
            self.sr_in = self.sr_in[:-1]
        elif getattr(e, "unicode", "") and e.unicode.isprintable() and len(self.sr_in) < 40:
            self.sr_in += e.unicode
            sound.play("key", 0.3)

    def search_results(self):
        q = self.sr_in.strip().lower()
        out = []
        for wid, name, _ in APPS:
            if wid != "search" and (not q or q in name.lower() or q in wid):
                out.append(("app", name, lambda p, w=wid: self.open_win(w), wid))
        if q:
            for path in sorted(self.fs_files()) + list(LOGS):
                if q in path.lower():
                    out.append(("file", path, lambda p, pa=path: self.np_open(pa), None))
        return out[:9]

    # ---------- file manager ----------
    def key_files(self, e):
        fm = self.fm
        if fm["new_in"] is not None:
            if e.key == pygame.K_RETURN:
                self.fm_create(fm["new_in"])
            elif e.key == pygame.K_BACKSPACE:
                fm["new_in"] = fm["new_in"][:-1]
            else:
                ch = getattr(e, "unicode", "")
                if ch and (ch.isalnum() or ch in " _-.") and len(fm["new_in"]) < 28:
                    fm["new_in"] += ch
                    sound.play("key", 0.3)
            return
        names = self.fs_list(fm["folder"])
        if e.key in (pygame.K_DOWN, pygame.K_UP) and names:
            i = names.index(fm["sel"]) if fm["sel"] in names else -1
            i = (i + (1 if e.key == pygame.K_DOWN else -1)) % len(names)
            fm["sel"] = names[i]
            sound.play("hover", 0.4)
        elif e.key == pygame.K_RETURN and fm["sel"]:
            self.np_open(fm["folder"] + "/" + fm["sel"])
        elif e.key == pygame.K_DELETE and fm["sel"]:
            self.fm_delete()

    def fm_select_folder(self, fo):
        self.fm.update(folder=fo, sel=None, new_in=None, msg="")
        sound.play("click", 0.4)

    def fm_row_click(self, name):
        fm = self.fm
        now = self.t
        if fm["sel"] == name and fm["last"][0] == name and now - fm["last"][1] < 0.5:
            self.np_open(fm["folder"] + "/" + name)
            return
        fm["sel"] = name
        fm["last"] = (name, now)
        sound.play("click", 0.3)

    def fm_start_new(self, pos=None):
        self.fm["new_in"] = ""
        self.fm["msg"] = "Type a name and press ENTER"

    def fm_cancel_new(self, pos=None):
        self.fm["new_in"] = None
        self.fm["msg"] = ""

    def fm_create(self, name):
        fm = self.fm
        name = re.sub(r"[^A-Za-z0-9 _.\-]", "", name).strip()
        if not name:
            fm["msg"] = "Name can't be empty"
            return
        if not name.lower().endswith(".txt"):
            name += ".txt"
        path = fm["folder"] + "/" + name
        if path in LOGS:
            fm["msg"] = "That name is reserved"
            return
        if name in self.fs_list(fm["folder"]):
            fm["msg"] = "A file with that name already exists"
            return
        self.fs_write(path, "")
        fm["new_in"] = None
        fm["sel"] = name
        fm["msg"] = "Created " + name
        sound.play("unlock", 0.4)
        self.np_open(path)

    def fm_delete(self, pos=None):
        fm = self.fm
        if not fm["sel"]:
            fm["msg"] = "Select a file first"
            return
        path = fm["folder"] + "/" + fm["sel"]
        if self.fs_delete(path):
            fm["msg"] = "Deleted " + fm["sel"]
            if self.np["path"] == path:
                self.np.update(path=None, lines=[""], r=0, c=0, top=0, dirty=False, ro=False)
            fm["sel"] = None
            sound.play("back", 0.5)
        else:
            fm["msg"] = "Read-only system log - can't delete"

    def fm_open_sel(self, pos=None):
        if self.fm["sel"]:
            self.np_open(self.fm["folder"] + "/" + self.fm["sel"])
        else:
            self.fm["msg"] = "Select a file first"

    # ---------- notepad ----------
    def np_open(self, path):
        np = self.np
        if np["dirty"] and np["path"] and not np["ro"]:
            self.fs_write(np["path"], "\n".join(np["lines"]))
        text = self.fs_read(path)
        lines = []
        for ln in text.split("\n"):                       # lomba line ke MAX_LINE e bhenge dei
            lines.extend([ln[i:i + MAX_LINE] for i in range(0, len(ln), MAX_LINE)] or [""])
        np.update(path=path, lines=lines or [""], r=0, c=0, top=0, dirty=False,
                  ro=(path in LOGS), name_in=None, msg="")
        self.open_win("notes")

    def np_new(self, pos=None):
        np = self.np
        if np["dirty"] and np["path"] and not np["ro"]:
            self.fs_write(np["path"], "\n".join(np["lines"]))
        np.update(path=None, lines=[""], r=0, c=0, top=0, dirty=False, ro=False, name_in=None, msg="New note")
        sound.play("pop", 0.4)

    def np_save(self, pos=None):
        np = self.np
        if np["ro"]:
            np["msg"] = "Read-only log"
            return
        if np["path"] is None:
            np["name_in"] = ""
            return
        self.fs_write(np["path"], "\n".join(np["lines"]))
        np["dirty"] = False
        np["msg"] = "Saved " + np["path"]
        sound.play("unlock", 0.4)

    def np_commit_name(self):
        np = self.np
        name = re.sub(r"[^A-Za-z0-9 _.\-]", "", np["name_in"]).strip()
        if not name:
            np["msg"] = "Name can't be empty"
            return
        if not name.lower().endswith(".txt"):
            name += ".txt"
        path = "Documents/" + name
        if path in LOGS:
            np["msg"] = "That name is reserved"
            return
        np["path"], np["name_in"] = path, None
        self.fm["folder"], self.fm["sel"] = "Documents", name
        self.np_save()

    def np_insert(self, ch):
        np = self.np
        line = np["lines"][np["r"]]
        if len(line) >= MAX_LINE:
            self.np_newline()
            line = np["lines"][np["r"]]
        np["lines"][np["r"]] = line[:np["c"]] + ch + line[np["c"]:]
        np["c"] += 1
        np["dirty"] = True

    def np_newline(self):
        np = self.np
        if len(np["lines"]) >= MAX_LINES:
            return
        line = np["lines"][np["r"]]
        np["lines"][np["r"]] = line[:np["c"]]
        np["lines"].insert(np["r"] + 1, line[np["c"]:])
        np["r"] += 1
        np["c"] = 0
        np["dirty"] = True

    def key_notes(self, e):
        np = self.np
        if np["name_in"] is not None:
            if e.key == pygame.K_RETURN:
                self.np_commit_name()
            elif e.key == pygame.K_BACKSPACE:
                np["name_in"] = np["name_in"][:-1]
            else:
                ch = getattr(e, "unicode", "")
                if ch and (ch.isalnum() or ch in " _-.") and len(np["name_in"]) < 28:
                    np["name_in"] += ch
                    sound.play("key", 0.3)
            return
        mod = getattr(e, "mod", 0)
        if e.key == pygame.K_s and mod & pygame.KMOD_CTRL:
            self.np_save()
            return
        k = e.key
        if k == pygame.K_LEFT:
            if np["c"] > 0:
                np["c"] -= 1
            elif np["r"] > 0:
                np["r"] -= 1
                np["c"] = len(np["lines"][np["r"]])
        elif k == pygame.K_RIGHT:
            if np["c"] < len(np["lines"][np["r"]]):
                np["c"] += 1
            elif np["r"] < len(np["lines"]) - 1:
                np["r"] += 1
                np["c"] = 0
        elif k == pygame.K_UP and np["r"] > 0:
            np["r"] -= 1
            np["c"] = min(np["c"], len(np["lines"][np["r"]]))
        elif k == pygame.K_DOWN and np["r"] < len(np["lines"]) - 1:
            np["r"] += 1
            np["c"] = min(np["c"], len(np["lines"][np["r"]]))
        elif k == pygame.K_HOME:
            np["c"] = 0
        elif k == pygame.K_END:
            np["c"] = len(np["lines"][np["r"]])
        elif np["ro"]:
            return
        elif k == pygame.K_RETURN:
            self.np_newline()
        elif k == pygame.K_BACKSPACE:
            if np["c"] > 0:
                ln = np["lines"][np["r"]]
                np["lines"][np["r"]] = ln[:np["c"] - 1] + ln[np["c"]:]
                np["c"] -= 1
                np["dirty"] = True
            elif np["r"] > 0:
                prev = np["lines"][np["r"] - 1]
                np["c"] = len(prev)
                np["lines"][np["r"] - 1] = prev + np["lines"][np["r"]]
                del np["lines"][np["r"]]
                np["r"] -= 1
                np["dirty"] = True
        elif k == pygame.K_DELETE:
            ln = np["lines"][np["r"]]
            if np["c"] < len(ln):
                np["lines"][np["r"]] = ln[:np["c"]] + ln[np["c"] + 1:]
                np["dirty"] = True
            elif np["r"] < len(np["lines"]) - 1:
                np["lines"][np["r"]] = ln + np["lines"][np["r"] + 1]
                del np["lines"][np["r"] + 1]
                np["dirty"] = True
        elif k == pygame.K_TAB:
            for _ in range(4):
                self.np_insert(" ")
        else:
            ch = getattr(e, "unicode", "")
            if ch and ch.isprintable():
                self.np_insert(ch)
                sound.play("key", 0.25)

    # ---------- task manager ----------
    def key_tasks(self, e):
        rows = self.proc_rows()
        if e.key in (pygame.K_DOWN, pygame.K_UP) and rows:
            names = [r["name"] for r in rows]
            i = names.index(self.tm["sel"]) if self.tm["sel"] in names else -1
            self.tm["sel"] = names[(i + (1 if e.key == pygame.K_DOWN else -1)) % len(names)]
        elif e.key in (pygame.K_DELETE, pygame.K_RETURN):
            self.tm_end_task()

    def proc_rows(self):
        w = self.world
        rows = []
        for i, (n, d, fn) in enumerate(w.os_alerts() if w is not None and hasattr(w, "os_alerts") else []):
            rows.append({"name": n, "kind": "ALERT", "desc": d, "kill": fn, "cpu": 4.0 + 6 * abs(math.sin(self.t * 2 + i))})
        guards = len([g for g in getattr(w, "guards", []) if g.alive])
        cams = len([c for c in getattr(w, "cams", []) if not getattr(c, "hacked", False)])
        dogs = len([d for d in getattr(w, "dogs", []) if d.alive])
        base = [("abix_ninja.exe", "App", f"pygame main loop  ({self.title[:22]})", self.cpu),
                ("level_process.exe", "Level process", "heist world simulation", 1.0 + self.cpu * 0.3),
                (f"guard_ai.exe  x{guards}", "Background", "guards patrolling", 0.6),
                (f"cctv_stream.exe  x{cams}", "Background", "cameras online", 0.4)]
        if dogs:
            base.append((f"k9_tracker.exe  x{dogs}", "Background", "dog scent tracking", 0.3))
        base += [("sound.py (mixer thread)", "Background", "audio", 0.2),
                 ("laptop_os.exe", "App", "ABIX OS 11", 0.5),
                 ("firewall.sys", "System", "ACTIVE" if self.cfg["firewall"] else "DISABLED", 0.1)]
        for i, (n, k, d, c) in enumerate(base):
            rows.append({"name": n, "kind": k, "desc": d, "kill": None, "cpu": c + 0.25 * abs(math.sin(self.t + i))})
        return rows

    def tm_end_task(self, pos=None):
        sel = self.tm["sel"]
        row = next((r for r in self.proc_rows() if r["name"] == sel), None)
        if row is None:
            self.tm["msg"] = "Select a process first"
            return
        if row["kill"] is None:
            self.tm["msg"] = "Access is denied  -  system process"
            sound.play("hover", 0.5)
            return
        w = self.world
        ok = w.kill_alert(row["kill"]) if w is not None and hasattr(w, "kill_alert") else (row["kill"]() or True)
        if ok:
            self.tm["msg"] = row["name"] + " terminated"
            self.tm["sel"] = None
        else:
            self.tm["msg"] = f"Cooling down  -  wait {w.kill_cd:.0f}s"
            sound.play("hover", 0.5)

    # ---------- settings ----------
    def toggle_fullscreen(self, pos=None):
        try:
            ok = pygame.display.toggle_fullscreen()
        except Exception:
            ok = 0
        self.toast("Fullscreen toggled" if ok else "Fullscreen is not supported on this display")

    def toggle_firewall(self, pos=None):
        self.cfg["firewall"] = not self.cfg["firewall"]
        self.persist()
        sound.play("click", 0.5)

    def set_theme(self, name):
        self.cfg["theme"] = name
        self.wall = None
        self.persist()
        sound.play("pop", 0.5)

    # ---------- python terminal ----------
    def out(self, *lines):
        self.py_lines.extend(lines)
        self.py_lines = self.py_lines[-60:]

    def run_py(self, raw):
        txt = raw.strip()
        self.out(">>> " + raw)
        if not txt:
            return
        self.hist.append(txt)
        self.hist_i = len(self.hist)
        low = txt.lower()
        norm = re.sub(r"\s+", " ", low).strip()
        if norm == "/godsummon":
            if self.god_fn:
                on = self.god_fn()
                self.out("[ * ]  GOD MODE " + ("ACTIVATED" if on else "DEACTIVATED"))
                sound.play("star")
            return
        if norm in ("unlock", "unlock()", "unlock all", "unlock(all)", "unlock('all')", 'unlock("all")', "unlock all()"):
            self.grant()
            return
        if self.accept and norm == self.accept[min(self.prog, len(self.accept) - 1)]:
            self.prog += 1
            self.out("OK")
            if self.prog >= len(self.accept):
                self.grant()
            sound.play("key", 0.5)
            return
        if norm in ("help", "help()", "?"):
            self.out("This terminal is LOCKED.  Write the right code to unlock it.",
                     "Don't know it?  Open ABIX AI and ask 'how do I unlock the terminal?'")
            return
        if norm in ("clear", "cls"):
            self.py_lines = []
            return
        if norm in ("exit", "exit()", "quit()"):
            self.close_win("py")
            return
        m = re.fullmatch(r"print\((.*)\)", txt)
        if m:
            arg = m.group(1).strip()
            if len(arg) >= 2 and arg[0] in "'\"" and arg[-1] == arg[0]:
                self.out(arg[1:-1])
                return
            if re.fullmatch(r"[0-9+\-*/(). %]+", arg):
                try:
                    self.out(str(eval(arg, {"__builtins__": {}}, {})))
                except Exception:
                    self.out("SyntaxError: invalid syntax")
                return
        if re.fullmatch(r"[0-9+\-*/(). %]+", txt):
            try:
                self.out(str(eval(txt, {"__builtins__": {}}, {})))
            except Exception:
                self.out("SyntaxError: invalid syntax")
            return
        word = re.match(r"[A-Za-z_]\w*", txt)
        if txt.startswith("/"):
            self.out("bash: " + txt.split()[0] + ": command not found")
        elif word:
            self.out(f"NameError: name '{word.group(0)}' is not defined")
        else:
            self.out("SyntaxError: invalid syntax")
        sound.play("hover", 0.5)

    def grant(self):
        if self.free:
            self.out("ERROR: no terminal found.", "unlock all does nothing here  -  walk up to a locked terminal first.")
            sound.play("lock", 0.5)
            return
        self.done = True
        self.out("Running...", "[OK] security.override()", "STATUS: UNLOCKED", "ACCESS GRANTED")
        sound.play("unlock")
        if self.done_fn:
            self.done_fn()

    # ------------------------------------------------------------------
    # update
    # ------------------------------------------------------------------
    def update(self, dt):
        self.t += dt
        self.boot += dt
        self.key_flash = max(0.0, self.key_flash - dt)
        for sp in self.wire_fx:
            sp[0] += sp[2] * dt
            sp[1] += sp[3] * dt
            sp[3] += 420 * dt
            sp[4] -= dt
        self.wire_fx = [sp for sp in self.wire_fx if sp[4] > 0]
        self.wire.update(dt)
        self.update_extra(dt)
        if dt > 0:
            self.fps = self.fps * 0.92 + (1.0 / dt) * 0.08
        self.browser_t = max(0.0, self.browser_t - dt)
        for tt in self.toasts:
            tt[1] -= dt
        self.toasts = [tt for tt in self.toasts if tt[1] > 0]
        self._sa += dt
        if self._sa >= 0.5:
            self._sa = 0.0
            wall, cpu = time.perf_counter(), time.process_time()
            used = (cpu - self._cpu0) / max(1e-3, wall - self._wall0) * 100.0 / max(1, os.cpu_count() or 1)
            self._cpu0, self._wall0 = cpu, wall
            self.cpu = max(0.5, min(99.0, used))
            self.mem = proc_mem_mb()
            self.cpu_hist.append(self.cpu)
            self.mem_hist.append(self.mem)
        for wid in list(self.pending):
            tm, txt = self.pending[wid]
            tm -= dt
            if tm <= 0:
                self.chat[wid].append(("ai", txt))
                del self.pending[wid]
                sound.play("pop", 0.4)
            else:
                self.pending[wid] = (tm, txt)

    # ------------------------------------------------------------------
    # drawing helpers
    # ------------------------------------------------------------------
    def txt(self, surf, s, pos, size=14, col=(30, 34, 46), bold=False, mono=False, anchor="topleft", maxw=None):
        f = font(size, bold, mono)
        s = str(s)
        if maxw and f.size(s)[0] > maxw:
            while len(s) > 1 and f.size(s + "...")[0] > maxw:
                s = s[:-1]
            s += "..."
        img = f.render(s, True, col)
        r = img.get_rect(**{anchor: pos})
        surf.blit(img, r)
        return r

    def button(self, surf, rect, label, fn, mouse, col=None, enabled=True, size=13):
        r = pygame.Rect(rect)
        base = col or self.accent
        if not enabled:
            c = (176, 180, 190)
        elif r.collidepoint(mouse):
            c = tuple(min(255, v + 28) for v in base)
        else:
            c = base
        pygame.draw.rect(surf, c, r, border_radius=6)
        self.txt(surf, label, r.center, size, (255, 255, 255), True, anchor="center")
        self.hit(r, fn if enabled else None)

    def make_wall(self):
        a = self.accent
        r = self.scr
        w = pygame.Surface(r.size)
        for y in range(r.h):
            k = y / r.h
            w.fill((int(a[0] * (0.10 + 0.25 * k)), int(a[1] * (0.12 + 0.30 * k)), int(a[2] * (0.20 + 0.40 * k))),
                   (0, y, r.w, 1))
        cx, cy = r.w // 2, r.h // 2 - 20
        cols = (a, (a[2], a[0], a[1]), (a[1], a[2], a[0]))
        for i in range(6):                                      # bloom petals
            ang = i * math.tau / 6 + 0.3
            pts = [(cx, cy)]
            for k in range(-6, 7):
                aa = ang + k * 0.07
                rad = 190 * (1 - abs(k) / 8)
                pts.append((cx + math.cos(aa) * rad, cy + math.sin(aa) * rad * 0.8))
            ps = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.polygon(ps, cols[i % 3] + (105,), pts)
            w.blit(ps, (0, 0))
        return w

    def app_icon(self, surf, wid, rect, small=False):
        col = COL[wid]
        pygame.draw.rect(surf, col, rect, border_radius=10 if not small else 8)
        c = rect.center
        u = rect.w / 44.0                 # unit: 44px icon er jonno design
        W = (255, 255, 255)
        if wid == "py":
            r = rect.w * 0.26
            pygame.draw.rect(surf, (255, 220, 70), (c[0] - r * 0.1, c[1] - r * 0.1, r * 1.3, r * 1.3), border_radius=int(r * 0.4))
            pygame.draw.rect(surf, (235, 240, 255), (c[0] - r * 1.2, c[1] - r * 1.2, r * 1.3, r * 1.3), border_radius=int(r * 0.4))
        elif wid == "ai":
            r = rect.w * 0.3
            pts = [(c[0], c[1] - r), (c[0] + r * 0.3, c[1] - r * 0.3), (c[0] + r, c[1]), (c[0] + r * 0.3, c[1] + r * 0.3),
                   (c[0], c[1] + r), (c[0] - r * 0.3, c[1] + r * 0.3), (c[0] - r, c[1]), (c[0] - r * 0.3, c[1] - r * 0.3)]
            pygame.draw.polygon(surf, W, pts)
        elif wid == "detail":                       # scan target
            pygame.draw.circle(surf, W, c, int(13 * u), max(2, int(2.5 * u)))
            pygame.draw.circle(surf, W, c, int(4.5 * u))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                pygame.draw.line(surf, W, (c[0] + dx * 13 * u, c[1] + dy * 13 * u), (c[0] + dx * 18 * u, c[1] + dy * 18 * u), max(2, int(2.5 * u)))
        elif wid == "search":                       # magnifier
            pygame.draw.circle(surf, W, (int(c[0] - 3 * u), int(c[1] - 3 * u)), int(10 * u), max(2, int(3 * u)))
            pygame.draw.line(surf, W, (c[0] + 4 * u, c[1] + 4 * u), (c[0] + 13 * u, c[1] + 13 * u), max(2, int(3.5 * u)))
        elif wid == "files":                        # folder
            pygame.draw.rect(surf, (255, 240, 170), (c[0] - 15 * u, c[1] - 12 * u, 13 * u, 7 * u), border_radius=3)
            pygame.draw.rect(surf, W, (c[0] - 15 * u, c[1] - 7 * u, 30 * u, 20 * u), border_radius=max(2, int(3 * u)))
        elif wid == "browser":                      # globe
            pygame.draw.circle(surf, W, c, int(15 * u), max(2, int(2.5 * u)))
            pygame.draw.ellipse(surf, W, (c[0] - 6 * u, c[1] - 15 * u, 12 * u, 30 * u), max(1, int(2 * u)))
            pygame.draw.line(surf, W, (c[0] - 15 * u, c[1]), (c[0] + 15 * u, c[1]), max(1, int(2 * u)))
        elif wid == "notes":                        # notepad page
            pygame.draw.rect(surf, W, (c[0] - 11 * u, c[1] - 15 * u, 22 * u, 30 * u), border_radius=max(2, int(3 * u)))
            for i in range(4):
                pygame.draw.line(surf, col, (c[0] - 7 * u, c[1] - 8 * u + i * 6 * u), (c[0] + 7 * u, c[1] - 8 * u + i * 6 * u), max(1, int(2 * u)))
        elif wid == "settings":                     # gear
            for i in range(8):
                a = i * math.tau / 8
                pygame.draw.line(surf, W, (c[0] + math.cos(a) * 9 * u, c[1] + math.sin(a) * 9 * u),
                                 (c[0] + math.cos(a) * 16 * u, c[1] + math.sin(a) * 16 * u), max(2, int(4 * u)))
            pygame.draw.circle(surf, W, c, int(11 * u))
            pygame.draw.circle(surf, col, c, int(5 * u))
        elif wid == "wire":                         # 2 node + tar
            pygame.draw.circle(surf, W, (int(c[0] - 12 * u), int(c[1] + 8 * u)), max(2, int(4.5 * u)))
            pygame.draw.circle(surf, W, (int(c[0] + 12 * u), int(c[1] - 8 * u)), max(2, int(4.5 * u)))
            pts = [(c[0] - 12 * u, c[1] + 8 * u), (c[0] - 3 * u, c[1] + 8 * u), (c[0] + 3 * u, c[1] - 8 * u), (c[0] + 12 * u, c[1] - 8 * u)]
            pygame.draw.lines(surf, W, False, pts, max(2, int(2.5 * u)))
        elif wid == "tasks":                        # pulse graph
            pygame.draw.rect(surf, W, (c[0] - 16 * u, c[1] - 14 * u, 32 * u, 28 * u), max(1, int(2 * u)), border_radius=3)
            pts = [(c[0] - 12 * u, c[1] + 4 * u), (c[0] - 5 * u, c[1] + 4 * u), (c[0] - 1 * u, c[1] - 8 * u),
                   (c[0] + 3 * u, c[1] + 8 * u), (c[0] + 7 * u, c[1]), (c[0] + 12 * u, c[1])]
            pygame.draw.lines(surf, W, False, pts, max(1, int(2 * u)))
        else:
            self.icon_extra(surf, wid, rect, col)

    # ------------------------------------------------------------------
    # draw
    # ------------------------------------------------------------------
    def draw(self, surf, mouse=None):
        mouse = mouse or pygame.mouse.get_pos()
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 205))
        surf.blit(dim, (0, 0))
        s = self.scr
        bz = s.inflate(24, 24)
        pygame.draw.rect(surf, (20, 22, 28), bz, border_radius=18)
        pygame.draw.rect(surf, (90, 94, 108), bz, 3, border_radius=18)
        if self.boot < 1.8:
            pygame.draw.rect(surf, (0, 0, 0), s)
            c = s.center
            for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                pygame.draw.rect(surf, (0, 140, 240), (c[0] + dx * 22 - (0 if dx > 0 else 40) + (2 if dx > 0 else 0),
                                                       c[1] + dy * 22 - (0 if dy > 0 else 40) + (2 if dy > 0 else 0), 40, 40))
            for k in range(8):
                a = self.t * 6 - k * 0.5
                pygame.draw.circle(surf, (255, 255, 255), (int(c[0] + math.cos(a) * 20), int(c[1] + 110 + math.sin(a) * 20)), 3)
            f = font(18).render("ABIX OS 11  -  starting...", True, (210, 220, 240))
            surf.blit(f, f.get_rect(center=(c[0], c[1] + 160)))
            bar = pygame.Rect(0, 0, 260, 8)
            bar.center = (c[0], c[1] + 190)
            pygame.draw.rect(surf, (30, 36, 56), bar, border_radius=4)
            pygame.draw.rect(surf, (0, 160, 255), (bar.x, bar.y, int(bar.w * min(1.0, self.boot / 1.8)), bar.h), border_radius=4)
            self.draw_cursor(surf, mouse)
            return
        self.hot = []
        clip = surf.get_clip()
        surf.set_clip(s)
        if self.wall is None:
            self.wall = self.make_wall()
        surf.blit(self.wall, s.topleft)
        # desktop icons (2 column)
        for i, wid in enumerate(self.vis(DESK)):
            col, row = divmod(i, 5)
            r = pygame.Rect(s.x + 10 + col * 92, s.y + 12 + row * 84, 88, 80)
            if r.collidepoint(mouse):
                hl = pygame.Surface(r.size, pygame.SRCALPHA)
                pygame.draw.rect(hl, (255, 255, 255, 40), hl.get_rect(), border_radius=8)
                surf.blit(hl, r.topleft)
            self.app_icon(surf, wid, pygame.Rect(r.centerx - 22, r.y + 6, 44, 44))
            self.txt(surf, NAME[wid], (r.centerx, r.y + 56), 12, (255, 255, 255), anchor="midtop")
            self.hit(r, lambda p, w=wid: self.open_win(w))
        # windows
        for wid in list(self.order):
            if self.wins[wid]["open"] and not self.wins[wid]["min"]:
                self.draw_window(surf, wid, mouse)
        # start menu
        if self.start:
            self.hit(s, lambda p: setattr(self, "start", False))
            self.draw_start(surf, mouse)
        self.draw_taskbar(surf, mouse)
        self.draw_toasts(surf)
        if self.done:
            ov = pygame.Surface(s.size, pygame.SRCALPHA)
            ov.fill((0, 40, 10, 90))
            surf.blit(ov, s.topleft)
            f = font(40, True).render("ACCESS GRANTED", True, (90, 255, 150))
            surf.blit(f, f.get_rect(center=(s.centerx, s.centery)))
        surf.set_clip(clip)
        self.draw_cursor(surf, mouse)

    def draw_toasts(self, surf):
        tb = pygame.Rect(self.scr.x, self.scr.bottom - TASKBAR_H, self.scr.w, TASKBAR_H)
        y = tb.y - 10
        for text, tl in reversed(self.toasts):
            f = font(13)
            w = f.size(text)[0] + 28
            r = pygame.Rect(0, 0, w, 32)
            r.bottomright = (tb.right - 12, y)
            frost(surf, r, (24, 28, 40), 190)
            pygame.draw.rect(surf, self.accent, r, 1, border_radius=8)
            self.txt(surf, text, (r.x + 14, r.y + 8), 13, (235, 240, 250))
            y -= 38

    # ---------- taskbar ----------
    def taskbar_rects(self):
        tb = pygame.Rect(self.scr.x, self.scr.bottom - TASKBAR_H, self.scr.w, TASKBAR_H)
        n = 1 + len(self.vis(TASKBAR))
        x0 = tb.centerx - (n * 44) // 2
        start = pygame.Rect(x0, tb.y + 4, 40, 36)
        apps = {wid: pygame.Rect(x0 + 44 * (i + 1), tb.y + 4, 40, 36) for i, wid in enumerate(self.vis(TASKBAR))}
        return tb, start, apps

    def tb_app_click(self, wid):
        w = self.wins.get(wid)
        if wid == "browser":
            self.launch_browser()
        elif w and w["open"] and not w["min"] and self.focus == wid:
            self.min_win(wid)
        else:
            self.open_win(wid)

    def draw_taskbar(self, surf, mouse):
        tb, st, apps = self.taskbar_rects()
        frost(surf, tb, (24, 28, 42), 150)                       # frosted glass bar
        pygame.draw.line(surf, (120, 130, 160), tb.topleft, tb.topright)
        self.hit(tb, None)
        # left widget (weather)
        pygame.draw.circle(surf, (250, 220, 110), (tb.x + 22, tb.y + 22), 9)
        pygame.draw.circle(surf, (40, 46, 70), (tb.x + 26, tb.y + 19), 8)
        self.txt(surf, "21°C", (tb.x + 38, tb.y + 7), 13, (235, 240, 250), True)
        self.txt(surf, "Clear night", (tb.x + 38, tb.y + 24), 11, (170, 180, 200))
        # start
        if st.collidepoint(mouse) or self.start:
            pygame.draw.rect(surf, (80, 88, 118), st, border_radius=6)
        for dx in (0, 1):
            for dy in (0, 1):
                pygame.draw.rect(surf, self.accent, (st.centerx - 9 + dx * 10, st.centery - 9 + dy * 10, 8, 8), border_radius=1)
        self.hit(st, self.toggle_start)
        for wid, r in apps.items():
            w = self.wins.get(wid)
            active = bool(w and w["open"] and self.focus == wid and not w["min"])
            if r.collidepoint(mouse) or active:
                pygame.draw.rect(surf, (80, 88, 118), r, border_radius=6)
            self.app_icon(surf, wid, pygame.Rect(r.centerx - 13, r.centery - 13, 26, 26), small=True)
            if (w and w["open"]) or (wid == "browser" and self.browser_t > 0):
                pygame.draw.line(surf, self.accent if active else (150, 160, 185), (r.centerx - 8, r.bottom - 2), (r.centerx + 8, r.bottom - 2), 3)
            self.hit(r, lambda p, wd=wid: self.tb_app_click(wd))
        # tray: wifi, speaker, battery, clock + date
        x = tb.right - 118
        for k in range(3):
            pygame.draw.arc(surf, (225, 230, 245), (x - 8 - k * 4, tb.y + 22 - k * 4, 16 + k * 8, 14 + k * 8), 0.9, 2.25, 2)
        pygame.draw.circle(surf, (225, 230, 245), (x, tb.y + 26), 2)
        vol = self.cfg.get("volume", 0.8)
        sx = x - 34
        pygame.draw.polygon(surf, (225, 230, 245), [(sx, tb.y + 19), (sx + 5, tb.y + 19), (sx + 10, tb.y + 14),
                                                    (sx + 10, tb.y + 30), (sx + 5, tb.y + 25), (sx, tb.y + 25)])
        if vol > 0.02:
            pygame.draw.arc(surf, (225, 230, 245), (sx + 6, tb.y + 16, 12, 12), -0.9, 0.9, 2)
        bx = x - 62
        pygame.draw.rect(surf, (225, 230, 245), (bx, tb.y + 17, 18, 10), 2, border_radius=2)
        pygame.draw.rect(surf, (225, 230, 245), (bx + 3, tb.y + 20, 9, 4))
        now = time.localtime()
        self.txt(surf, time.strftime("%I:%M %p", now).lstrip("0"), (tb.right - 10, tb.y + 6), 13, (235, 240, 250), anchor="topright")
        self.txt(surf, time.strftime("%m/%d/%Y", now), (tb.right - 10, tb.y + 23), 12, (190, 198, 215), anchor="topright")

    # ---------- start ----------
    def start_menu_rects(self):
        tb, st, apps = self.taskbar_rects()
        m = pygame.Rect(0, 0, 580, 370)
        m.midbottom = (tb.centerx, tb.y - 8)
        tiles = {}
        for i, wid in enumerate(self.vis(START_TILES)):
            col, row = i % 5, i // 5
            tiles[wid] = pygame.Rect(m.x + 24 + col * 108, m.y + 96 + row * 104, 100, 96)
        power = pygame.Rect(m.right - 56, m.bottom - 50, 36, 34)
        search = pygame.Rect(m.x + 24, m.y + 20, m.w - 48, 34)
        return m, tiles, power, search

    def draw_start(self, surf, mouse):
        m, tiles, power, search = self.start_menu_rects()
        frost(surf, m, (30, 34, 52), 200)
        pygame.draw.rect(surf, (110, 120, 150), m, 2, border_radius=2)
        self.hit(m, None)
        pygame.draw.rect(surf, (54, 60, 84), search, border_radius=17)
        self.txt(surf, "Type here to search", (search.x + 42, search.y + 8), 14, (170, 180, 200))
        pygame.draw.circle(surf, (170, 180, 200), (search.x + 22, search.y + 16), 6, 2)
        self.hit(search, lambda p: self.open_win("search"))
        self.txt(surf, "Pinned", (m.x + 26, m.y + 68), 14, (235, 240, 250), True)
        for wid, r in tiles.items():
            if r.collidepoint(mouse):
                pygame.draw.rect(surf, (66, 74, 104), r, border_radius=8)
            self.app_icon(surf, wid, pygame.Rect(r.centerx - 22, r.y + 8, 44, 44))
            self.txt(surf, NAME[wid], (r.centerx, r.y + 62), 13, (235, 240, 250), anchor="midtop")
            self.hit(r, lambda p, w=wid: self.open_win(w))
        pygame.draw.line(surf, (80, 88, 116), (m.x + 20, m.bottom - 62), (m.right - 20, m.bottom - 62))
        pygame.draw.circle(surf, self.accent, (m.x + 40, m.bottom - 32), 14)
        self.txt(surf, "Ninja", (m.x + 62, m.bottom - 40), 14, (235, 240, 250))
        pygame.draw.rect(surf, (66, 74, 104) if power.collidepoint(mouse) else (50, 56, 80), power, border_radius=8)
        pygame.draw.arc(surf, (235, 240, 250), power.inflate(-14, -14), 0.9, 8.4, 2)
        pygame.draw.line(surf, (235, 240, 250), (power.centerx, power.centery - 11), (power.centerx, power.centery - 2), 2)
        self.hit(power, lambda p: setattr(self, "want_close", True))

    # ---------- windows ----------
    def draw_window(self, surf, wid, mouse):
        r = self.win_rect(wid)
        sh = pygame.Surface((r.w + 24, r.h + 24), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 80), sh.get_rect(), border_radius=16)
        surf.blit(sh, (r.x - 12, r.y - 6))
        dark = wid in DARK_APPS
        pygame.draw.rect(surf, (30, 30, 34) if dark else (243, 245, 250), r, border_radius=10)
        bar = pygame.Rect(r.x, r.y, r.w, 34)
        pygame.draw.rect(surf, (44, 46, 54) if dark else (230, 234, 244), bar, border_top_left_radius=10, border_top_right_radius=10)
        # hit zones: window body (focus), titlebar drag, min, close
        self.hit(r, lambda p, w=wid: self.raise_win(w))
        self.hit(bar, lambda p, w=wid: self.begin_drag(w, p))
        self.app_icon(surf, wid, pygame.Rect(r.x + 10, r.y + 7, 20, 20), small=True)
        tcol = (235, 238, 245) if dark else (30, 34, 46)
        title = TITLES[wid]
        if wid == "notes":
            title = (self.np["path"].split("/")[-1] if self.np["path"] else "Untitled") + ("*" if self.np["dirty"] else "") + " - Notepad"
        self.txt(surf, title, (r.x + 40, r.y + 8), 14, tcol)
        mn = pygame.Rect(r.right - 92, r.y, 46, 34)
        cl = pygame.Rect(r.right - 46, r.y, 46, 34)
        if mn.collidepoint(mouse):
            pygame.draw.rect(surf, (90, 96, 112) if dark else (205, 210, 225), mn)
        if cl.collidepoint(mouse):
            pygame.draw.rect(surf, (210, 50, 60), cl, border_top_right_radius=10)
        pygame.draw.line(surf, tcol, (mn.centerx - 6, mn.centery), (mn.centerx + 6, mn.centery), 2)
        xc = (255, 255, 255) if cl.collidepoint(mouse) else tcol
        pygame.draw.line(surf, xc, (cl.centerx - 6, cl.centery - 6), (cl.centerx + 6, cl.centery + 6), 2)
        pygame.draw.line(surf, xc, (cl.centerx - 6, cl.centery + 6), (cl.centerx + 6, cl.centery - 6), 2)
        self.hit(mn, lambda p, w=wid: self.min_win(w))
        self.hit(cl, lambda p, w=wid: self.close_win(w))
        pygame.draw.rect(surf, self.accent if self.focus == wid else (150, 154, 170), r, 2, border_radius=10)
        inner = pygame.Rect(r.x + 4, r.y + 36, r.w - 8, r.h - 40)
        if wid == "py":
            self.draw_py(surf, inner)
        elif wid in ("ai", "detail"):
            self.draw_chat(surf, inner, wid, COL[wid])
        else:
            getattr(self, "draw_" + wid)(surf, inner, mouse)

    # ---------- wire connecting ----------
    def wire_new(self, pos=None):
        self.wire.reset()
        sound.play("pop", 0.5)

    def wire_grab(self, i, pos):
        g = self.wire
        if g.solved or i in g.link:
            return
        g.sel = i
        g.cursor = pos
        self.drag = ("wire", i)
        sound.play("key", 0.4)

    def wire_click_port(self, j, pos=None):
        g = self.wire
        if g.sel is not None:
            self.wire_try(g.sel, j)

    def wire_try(self, i, j):
        g = self.wire
        res = g.connect(i, j)
        if res == "ok":
            pr = self.wire_ports.get(j)
            if pr is not None:                                  # connect hole spark
                col = g.color(g.cols[i])
                for _ in range(26):
                    self.wire_fx.append([pr.centerx, pr.centery, random.uniform(-220, 220), random.uniform(-260, 80),
                                         random.uniform(0.35, 0.8), col])
            sound.play("hack", 0.6)
            if g.solved:
                self.wire_solved()
        elif res == "wrong":
            sound.play("zap", 0.6)
        elif res == "used":
            sound.play("hover", 0.5)

    def wire_solved(self):
        if self.free:
            self.toast("Wiring OK  -  but no terminal found. Go to a terminal first")
            sound.play("unlock", 0.5)
        elif not self.done:
            self.out("[ * ]  WIRE CONNECT: all wires connected")
            self.grant()

    def draw_wire(self, surf, r, mouse):
        g = self.wire
        pygame.draw.rect(surf, (24, 28, 38), r)
        self.txt(surf, "SECURITY PANEL  -  WIRE CONNECTING", (r.x + 16, r.y + 10), 16, (235, 238, 248), True)
        mc = (110, 240, 150) if g.solved else ((255, 120, 120) if g.shake > 0 else (170, 180, 205))
        self.txt(surf, g.msg, (r.x + 16, r.y + 36), 13, mc)
        n = g.n
        gap = 58 if n >= 4 else 76
        top = r.y + 104
        lx, rx = r.x + 60, r.right - 60
        sh = int(math.sin(self.t * 70) * 5) if g.shake > 0 else 0
        for bx in (pygame.Rect(r.x + 16, top - 38, 44, gap * (n - 1) + 76),
                   pygame.Rect(r.right - 60 + sh, top - 38, 44, gap * (n - 1) + 76)):
            pygame.draw.rect(surf, (46, 52, 70), bx, border_radius=8)
            pygame.draw.rect(surf, (96, 104, 130), bx, 2, border_radius=8)

        def wire_pts(a, b):
            pts = []
            for k in range(21):
                u = k / 20.0
                c1, c2 = (a[0] + 130, a[1]), (b[0] - 130, b[1])
                x = (1 - u) ** 3 * a[0] + 3 * (1 - u) ** 2 * u * c1[0] + 3 * (1 - u) * u * u * c2[0] + u ** 3 * b[0]
                y = (1 - u) ** 3 * a[1] + 3 * (1 - u) ** 2 * u * c1[1] + 3 * (1 - u) * u * u * c2[1] + u ** 3 * b[1]
                pts.append((x, y))
            return pts

        left = [(lx, top + i * gap) for i in range(n)]
        right = [(rx + sh, top + j * gap) for j in range(n)]
        for i, j in g.link.items():                                    # jukto kora tar
            col = g.color(g.cols[i])
            pts = wire_pts(left[i], right[j])
            pygame.draw.lines(surf, (0, 0, 0), False, pts, 9)
            pygame.draw.lines(surf, col, False, pts, 6)
            pygame.draw.lines(surf, tuple(min(255, v + 90) for v in col), False, pts, 2)
            for q in range(3):                                         # bidyut er pulse tar bore choley
                u = (self.t * 1.1 + q / 3.0 + i * 0.17) % 1.0
                px, py = pts[min(20, int(u * 20))]
                pygame.draw.circle(surf, (255, 255, 255), (int(px), int(py)), 4)
                pygame.draw.circle(surf, col, (int(px), int(py)), 7, 2)
        if g.sel is not None:                                          # ekhon taina hocche
            col = g.color(g.cols[g.sel])
            pts = wire_pts(left[g.sel], mouse)
            pygame.draw.lines(surf, (0, 0, 0), False, pts, 9)
            pygame.draw.lines(surf, col, False, pts, 6)
        self.wire_ports = {}
        for i in range(n):                                             # bam node
            c = left[i]
            col = g.color(g.cols[i])
            pygame.draw.circle(surf, (20, 22, 30), c, 20)
            pygame.draw.circle(surf, col, c, 16)
            if g.sel == i:
                pygame.draw.circle(surf, (255, 255, 255), c, 21 + int(2 * math.sin(self.t * 8)), 3)
            self.txt(surf, g.name(g.cols[i]), (c[0], c[1] - 33), 11, col, True, anchor="center")
            if i not in g.link:
                self.hit(pygame.Rect(c[0] - 24, c[1] - 24, 48, 48), lambda p, k=i: self.wire_grab(k, p))
        for j in range(n):                                             # dan port
            c = right[j]
            col = g.color(g.right[j])
            pr = pygame.Rect(0, 0, 38, 38)
            pr.center = c
            used = j in g.link.values()
            hov = g.sel is not None and not used and pr.collidepoint(mouse)
            pygame.draw.rect(surf, (20, 22, 30), pr.inflate(8, 8), border_radius=9)
            pygame.draw.rect(surf, col if used else tuple(int(v * 0.55) for v in col), pr, border_radius=7)
            pygame.draw.rect(surf, (255, 255, 255) if hov else col, pr, 3, border_radius=7)
            pygame.draw.circle(surf, (20, 22, 30), c, 6)
            self.txt(surf, "PORT " + g.name(g.right[j]), (c[0], c[1] - 33), 11, col, True, anchor="center")
            self.wire_ports[j] = pr
            if not used:
                self.hit(pr.inflate(10, 10), lambda p, k=j: self.wire_click_port(k, p))
        for sp in self.wire_fx:                                        # sparks
            pygame.draw.circle(surf, sp[5], (int(sp[0]), int(sp[1])), max(1, int(4 * sp[4] / 0.8) + 1))
            pygame.draw.circle(surf, (255, 255, 255), (int(sp[0]), int(sp[1])), 1)
        if g.flash > 0:                                                # thik hole port e ring
            for jj in g.link.values():
                pr = self.wire_ports.get(jj)
                if pr is not None:
                    rr = int(18 + (0.35 - g.flash) * 110)
                    pygame.draw.circle(surf, (255, 255, 255), pr.center, rr, 2)
        if g.solved:
            for q in range(3):                                         # sobuj ripple
                kk = (g.solved_t * 0.9 - q * 0.3)
                if 0 < kk < 1:
                    pygame.draw.circle(surf, (90, 255, 150), r.center, int(30 + kk * 330), 3)
            self.txt(surf, "ACCESS GRANTED" if not self.free else "WIRING FIXED", (r.centerx, r.bottom - 44), 26,
                     (90, 255, 150), True, anchor="center")
        else:
            self.txt(surf, "Drag a wire to its port  (or click the wire, then the port)", (r.centerx, r.bottom - 26), 12,
                     (130, 140, 168), anchor="center")
        self.button(surf, (r.x + 16, r.bottom - 38, 110, 26), "New wires", self.wire_new, mouse, (110, 120, 145), size=12)

    # ---------- python / chat ----------
    def draw_py(self, surf, r):
        if self.key_flash > 0:
            gl = pygame.Surface((r.w, 30), pygame.SRCALPHA)
            gl.fill((60, 255, 140, int(120 * self.key_flash / 0.12)))
            surf.blit(gl, (r.x, r.bottom - 36))
        f = font(15, mono=True)
        lh = 19
        maxl = (r.h - 30) // lh
        lines = []
        for ln in self.py_lines:
            lines.extend(wrap(ln, f, r.w - 24) or [""])
        lines = lines[-(maxl - 1):]
        y = r.y + 8
        for ln in lines:
            if ln.startswith(">>>"):
                c = (230, 235, 245)
            elif "GRANTED" in ln or "UNLOCKED" in ln or ln.startswith("[OK]") or ln == "OK":
                c = (110, 240, 140)
            elif "Error" in ln or "not found" in ln:
                c = (255, 120, 120)
            elif ln.startswith("[ * ]"):
                c = (255, 215, 90)
            elif ln.startswith("STATUS"):
                c = (255, 170, 90)
            else:
                c = (170, 200, 230)
            surf.blit(f.render(ln, True, c), (r.x + 12, y))
            y += lh
        prompt = ">>> " + self.py_in + ("_" if int(self.t * 2) % 2 == 0 and not self.done else "")
        surf.blit(f.render(prompt, True, (255, 255, 255)), (r.x + 12, r.bottom - 26))

    def draw_chat(self, surf, r, wid, col):
        f = font(15)
        inp = pygame.Rect(r.x + 10, r.bottom - 42, r.w - 20, 34)
        pygame.draw.rect(surf, (255, 255, 255), inp, border_radius=17)
        pygame.draw.rect(surf, col, inp, 2, border_radius=17)
        txt = self.chat_in[wid]
        blink = int(self.t * 2) % 2 == 0
        if not txt:
            surf.blit(font(14).render("Ask anything...  (ENTER to send)", True, (150, 156, 172)), (inp.x + 16, inp.y + 8))
            if blink:
                pygame.draw.line(surf, (60, 60, 70), (inp.x + 12, inp.y + 8), (inp.x + 12, inp.y + 26), 2)
        else:
            shown = txt + ("|" if blink else "")
            while f.size(shown)[0] > inp.w - 30:
                shown = shown[1:]
            surf.blit(f.render(shown, True, (30, 34, 46)), (inp.x + 14, inp.y + 7))
        msgs = list(self.chat[wid])
        if wid in self.pending:
            msgs.append(("ai", "..." if int(self.t * 4) % 2 else ".."))
        blocks = [(who, wrap(text, f, r.w - 130)) for who, text in msgs]
        y = inp.y - 10
        for who, ls in reversed(blocks):
            h = len(ls) * 20 + 14
            if y - h < r.y + 4:
                break
            w = max(f.size(l)[0] for l in ls) + 22
            bx = r.x + 12 if who == "ai" else r.right - 12 - w
            pygame.draw.rect(surf, (225, 230, 245) if who == "ai" else col, (bx, y - h, w, h), border_radius=12)
            tc = (30, 34, 46) if who == "ai" else (255, 255, 255)
            for i, l in enumerate(ls):
                surf.blit(f.render(l, True, tc), (bx + 11, y - h + 7 + i * 20))
            y -= h + 8

    # ---------- search ----------
    def draw_search(self, surf, r, mouse):
        box = pygame.Rect(r.x + 12, r.y + 10, r.w - 24, 34)
        pygame.draw.rect(surf, (255, 255, 255), box, border_radius=17)
        pygame.draw.rect(surf, self.accent, box, 2, border_radius=17)
        shown = self.sr_in + ("|" if int(self.t * 2) % 2 == 0 else "")
        if self.sr_in or int(self.t * 2) % 2 == 0:
            self.txt(surf, shown or "|", (box.x + 16, box.y + 8), 15)
        if not self.sr_in:
            self.txt(surf, "Search apps and files", (box.x + 28, box.y + 8), 14, (150, 156, 172))
        y = r.y + 56
        for kind, name, fn, wid in self.search_results():
            row = pygame.Rect(r.x + 12, y, r.w - 24, 28)
            if row.collidepoint(mouse):
                pygame.draw.rect(surf, (222, 230, 246), row, border_radius=6)
            if wid:
                self.app_icon(surf, wid, pygame.Rect(row.x + 4, row.y + 3, 22, 22), small=True)
            else:
                pygame.draw.rect(surf, (255, 255, 255), (row.x + 8, row.y + 4, 14, 20), border_radius=2)
                pygame.draw.rect(surf, (150, 156, 172), (row.x + 8, row.y + 4, 14, 20), 1, border_radius=2)
            self.txt(surf, name, (row.x + 36, row.y + 5), 14, maxw=row.w - 120)
            self.txt(surf, "App" if kind == "app" else "File", (row.right - 10, row.y + 6), 12, (120, 126, 142), anchor="topright")
            self.hit(row, fn)
            y += 30

    # ---------- file manager ----------
    def draw_files(self, surf, r, mouse):
        fm = self.fm
        pygame.draw.rect(surf, (233, 237, 246), (r.x, r.y, 150, r.h))
        self.txt(surf, "This PC", (r.x + 14, r.y + 10), 13, (90, 96, 114), True)
        for i, fo in enumerate(FOLDERS):
            row = pygame.Rect(r.x + 6, r.y + 34 + i * 30, 138, 26)
            if fo == fm["folder"]:
                pygame.draw.rect(surf, (205, 218, 244), row, border_radius=6)
                pygame.draw.rect(surf, self.accent, (row.x, row.y + 5, 3, 16), border_radius=2)
            elif row.collidepoint(mouse):
                pygame.draw.rect(surf, (221, 228, 244), row, border_radius=6)
            pygame.draw.rect(surf, (238, 184, 50), (row.x + 10, row.y + 7, 16, 12), border_radius=2)
            self.txt(surf, fo, (row.x + 32, row.y + 5), 13, maxw=100)
            self.hit(row, lambda p, f=fo: self.fm_select_folder(f))
        mx = r.x + 160
        mw = r.right - mx - 6
        path = pygame.Rect(mx, r.y + 6, mw, 26)
        pygame.draw.rect(surf, (255, 255, 255), path, border_radius=6)
        pygame.draw.rect(surf, (200, 205, 218), path, 1, border_radius=6)
        self.txt(surf, f"This PC  >  {fm['folder']}", (path.x + 10, path.y + 5), 13, (60, 66, 84))
        self.button(surf, (mx, r.y + 38, 130, 26), "+ New text file", self.fm_start_new, mouse)
        self.button(surf, (mx + 138, r.y + 38, 64, 26), "Open", self.fm_open_sel, mouse, (90, 150, 110))
        self.button(surf, (mx + 210, r.y + 38, 70, 26), "Delete", self.fm_delete, mouse, (200, 80, 90))
        y = r.y + 72
        if fm["new_in"] is not None:
            box = pygame.Rect(mx, y, mw - 44, 28)
            pygame.draw.rect(surf, (255, 255, 255), box, border_radius=6)
            pygame.draw.rect(surf, self.accent, box, 2, border_radius=6)
            self.txt(surf, "Name: " + fm["new_in"] + ("|" if int(self.t * 2) % 2 == 0 else "") + "   (.txt)", (box.x + 10, box.y + 6), 14)
            self.button(surf, (box.right + 6, y, 36, 28), "x", self.fm_cancel_new, mouse, (150, 154, 170))
            y += 34
        self.txt(surf, "Name", (mx + 30, y), 12, (110, 116, 134), True)
        self.txt(surf, "Size", (r.right - 14, y), 12, (110, 116, 134), True, anchor="topright")
        pygame.draw.line(surf, (210, 214, 226), (mx, y + 18), (r.right - 6, y + 18))
        y += 22
        names = self.fs_list(fm["folder"])
        for name in names[:max(1, (r.bottom - 30 - y) // 24)]:
            row = pygame.Rect(mx, y, mw, 24)
            if name == fm["sel"]:
                pygame.draw.rect(surf, (205, 218, 244), row, border_radius=5)
            elif row.collidepoint(mouse):
                pygame.draw.rect(surf, (230, 235, 247), row, border_radius=5)
            pygame.draw.rect(surf, (255, 255, 255), (row.x + 8, row.y + 3, 13, 18), border_radius=2)
            pygame.draw.rect(surf, (130, 136, 154), (row.x + 8, row.y + 3, 13, 18), 1, border_radius=2)
            self.txt(surf, name, (row.x + 30, row.y + 4), 14, maxw=row.w - 120)
            size = len(self.fs_read(fm["folder"] + "/" + name).encode("utf-8", "ignore"))
            self.txt(surf, f"{size} B", (row.right - 10, row.y + 5), 13, (110, 116, 134), anchor="topright")
            self.hit(row, lambda p, n=name: self.fm_row_click(n))
            y += 24
        if not names:
            self.txt(surf, "This folder is empty.", (mx + 10, y + 6), 14, (130, 136, 154))
        self.txt(surf, f"{len(names)} item(s)    " + fm["msg"], (mx, r.bottom - 22), 12, (90, 96, 114))

    # ---------- notepad ----------
    def draw_notes(self, surf, r, mouse):
        np = self.np
        self.button(surf, (r.x + 8, r.y + 6, 56, 26), "New", self.np_new, mouse, (120, 130, 150))
        self.button(surf, (r.x + 70, r.y + 6, 64, 26), "Save", self.np_save, mouse, enabled=not np["ro"])
        self.button(surf, (r.x + 140, r.y + 6, 86, 26), "Open...", lambda p: self.open_win("files"), mouse, (90, 150, 110))
        self.txt(surf, np["path"] or "(not saved yet)  -  Ctrl+S", (r.right - 10, r.y + 12), 12, (110, 116, 134), anchor="topright")
        area = pygame.Rect(r.x + 8, r.y + 40, r.w - 16, r.h - 70)
        pygame.draw.rect(surf, (255, 255, 255), area, border_radius=4)
        pygame.draw.rect(surf, (200, 205, 218), area, 1, border_radius=4)
        f = font(15, mono=True)
        lh, cw = 18, f.size("M")[0]
        rows = max(1, (area.h - 8) // lh)
        if np["r"] < np["top"]:
            np["top"] = np["r"]
        if np["r"] >= np["top"] + rows:
            np["top"] = np["r"] - rows + 1
        for i in range(rows):
            li = np["top"] + i
            if li >= len(np["lines"]):
                break
            self.txt(surf, np["lines"][li], (area.x + 8, area.y + 4 + i * lh), 15, (30, 34, 46), mono=True)
        if np["name_in"] is None and int(self.t * 2) % 2 == 0:
            cx = area.x + 8 + np["c"] * cw
            cy = area.y + 4 + (np["r"] - np["top"]) * lh
            pygame.draw.line(surf, (30, 34, 46), (cx, cy), (cx, cy + lh - 2), 2)

        def place(p):
            li = np["top"] + max(0, (p[1] - area.y - 4) // lh)
            np["r"] = max(0, min(li, len(np["lines"]) - 1))
            np["c"] = max(0, min(int((p[0] - area.x - 8 + cw // 2) // cw), len(np["lines"][np["r"]])))
        self.hit(area, place)
        status = f"Ln {np['r'] + 1}, Col {np['c'] + 1}     " + ("READ-ONLY   " if np["ro"] else ("UNSAVED   " if np["dirty"] else "saved   ")) + np["msg"]
        self.txt(surf, status, (r.x + 10, r.bottom - 22), 12, (90, 96, 114))
        if np["name_in"] is not None:
            box = pygame.Rect(0, 0, 400, 80)
            box.center = area.center
            pygame.draw.rect(surf, (250, 251, 255), box, border_radius=10)
            pygame.draw.rect(surf, self.accent, box, 2, border_radius=10)
            self.hit(box, None)
            self.txt(surf, "Save as  (Documents/)  -  type a name, ENTER", (box.x + 14, box.y + 10), 13, (60, 66, 84))
            inp = pygame.Rect(box.x + 14, box.y + 36, box.w - 28, 30)
            pygame.draw.rect(surf, (255, 255, 255), inp, border_radius=6)
            pygame.draw.rect(surf, (200, 205, 218), inp, 1, border_radius=6)
            self.txt(surf, np["name_in"] + ("|" if int(self.t * 2) % 2 == 0 else "") + "  .txt", (inp.x + 8, inp.y + 6), 15)

    # ---------- task manager ----------
    def draw_tasks(self, surf, r, mouse):
        w = self.world
        cards = [("CPU", f"{self.cpu:.0f}%", self.cpu_hist, 100.0, (60, 140, 250)),
                 ("Memory", f"{self.mem:.0f} MB", self.mem_hist, max(self.mem_hist) * 1.3 + 1, (150, 100, 240)),
                 ("Threads", f"{threading.active_count()}", None, 0, (50, 190, 120)),
                 ("Frame rate", f"{self.fps:.0f} fps", None, 0, (240, 150, 50))]
        cw = (r.w - 16 - 3 * 8) // 4
        for i, (name, val, hist, mx, col) in enumerate(cards):
            c = pygame.Rect(r.x + 8 + i * (cw + 8), r.y + 4, cw, 56)
            pygame.draw.rect(surf, (255, 255, 255), c, border_radius=8)
            pygame.draw.rect(surf, col, c, 2, border_radius=8)
            self.txt(surf, name, (c.x + 10, c.y + 6), 12, (100, 106, 124))
            self.txt(surf, val, (c.x + 10, c.y + 22), 18, (30, 34, 46), True)
            if hist:
                pts = [(c.right - 70 + k * 60 / 59.0, c.bottom - 8 - min(1.0, v / mx) * 26) for k, v in enumerate(hist)]
                pygame.draw.lines(surf, col, False, pts, 2)
        top = r.y + 66
        self.txt(surf, "Processes", (r.x + 10, top), 13, (60, 66, 84), True)
        self.txt(surf, f"active level: {self.title[:34]}", (r.right - 10, top + 1), 12, (110, 116, 134), anchor="topright")
        hy = top + 20
        cols = [r.x + 10, r.x + 250, r.x + 360, r.x + 420]
        for x, h in zip(cols, ("Name", "Type", "CPU", "Details")):
            self.txt(surf, h, (x, hy), 12, (110, 116, 134), True)
        pygame.draw.line(surf, (210, 214, 226), (r.x + 6, hy + 16), (r.right - 6, hy + 16))
        rows = self.proc_rows()
        y = hy + 20
        maxrows = max(1, (r.bottom - 44 - y) // 21)
        for row in rows[:maxrows]:
            rr = pygame.Rect(r.x + 6, y, r.w - 12, 21)
            alert = row["kill"] is not None
            if row["name"] == self.tm["sel"]:
                pygame.draw.rect(surf, (205, 218, 244), rr, border_radius=4)
            elif alert:
                pygame.draw.rect(surf, (255, 226, 226), rr, border_radius=4)
            elif rr.collidepoint(mouse):
                pygame.draw.rect(surf, (230, 235, 247), rr, border_radius=4)
            tc = (190, 40, 50) if alert else (30, 34, 46)
            self.txt(surf, row["name"], (cols[0], y + 2), 13, tc, alert, maxw=230)
            self.txt(surf, row["kind"], (cols[1], y + 2), 13, tc)
            self.txt(surf, f"{row['cpu']:.1f}%", (cols[2], y + 2), 13, tc)
            self.txt(surf, row["desc"], (cols[3], y + 2), 12, (110, 116, 134) if not alert else tc, maxw=r.right - cols[3] - 10)
            self.hit(rr, lambda p, n=row["name"]: self.tm.__setitem__("sel", n))
            y += 21
        if not any(rw["kill"] for rw in rows):
            self.txt(surf, "No alert-level process is running.", (r.x + 12, r.bottom - 42), 12, (40, 150, 80))
        cd = getattr(w, "kill_cd", 0.0) if w is not None else 0.0
        self.button(surf, (r.right - 112, r.bottom - 34, 104, 26), "End task" if cd <= 0 else f"Wait {cd:.0f}s", self.tm_end_task, mouse,
                    (200, 80, 90), enabled=True)
        self.txt(surf, self.tm["msg"], (r.x + 10, r.bottom - 24), 12, (90, 96, 114), maxw=r.w - 140)

    # ---------- settings ----------
    def draw_settings(self, surf, r, mouse):
        pygame.draw.rect(surf, (233, 237, 246), (r.x, r.y, 150, r.h))
        self.txt(surf, "Settings", (r.x + 14, r.y + 10), 15, (40, 46, 62), True)
        for i, tab in enumerate(("Display", "Sound", "Security", "Personalization")):
            row = pygame.Rect(r.x + 6, r.y + 40 + i * 32, 138, 28)
            if tab == self.st["tab"]:
                pygame.draw.rect(surf, (205, 218, 244), row, border_radius=6)
                pygame.draw.rect(surf, self.accent, (row.x, row.y + 6, 3, 16), border_radius=2)
            elif row.collidepoint(mouse):
                pygame.draw.rect(surf, (221, 228, 244), row, border_radius=6)
            self.txt(surf, tab, (row.x + 14, row.y + 6), 13)
            self.hit(row, lambda p, t=tab: self.st.__setitem__("tab", t))
        x, w = r.x + 170, r.w - 186
        tab = self.st["tab"]
        self.txt(surf, tab, (x, r.y + 12), 20, (30, 34, 46), True)
        y = r.y + 54
        if tab == "Display":
            card = pygame.Rect(x, y, w, 56)
            pygame.draw.rect(surf, (255, 255, 255), card, border_radius=8)
            self.txt(surf, "Display resolution", (card.x + 14, card.y + 8), 14, (30, 34, 46), True)
            self.txt(surf, f"{WIDTH} x {HEIGHT}  (native game resolution - fixed)", (card.x + 14, card.y + 30), 13, (90, 96, 114))
            try:
                ds = pygame.display.get_desktop_sizes()[0]
                dtxt = f"Your monitor: {ds[0]} x {ds[1]}"
            except Exception:
                dtxt = "Your monitor: unknown"
            card2 = pygame.Rect(x, y + 66, w, 56)
            pygame.draw.rect(surf, (255, 255, 255), card2, border_radius=8)
            self.txt(surf, "Fullscreen", (card2.x + 14, card2.y + 8), 14, (30, 34, 46), True)
            self.txt(surf, dtxt, (card2.x + 14, card2.y + 30), 13, (90, 96, 114))
            self.button(surf, (card2.right - 120, card2.y + 14, 106, 28), "Toggle", self.toggle_fullscreen, mouse)
        elif tab == "Sound":
            card = pygame.Rect(x, y, w, 90)
            pygame.draw.rect(surf, (255, 255, 255), card, border_radius=8)
            vol = self.cfg["volume"]
            self.txt(surf, "Master volume", (card.x + 14, card.y + 8), 14, (30, 34, 46), True)
            self.txt(surf, f"{int(round(vol * 100))}%", (card.right - 14, card.y + 8), 14, (30, 34, 46), True, anchor="topright")
            track = pygame.Rect(card.x + 20, card.y + 50, card.w - 40, 6)
            pygame.draw.rect(surf, (200, 205, 218), track, border_radius=3)
            pygame.draw.rect(surf, self.accent, (track.x, track.y, int(track.w * vol), track.h), border_radius=3)
            knob = (track.x + int(track.w * vol), track.centery)
            pygame.draw.circle(surf, (255, 255, 255), knob, 10)
            pygame.draw.circle(surf, self.accent, knob, 10, 3)
            zone = track.inflate(24, 30)

            def grab(p, tr=track):
                self.drag = ("vol", tr)
                self.set_volume_from(p[0], tr)
            self.hit(zone, grab)
            self.txt(surf, "Changes the whole game's sound (music + effects).", (x, y + 100), 12, (110, 116, 134))
            self.button(surf, (x, y + 124, 120, 28), "Test sound", lambda p: sound.play("pop", 1.0), mouse, (120, 130, 150))
        elif tab == "Security":
            card = pygame.Rect(x, y, w, 70)
            pygame.draw.rect(surf, (255, 255, 255), card, border_radius=8)
            on = self.cfg["firewall"]
            self.txt(surf, "Firewall", (card.x + 14, card.y + 8), 14, (30, 34, 46), True)
            self.txt(surf, "ACTIVE  -  network protected" if on else "DISABLED  -  not protected",
                     (card.x + 14, card.y + 32), 14, (40, 150, 80) if on else (200, 60, 70), True)
            pygame.draw.circle(surf, (40, 170, 90) if on else (210, 60, 70), (card.right - 150, card.centery), 8)
            self.button(surf, (card.right - 120, card.y + 20, 106, 28), "Turn off" if on else "Turn on", self.toggle_firewall, mouse,
                        (200, 80, 90) if on else (60, 160, 100))
            card2 = pygame.Rect(x, y + 80, w, 54)
            pygame.draw.rect(surf, (255, 255, 255), card2, border_radius=8)
            self.txt(surf, "Real-time threat protection", (card2.x + 14, card2.y + 8), 14, (30, 34, 46), True)
            n = len(self.world.os_alerts()) if self.world is not None and hasattr(self.world, "os_alerts") else 0
            self.txt(surf, f"{n} alert process(es) running  -  see Task Manager", (card2.x + 14, card2.y + 30), 13, (90, 96, 114))
            self.txt(surf, "(simulated - for the story, it doesn't change the level)", (x, y + 142), 12, (130, 136, 154))
        else:
            self.txt(surf, "Theme color", (x, y), 14, (30, 34, 46), True)
            for i, (name, c) in enumerate(THEMES.items()):
                sw = pygame.Rect(x + i * 70, y + 30, 60, 60)
                pygame.draw.rect(surf, c, sw, border_radius=12)
                if name == self.cfg["theme"]:
                    pygame.draw.rect(surf, (255, 255, 255), sw.inflate(-10, -10), 3, border_radius=8)
                    pygame.draw.rect(surf, (30, 34, 46), sw.inflate(6, 6), 2, border_radius=14)
                self.txt(surf, name, (sw.centerx, sw.bottom + 6), 12, (60, 66, 84), anchor="midtop")
                self.hit(sw, lambda p, n=name: self.set_theme(n))
            self.txt(surf, "Changes the wallpaper, taskbar and window accents.", (x, y + 120), 12, (110, 116, 134))

    def draw_cursor(self, surf, mouse):
        x, y = mouse
        pts = [(x, y), (x, y + 18), (x + 5, y + 14), (x + 9, y + 22), (x + 12, y + 20), (x + 8, y + 13), (x + 14, y + 13)]
        pygame.draw.polygon(surf, (0, 0, 0), [(a + 1, b + 1) for a, b in pts])
        pygame.draw.polygon(surf, (255, 255, 255), pts)
        pygame.draw.polygon(surf, (0, 0, 0), pts, 1)
