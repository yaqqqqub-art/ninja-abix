"""
police.py - POLICE update.

Ninja jekhane thake, police shekhane chole ashe ar bole  "You little thief!".

  * Kokhon ashe?   Guard dekhle / camera dekhle / laser chhuile / alarm hole  (POLICE_MODE = "alarm")
                   Shob shomoy chaile  POLICE_MODE = "always"  koro.
  * Ki kore?       Dour diye ninja r kache jay, "You little thief!" bole, dhorle 1 health kome (1.4 sec por por).
  * Kibhabe bachbe? - Police er speed (215) ninja r (250) cheye kom, dour dao.
                    - Ledge / upore uthle police nichei dariye chilay.
                    - Lukale (hide) police last jaygay jay, tarpor khujte thake, shesh e chole jay.
                    - Knife / Punch dile police 6 second KO hoy (mare na).
                    - Door / laser police ke atkay.
  * Shob level e kaj kore (World class er upor hook, level file bodlano lage na).
  * Settings e save["settings"]["police"] = False korle bondho.

Shudhu  police.install()  ekbar chalate hoy (main_game.py te kora ache).

LEVEL 11 - ELITE POLICE  (world e  ELITE_POLICE = {...}  thakle chalu hoy; level11.py dekho)
  * Shob shomoy ashe (always), 5 HP.   KNIFE = 1 HP,  SUPER PUNCH = 2 HP  (3 punch e KO).
  * GOD MODE:  police er SHAMNE (je dik e mukh) theke knife / punch kaj kore na!  Pichon theke mara lagbe.
    Lafiye pichone jao - police ghurte 0.45 sec shomoy nei (tokhon e mar).
  * CATCH BAR:  police ninja ke dhorle ninja r matha r upor bar bhore.  SPACE/W mere (mash) bar komao ba dour dao.
    Bar bhore gele  CAUGHT 1/3.  3 bar dhora porle  ->  3D animation e police tomake JAIL e niye jay.
"""
import math
import random

import pygame

import hd_animation as HD
import level1 as L1
import sound
import sprites as SP
from animation import WIDTH, get_font

POLICE_MODE = "alarm"        # "alarm" | "always"
MAX_COPS = 3
COP_SPEED = 215.0
LEAVE_SPEED = 170.0
HEAT_TIME = 9.0              # alarm er por koto second police thake
SPAWN_EVERY = 5.5
GRAB_CD = 1.4
KO_TIME = 6.0
KNIFE_REACH = L1.KNIFE_REACH + 34

ELITE_DEFAULT = {"from": 0, "max": 3, "hp": 5, "knife": 1, "punch": 2, "catch_time": 1.5, "catch_max": 3,
                 "spawn_every": 7.0, "turn": 0.45, "speed": 200.0, "ko_time": 10.0}

SHOUTS = ["You little thief!", "You little thief, stop!", "Stop right there!", "Don't run, thief!", "Get that thief!"]
GRABS = ["Got you!", "Caught you, thief!"]
LOST = ["Where did that thief go?", "Come out, you little thief!", "He's hiding somewhere..."]

ELITE_PAL = {"shirt": (24, 26, 40), "shirt_d": (12, 14, 26), "shirt_l": (60, 64, 92),
             "pants": (10, 10, 18), "pants_l": (34, 34, 52), "navy": (10, 12, 24), "navy_l": (34, 38, 70)}

POLICE_PAL = {"shirt": (34, 52, 112), "shirt_d": (22, 34, 80), "shirt_l": (62, 88, 160),
              "pants": (18, 20, 34), "pants_l": (40, 44, 70), "navy": (16, 22, 58), "navy_l": (40, 52, 104)}


class Cop:
    HW, HH = 30, 60

    def __init__(self, x, facing, elite=None):
        self.x, self.facing = x, facing
        self.elite = elite                       # None = shadharon police, dict = ELITE police
        self.hp = self.max_hp = (elite or {}).get("hp", 1)
        self.turn_t = 0.0                        # ghurte shomoy lage (pichon khola thake)
        self.stagger = 0.0                       # mar khele ghurte / chalte pare na
        self.god_t = 0.0                         # GOD MODE shield flash
        self.state = "run"           # run | search | leave | ko
        self.anim_t = random.uniform(0, 5)
        self.bubble, self.bubble_t = "", 0.0
        self.talk = random.uniform(1.2, 2.5)
        self.grab_cd = 0.0
        self.grab_t = 0.0
        self.ko_t = 0.0
        self.age = 0.0

    def say(self, text, secs=2.0):
        self.bubble, self.bubble_t = text, secs

    def rect(self):
        return pygame.Rect(int(self.x - self.HW / 2), L1.GROUND_Y - self.HH, self.HW, self.HH)


