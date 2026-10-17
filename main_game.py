"""
main_game.py - Intro shesh hole ekhane ashe (main menu).
Direct chalaben na, intro.py chalan:  python intro.py

Menu (shob button RGB color e ghurte thake):
  - Upor theke slide hoye ashe: PLAY      -> Chapter / Level select screen
  - Majhkhane: ABIX TOOLS                 -> Coming Soon
  - Niche theke slide hoye ashe: SETTINGS -> Coming Soon

Level select:
  - 5 ta chapter, protita chapter e 20 ta level
  - Shuru te sudhu Chapter 1 / Level 1 khola. Ekta level shesh korle porer level unlock hoy.
  - Chapter er 20 number level shesh korle porer chapter khule.
  - < > button diye chapter bodlano jay. Protita chapter e laf mara ninja
    bolche "Play me, don't die me!"
  - Chapter 1 / Level 1 = asol game (level1.py). Baki level e click korle "Coming Soon".
  - Level tile er upore koyta star paoa gese (3 er moddhe) dekhay.
ESC = back.
"""
import json
import math
import os
import sys
import pygame

import sound
import trailer
import codes as CD
import modloader as MD
import modsui
import controls as CT
import economy as EC
import lang
import menus
import pc as PCMOD
import level1
import level2
import level3
import level4
import level5
import level6
import level7
import level8
import level9
import level10
import level11
import level12
import level13
import level14
import level15
import game3d
import recorder
import sprites as SP
import ninjas
import police
import tools as TL
import abix_fx as FX
from animation import GOLD, get_font
from animation import (
    WIDTH, HEIGHT, BG, WHITE, RED, GOLD,
    Starfield, Embers, FadeText, MenuButton, ComingSoon,
    LevelTile, ArrowButton,
    draw_logo, fade_overlay, get_font, rgb_color,
)

police.install()                 # POLICE update (shob level e)


def FX_LOGO():
    from animation import logo_available
    return logo_available()


CHAPTERS = 5
LEVELS = 20            # protita chapter e
CHAPTER_NAMES = ["CITY BANK", "JEWELRY MALL", "CASINO", "MUSEUM", "CENTRAL VAULT"]

# Level e jodi dukhe test korte chan: Coming Soon screen e ENTER chaple oi level "shesh" hoy
# ar porer level unlock hoy. Asol game toiri hole complete_level() ke game theke call korben,
# tokhon eta False kore din.
DEV_WIN_KEY = True

def _save_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "AbixNinja")
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        d = os.path.dirname(os.path.abspath(__file__))
    return d


SAVE_FILE = os.path.join(_save_dir(), "abix_save.json")


# ------------------------------------------------------------------
# Save (file e thake): kon level shesh, koyta star, koto bar mrittu, intro dekha hoyeche kina
# ------------------------------------------------------------------
def _load_save_raw():
    save = {"done": [0] * CHAPTERS, "stars": [[0] * LEVELS for _ in range(CHAPTERS)],
            "deaths": 0, "money": 0, "tv_seen": False,
            "taken": {},      # level -> {"loot", "got", "cash", "bonus"}: je jinish nilo, replay te ar thakbe na
            "laptop": {"files": {}, "deleted": [], "theme": "Blue", "volume": 0.8, "firewall": True}}
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return save
    try:
        for i in range(CHAPTERS):
            save["done"][i] = max(0, min(LEVELS, int(data["done"][i])))
    except (KeyError, IndexError, TypeError, ValueError):
        pass
    try:
        for i in range(CHAPTERS):
            for j in range(LEVELS):
                save["stars"][i][j] = max(0, min(3, int(data["stars"][i][j])))
    except (KeyError, IndexError, TypeError, ValueError):
        pass
    try:
        save["deaths"] = max(0, int(data["deaths"]))
    except (KeyError, TypeError, ValueError):
        pass
    try:
        save["money"] = max(0, int(data["money"]))
        save["tv_seen"] = bool(data["tv_seen"])
    except (KeyError, TypeError, ValueError):
        pass
    try:                                   # laptop er file / setting + nilo jinish
        t = data.get("taken", {})
        if isinstance(t, dict):
            for k, v in t.items():
                if isinstance(v, dict):
                    save["taken"][str(k)] = {
                        "loot": bool(v.get("loot", False)),
                        "got": [bool(x) for x in v.get("got", [])],
                        "cash": [bool(x) for x in v.get("cash", [])],
                        "bonus": [str(x) for x in v.get("bonus", [])]}
        lp = data.get("laptop", {})
        if isinstance(lp, dict):
            L = save["laptop"]
            if isinstance(lp.get("files"), dict):
                L["files"] = {str(a): str(b) for a, b in lp["files"].items()}
            if isinstance(lp.get("deleted"), list):
                L["deleted"] = [str(a) for a in lp["deleted"]]
            if isinstance(lp.get("theme"), str):
                L["theme"] = lp["theme"]
            L["volume"] = max(0.0, min(1.0, float(lp.get("volume", 0.8))))
            L["firewall"] = bool(lp.get("firewall", True))
    except (TypeError, ValueError, AttributeError):
        pass
    return save


