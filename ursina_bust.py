"""
ursina_bust.py - REAL 3D "BUSTED!" arrest animation (URSINA engine).

Install:   pip install ursina
Game (bust_ursina.py) ei file ta alada process e chalay.  Ursina na thakle / error hole game nijer bust3d.py (pygame 3D) use kore.

Manual test:   python ursina_bust.py            (ESC / SPACE = skip)
Options:       --duration 10.4     --rounds 3     --test (offscreen, shorter)

Scene:  police ninja ke handcuff pore jail cell e niye jay, camera ghure (orbit) dekhay, lohar dorja khule bondho hoy,
        BUSTED! text pop kore.  (shob model Ursina cube / sphere diye bana - kono extra file lage na)
Exit code 0 = shesh holo,  1 = error (game fallback use korbe).
"""
import math
import sys

TEST = "--test" in sys.argv


def _arg(name, default):
    if name in sys.argv:
        try:
            return float(sys.argv[sys.argv.index(name) + 1])
        except (ValueError, IndexError):
            pass
    return default


DURATION = _arg("--duration", 10.4)
ROUNDS = int(_arg("--rounds", 3))
if TEST:
    DURATION = min(DURATION, 2.0)

try:
    if TEST:
        from panda3d.core import loadPrcFileData
        loadPrcFileData("", "window-type offscreen\naudio-library-name null\nload-display p3tinydisplay")
    from ursina import *            # noqa: F401,F403
    app = Ursina(title="ABIX NINJA - BUSTED!", borderless=False, development_mode=False,
                 editor_ui_enabled=False, vsync=True,
                 window_type="offscreen" if TEST else "onscreen")
except Exception as ex:             # ursina nei / window khola gelo na
    print("ursina failed:", ex)
    sys.exit(1)


def C(r, g, b, a=255):
    return Color(r / 255, g / 255, b / 255, a / 255)


def clamp01(v):
    return 0.0 if v < 0 else (1.0 if v > 1 else v)


def ease(k):
    k = clamp01(k)
    return k * k * (3 - 2 * k)


def seg(t, a, b):
    return clamp01((t - a) / (b - a))


window.color = C(6, 8, 18)
try:
    window.fps_counter.enabled = False
    window.exit_button.visible = False
    window.cog_button.enabled = False
except Exception:
    pass

# ------------------------------------------------------------------ world
FLOOR_Y = 0.0
floor = Entity(model="cube", scale=(60, 0.4, 26), y=-0.2, x=6, color=C(46, 48, 62),
               texture="white_cube", texture_scale=(60, 26))
back_wall = Entity(model="cube", scale=(60, 9, 0.5), position=(6, 4.5, 8), color=C(30, 40, 78))
stripe = Entity(model="cube", scale=(60, 0.5, 0.6), position=(6, 4.2, 7.7), color=C(70, 120, 240))
ceiling_lamps = []
for lx in (-8, 0, 8, 16):
    Entity(model="cube", scale=(2.4, 0.15, 0.5), position=(lx, 8.2, 6.6), color=C(255, 244, 200))
    ceiling_lamps.append(lx)
# police badge on wall
Entity(model="sphere", scale=(2.6, 2.6, 0.3), position=(-6, 5.2, 7.6), color=C(230, 200, 60))
Entity(model="sphere", scale=(2.0, 2.0, 0.35), position=(-6, 5.2, 7.5), color=C(30, 50, 130))

# jail cell (x 10 .. 16)
CELL_X0, CELL_X1 = 10.0, 16.0
cell_floor = Entity(model="cube", scale=(CELL_X1 - CELL_X0, 0.1, 6), position=((CELL_X0 + CELL_X1) / 2, 0.05, 3.5),
                    color=C(60, 58, 50))
Entity(model="cube", scale=(0.3, 6, 6), position=(CELL_X1, 3, 3.5), color=C(70, 74, 92))      # side wall
bars_col = C(170, 176, 190)
for bx in range(0, 7):                                                                         # back bars
    Entity(model="cube", scale=(0.12, 6, 0.12), position=(CELL_X0 + bx, 3, 6.4), color=bars_col)
for bz in (0.6, 1.9, 3.2, 4.5, 5.8):                                                           # side bars (front face with door gap)
    Entity(model="cube", scale=(0.12, 6, 0.12), position=(CELL_X0, 3, bz), color=bars_col)
Entity(model="cube", scale=(CELL_X1 - CELL_X0, 0.15, 0.15), position=((CELL_X0 + CELL_X1) / 2, 6, 0.3), color=bars_col)
bunk = Entity(model="cube", scale=(2.6, 0.4, 1.2), position=(CELL_X1 - 1.8, 0.9, 5.6), color=C(80, 70, 60))