# ------------------------------------------------------------------
def _st(w):
    st = getattr(w, "_pol", None)
    if st is None or st["p"] is not w.p:             # notun level / respawn = notun hishab
        st = w._pol = {"p": w.p, "cops": [], "heat": 0.0, "spawn_cd": 0.5, "seen_x": w.p.x,
                       "hid_t": 0.0, "pf": bool(getattr(w.p, "punch_fired", False)), "banner": 0.0,
                       "kt": 0.0, "jb": 0.0, "bar": 0.0, "catch": 0, "decay": 0.0, "bust": False, "hint": 0.0}
    return st


def _heat_source(w):
    for g in getattr(w, "guards", []):
        if getattr(g, "alive", False) and (getattr(g, "state", "") in ("aim", "shoot", "recover")
                                           or getattr(g, "alert", 0) > 0):
            return True
    for c in getattr(w, "cams", []):
        if getattr(c, "danger", 0) > 0.05 and not getattr(c, "hacked", False):
            return True
    return getattr(w, "extra_danger", 0) > 0.05


def _cfg(w):
    """Elite police config (level 11) ba None."""
    c = getattr(w, "ELITE_POLICE", None)
    if not c:
        return None
    d = dict(ELITE_DEFAULT)
    d.update(c)
    return d


def _clear_path(w, x0, x1):
    """x0 theke x1 er moddhe door / laser nei?  (nahole police atke thakbe)"""
    try:
        lo, hi = min(x0, x1), max(x0, x1)
        for r in w.solids():
            if r.top < L1.GROUND_Y - 20 and r.right > lo and r.left < hi and r.bottom > L1.GROUND_Y - 40:   # floor bad (V12 fix)
                return False
    except Exception:
        pass
    return True


def _level_w(w):
    return getattr(w, "level_w", L1.LEVEL_W)


def _spawn(w, st, first=False, cfg=None):
    p = w.p
    lw = _level_w(w)
    cam = w.cam
    sides = [-1, 1]
    random.shuffle(sides)
    x = None
    for s in sides:                                   # screen er baire theke ashe
        cx = cam - 150 if s < 0 else cam + WIDTH + 150
        if 30 <= cx <= lw - 30 and abs(cx - p.x) > 420:
            x = cx
            break
    if x is None:
        x = max(30, min(lw - 30, cam + WIDTH + 150 if p.x < lw / 2 else cam - 150))
    if cfg and not _clear_path(w, x, p.x):             # elite police door er opashe spawn hobe na
        return None
    c = Cop(x, 1 if p.x > x else -1, cfg)
    c.say(SHOUTS[0] if first else random.choice(SHOUTS), 2.4)
    st["cops"].append(c)
    return c


