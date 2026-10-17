"""modloader.py - ABIX MODS.

  Folder:   %APPDATA%\\AbixNinja\\AbixMods\\<mod name>\\   (mod.json + main.py)
  V12: MOD CHECKER REMOVED.  Kono security server / code scan / block nei - jekono mod folder cholbe.
  (Mod ekhon full Python power pay - shudhu nijer trust kora mod chalao.)
Mod er hook: on_load(api)  on_update(dt, api)  on_draw(api)  on_event(ev, api)
"""
import hashlib
import hmac
import json
import os
import secrets
import sys
import threading
import time
import types
import urllib.request

import modsec

GAME_ID = "ABIX-NINJA-3"
SAFE_BUILTINS = ("abs all any bool dict divmod enumerate filter float int isinstance len list map max min "
                 "pow range reversed round set sorted str sum tuple zip chr ord hex bin bytes repr "
                 "object super Exception ValueError TypeError KeyError IndexError ZeroDivisionError "
                 "True False None").split()


def asset(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", name)


def home_dir():
    base = os.environ.get("ABIX_HOME") or os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "AbixNinja") if not os.environ.get("ABIX_HOME") else base
    os.makedirs(d, exist_ok=True)
    return d


def sign(secret, nonce, results):
    msg = nonce + "|" + json.dumps(results, sort_keys=True, separators=(",", ":"))
    return hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


class ModAPI:
    """Mod er jonno chhoto, nirapod API (pygame / file / network ekhane nei)."""
    MAX_OPS = 20000

    def __init__(self, mgr, entry):
        self._mgr, self._e = mgr, entry
        self.mod_id = entry.id
        self.width, self.height = 960, 540
        self._scr, self._ops, self._imgs = None, 0, {}

    # ---- internal
    def _begin(self, screen):
        self._scr, self._ops = screen, 0

    def _end(self):
        self._scr = None

    def _ok(self):
        self._ops += 1
        return self._scr is not None and self._ops <= self.MAX_OPS

    @staticmethod
    def _col(c):
        try:
            return tuple(max(0, min(255, int(v))) for v in tuple(c)[:3])
        except Exception:
            return (255, 255, 255)

    # ---- drawing
    def rect(self, color, x, y, w, h, border=0, radius=0):
        if self._ok():
            import pygame
            pygame.draw.rect(self._scr, self._col(color), (int(x), int(y), int(w), int(h)),
                             max(0, int(border)), border_radius=max(0, int(radius)))

    def circle(self, color, x, y, r, border=0):
        if self._ok():
            import pygame
            pygame.draw.circle(self._scr, self._col(color), (int(x), int(y)), max(1, int(r)), max(0, int(border)))

    def line(self, color, x1, y1, x2, y2, width=1):
        if self._ok():
            import pygame
            pygame.draw.line(self._scr, self._col(color), (int(x1), int(y1)), (int(x2), int(y2)), max(1, int(width)))

    def text(self, s, x, y, size=20, color=(255, 255, 255), center=False):
        if self._ok():
            from animation import get_font
            img = get_font(max(8, min(80, int(size))), True).render(str(s)[:120], True, self._col(color))
            r = img.get_rect()
            if center:
                r.center = (int(x), int(y))
            else:
                r.topleft = (int(x), int(y))
            self._scr.blit(img, r)

    def image(self, name, x, y, w=None, h=None):
        if not self._ok():
            return
        import pygame
        name = str(name)
        if os.path.basename(name) != name or os.path.splitext(name)[1].lower() not in (".png", ".jpg", ".jpeg"):
            return
        img = self._imgs.get(name)
        if img is None:
            try:
                img = pygame.image.load(os.path.join(self._e.folder, name)).convert_alpha()
                if max(img.get_size()) > 2048:
                    img = pygame.Surface((1, 1))
            except Exception:
                img = pygame.Surface((1, 1))
            self._imgs[name] = img
        if w and h:
            key = (name, int(w), int(h))
            sc = self._imgs.get(key)
            if sc is None:
                sc = pygame.transform.smoothscale(img, (max(1, min(2048, int(w))), max(1, min(2048, int(h)))))
                self._imgs[key] = sc
            img = sc
        self._scr.blit(img, (int(x), int(y)))

    # ---- input / info (read only)
    def mouse(self):
        import pygame
        return pygame.mouse.get_pos()

    def stat(self, name):
        """money / dollars / diamonds / deaths - shudhu poRa jay, bodlano jay na."""
        return self._mgr.stats.get(str(name), 0)

    def log(self, *a):
        self._mgr.log(self._e.id, " ".join(str(x) for x in a)[:200])

    def load_data(self):
        try:
            with open(self._mgr.data_path(self.mod_id), "r", encoding="utf-8") as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_data(self, data):
        try:
            raw = json.dumps(data)
            if len(raw) <= 32 * 1024:
                with open(self._mgr.data_path(self.mod_id), "w", encoding="utf-8") as f:
                    f.write(raw)
                return True
        except (OSError, TypeError, ValueError):
            pass
        return False