def load_save():
    """Ager save + notun field (dollar, diamond, special tools, settings, god)."""
    save = _load_save_raw()
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in ("dollars", "diamonds", "special", "bonus20", "settings", "god", "unlimited", "ninja"):
            if k in data:
                save[k] = data[k]
    except (OSError, ValueError, TypeError):
        pass
    save = EC.ensure(save)
    CD.top_up(save)
    return save


def write_save(save):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(save, f)
    except OSError:
        pass


LAST_AWARD = 0          # sheshbar complete_level e koto diamond bonus pelo


def set_cursor(hand):
    """Kichu system e cursor bodlano jay na - tokhon chup thake."""
    try:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if hand else pygame.SYSTEM_CURSOR_ARROW)
    except pygame.error:
        pass


def chapter_open(done, ch):
    """Chapter 1 shobshomoy khola; porer chapter khole age er chapter er level 20 shesh hole."""
    return ch == 0 or done[ch - 1] >= LEVELS


def level_state(done, ch, n):
    """'locked' | 'current' | 'done'"""
    if not chapter_open(done, ch):
        return "locked"
    if n <= done[ch]:
        return "done"
    if n == done[ch] + 1:
        return "current"
    return "locked"


def complete_level(save, ch, n):
    """Level n shesh hole eta call korun -> porer level unlock hobe. (ch 0-based, n 1-based)"""
    global LAST_AWARD
    LAST_AWARD = 0
    if level_state(save["done"], ch, n) == "current":
        save["done"][ch] = n
        if n == LEVELS:                                  # chapter er boss shesh: prothom bar +20 diamond
            LAST_AWARD = EC.award_chapter(save, ch)
        write_save(save)
        return True
    return False


# ------------------------------------------------------------------
# Level select screen
# ------------------------------------------------------------------
def clamp(v, a, b):
    return max(a, min(b, v))


class GuardTalker:
    """Level select e guard dariye bole: "You little thief, go!" (age ninja bubble chilo)."""
    def __init__(self, x, ground_y):
        self.x, self.ground = x, ground_y
        self.font = get_font(22)

    def draw(self, surf, t):
        # 2.2 sec por por baghe hat tule dhomkay
        ph = (t % 2.2) / 2.2
        anim = "aim" if 0.55 < ph < 0.85 else "idle"
        ap = clamp((ph - 0.55) / 0.2, 0, 1) if anim == "aim" else 0.0
        tmp = pygame.Surface((SP.TW, SP.TH), pygame.SRCALPHA)
        SP.draw_guard(tmp, SP.OX, SP.OY, 1, t, anim, ap)
        big = pygame.transform.smoothscale(tmp, (int(SP.TW * 2.6), int(SP.TH * 2.6)))
        surf.blit(big, big.get_rect(midbottom=(int(self.x), int(self.ground + SP.TH * 2.6 * (1 - SP.OY / SP.TH)))))

    def draw_bubble(self, surf, t):
        bob = math.sin(t * 3) * 4
        SP.draw_speech(surf, "You little thief,\nGO!", (self.x, self.ground - 232 + bob), self.font, shake=0.0)