def update(w, dt):
    if getattr(w, "_pol_off", False):
        return
    if w.state != "play" or w.paused or w.wheel or w.modal:
        return
    if not w.save.get("settings", {}).get("police", True):
        return
    p = w.p
    if not p.alive:
        return
    st = _st(w)
    cops = st["cops"]
    lw = _level_w(w)
    cfg = _cfg(w)
    HD.get(w).update(dt)

    # ---- heat (police ashbe ki na) ----
    if cfg:
        if p.x >= cfg["from"]:
            if st["heat"] <= 0 and not cops:
                st["spawn_cd"] = 1.0
            st["heat"] = HEAT_TIME
        else:
            st["heat"] = max(0.0, st["heat"] - dt)
    elif POLICE_MODE == "always" or _heat_source(w):
        if st["heat"] <= 0 and not cops:
            st["spawn_cd"] = 0.0
        st["heat"] = HEAT_TIME
    else:
        st["heat"] = max(0.0, st["heat"] - dt)

    # ---- player kothay ----
    if p.hidden:
        st["hid_t"] += dt
    else:
        st["hid_t"] = 0.0
        st["seen_x"] = p.x

    # ---- spawn ----
    st["spawn_cd"] -= dt
    active = [c for c in cops if c.state in ("run", "search")]
    if st["heat"] > 0 and len(active) < (cfg["max"] if cfg else MAX_COPS) and st["spawn_cd"] <= 0 and not st["bust"]:
        first = not cops
        newc = _spawn(w, st, first, cfg)
        if newc is None:
            st["spawn_cd"] = 1.0                       # path atka - ektu pore abar chesta
        else:
            st["spawn_cd"] = 0.9 if first else (cfg["spawn_every"] if cfg else SPAWN_EVERY)
            if first:
                sound.play("siren", 0.7)
                st["banner"] = 4.5 if cfg else 3.0
                try:
                    L1.speak(SHOUTS[0])
                except Exception:
                    pass
    st["banner"] = max(0.0, st["banner"] - dt)

    # ---- player er attack (knife / punch) ----
    pf = bool(getattr(p, "punch_fired", False))
    punched = pf and not st["pf"]
    st["pf"] = pf
    stabbing = getattr(p, "knife_t", 0.0) > 0
    kt = getattr(p, "knife_t", 0.0)
    stab_new = kt > st["kt"] + 1e-6                   # notun knife swing (elite er jonno 1 swing = 1 hit)
    st["kt"] = kt
    jb = getattr(p, "jump_buf", 0.0)
    jump_press = jb > 0.1 and st["jb"] <= 0.1         # SPACE/W/UP notun chapa
    st["jb"] = jb

    try:
        solids = [r for r in w.solids() if r.height < 900]       # mati (floor) bad
    except Exception:
        solids = []
    cam_mid = w.cam + WIDTH / 2
    near_cop = None

    for c in cops:
        c.anim_t += dt
        c.age += dt
        c.grab_cd = max(0.0, c.grab_cd - dt)
        c.grab_t = max(0.0, c.grab_t - dt)
        c.bubble_t = max(0.0, c.bubble_t - dt)
        dx = p.x - c.x

        c.stagger = max(0.0, c.stagger - dt)
        c.god_t = max(0.0, c.god_t - dt)

        if c.state == "ko":
            c.ko_t -= dt
            if c.ko_t <= 0:
                c.state = "run"
                if c.elite:
                    c.hp = max(3, c.hp)
                c.say("Ow... You little thief!", 2.0)
            continue

        # ---- ELITE: GOD MODE samne, 5 knife / 3 punch pichon theke ----
        if c.elite:
            tried = False
            if stab_new and abs(p.y - L1.GROUND_Y) < 90 and -12 <= (c.x - p.x) * p.facing <= KNIFE_REACH:
                tried = _elite_hit(w, c, p, c.elite["knife"], "KNIFE")
            if punched and abs(c.x - p.x) <= L1.PUNCH_RADIUS and abs(p.y - L1.GROUND_Y) < 90:
                tried = _elite_hit(w, c, p, c.elite["punch"], "SUPER PUNCH") or tried
            if c.state == "ko":
                continue

        # knife / punch
        if not c.elite and stabbing and abs(p.y - L1.GROUND_Y) < 90 and -12 <= (c.x - p.x) * p.facing <= KNIFE_REACH:
            _knock(w, c)
            continue
        if not c.elite and punched and abs(c.x - p.x) <= L1.PUNCH_RADIUS and abs(p.y - L1.GROUND_Y) < 90:
            _knock(w, c)
            continue

        # state change
        if c.state in ("run", "search") and st["heat"] <= 0:
            c.state = "leave"
            c.say("Next time, thief!", 2.0)
        elif c.state == "run" and st["hid_t"] > 2.5:
            c.state = "search"
            c.say(random.choice(LOST), 2.4)
        elif c.state == "search" and st["hid_t"] <= 0:
            c.state = "run"
            c.say(random.choice(SHOUTS), 2.0)

        if c.state == "leave":
            d = -1 if c.x < cam_mid else 1
            c.facing = d
            c.x += d * LEAVE_SPEED * dt
            continue

        target = st["seen_x"]
        tdx = target - c.x
        move = 0
        if abs(tdx) > 46:
            move = 1 if tdx > 0 else -1
        elif c.state == "search":
            move = 0 if int(c.anim_t * 0.9) % 2 else (1 if int(c.anim_t * 0.45) % 2 else -1)
            c.facing = move or c.facing
        if c.elite:                                   # ghurte shomoy lage, mar khele thome jay
            want = 1 if dx > 0 else -1
            if c.stagger > 0:
                move = 0
            elif c.state == "run" and abs(dx) > 8 and want != c.facing:
                c.turn_t += dt
                move = 0
                if c.turn_t >= c.elite["turn"]:
                    c.facing, c.turn_t = want, 0.0
            else:
                c.turn_t = 0.0
        if move:
            if c.state == "search" and abs(tdx) <= 46:
                spd = COP_SPEED * 0.3
            else:
                spd = c.elite["speed"] if c.elite else COP_SPEED
            nx = c.x + move * spd * dt
            test = pygame.Rect(int(nx - 15), L1.GROUND_Y - 52, 30, 46)
            if any(test.colliderect(r) for r in solids):          # door / laser atkay
                move = 0
            else:
                c.x = max(20.0, min(lw - 20.0, nx))
            if not c.elite:
                c.facing = move or (1 if dx > 0 else -1)
            elif move:
                c.facing = move
        elif abs(dx) > 8 and c.state == "run" and not c.elite:
            c.facing = 1 if dx > 0 else -1

        if c.elite and c.state == "run" and c.stagger <= 0 and not p.hidden and abs(dx) < 58 \
                and abs(p.y - L1.GROUND_Y) < 70:
            near_cop = c                              # dhorar range e
            c.grab_t = 0.25

        # chilla'na
        c.talk -= dt
        if c.talk <= 0 and c.bubble_t <= 0 and abs(c.x - w.cam - WIDTH / 2) < WIDTH * 0.75:
            c.talk = random.uniform(3.0, 5.0)
            c.say(random.choice(SHOUTS), 1.8)

        # dhora
        if (not c.elite and c.state == "run" and c.grab_cd <= 0 and not p.hidden and abs(dx) < 52
                and abs(p.y - L1.GROUND_Y) < 70):
            c.grab_cd = GRAB_CD
            c.grab_t = 0.45
            c.say(random.choice(GRABS), 1.2)
            sound.play("punch", 0.6)
            w.hurt_player(1 if dx > 0 else -1, "police")
            if w.state != "play":
                return

    # ---- ELITE: CATCH BAR ----
    if cfg:
        if near_cop is not None and p.inv <= 0:
            st["bar"] = min(1.0, st["bar"] + dt / cfg["catch_time"])
            st["decay"] = 0.0
        else:
            st["bar"] = max(0.0, st["bar"] - dt * 0.9)
        if st["bar"] > 0 and jump_press:                  # SPACE / W mere chharano
            st["bar"] = max(0.0, st["bar"] - 0.2)
            sound.play("hover", 0.4)
        if st["catch"] > 0 and st["bar"] <= 0:
            st["decay"] += dt
            if st["decay"] > 22.0:                        # onek khon na dhorle 1 ta catch mafe
                st["catch"] -= 1
                st["decay"] = 0.0
        if st["bar"] >= 1.0 and near_cop is not None and not st["bust"]:
            st["bar"] = 0.0
            st["catch"] += 1
            w.floats.append({"x": p.x, "y": p.y - 100, "t": 1.4, "txt": f"CAUGHT  {st['catch']} / {cfg['catch_max']}",
                             "c": (255, 90, 90)})
            sound.play("punch", 0.7)
            near_cop.say(random.choice(GRABS), 1.4)
            if st["catch"] >= cfg["catch_max"] and hasattr(w, "start_bust"):
                st["bust"] = True
                w.start_bust(near_cop)
                return
            d = 1 if p.x > near_cop.x else -1             # dhakka diye soriye dey
            p.vx, p.vy, p.on_ground = d * 380, -240, False
            p.inv = 1.6
            w.shake, w.red_flash = 0.3, 0.2
            for c2 in cops:
                if c2.state == "run":
                    c2.stagger = 0.7

    # chole geche / onek dure
    st["cops"] = [c for c in cops if not (c.state == "leave" and (abs(c.x - cam_mid) > WIDTH / 2 + 260
                                                                  or c.age > 60 or c.x < -100 or c.x > lw + 100))]