# door (hinge on z = 0.3 side, swings in the x-z plane)
door_hinge = Entity(position=(CELL_X0, 0, 0.3))
for dz in range(0, 5):
    Entity(parent=door_hinge, model="cube", scale=(0.12, 6, 0.12), position=(0, 3, 0.4 + dz * 1.0), color=bars_col)
Entity(parent=door_hinge, model="cube", scale=(0.12, 0.15, 4.4), position=(0, 5.9, 2.4), color=bars_col)
Entity(parent=door_hinge, model="cube", scale=(0.12, 0.15, 4.4), position=(0, 0.3, 2.4), color=bars_col)
door_hinge.rotation_y = -105.0         # khola


# ------------------------------------------------------------------ people
def make_person(shirt, pants, skin, hat=None, mask=None):
    root = Entity()
    body = Entity(parent=root, model="cube", scale=(0.9, 1.3, 0.55), y=1.75, color=shirt)
    Entity(parent=root, model="cube", scale=(0.92, 0.18, 0.57), y=1.15, color=C(30, 24, 20))          # belt
    head = Entity(parent=root, model="cube", scale=(0.62, 0.62, 0.62), y=2.75, color=skin)
    if hat:
        Entity(parent=root, model="cube", scale=(0.7, 0.25, 0.7), y=3.12, color=hat)
        Entity(parent=root, model="cube", scale=(0.7, 0.06, 0.4), y=3.0, z=-0.45, color=hat)
    if mask:
        Entity(parent=root, model="cube", scale=(0.66, 0.3, 0.66), y=2.75, color=mask)
        Entity(parent=root, model="cube", scale=(0.4, 0.07, 0.02), y=2.78, z=-0.34, color=C(255, 255, 255))   # eyes slit
    legs, arms = [], []
    for sx in (-0.25, 0.25):
        pivot = Entity(parent=root, position=(sx, 1.1, 0))
        Entity(parent=pivot, model="cube", scale=(0.4, 1.1, 0.45), y=-0.55, color=pants)
        legs.append(pivot)
    for sx in (-0.62, 0.62):
        pivot = Entity(parent=root, position=(sx, 2.3, 0))
        Entity(parent=pivot, model="cube", scale=(0.3, 1.0, 0.35), y=-0.5, color=shirt)
        Entity(parent=pivot, model="cube", scale=(0.26, 0.26, 0.3), y=-1.05, color=skin)
        arms.append(pivot)
    root.legs, root.arms, root.head, root.body = legs, arms, head, body
    return root


cop = make_person(C(34, 52, 112), C(18, 20, 34), C(224, 180, 150), hat=C(16, 22, 58))
ninja = make_person(C(24, 24, 32), C(14, 14, 20), C(224, 180, 150), mask=C(24, 24, 32))
Entity(parent=ninja, model="cube", scale=(0.7, 0.14, 0.7), y=2.95, color=C(220, 40, 50))           # headband
Entity(parent=ninja, model="cube", scale=(0.5, 0.12, 0.1), y=2.9, z=0.42, x=0.3, color=C(220, 40, 50))
# cop badge
Entity(parent=cop, model="sphere", scale=(0.22, 0.22, 0.06), position=(0.25, 2.15, -0.3), color=C(240, 210, 70))
# handcuffs (ninja hands behind)
cuffs = [Entity(parent=ninja, model="sphere", scale=(0.28, 0.14, 0.28), position=(sx, 1.2, 0.38), color=C(200, 204, 214))
         for sx in (-0.15, 0.15)]
Entity(parent=ninja, model="cube", scale=(0.34, 0.05, 0.05), position=(0, 1.2, 0.38), color=C(200, 204, 214))
# siren light on cop shoulder
siren = Entity(parent=cop, model="sphere", scale=0.2, position=(-0.5, 2.55, 0), color=C(255, 50, 60))

for p_ in (cop, ninja):
    p_.rotation_y = 90          # +x dike mukh
cop.x, ninja.x = -14.0, -11.6
cop.z = ninja.z = 2.2

title = Text(text="BUSTED!", origin=(0, 0), scale=5, y=0.12, color=C(255, 70, 80), enabled=False)
sub = Text(text="ELITE POLICE took you to JAIL  -  %d / %d catches" % (ROUNDS, ROUNDS), origin=(0, 0), scale=1.4,
           y=-0.02, color=C(255, 230, 150), enabled=False)