class LevelSelect:
    COLS, ROWS, TILE, GAP = 5, 4, 78, 14
    GRID_X, GRID_Y = 470, 118

    def __init__(self):
        self.ch = 0
        self.page_t = 0.0
        self.tiles = []
        for i in range(LEVELS):
            r, c = divmod(i, self.COLS)
            x = self.GRID_X + c * (self.TILE + self.GAP)
            y = self.GRID_Y + r * (self.TILE + self.GAP)
            self.tiles.append(LevelTile(i + 1, (x, y, self.TILE, self.TILE)))
        self.prev_btn = ArrowButton(-1, (WIDTH // 2 - 250, 52), rgb_offset=0.0)
        self.next_btn = ArrowButton(+1, (WIDTH // 2 + 250, 52), rgb_offset=0.5)
        self.ninja = GuardTalker(225, 482)
        self.title_font = get_font(34)
        self.sub_font = get_font(16)
        self.hint_font = get_font(16)

    def open(self, done):
        """PLAY chaple: je chapter e khelchen shetay niye jay."""
        self.ch = 0
        while self.ch < CHAPTERS - 1 and done[self.ch] >= LEVELS:
            self.ch += 1
        self.page_t = 0.0
        for tile in self.tiles:
            tile.shake = 0.0

    def go_chapter(self, new_ch):
        self.ch = new_ch
        self.page_t = 0.0
        for tile in self.tiles:
            tile.shake = 0.0

    def update(self, dt):
        self.page_t += dt
        for tile in self.tiles:
            tile.shake = max(0.0, tile.shake - dt)
        self.prev_btn.enabled = self.ch > 0
        self.next_btn.enabled = self.ch < CHAPTERS - 1

    def _appear(self, i):
        return max(0.0, min(1.0, (self.page_t - i * 0.025) / 0.4))

    def hover_target(self, mouse, done):
        """Mouse kon jinish er upor (sound ar cursor er jonno)."""
        if self.prev_btn.hovered(mouse):
            return "prev"
        if self.next_btn.hovered(mouse):
            return "next"
        for i, tile in enumerate(self.tiles):
            if tile.hovered(mouse, self._appear(i)):
                return ("level", i + 1, level_state(done, self.ch, i + 1) != "locked")
        return None

    def click(self, mouse, done):
        """Return: None | ('chapter',) | ('level', ch, n)"""
        if self.prev_btn.hovered(mouse):
            self.go_chapter(self.ch - 1)
            return ("chapter",)
        if self.next_btn.hovered(mouse):
            self.go_chapter(self.ch + 1)
            return ("chapter",)
        for i, tile in enumerate(self.tiles):
            if tile.hovered(mouse, self._appear(i)):
                if level_state(done, self.ch, i + 1) == "locked":
                    tile.shake = 0.35
                    sound.play("lock")
                    return None
                return ("level", self.ch, i + 1)
        return None

    def draw(self, screen, t, mouse, save):
        done = save["done"]
        # chapter naam
        a = min(1.0, self.page_t / 0.35)
        shift = int((1 - a) * 18)
        title = self.title_font.render(f"CHAPTER {self.ch + 1}", True, WHITE)
        title.set_alpha(int(255 * a))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 40 + shift)))
        sub = self.sub_font.render(CHAPTER_NAMES[self.ch], True, GOLD)
        sub.set_alpha(int(255 * a))
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 76 + shift)))
        for i in range(CHAPTERS):                         # chapter dots
            col = RED if i == self.ch else (70, 70, 95)
            pygame.draw.circle(screen, col, (WIDTH // 2 + (i - 2) * 22, 98), 5 if i == self.ch else 4)

        self.prev_btn.draw(screen, t, mouse)
        self.next_btn.draw(screen, t, mouse)

        # level tile
        for i, tile in enumerate(self.tiles):
            tile.draw(screen, t, mouse, level_state(done, self.ch, i + 1), self.ch, self._appear(i))
        # protita level tile er upore koyta star paoa gese (3 er moddhe)
        for i, tile in enumerate(self.tiles):
            if self._appear(i) < 1.0 or level_state(done, self.ch, i + 1) == "locked":
                continue
            got = save["stars"][self.ch][i]
            cx, cy = tile.rect.centerx, tile.rect.top + 12
            for k in range(3):
                c = (cx + (k - 1) * 17, cy)
                pygame.draw.polygon(screen, (18, 18, 30), SP.star_points(c[0], c[1], 9))
                SP.draw_star_icon(screen, c, 7, k < got)

        # laf mara ninja + bubble
        self.ninja.draw(screen, t)
        if self.page_t > 0.5:
            self.ninja.draw_bubble(screen, t)

        # kotota level shesh
        if chapter_open(done, self.ch):
            txt = f"{done[self.ch]} / {LEVELS} completed"
        else:
            txt = f"Locked - finish Chapter {self.ch} first"
        info = self.hint_font.render(txt, True, (150, 150, 170))
        screen.blit(info, info.get_rect(midright=(self.GRID_X + self.COLS * (self.TILE + self.GAP) - self.GAP,
                                                  HEIGHT - 28)))
        h = self.hint_font.render("Press ESC to go back", True, (150, 150, 170))
        screen.blit(h, h.get_rect(midleft=(30, HEIGHT - 28)))


def make_level_soon(ch, n):
    """Level e click korle 'Coming Soon' screen."""
    return ComingSoon(f"CHAPTER {ch + 1} - LEVEL {n}")


def run(screen, clock):
    recorder.install()                       # F9 = record, F10 = screenshot (shob jaygay)
    stars = Starfield()
    embers = Embers()
    save = load_save()
    menus.apply_settings(save)               # bhasha, controller mode, volume lagao
    done = save["done"]
    levels = LevelSelect()
    tools_screen = TL.ToolsScreen()
    settings_screen = menus.SettingsScreen()
    special_screen = menus.SpecialScreen()
    ninja_screen = ninjas.NinjaScreen()
    ninjas.apply(save)                       # select kora ninja skin lagao
    ninja_btn = pygame.Rect(WIDTH - 190, 62, 172, 40)           # NINJAS button (N)
    play3d_btn = pygame.Rect(WIDTH - 190, 108, 172, 40)         # PLAY 3D NINJA button (3)
    tut = FX.Tutorial()
    code_box = CD.CodeBox()
    mods = MD.ModManager()                                     # ABIX MODS (AppData\\AbixNinja\\AbixMods)
    mods_panel = modsui.ModsPanel(mods)
    mods_btn = pygame.Rect(18, 60, 120, 36)
    code_btn = pygame.Rect(18, 18, 120, 36)                    # CODE button (secret code)
    trl_btn = pygame.Rect(WIDTH - 180, HEIGHT - 110, 160, 90)   # TRAILER picture button (no text)
    try:
        trl_thumb = pygame.image.load(trailer.asset("trailer_thumb.png")).convert()
    except Exception:
        trl_thumb = None
    tut_btn = pygame.Rect(18, HEIGHT - 58, 170, 40)         # main menu te choto TUTORIAL button
    save_fn = lambda: write_save(save)
    cx = WIDTH // 2

    title = FadeText("ABIX NINJA", 40, WHITE, (cx, 128), start=0.2, fade=0.8, glow=RED)

    def make_buttons(settled=False):
        """5 ta button: PLAY / SETTINGS / ABIX TOOLS / SPECIAL TOOLS / GAMING PC  (shob RGB)."""
        spec = [("play", "play", (0, -420)), ("settings", "settings", (-560, 0)), ("tools", "abix_tools", (560, 0)),
                ("special", "special_tools", (-560, 0)), ("pc", "gaming_pc", (0, 420))]
        out = {}
        for i, (key, lab, off) in enumerate(spec):
            out[key] = MenuButton(lang.tr(lab), (cx, 200 + i * 68), size=(360, 58), rgb=True, rgb_offset=i * 0.2,
                                  start=(-5.0 if settled else 0.4 + i * 0.3), from_offset=off)
        return out

    buttons = make_buttons()
    pending = [(0.4 + i * 0.3, "whoosh" if i % 2 == 0 else "pop") for i in range(5)]
    if not save.get("tutorial_done"):                       # prothom bar = tutorial
        save["tutorial_done"] = True
        write_save(save)
        tut.open(save["settings"].get("control", "keyboard"))
    menu_sel = 0

    sound.play_music("menu", loops=-1)

    state = "menu"          # "menu" | "levels" | "soon" | "tools" | "settings" | "special" | "pc"
    soon_from = "menu"      # Coming Soon theke ESC chaple kothay jabe
    soon_level = None       # (ch, n) jodi level er Coming Soon hoy
    coming = None
    pc = None
    toast, toast_t = "", 0.0
    t = 0.0          # menu er shomoy
    lv_t = 0.0       # level select er shomoy
    soon_t = 0.0     # coming soon screen er shomoy
    tools_t = 0.0    # tools screen er shomoy
    fade_in = 0.0    # screen fade-in
    last_hover = None

    def go(key):
        nonlocal state, lv_t, pc
        sound.play("click")
        sound.play("chime")
        if key == "play":
            levels.open(done)
            lv_t = 0.0
            state = "levels"
        elif key == "tools":
            tools_screen.open()
            state = "tools"
        elif key == "settings":
            settings_screen.open(save)
            state = "settings"
        elif key == "special":
            special_screen.open(save)
            state = "special"
        elif key == "pc":
            pc = PCMOD.make_pc(save, save_fn)      # PC on hoy (boot)
            state = "pc"

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.1)
        fade_in += dt
        toast_t = max(0.0, toast_t - dt)
        if state == "menu":
            t += dt
        elif state == "levels":
            lv_t += dt
            levels.update(dt)
        elif state == "tools":
            tools_t += dt
        elif state == "settings":
            settings_screen.update(dt)
        elif state == "special":
            special_screen.update(dt)
        elif state == "ninjas":
            ninja_screen.update(dt)
        elif state == "pc":
            pc.update(dt)
        else:
            soon_t += dt

        mouse = pygame.mouse.get_pos()
        CT.set_ctx(True)
        tut.update(dt)
        code_box.update(dt)
        mods.stats = {"money": save.get("money", 0), "dollars": save.get("dollars", 0),
                      "diamonds": save.get("diamonds", 0), "deaths": save.get("deaths", 0)}
        mods.update(dt)
        mods_panel.update(dt)
        if state == "menu" and not (tut.active or code_box.active or mods_panel.active):
            mods.menu_update(dt)
        CD.top_up(save)
        for e in CT.filter(pygame.event.get()):
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if code_box.active:                             # CODE box khola - shob event oikhane
                code_box.event(e, save, save_fn, sound)
                continue
            if mods_panel.active:                           # MODS panel khola
                mods_panel.event(e)
                continue
            if state == "menu" and not tut.active and ((e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and mods_btn.collidepoint(getattr(e, "pos", mouse)))
                                                      or (e.type == pygame.KEYDOWN and e.key == pygame.K_m)):
                sound.play("click")
                mods_panel.open()
                continue
            if state == "menu" and not tut.active:
                mods.menu_event(e)
            if state == "menu" and not tut.active and ((e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and code_btn.collidepoint(getattr(e, "pos", mouse)))
                                                      or (e.type == pygame.KEYDOWN and e.key == pygame.K_c)):
                sound.play("click")
                code_box.open()
                continue
            if state == "menu" and not tut.active and ((e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and ninja_btn.collidepoint(getattr(e, "pos", mouse)))
                                                      or (e.type == pygame.KEYDOWN and e.key == pygame.K_n)):
                sound.play("click")
                sound.play("chime")
                ninja_screen.open(save)
                state = "ninjas"
                continue
            if state == "menu" and not tut.active and ((e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and play3d_btn.collidepoint(getattr(e, "pos", mouse)))
                                                      or (e.type == pygame.KEYDOWN and e.key == pygame.K_3)):
                sound.play("click")
                sound.play("chime")
                set_cursor(False)
                game3d.run(screen, clock, save, save_fn)          # PLAY 3D NINJA
                sound.play_music("menu", loops=-1)
                pygame.event.clear()
                fade_in = 0.3
                continue
            if tut.active:                                  # tutorial khola - shob event oikhane
                tut.event(e)
                continue
            if state == "menu" and ((e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and trl_btn.collidepoint(getattr(e, "pos", mouse)))
                                    or (e.type == pygame.KEYDOWN and e.key == pygame.K_v)):
                sound.play("click")
                trailer.play(screen, clock)
                pygame.event.clear()
                continue
            if state == "menu" and ((e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and tut_btn.collidepoint(getattr(e, "pos", mouse)))
                                    or (e.type == pygame.KEYDOWN and e.key in (pygame.K_t, pygame.K_F1))):
                tut.open(save["settings"].get("control", "keyboard"))
                continue
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                if state == "menu":
                    pygame.quit()
                    sys.exit()
                if state == "special" and special_screen.back():
                    continue
                sound.play("back")
                state = soon_from if state == "soon" else "menu"
                if state == "menu":
                    buttons = make_buttons(True)          # bhasha bodlale button er lekha bodlay
                soon_level = None
                continue
            if (DEV_WIN_KEY and e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
                    and state == "soon" and soon_level):
                if complete_level(save, *soon_level):
                    sound.play("ding")
                    if LAST_AWARD:
                        toast, toast_t = lang.tr("bonus20"), 3.5
                    state = "levels"
                    soon_level = None
            # ---- keyboard / controller: main menu ----
            if state == "menu" and e.type == pygame.KEYDOWN:
                keys_ = list(buttons)
                if e.key == pygame.K_UP:
                    menu_sel = (menu_sel - 1) % len(keys_)
                    sound.play("hover", 0.6)
                elif e.key == pygame.K_DOWN:
                    menu_sel = (menu_sel + 1) % len(keys_)
                    sound.play("hover", 0.6)
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    go(keys_[menu_sel])
                    continue
            # ---- notun screen gulo ----
            if state == "settings" and e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                                                  pygame.MOUSEMOTION):
                settings_screen.event(e)
                continue
            if state == "special" and e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                special_screen.event(e)
                continue
            if state == "ninjas" and e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                ninja_screen.event(e)
                continue
            if state == "pc" and e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                                            pygame.MOUSEMOTION):
                pc.event(e)
                continue
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                click_pos = getattr(e, "pos", mouse)
                if state == "menu":
                    for key, b in buttons.items():
                        if b.hovered(click_pos, t):
                            go(key)
                            break
                elif state == "tools":
                    if tools_screen.click(click_pos):
                        sound.play("click")
                elif state == "levels":
                    res = levels.click(click_pos, done)
                    if res and res[0] == "chapter":
                        sound.play("click")
                    elif res and res[0] == "level":
                        _, ch, n = res
                        sound.play("click")
                        if ch == 0 and n in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15):   # Chapter 1 / Level 1-11 = asol game
                            set_cursor(False)
                            mod = {1: level1, 2: level2, 3: level3, 4: level4, 5: level5, 6: level6,
                                   7: level7, 8: level8, 9: level9, 10: level10, 11: level11, 12: level12, 13: level13, 14: level14, 15: level15}[n]
                            r = mod.run(screen, clock, save, save_fn)
                            sound.play_music("menu", loops=-1)
                            if r["won"]:
                                complete_level(save, 0, n)
                                save["stars"][0][n - 1] = max(save["stars"][0][n - 1], r["stars"])
                                write_save(save)
                            levels.page_t = 3.0                  # tile gulo sathe sathe dekhabe
                            fade_in = 0.3
                            continue
                        sound.play("roar" if n == LEVELS else "chime")
                        coming = make_level_soon(ch, n)
                        soon_level = (ch, n)
                        soon_t = 0.0
                        soon_from = "levels"
                        state = "soon"

        # kena / bodlano jinish save koro
        if settings_screen.dirty:
            settings_screen.dirty = False
            write_save(save)
        if special_screen.dirty:
            special_screen.dirty = False
            write_save(save)
        if ninja_screen.dirty:
            ninja_screen.dirty = False
            write_save(save)
        if state == "pc" and pc.want_close:
            state = "menu"
            buttons = make_buttons(True)

        while pending and t >= pending[0][0]:
            sound.play(pending.pop(0)[1], 0.8)

        stars.update()
        embers.update()
        screen.fill(BG)
        stars.draw(screen, fade_in)
        embers.draw(screen, fade_in)

        if state == "menu":
            draw_logo(screen, (cx, 68), t, scale=0.42, appear=min(1.0, t / 0.8))
            if FX_LOGO():
                by = get_font(15).render("BY ABU BAKKAR", True, GOLD)
                by.set_alpha(int(255 * min(1.0, t / 1.2)))
                screen.blit(by, by.get_rect(center=(cx, 148)))
            if not FX_LOGO():
                title.draw(screen, t)
            menus.draw_wallet(screen, save, 28)
            hover_key = None
            for key, b in buttons.items():
                b.draw(screen, t, mouse)
                if b.hovered(mouse, t):
                    hover_key = key
            if hover_key and hover_key != last_hover:
                sound.play("hover")
            if hover_key:
                menu_sel = list(buttons).index(hover_key)
            last_hover = hover_key
            fb = buttons[list(buttons)[menu_sel]]
            if fb.ready(t):                                  # keyboard / controller focus
                pygame.draw.rect(screen, (255, 230, 120), fb.rect.inflate(16, 10), 3, border_radius=20)
            set_cursor(hover_key)
        elif state == "levels":
            levels.draw(screen, lv_t, mouse, save)
            target = levels.hover_target(mouse, done)
            clickable = target in ("prev", "next") or (isinstance(target, tuple) and target[2])
            if target != last_hover and target is not None:
                sound.play("hover")
            last_hover = target
            set_cursor(clickable)
        elif state == "tools":
            tools_screen.draw(screen, tools_t, mouse, save["money"])
            set_cursor(tools_screen.index_at(mouse) is not None)
        elif state == "settings":
            settings_screen.draw(screen, mouse)
            set_cursor(False)
        elif state == "special":
            special_screen.draw(screen, mouse)
            set_cursor(False)
        elif state == "ninjas":
            ninja_screen.draw(screen, mouse)
            set_cursor(False)
        elif state == "pc":
            pc.draw(screen, mouse)
            set_cursor(False)
        else:
            last_hover = None
            set_cursor(False)
            coming.draw(screen, soon_t)

        if state == "menu" and not tut.active:
            hot = tut_btn.collidepoint(mouse)
            pygame.draw.rect(screen, rgb_color(t, offset=0.9) if hot else (34, 34, 58), tut_btn, border_radius=12)
            pygame.draw.rect(screen, WHITE if hot else (95, 95, 125), tut_btn, 3, border_radius=12)
            img = get_font(18).render("? TUTORIAL  (T)", True, (15, 15, 25) if hot else WHITE)
            screen.blit(img, img.get_rect(center=tut_btn.center))
            hot = trl_btn.collidepoint(mouse)
            if trl_thumb:
                screen.blit(trl_thumb, trl_btn)
                if not hot:                                  # hover na hole ektu dim
                    dim = pygame.Surface(trl_btn.size, pygame.SRCALPHA)
                    dim.fill((0, 0, 0, 90))
                    screen.blit(dim, trl_btn)
            else:
                pygame.draw.rect(screen, (34, 34, 58), trl_btn)
            pc_ = trl_btn.center                              # play icon (lekha nai)
            rr = 20 + (3 if hot else int(2 * math.sin(t * 4)))
            pygame.draw.circle(screen, (15, 15, 25), pc_, rr + 3)
            pygame.draw.circle(screen, rgb_color(t, offset=0.4) if hot else WHITE, pc_, rr, 3)
            pygame.draw.polygon(screen, WHITE, [(pc_[0] - 7, pc_[1] - 11), (pc_[0] - 7, pc_[1] + 11), (pc_[0] + 12, pc_[1])])
            pygame.draw.rect(screen, rgb_color(t, offset=0.4) if hot else (95, 95, 125), trl_btn, 3, border_radius=4)
        if state == "menu" and not tut.active:
            hot = code_btn.collidepoint(mouse)
            pygame.draw.rect(screen, rgb_color(t, offset=0.7) if hot else (34, 34, 58), code_btn, border_radius=12)
            pygame.draw.rect(screen, WHITE if hot else (95, 95, 125), code_btn, 3, border_radius=12)
            img = get_font(18).render("CODE (C)", True, (15, 15, 25) if hot else WHITE)
            screen.blit(img, img.get_rect(center=code_btn.center))
        if state == "menu" and not tut.active:
            hot = ninja_btn.collidepoint(mouse)
            pygame.draw.rect(screen, rgb_color(t, offset=0.2) if hot else (34, 34, 58), ninja_btn, border_radius=12)
            pygame.draw.rect(screen, WHITE if hot else (95, 95, 125), ninja_btn, 3, border_radius=12)
            img = get_font(18).render("NINJAS (N)", True, (15, 15, 25) if hot else WHITE)
            screen.blit(img, img.get_rect(center=ninja_btn.center))
        if state == "menu" and not tut.active:
            hot = play3d_btn.collidepoint(mouse)
            pygame.draw.rect(screen, rgb_color(t, offset=0.35) if hot else (34, 34, 58), play3d_btn, border_radius=12)
            pygame.draw.rect(screen, WHITE if hot else (110, 240, 150), play3d_btn, 3, border_radius=12)
            img = get_font(18).render("PLAY 3D NINJA (3)", True, (15, 15, 25) if hot else WHITE)
            screen.blit(img, img.get_rect(center=play3d_btn.center))
        if state == "menu" and not tut.active:
            mods.menu_draw(screen)
            hot = mods_btn.collidepoint(mouse)
            col = (110, 240, 150) if mods.security == "on" else ((255, 110, 110) if mods.security == "off" else (150, 190, 255))
            pygame.draw.rect(screen, rgb_color(t, offset=0.5) if hot else (34, 34, 58), mods_btn, border_radius=12)
            pygame.draw.rect(screen, WHITE if hot else col, mods_btn, 3, border_radius=12)
            n = mods.active_count()
            img = get_font(18).render("MODS (M)" + (" %d" % n if n else ""), True, (15, 15, 25) if hot else WHITE)
            screen.blit(img, img.get_rect(center=mods_btn.center))
        tut.draw(screen)
        mods_panel.draw(screen, mouse)
        code_box.draw(screen)

        if toast_t > 0:
            img = get_font(26).render(toast, True, (110, 240, 150))
            screen.blit(img, img.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

        fade_overlay(screen, 1.0 - fade_in / 0.8)
        pygame.display.flip()


if __name__ == "__main__":
    pygame.init()
    scr = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    sound.init()
    try:
        sound.set_master(load_save()["laptop"]["volume"])
    except Exception:
        pass
    run(scr, pygame.time.Clock())