def _elite_hit(w, c, p, dmg, what):
    """ELITE police e hit.  Samne = GOD MODE (kono kaj nei).  Pichon = damage.  True = hit try hoyeche."""
    front = (p.x - c.x) * c.facing > 0               # police ninja r dike mukh kore ache
    hd = HD.get(w)
    if front and c.stagger <= 0:
        c.god_t = 0.45
        sound.play("hit", 0.6)
        hd.block(c.x, L1.GROUND_Y - 62, c.facing)    # HD GOD MODE animation (ring + shards + stamp)
        return True
    c.hp -= dmg
    c.stagger = 0.65
    c.turn_t = 0.0
    c.x += p.facing * 12
    sound.play("stab" if what == "KNIFE" else "hit", 0.7)
    hd.hit(c.x, L1.GROUND_Y - 56, big=(what != "KNIFE"))
    w.burst(c.x, L1.GROUND_Y - 50, (230, 40, 60), 12, 190, 0.6)
    if c.hp <= 0:
        c.state, c.ko_t, c.hp = "ko", c.elite["ko_time"], 0
        c.say("", 0.0)
        hd.ko(c.x, L1.GROUND_Y - 60)
        w.shake = max(w.shake, 0.2)
    else:
        w.floats.append({"x": c.x, "y": L1.GROUND_Y - 130, "t": 0.9, "txt": f"{what} -{dmg}   ({c.hp}/{c.max_hp})",
                         "c": (255, 150, 150)})
    return True