class ModEntry:
    def __init__(self, mid, folder):
        self.id, self.folder = mid, folder
        self.name, self.version, self.author, self.desc = mid, "?", "?", ""
        self.status, self.reason = "checking", ""
        self.sha, self.loaded_hash = "", None
        self.hooks, self.api = {}, None
        self.active, self.strikes, self.slow = False, 0, 0


class ModManager:
    def __init__(self):
        self.home = home_dir()
        self.dir = os.path.join(self.home, "AbixMods")
        self.data_dir = os.path.join(self.home, "mod_data")
        os.makedirs(self.dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        self._write_readme()
        self.cfg = self._load_cfg()
        self.entries = {}
        self.security = "on"                # V12: checker nei, shob mod open
        self.error = ""
        self.stats = {}
        self.logs = []
        self._lock = threading.Lock()
        self._pending = None
        self._busy = False
        self._next = 0.0

    # ------------------------------------------------ setup
    def _write_readme(self):
        p = os.path.join(self.dir, "README.txt")
        if not os.path.exists(p):
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write("ABIX MODS folder\n\nPut each mod in its own folder here:\n"
                            "  AbixMods\\MyMod\\mod.json\n  AbixMods\\MyMod\\main.py\n\n"
                            "Any mod runs - there is no security checker any more.\n"
                            "See MODS_GUIDE.txt that came with the game kit.\n")
            except OSError:
                pass

    def _load_cfg(self):
        p = os.path.join(self.home, "mods_config.json")
        if not os.path.exists(p):
            try:
                with open(asset("mods_config_default.json"), "r", encoding="utf-8") as f:
                    raw = f.read()
            except OSError:
                raw = json.dumps({"server_url": "http://127.0.0.1:8765", "secret": "", "check_interval_sec": 45,
                                  "enabled": True})
            try:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(raw)
            except OSError:
                pass
        try:
            with open(p, "r", encoding="utf-8") as f:
                c = json.load(f)
        except (OSError, ValueError):
            c = {}
        c.setdefault("server_url", "http://127.0.0.1:8765")
        c.setdefault("secret", "")
        c["check_interval_sec"] = max(15, int(c.get("check_interval_sec", 45) or 45))
        c.setdefault("enabled", True)
        return c

    def data_path(self, mod_id):
        safe = "".join(ch for ch in mod_id if ch.isalnum() or ch in "-_")[:40] or "mod"
        return os.path.join(self.data_dir, safe + ".json")

    def log(self, mid, msg):
        self.logs.append(f"[{mid}] {msg}")
        del self.logs[:-50]

    # ------------------------------------------------ security check (background)
    def recheck(self):
        self._next = 0.0

    def update(self, dt=0.0):
        now = time.time()
        if not self._busy and now >= self._next:
            self._busy = True
            if self.security != "on":
                self.security = "checking" if not self.entries and self.security == "checking" else self.security
            threading.Thread(target=self._worker, daemon=True).start()
        with self._lock:
            pend, self._pending = self._pending, None
        if pend:
            self._apply(pend)
            self._busy = False
            self._next = time.time() + self.cfg["check_interval_sec"]

    def _worker(self):
        infos = []
        try:
            for d in sorted(os.listdir(self.dir)):
                full = os.path.join(self.dir, d)
                if not os.path.isdir(full) or d.startswith((".", "_")):
                    continue
                try:
                    manifest = self._open_manifest(full, d)
                    sha = modsec.hash_mod(full)          # shudhu file bodlale reload korar jonno (check na)
                except Exception as ex:
                    manifest, sha = None, ""
                    self.log(d, f"scan skipped: {ex}")
                infos.append({"id": d, "folder": full, "manifest": manifest, "problems": [], "sha": sha})
        except OSError:
            pass
        with self._lock:
            self._pending = {"infos": infos, "online": True, "results": {}, "err": None}

    @staticmethod
    def _open_manifest(folder, d):
        """mod.json thakle pore, na thakle folder er nam / main.py (ba prothom .py) niye chalay. Kono check nei."""
        m = {}
        try:
            with open(os.path.join(folder, "mod.json"), "r", encoding="utf-8") as f:
                m = json.load(f)
            if not isinstance(m, dict):
                m = {}
        except (OSError, ValueError):
            m = {}
        entry = str(m.get("entry", "main.py"))
        if not os.path.isfile(os.path.join(folder, entry)):
            pys = sorted(x for x in os.listdir(folder) if x.endswith(".py"))
            entry = "main.py" if os.path.isfile(os.path.join(folder, "main.py")) else (pys[0] if pys else entry)
        return {"name": str(m.get("name", d))[:40], "version": str(m.get("version", "1.0"))[:16],
                "author": str(m.get("author", "?"))[:32], "entry": entry,
                "description": str(m.get("description", ""))[:120]}

    # ------------------------------------------------ apply result (main thread)
    def _apply(self, p):
        self.security = "on"                    # checker nei - shob mod open
        self.error = ""
        seen = set()
        for info in p["infos"]:
            mid = info["id"]
            seen.add(mid)
            e = self.entries.get(mid) or self.entries.setdefault(mid, ModEntry(mid, info["folder"]))
            m = info["manifest"]
            if m:
                e.name, e.version, e.author, e.desc = m["name"], m["version"], m["author"], m["description"]
            e.sha = info["sha"]
            if not m:
                self._unload(e, "error", "folder read error")
                continue
            if e.loaded_hash != e.sha:
                self._load(e, m)
            else:
                e.active = e.status in ("loaded", "disabled", "checking") and e.strikes < 20
                if e.active:
                    e.status, e.reason = "loaded", ""
        for mid in list(self.entries):
            if mid not in seen:
                self._unload(self.entries.pop(mid), "gone", "")

    def _unload(self, e, status, reason):
        e.active, e.hooks, e.api, e.loaded_hash = False, {}, None, None
        e.status, e.reason = status, reason

    def _load(self, e, manifest):
        """Kono scan / kono block nei - mod er main.py ta shorashori chole (full builtins, full import)."""
        try:
            path = os.path.join(e.folder, manifest["entry"])
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
            import builtins as _b
            import pygame as _pg
            e.api = ModAPI(self, e)
            e.api.pygame = _pg                                   # mod chaile pygame shorashori pabe
            e.api.folder = e.folder
            if e.folder not in sys.path:
                sys.path.insert(0, e.folder)                     # mod er nijer .py file gulo import kora jay
            ns = {"__builtins__": _b, "__name__": "abix_mod_" + e.id, "__file__": path, "api": e.api}
            exec(compile(src, path, "exec"), ns)
            e.hooks = {k: ns[k] for k in ("on_load", "on_update", "on_draw", "on_event") if callable(ns.get(k))}
            e.loaded_hash, e.strikes, e.slow, e.active = e.sha, 0, 0, True
            e.status, e.reason = "loaded", ""
            self._call(e, "on_load")
        except Exception as ex:
            self._unload(e, "error", (type(ex).__name__ + ": " + str(ex))[:100])

    # ------------------------------------------------ hooks
    def _call(self, e, name, *args, screen=None):
        fn = e.hooks.get(name)
        if not (e.active and fn and e.api):
            return
        t0 = time.perf_counter()
        try:
            if screen is not None:
                e.api._begin(screen)
            fn(*args, e.api)
        except Exception as ex:
            e.strikes += 1
            self.log(e.id, f"{name} error: {ex}")
            if e.strikes >= 20:
                e.active, e.status, e.reason = False, "error", ("crashed: " + str(ex))[:90]
        finally:
            e.api._end()
        if time.perf_counter() - t0 > 0.25:
            e.slow += 1
            if e.slow >= 120:
                e.active, e.status, e.reason = False, "error", "too slow (stopped)"
        else:
            e.slow = max(0, e.slow - 1)

    def menu_update(self, dt):
        for e in self.entries.values():
            self._call(e, "on_update", dt)

    def menu_draw(self, screen):
        for e in self.entries.values():
            self._call(e, "on_draw", screen=screen)

    def menu_event(self, pe):
        import pygame
        ev = None
        if pe.type in (pygame.KEYDOWN, pygame.KEYUP):
            ev = types.SimpleNamespace(type="keydown" if pe.type == pygame.KEYDOWN else "keyup",
                                       key=pygame.key.name(pe.key), pos=(0, 0), button=0)
        elif pe.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            ev = types.SimpleNamespace(type="mousedown" if pe.type == pygame.MOUSEBUTTONDOWN else "mouseup",
                                       key="", pos=tuple(pe.pos), button=pe.button)
        if ev:
            for e in self.entries.values():
                self._call(e, "on_event", ev)

    def active_count(self):
        return sum(1 for e in self.entries.values() if e.active)

    def open_folder(self):
        try:
            os.startfile(self.dir)          # Windows
        except Exception:
            pass