hint = Text(text="ESC / SPACE = skip", origin=(0.5, 0), x=0.62, y=-0.46, scale=0.9, color=C(180, 180, 200))
bar_top = Entity(parent=camera.ui, model="quad", scale=(2, 0.12), y=0.47, color=C(0, 0, 0, 230))
bar_bot = Entity(parent=camera.ui, model="quad", scale=(2, 0.12), y=-0.47, color=C(0, 0, 0, 230))
flash_q = Entity(parent=camera.ui, model="quad", scale=(3, 2), color=C(255, 255, 255, 0), z=-1)

T = {"t": 0.0, "shake": 0.0, "clang": False}
WALK_END, DOOR_OPEN, ENTER, DOOR_SHUT, CLANG = 5.2, (5.0, 5.9), (5.9, 7.2), (7.4, 8.3), 8.3


def swing(person, t, amp, speed=7.0):
    for i, leg in enumerate(person.legs):
        leg.rotation_x = math.sin(t * speed + i * math.pi) * amp
    person.y = abs(math.sin(t * speed)) * 0.06 * (amp / 35.0)


def update():
    dt = time.dt
    t = T["t"] = T["t"] + dt
    # ---- positions ----
    walk_k = ease(seg(t, 0.0, WALK_END))
    enter_k = ease(seg(t, ENTER[0], ENTER[1]))
    ninja.x = -11.6 + walk_k * (CELL_X0 - 1.2 + 11.6) + enter_k * 4.2
    cop.x = ninja.x - 2.4 if t < ENTER[0] else (CELL_X0 - 3.6 + ease(seg(t, ENTER[0], ENTER[0] + 0.3)) * 0.4)
    walking = t < WALK_END or ENTER[0] < t < ENTER[1]
    swing(ninja, t, 30 if walking else 0)
    swing(cop, t + 0.4, 32 if t < WALK_END else 0)
    for a in ninja.arms:
        a.rotation_x = -75 if t < CLANG else -15          # hat pichone
    cop.arms[0].rotation_x = math.sin(t * 7) * 30 if t < WALK_END else 0
    cop.arms[1].rotation_x = -80 if ENTER[0] < t < ENTER[1] else (0 if t >= WALK_END else -math.sin(t * 7) * 30)
    ninja.head.rotation_x = 8 + math.sin(t * 2) * 3
    siren.color = C(255, 50, 60) if int(t * 6) % 2 == 0 else C(70, 120, 255)
    # ---- door ----
    if t < DOOR_OPEN[0]:
        door_hinge.rotation_y = 0.0
    elif t < DOOR_SHUT[0]:
        door_hinge.rotation_y = -105.0 * ease(seg(t, DOOR_OPEN[0], DOOR_OPEN[1]))
    else:
        door_hinge.rotation_y = -105.0 * (1 - ease(seg(t, DOOR_SHUT[0], DOOR_SHUT[1])))
    # ---- clang ----
    if t >= CLANG and not T["clang"]:
        T["clang"] = True
        T["shake"] = 0.6
        title.enabled = sub.enabled = True
    if T["clang"]:
        k = t - CLANG
        title.scale = 5 + 1.5 * max(0.0, 1 - k * 4) + math.sin(k * 3) * 0.1
        ninja.rotation_y = 90 + 90 * ease(seg(k, 0.0, 0.8))        # cell er dike ghure
        a = max(0.0, 0.6 - k * 2.0)
        flash_q.color = C(255, 255, 255, int(255 * a))
    # ---- camera orbit ----
    tx = ninja.x * 0.6 + cop.x * 0.4 if t < ENTER[0] else ninja.x
    ang = -0.55 + ease(seg(t, 0.0, DURATION)) * 2.3 + (0.2 if T["clang"] else 0.0)
    dist = 13.0 - 3.0 * ease(seg(t, 4.0, 8.0))
    camera.x = tx + math.sin(ang) * dist * 0.55
    camera.z = 2.2 - math.cos(ang) * dist
    camera.y = 3.4 + math.sin(t * 0.7) * 0.25 + 1.2 * ease(seg(t, 0.0, 3.0))
    if T["shake"] > 0:
        T["shake"] = max(0.0, T["shake"] - dt)
        camera.x += math.sin(t * 90) * T["shake"] * 0.3
        camera.y += math.cos(t * 77) * T["shake"] * 0.3
    camera.look_at(Vec3(tx, 1.9, 2.4))
    if t >= DURATION + 0.6:
        application.quit()


def input(key):
    if key in ("escape", "space", "enter"):
        application.quit()


try:
    app.run()
    sys.exit(0)
except SystemExit:
    raise
except Exception as ex:
    print("ursina error:", ex)
    sys.exit(1)