def _knock(w, c):
    c.state, c.ko_t = "ko", KO_TIME
    c.say("", 0.0)
    sound.play("stab", 0.7)
    w.burst(c.x, L1.GROUND_Y - 34, (255, 255, 160), 10, 170, 0.6)
    w.floats.append({"x": c.x, "y": L1.GROUND_Y - 90, "t": 1.0, "txt": "COP KO!", "c": (150, 190, 255)})


# ------------------------------------------------------------------
def draw(w, surf, cam):
    st = getattr(w, "_pol", None)
    if not st or st["p"] is not w.p:
        return
    t = w.t
    f16 = get_font(16)
    for c in st["cops"]:
        x = c.x - cam
        if x < -120 or x > WIDTH + 120:
            continue
        pal, gs = (ELITE_PAL, 0.72) if c.elite else (POLICE_PAL, 0.62)
        if c.state == "ko":
            SP.draw_guard(surf, x, L1.GROUND_Y, c.facing, t, "dead", pal=pal, s=gs)
            for i in range(3):                                          # ghurche (stars)
                a = t * 5 + i * 2.1
                pygame.draw.circle(surf, (255, 235, 110), (int(x + math.cos(a) * 16), int(L1.GROUND_Y - 24 + math.sin(a) * 4)), 3)
            continue
        if c.grab_t > 0:
            anim = "shoot"
        elif c.state in ("run", "leave") and (abs(c.x - st["seen_x"]) > 46 or c.state == "leave"):
            anim = "walk"
        else:
            anim = "idle"
        SP.draw_guard(surf, x, L1.GROUND_Y, c.facing, c.anim_t * (1.9 if anim == "walk" else 1.0), anim, 0.0,
                      flash=0.0, pal=pal, s=gs)
        if c.elite:
            _draw_elite_extras(surf, c, x, t, f16)
        # siren light (HD cone)
        top = 128 if c.elite else 112
        HD.draw_siren(surf, x + 2, L1.GROUND_Y - top, t, c.facing)
        col = (255, 50, 60) if int(t * 6) % 2 == 0 else (70, 120, 255)
        if c.state in ("run", "search"):
            ex = f16.render("!" if c.state == "run" else "?", True, (255, 60, 60) if c.state == "run" else (255, 210, 90))
            surf.blit(ex, ex.get_rect(center=(x, L1.GROUND_Y - top - 22)))
        if c.bubble_t > 0 and c.bubble:
            SP.draw_speech(surf, c.bubble, (x, L1.GROUND_Y - top - 32), f16, shake=0.0, border=(60, 100, 230))
    HD.get(w).draw(surf, cam)
    if st["banner"] > 0 and st["cops"]:
        on = int(t * 5) % 2 == 0
        col = (255, 70, 80) if on else (90, 140, 255)
        cfg = _cfg(w)
        HD.rgb_text(surf, "ELITE POLICE!" if cfg else "POLICE!  Run, thief!", (WIDTH // 2, 112), 26, t,
                    alpha=int(255 * min(1.0, st["banner"])))
        if cfg:
            sub = get_font(16).render("FRONT = GOD MODE.  Jump over them and stab from BEHIND (5 knife / 3 punch)",
                                      True, (255, 225, 130))
            sub.set_alpha(int(255 * min(1.0, st["banner"])))
            surf.blit(sub, sub.get_rect(center=(WIDTH // 2, 142)))
    if _cfg(w) and w.state == "play":
        _draw_catch_hud(w, surf, cam, st, t)


def _draw_elite_extras(surf, c, x, t, f16):
    """GOD MODE shield (samne), HP bar, ELITE label."""
    gy = L1.GROUND_Y
    if c.state == "run" or c.state == "search":
        # HD GOD MODE shield (hex dome) - samne thake, mar thekale jholke uthe
        HD.draw_god_shield(surf, x, gy, c.facing, t, flash=min(1.0, c.god_t / 0.45), stagger=c.stagger > 0)
        HD.draw_halo(surf, x, gy - 140, t)
    # HP pips
    n, w_ = c.max_hp, 11
    x0 = x - n * w_ / 2
    y0 = gy - 118 if c.state != "ko" else gy - 60
    for i in range(n):
        col = (230, 60, 70) if i < c.hp else (50, 24, 30)
        pygame.draw.rect(surf, col, (x0 + i * w_, y0, w_ - 2, 6), border_radius=2)
    if c.stagger > 0:
        pygame.draw.circle(surf, (255, 255, 255), (int(x - c.facing * 18), gy - 60), 5, 2)


def _draw_catch_hud(w, surf, cam, st, t):
    cfg = _cfg(w)
    p = w.p
    bar, catch = st["bar"], st["catch"]
    if bar > 0.01:                                       # ninja r matha r upor CATCH BAR
        r = pygame.Rect(0, 0, 84, 12)
        r.center = (int(p.x - cam), int(p.y - 118))
        pygame.draw.rect(surf, (20, 10, 14), r.inflate(6, 6), border_radius=7)
        col = (255, 200, 70) if bar < 0.6 else (255, 70, 70)
        pygame.draw.rect(surf, col, (r.x, r.y, int(r.w * bar), r.h), border_radius=5)
        pygame.draw.rect(surf, (255, 255, 255), r, 2, border_radius=5)
        f = get_font(13).render("CAUGHT!  mash SPACE", True, (255, 230, 150))
        surf.blit(f, f.get_rect(midbottom=(r.centerx, r.y - 6)))
    if st["cops"] or catch:                              # ARREST meter (3 handcuff)
        base = pygame.Rect(0, 0, 150, 30)
        base.midtop = (WIDTH // 2, 172)
        bg = pygame.Surface(base.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (8, 10, 24, 180), bg.get_rect(), border_radius=10)
        surf.blit(bg, base.topleft)
        for i in range(cfg["catch_max"]):
            cx, cy = base.x + 28 + i * 47, base.centery
            on = i < catch
            col = (255, 70, 80) if on else (90, 96, 130)
            pygame.draw.circle(surf, col, (cx - 6, cy), 7, 3)
            pygame.draw.circle(surf, col, (cx + 6, cy), 7, 3)
            pygame.draw.line(surf, col, (cx - 2, cy), (cx + 2, cy), 3)
        lab = get_font(12).render("ARREST", True, (200, 205, 230))
        surf.blit(lab, lab.get_rect(midbottom=(base.centerx, base.y - 1)))


# ------------------------------------------------------------------
_installed = False


def install():
    """level1.World (ar tar shob subclass: level 2..10) e police hook bosay."""
    global _installed
    if _installed:
        return
    _installed = True
    W = L1.World
    orig_special = W.special_update
    orig_draw_player = W.draw_player

    def special_update(self, dt):
        orig_special(self, dt)
        try:
            update(self, dt)
        except Exception as ex:                       # police e bug thakleo game crash korbe na
            self._pol_off = True
            print("police disabled:", repr(ex))

    def draw_player(self, surf, cam):
        if not getattr(self, "_pol_off", False):
            try:
                draw(self, surf, cam)
            except Exception as ex:
                self._pol_off = True
                print("police draw disabled:", repr(ex))
        orig_draw_player(self, surf, cam)

    W.special_update = special_update
    W.draw_player = draw_player
