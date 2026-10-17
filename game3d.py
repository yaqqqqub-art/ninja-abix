"""
game3d.py - PLAY 3D NINJA   (pygame raycaster 3D - phone e o cholbe, kono extra install lage na)

main_game.py theke:   game3d.run(screen, clock, save, save_fn)

3 ta 3D LEVEL (proti level ager cheye boro / kothin).  Lokkho:  DIAMOND churi koro, tarpor EXIT (shobuj ful) e palao.
  - CCTV (chhader camera):  ghure ghure dekhe.  Tomake dekhle SPOT meter bhore -> ALARM -> shob POLICE tomar dike chole ashe.
  - POLICE:  patrol kore.  Samne dekhle (ba alarm hole) tomake tare kore.  Ninja r cheye ektu dhire.
  - CATCH:  police dhorle CATCH BAR bhore.  SPACE mere (mash) chharao.  3 bar dhora porle -> JAIL.
  - JAIL (jail.py):  PAY 10000 Tk  /  WAIT 1 MIN  /  BREAK OUT  (3 bar + 2 window).
  - SNEAK (SHIFT / C / SNEAK button):  dhire hnete, CCTV r police dekhte pay kom.

Keys:   W S = agey pichone     A D = pash       <- -> = ghuro       SHIFT / C = sneak      SPACE = catch e mash
        ESC = pause / bahire
Phone:  nijer on-screen button (multi-touch).
Reward:  level 1 = 2000,  2 = 3500,  3 = 6000 Tk.   Level 1 shuru te khola, porergulo ager ta shesh korle.
"""
import math
import random
from collections import deque

import pygame

import sound
import controls as CT
from animation import WIDTH, HEIGHT, get_font
import jail as JAIL

SAVE_KEY = "done3d"
REWARDS = [2000, 3500, 6000]
LEVEL_NAMES = ["BANK VAULT", "MUSEUM NIGHT", "POLICE FORTRESS"]
# (room cols, room rows, cctv, cops, seed, loops, cop_speed, cctv_range)
LEVELS = [
    (4, 3, 2, 1, 11, 2, 2.2, 7.0),
    (5, 4, 4, 2, 23, 4, 2.4, 7.5),
    (6, 5, 6, 4, 37, 6, 2.6, 8.0),
]
PLAYER_SPEED = 3.1
SNEAK_SPEED = 1.5
FOV = math.radians(66)
CATCH_TIME = 1.5
CATCHES_MAX = 3
ALARM_TIME = 22.0


# ====================================================================
#  MAP GENERATOR   (room-grid maze, shob shomoy connected)
# ====================================================================
def build_map(rc, rr, seed, loops):
    rnd = random.Random(seed)
    W, H = rc * 4 + 1, rr * 4 + 1
    g = [["#"] * W for _ in range(H)]
    for ry in range(rr):                                   # protita room 3x3
        for rx in range(rc):
            for y in range(3):
                for x in range(3):
                    g[ry * 4 + 1 + y][rx * 4 + 1 + x] = "."

    def link(a, b):                                        # 2 room er majhe door
        (ax, ay), (bx, by) = a, b
        if ay == by:
            x = min(ax, bx) * 4 + 4
            y = ay * 4 + 1 + rnd.randint(0, 2)
            g[y][x] = "."
        else:
            y = min(ay, by) * 4 + 4
            x = ax * 4 + 1 + rnd.randint(0, 2)
            g[y][x] = "."

    seen = {(0, 0)}
    stack = [(0, 0)]
    while stack:                                           # spanning tree maze
        cx, cy = stack[-1]
        nb = [(cx + dx, cy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
              if 0 <= cx + dx < rc and 0 <= cy + dy < rr and (cx + dx, cy + dy) not in seen]
        if not nb:
            stack.pop()
            continue
        n = rnd.choice(nb)
        link((cx, cy), n)
        seen.add(n)
        stack.append(n)
    for _ in range(loops):                                 # kichu extra door (loop)
        rx, ry = rnd.randrange(rc), rnd.randrange(rr)
        if rnd.random() < 0.5 and rx + 1 < rc:
            link((rx, ry), (rx + 1, ry))
        elif ry + 1 < rr:
            link((rx, ry), (rx, ry + 1))
    return ["".join(r) for r in g]


def room_center(rx, ry):
    return (rx * 4 + 2.5, ry * 4 + 2.5)


def bfs_dist(grid, start):
    H, W = len(grid), len(grid[0])
    d = {start: 0}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < W and 0 <= n[1] < H and grid[n[1]][n[0]] != "#" and n not in d:
                d[n] = d[(x, y)] + 1
                q.append(n)
    return d


def bfs_path(grid, a, b, limit=2000):
    """a, b = (tx, ty).  Tile list (a chhara, b soho)."""
    if a == b:
        return []
    H, W = len(grid), len(grid[0])
    prev = {a: None}
    q = deque([a])
    while q and limit > 0:
        limit -= 1
        cur = q.popleft()
        if cur == b:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cur[0] + dx, cur[1] + dy)
            if 0 <= n[0] < W and 0 <= n[1] < H and grid[n[1]][n[0]] != "#" and n not in prev:
                prev[n] = cur
                q.append(n)
    if b not in prev:
        return []
    path = []
    cur = b
    while cur != a:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


# ====================================================================
#  SIMULATION  (pygame chhara - test kora jay)
# ====================================================================
class Sim3D:
    def __init__(self, level):
        self.level = level
        rc, rr, ncam, ncop, seed, loops, self.cop_speed, self.cam_range = LEVELS[level]
        self.rc, self.rr = rc, rr
        self.grid = build_map(rc, rr, seed, loops)
        self.H, self.W = len(self.grid), len(self.grid[0])
        rnd = random.Random(seed * 7 + 1)
        self.rnd = rnd
        start_room = (0, 0)
        self.start = room_center(*start_room)
        # shob room er dist
        dist = bfs_dist(self.grid, (int(self.start[0]), int(self.start[1])))
        rooms = [(x, y) for y in range(rr) for x in range(rc) if (x, y) != start_room]
        rooms.sort(key=lambda r: dist.get((int(room_center(*r)[0]), int(room_center(*r)[1])), 0), reverse=True)
        self.loot_pos = room_center(*rooms[0])                    # shobcheye dure
        self.exit_pos = self.start
        rest = rooms[1:]
        rnd.shuffle(rest)
        # CCTV : room er kone (ceiling), room er majhe tak kore
        self.cams = []
        for i in range(ncam):
            r = rest[i % len(rest)]
            cx, cy = room_center(*r)
            corner = rnd.choice(((-1, -1), (1, -1), (-1, 1), (1, 1)))
            px, py = cx + corner[0] * 1.0, cy + corner[1] * 1.0
            base = math.atan2(cy - py, cx - px) + rnd.uniform(-0.6, 0.6)
            self.cams.append({"x": px, "y": py, "base": base, "sweep": rnd.uniform(0.9, 1.5),
                              "speed": rnd.uniform(0.5, 0.9), "ph": rnd.uniform(0, 6.28), "ang": base,
                              "seeing": 0.0})
        # police : 2 ta room er majhe patrol
        self.cops = []
        for i in range(ncop):
            a = rest[(i * 2 + 1) % len(rest)]
            b = rest[(i * 2 + 2) % len(rest)]
            c = rooms[(i + 1) % len(rooms)]
            wps = [room_center(*a), room_center(*b), room_center(*c)]
            self.cops.append({"x": wps[0][0], "y": wps[0][1], "dir": 0.0, "wps": wps, "wi": 1, "path": [],
                              "path_t": 0.0, "mode": "patrol", "lose_t": 0.0, "stun": 0.0, "home": wps[0],
                              "walk": 0.0})
        self.reset_player()
        self.t = 0.0
        self.loot_taken = False
        self.alarm = 0.0
        self.spot = 0.0
        self.catch = 0.0
        self.catches = 0
        self.grace = 0.0
        self.state = "play"               # play | jail | won
        self.msg, self.msg_t = "", 0.0
        self.catcher = None

    # ----- helpers -----
    def reset_player(self):
        self.px, self.py = self.start
        self.ang = 0.0
        self.sneak = False

    def respawn_after_jail(self):
        self.reset_player()
        self.catches, self.catch, self.alarm, self.spot = 0, 0.0, 0.0, 0.0
        self.grace = 3.0
        self.state = "play"
        for c in self.cops:
            c["x"], c["y"] = c["home"]
            c["mode"], c["stun"], c["path"] = "patrol", 0.0, []
        self.say("Free again!  Be careful.")

    def say(self, s, t=2.2):
        self.msg, self.msg_t = s, t

    def wall(self, x, y):
        ix, iy = int(math.floor(x)), int(math.floor(y))
        if ix < 0 or iy < 0 or ix >= self.W or iy >= self.H:
            return True
        return self.grid[iy][ix] == "#"

    def los(self, ax, ay, bx, by):
        d = math.hypot(bx - ax, by - ay)
        n = max(2, int(d / 0.15))
        for i in range(1, n):
            k = i / n
            if self.wall(ax + (bx - ax) * k, ay + (by - ay) * k):
                return False
        return True

    def move(self, ent_x, ent_y, dx, dy, r=0.25):
        nx, ny = ent_x + dx, ent_y
        if not (self.wall(nx + r * (1 if dx > 0 else -1), ent_y + r) or self.wall(nx + r * (1 if dx > 0 else -1), ent_y - r)):
            ent_x = nx
        ny = ent_y + dy
        if not (self.wall(ent_x + r, ny + r * (1 if dy > 0 else -1)) or self.wall(ent_x - r, ny + r * (1 if dy > 0 else -1))):
            ent_y = ny
        return ent_x, ent_y

    # ----- main update -----
    def update(self, dt, inp):
        """inp: fwd, strafe, turn (-1..1), sneak (bool), mash (int: SPACE press count)"""
        self.t += dt
        self.msg_t = max(0.0, self.msg_t - dt)
        if self.state != "play":
            return
        self.grace = max(0.0, self.grace - dt)
        self.alarm = max(0.0, self.alarm - dt)
        caught_now = self.catcher is not None and self.catch > 0
        # ---- player ----
        self.sneak = bool(inp.get("sneak"))
        self.ang += inp.get("turn", 0.0) * 2.4 * dt
        if not caught_now:
            sp = SNEAK_SPEED if self.sneak else PLAYER_SPEED
            f, s = inp.get("fwd", 0.0), inp.get("strafe", 0.0)
            vx = math.cos(self.ang) * f - math.sin(self.ang) * s
            vy = math.sin(self.ang) * f + math.cos(self.ang) * s
            n = math.hypot(vx, vy)
            if n > 1:
                vx, vy = vx / n, vy / n
            self.px, self.py = self.move(self.px, self.py, vx * sp * dt, vy * sp * dt)
        # ---- loot / exit ----
        if not self.loot_taken and math.hypot(self.px - self.loot_pos[0], self.py - self.loot_pos[1]) < 0.9:
            self.loot_taken = True
            self.alarm = max(self.alarm, 8.0)
            self.say("DIAMOND STOLEN!  Run to the EXIT!   (alarm!)", 3.0)
            sound.play("cash")
        if self.loot_taken and math.hypot(self.px - self.exit_pos[0], self.py - self.exit_pos[1]) < 0.9:
            self.state = "won"
            sound.play("chime")
            return
        # ---- CCTV ----
        seen_by_cam = False
        for c in self.cams:
            c["ang"] = c["base"] + math.sin(self.t * c["speed"] + c["ph"]) * c["sweep"]
            c["seeing"] = max(0.0, c["seeing"] - dt * 2)
            d = math.hypot(self.px - c["x"], self.py - c["y"])
            rng = self.cam_range * (0.6 if self.sneak else 1.0)
            if d < rng and self.grace <= 0:
                a = math.atan2(self.py - c["y"], self.px - c["x"])
                diff = abs((a - c["ang"] + math.pi) % math.tau - math.pi)
                if diff < math.radians(26) and self.los(c["x"], c["y"], self.px, self.py):
                    c["seeing"] = 1.0
                    seen_by_cam = True
        # ---- cops ----
        seen_by_cop = False
        for c in self.cops:
            c["stun"] = max(0.0, c["stun"] - dt)
            if c["stun"] > 0:
                continue
            d = math.hypot(self.px - c["x"], self.py - c["y"])
            rng = 8.0 * (0.55 if self.sneak else 1.0)
            sees = False
            if d < rng and self.grace <= 0 and self.los(c["x"], c["y"], self.px, self.py):
                a = math.atan2(self.py - c["y"], self.px - c["x"])
                diff = abs((a - c["dir"] + math.pi) % math.tau - math.pi)
                sees = diff < math.radians(55) or d < 1.6
            if sees:
                seen_by_cop = True
                c["mode"], c["lose_t"] = "chase", 4.0
            elif self.alarm > 0 and self.grace <= 0:
                c["mode"], c["lose_t"] = "chase", max(c["lose_t"], 1.0)
            elif c["mode"] == "chase":
                c["lose_t"] -= dt
                if c["lose_t"] <= 0:
                    c["mode"], c["path"] = "patrol", []
            self.cop_move(c, dt)
        # ---- spot meter / alarm ----
        if seen_by_cam or seen_by_cop:
            self.spot = min(1.0, self.spot + dt * (0.9 if seen_by_cam else 1.6))
            if self.spot >= 1.0 and self.alarm <= 0:
                self.alarm = ALARM_TIME
                self.say("ALARM!  Police are coming!", 2.4)
                sound.play("alarm")
        else:
            self.spot = max(0.0, self.spot - dt * 0.35)
        if self.alarm > 0:
            self.spot = max(self.spot, 0.6)
        # ---- catch ----
        self.update_catch(dt, inp)

    def cop_move(self, c, dt):
        sp = self.cop_speed * (1.0 if c["mode"] == "chase" else 0.7)
        if c["mode"] == "chase":
            tgt = (int(self.px), int(self.py))
        else:
            wp = c["wps"][c["wi"]]
            tgt = (int(wp[0]), int(wp[1]))
            if math.hypot(c["x"] - wp[0], c["y"] - wp[1]) < 0.6:
                c["wi"] = (c["wi"] + 1) % len(c["wps"])
                c["path"] = []
                return
        c["path_t"] -= dt
        me = (int(c["x"]), int(c["y"]))
        if c["path_t"] <= 0 or not c["path"]:
            c["path"] = bfs_path(self.grid, me, tgt)
            c["path_t"] = 0.3
        # direct chase jodi kache + LOS
        if c["mode"] == "chase" and math.hypot(self.px - c["x"], self.py - c["y"]) < 3.0 and self.los(c["x"], c["y"], self.px, self.py):
            gx, gy = self.px, self.py
        elif c["path"]:
            gx, gy = c["path"][0][0] + 0.5, c["path"][0][1] + 0.5
            if math.hypot(gx - c["x"], gy - c["y"]) < 0.15:
                c["path"].pop(0)
                if c["path"]:
                    gx, gy = c["path"][0][0] + 0.5, c["path"][0][1] + 0.5
        else:
            return
        a = math.atan2(gy - c["y"], gx - c["x"])
        # drut ghurbe na - smooth
        diff = (a - c["dir"] + math.pi) % math.tau - math.pi
        c["dir"] += max(-6 * dt, min(6 * dt, diff))
        c["x"], c["y"] = self.move(c["x"], c["y"], math.cos(a) * sp * dt, math.sin(a) * sp * dt, r=0.2)
        c["walk"] += dt * sp

    def update_catch(self, dt, inp):
        mash = inp.get("mash", 0)
        if self.catcher is None:
            if self.grace > 0:
                return
            for c in self.cops:
                if c["stun"] <= 0 and c["mode"] == "chase" and math.hypot(self.px - c["x"], self.py - c["y"]) < 0.75:
                    self.catcher = c
                    self.catch = 0.02
                    self.say("CAUGHT!  Mash SPACE to break free!", 2.0)
                    sound.play("alarm", 0.6)
                    break
            return
        c = self.catcher
        if math.hypot(self.px - c["x"], self.py - c["y"]) > 1.1:         # chhere gelo
            self.catcher, self.catch = None, 0.0
            return
        self.catch += dt / CATCH_TIME
        self.catch -= mash * 0.2
        if self.catch <= 0:
            self.catcher, self.catch = None, 0.0
            c["stun"] = 2.5
            self.grace = 1.5
            self.say("You broke free!")
            return
        if self.catch >= 1.0:
            self.catches += 1
            self.catch = 0.0
            self.catcher = None
            c["stun"] = 2.0
            self.grace = 1.2
            sound.play("hit", 0.8)
            if self.catches >= CATCHES_MAX:
                self.state = "jail"
                self.say("BUSTED!", 1.0)
            else:
                self.say(f"CAUGHT {self.catches} / {CATCHES_MAX}", 2.0)


# ====================================================================
#  RENDERER
# ====================================================================
NUM_RAYS = 240
COL_W = WIDTH // NUM_RAYS
HORIZON = HEIGHT // 2 - 10
WALL_COLORS = [(92, 98, 140), (112, 84, 120), (84, 110, 130)]


def cast_ray(grid, W, H, ox, oy, ang):
    """DDA.  Return (dist, side, wallx)"""
    dx, dy = math.cos(ang), math.sin(ang)
    mx, my = int(ox), int(oy)
    ddx = abs(1 / dx) if dx else 1e30
    ddy = abs(1 / dy) if dy else 1e30
    if dx < 0:
        sx, sdx = -1, (ox - mx) * ddx
    else:
        sx, sdx = 1, (mx + 1 - ox) * ddx
    if dy < 0:
        sy, sdy = -1, (oy - my) * ddy
    else:
        sy, sdy = 1, (my + 1 - oy) * ddy
    side = 0
    for _ in range(64):
        if sdx < sdy:
            sdx += ddx
            mx += sx
            side = 0
        else:
            sdy += ddy
            my += sy
            side = 1
        if mx < 0 or my < 0 or mx >= W or my >= H or grid[my][mx] == "#":
            break
    if side == 0:
        d = sdx - ddx
        wx = oy + d * dy
    else:
        d = sdy - ddy
        wx = ox + d * dx
    return max(0.05, d), side, wx - math.floor(wx)


def _make_cop_sprite():
    s = pygame.Surface((80, 150), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 60), (14, 138, 52, 10))
    pygame.draw.rect(s, (28, 36, 70), (22, 82, 14, 54), border_radius=4)               # legs
    pygame.draw.rect(s, (28, 36, 70), (42, 82, 14, 54), border_radius=4)
    pygame.draw.rect(s, (20, 20, 30), (20, 130, 18, 8))
    pygame.draw.rect(s, (20, 20, 30), (40, 130, 18, 8))
    pygame.draw.rect(s, (46, 66, 150), (16, 40, 48, 50), border_radius=8)             # body
    pygame.draw.rect(s, (230, 200, 70), (36, 44, 8, 12))                               # badge
    pygame.draw.rect(s, (46, 66, 150), (6, 44, 12, 40), border_radius=5)               # arms
    pygame.draw.rect(s, (46, 66, 150), (62, 44, 12, 40), border_radius=5)
    pygame.draw.circle(s, (232, 196, 160), (40, 28), 15)                               # head
    pygame.draw.rect(s, (20, 26, 60), (22, 8, 36, 12), border_radius=4)                # cap
    pygame.draw.rect(s, (20, 26, 60), (18, 18, 44, 5))
    pygame.draw.circle(s, (20, 20, 20), (34, 28), 2)
    pygame.draw.circle(s, (20, 20, 20), (46, 28), 2)
    return s


def _make_cam_sprite(red):
    s = pygame.Surface((64, 48), pygame.SRCALPHA)
    pygame.draw.rect(s, (60, 62, 70), (22, 0, 20, 10))
    pygame.draw.polygon(s, (90, 94, 106), [(6, 12), (52, 8), (58, 30), (10, 36)])
    pygame.draw.circle(s, (20, 20, 26), (50, 20), 10)
    pygame.draw.circle(s, (255, 60, 60) if red else (60, 255, 120), (50, 20), 5)
    return s


def _make_diamond_sprite():
    s = pygame.Surface((60, 60), pygame.SRCALPHA)
    pts = [(30, 4), (54, 22), (30, 56), (6, 22)]
    pygame.draw.polygon(s, (140, 220, 255), pts)
    pygame.draw.polygon(s, (230, 250, 255), pts, 3)
    pygame.draw.polygon(s, (255, 255, 255), [(30, 4), (42, 22), (30, 22), (18, 22)])
    return s


def _make_exit_sprite():
    s = pygame.Surface((70, 110), pygame.SRCALPHA)
    pygame.draw.rect(s, (24, 60, 40), (6, 10, 58, 100), border_radius=6)
    pygame.draw.rect(s, (80, 255, 150), (6, 10, 58, 100), 4, border_radius=6)
    f = get_font(18).render("EXIT", True, (90, 255, 160))
    s.blit(f, f.get_rect(center=(35, 54)))
    return s


class Renderer:
    def __init__(self):
        self.cop = _make_cop_sprite()
        self.cam_g, self.cam_r = _make_cam_sprite(False), _make_cam_sprite(True)
        self.diamond = _make_diamond_sprite()
        self.exit = _make_exit_sprite()
        self.zbuf = [0.0] * NUM_RAYS
        self.bg = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            if y < HORIZON:
                k = y / HORIZON
                col = (int(14 + 18 * k), int(14 + 16 * k), int(26 + 24 * k))
            else:
                k = (y - HORIZON) / (HEIGHT - HORIZON)
                col = (int(40 - 22 * k + 6), int(36 - 20 * k + 6), int(44 - 22 * k + 6))
            pygame.draw.line(self.bg, col, (0, y), (WIDTH, y))

    def draw_world(self, surf, sim):
        surf.blit(self.bg, (0, 0))
        wc = WALL_COLORS[sim.level % 3]
        half = FOV / 2
        for i in range(NUM_RAYS):
            a = sim.ang - half + FOV * (i + 0.5) / NUM_RAYS
            d, side, wx = cast_ray(sim.grid, sim.W, sim.H, sim.px, sim.py, a)
            d_corr = d * math.cos(a - sim.ang)
            self.zbuf[i] = d_corr
            h = min(HEIGHT * 3, int(HEIGHT * 0.9 / d_corr))
            shade = max(0.18, 1.0 - d_corr / 11.0) * (0.78 if side else 1.0)
            base = (int(wc[0] * shade), int(wc[1] * shade), int(wc[2] * shade))
            y0 = HORIZON - h // 2
            surf.fill(base, (i * COL_W, y0, COL_W, h))
            if h > 40:                                         # brick line
                dark = (int(base[0] * 0.6), int(base[1] * 0.6), int(base[2] * 0.6))
                for k in (0.25, 0.5, 0.75):
                    surf.fill(dark, (i * COL_W, y0 + int(h * k), COL_W, 1))
                if int(wx * 6) % 2 == 0:
                    surf.fill(dark, (i * COL_W, y0, 1, h))

    def sprites(self, sim):
        out = []
        for c in sim.cops:
            out.append(("cop", c["x"], c["y"], c, 0.9, 0.0))
        for c in sim.cams:
            out.append(("cam", c["x"], c["y"], c, 0.45, -0.95))
        if not sim.loot_taken:
            out.append(("loot", sim.loot_pos[0], sim.loot_pos[1], None, 0.5, 0.15))
        out.append(("exit", sim.exit_pos[0], sim.exit_pos[1], None, 0.9, 0.0))
        return out

    def draw_sprites(self, surf, sim):
        items = []
        for kind, x, y, obj, scale, lift in self.sprites(sim):
            dx, dy = x - sim.px, y - sim.py
            dist = math.hypot(dx, dy)
            if dist < 0.3:
                continue
            a = math.atan2(dy, dx) - sim.ang
            a = (a + math.pi) % math.tau - math.pi
            if abs(a) > FOV * 0.75:
                continue
            items.append((dist, a, kind, obj, scale, lift))
        items.sort(key=lambda it: -it[0])
        for dist, a, kind, obj, scale, lift in items:
            dc = dist * math.cos(a)
            if dc < 0.2:
                continue
            sx = WIDTH / 2 + math.tan(a) * (WIDTH / 2) / math.tan(FOV / 2)
            size = int(HEIGHT * 0.9 / dc * scale)
            if size < 4 or size > 1400:
                continue
            if kind == "cop":
                img = self.cop
                if obj["stun"] > 0:
                    img = img.copy()
                    img.fill((255, 255, 255, 120), special_flags=pygame.BLEND_RGBA_MULT)
                w = int(size * img.get_width() / img.get_height())
                spr = pygame.transform.scale(img, (max(2, w), size))
                top = HORIZON + int(HEIGHT * 0.9 / dc * 0.5) - size
            elif kind == "cam":
                img = self.cam_r if obj["seeing"] > 0 else self.cam_g
                w = int(size * 1.3)
                spr = pygame.transform.scale(img, (max(2, w), max(2, int(size * 0.97))))
                top = HORIZON - int(HEIGHT * 0.9 / dc * 0.5) + int(size * 0.1)
            elif kind == "loot":
                bob = math.sin(sim.t * 3) * size * 0.05
                spr = pygame.transform.scale(self.diamond, (size, size))
                top = HORIZON + int(HEIGHT * 0.9 / dc * 0.5) - size - int(size * 0.5) + int(bob)
            else:
                w = int(size * 0.64)
                spr = pygame.transform.scale(self.exit, (max(2, w), size))
                top = HORIZON + int(HEIGHT * 0.9 / dc * 0.5) - size
                if not sim.loot_taken:
                    spr.set_alpha(120)
            sw = spr.get_width()
            x0 = int(sx - sw / 2)
            # column wise (zbuf occlusion)
            sh = spr.get_height()
            c0 = max(0, x0 // COL_W)
            c1 = min(NUM_RAYS - 1, (x0 + sw) // COL_W)
            for col in range(c0, c1 + 1):
                if self.zbuf[col] <= dc:
                    continue
                sx0 = col * COL_W - x0
                w_ = COL_W
                if sx0 < 0:
                    w_ += sx0
                    sx0 = 0
                if sx0 >= sw or w_ <= 0:
                    continue
                w_ = min(w_, sw - sx0)
                surf.blit(spr, (x0 + sx0, top), (sx0, 0, w_, sh))

    def draw_minimap(self, surf, sim):
        cs = 7
        mw, mh = sim.W * cs, sim.H * cs
        mp = pygame.Surface((mw, mh), pygame.SRCALPHA)
        mp.fill((0, 0, 0, 130))
        for y in range(sim.H):
            for x in range(sim.W):
                if sim.grid[y][x] == "#":
                    mp.fill((90, 96, 140, 210), (x * cs, y * cs, cs, cs))
        for c in sim.cams:
            a = c["ang"]
            pts = [(c["x"] * cs, c["y"] * cs)]
            for k in (-26, 0, 26):
                aa = a + math.radians(k)
                pts.append(((c["x"] + math.cos(aa) * 2.6) * cs, (c["y"] + math.sin(aa) * 2.6) * cs))
            pygame.draw.polygon(mp, (255, 220, 90, 110), pts)
            pygame.draw.circle(mp, (255, 220, 90), (int(c["x"] * cs), int(c["y"] * cs)), 3)
        for c in sim.cops:
            pygame.draw.circle(mp, (255, 70, 70) if c["mode"] == "chase" else (90, 150, 255), (int(c["x"] * cs), int(c["y"] * cs)), 3)
        if not sim.loot_taken:
            pygame.draw.circle(mp, (140, 230, 255), (int(sim.loot_pos[0] * cs), int(sim.loot_pos[1] * cs)), 3)
        pygame.draw.rect(mp, (80, 255, 150), (int(sim.exit_pos[0] * cs) - 3, int(sim.exit_pos[1] * cs) - 3, 6, 6), 1)
        pygame.draw.circle(mp, (255, 255, 255), (int(sim.px * cs), int(sim.py * cs)), 3)
        pygame.draw.line(mp, (255, 255, 255), (sim.px * cs, sim.py * cs),
                         ((sim.px + math.cos(sim.ang) * 1.5) * cs, (sim.py + math.sin(sim.ang) * 1.5) * cs), 2)
        surf.blit(mp, (WIDTH - mw - 10, 10))


# ====================================================================
#  TOUCH BUTTONS (multi-touch, ba mouse)
# ====================================================================
BTN = {
    "fwd": ((110, 380), 46, "UP"), "back": ((110, 490), 46, "DN"),
    "tl": ((36, 436), 38, "<"), "tr": ((184, 436), 38, ">"),
    "sneak": ((860, 400), 48, "SNEAK"), "act": ((860, 492), 48, "BREAK"),
}


class Pointers:
    def __init__(self):
        self.fingers = {}
        self.mouse = None

    def event(self, e):
        if e.type == pygame.FINGERDOWN or e.type == pygame.FINGERMOTION:
            self.fingers[e.finger_id] = (e.x * WIDTH, e.y * HEIGHT)
        elif e.type == pygame.FINGERUP:
            self.fingers.pop(e.finger_id, None)
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.mouse = e.pos
        elif e.type == pygame.MOUSEMOTION and self.mouse is not None:
            self.mouse = e.pos
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.mouse = None

    def points(self):
        pts = list(self.fingers.values())
        if self.mouse is not None and not pts:
            pts.append(self.mouse)
        return pts

    def held(self):
        out = set()
        for p in self.points():
            best, bd = None, 9e9
            for k, (c, r, _) in BTN.items():
                d = math.hypot(p[0] - c[0], p[1] - c[1]) / r
                if d < 1.35 and d < bd:
                    best, bd = k, d
            if best:
                out.add(best)
        return out


# ====================================================================
#  GAME (menu + play + jail + win)
# ====================================================================
class Game3D:
    def __init__(self, save, save_fn):
        self.save, self.save_fn = save, save_fn
        self.rend = Renderer()
        self.sim = None
        self.mode = "select"          # select | play | jail | won | lost
        self.sel = 0
        self.ptr = Pointers()
        self.touch_prev = set()
        self.mash = 0
        self.jail_ui = None
        self.t = 0.0
        self.sel_rects = [pygame.Rect(120 + i * 245, 190, 225, 190) for i in range(3)]
        self.won_t = 0.0
        self.reward = 0
        self.pause = False

    def done(self):
        return int(self.save.get(SAVE_KEY, 0))

    def money(self):
        return int(self.save.get("money", 0))

    def start_level(self, i):
        self.sim = Sim3D(i)
        self.mode = "play"
        self.sim.say(f"LEVEL {i + 1}:  steal the DIAMOND, reach the EXIT", 3.5)
        self.pause = False

    # --------------------------------------------------- events
    def event(self, e):
        self.ptr.event(e)
        if self.mode == "select":
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_LEFT, pygame.K_a):
                    self.sel = (self.sel - 1) % 3
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.sel = (self.sel + 1) % 3
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.pick(self.sel)
                elif e.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.pick(e.key - pygame.K_1)
                elif e.key == pygame.K_ESCAPE:
                    return "exit"
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for i, r in enumerate(self.sel_rects):
                    if r.collidepoint(e.pos):
                        self.sel = i
                        self.pick(i)
                if pygame.Rect(10, 10, 120, 40).collidepoint(e.pos):
                    return "exit"
        elif self.mode == "play":
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.pause = not self.pause
                elif e.key == pygame.K_SPACE:
                    self.mash += 1
                elif e.key == pygame.K_p and self.pause:
                    return "exit"
            elif e.type == pygame.MOUSEBUTTONDOWN and self.pause and e.button == 1:
                if pygame.Rect(WIDTH // 2 - 120, 300, 240, 46).collidepoint(e.pos):
                    self.pause = False
                if pygame.Rect(WIDTH // 2 - 120, 360, 240, 46).collidepoint(e.pos):
                    return "exit"
        elif self.mode == "jail":
            if self.jail_ui:
                self.jail_ui.event(e)
        elif self.mode == "won":
            if self.won_t > 1.2 and (e.type == pygame.KEYDOWN or (e.type == pygame.MOUSEBUTTONDOWN)):
                self.mode = "select"
        return None

    def pick(self, i):
        if i <= self.done():
            sound.play("click")
            self.start_level(i)
        else:
            sound.play("back")

    # --------------------------------------------------- update
    def update(self, dt, keys):
        self.t += dt
        if self.mode == "won":
            self.won_t += dt
            return
        if self.mode == "jail":
            self.jail_ui.update(dt)
            if self.jail_ui.result == "free":
                self.save["money"] = self.jail_ui.money
                self.save_fn()
                self.jail_ui = None
                self.sim.respawn_after_jail()
                self.mode = "play"
            return
        if self.mode != "play" or self.pause:
            return
        held = self.ptr.held()
        newly = held - self.touch_prev
        self.touch_prev = held
        if "act" in newly:
            self.mash += 1
        K = pygame
        fwd = (1 if keys[K.K_w] or keys[K.K_UP] else 0) - (1 if keys[K.K_s] or keys[K.K_DOWN] else 0)
        fwd += (1 if "fwd" in held else 0) - (1 if "back" in held else 0)
        strafe = (1 if keys[K.K_d] else 0) - (1 if keys[K.K_a] else 0)
        turn = (1 if keys[K.K_RIGHT] else 0) - (1 if keys[K.K_LEFT] else 0)
        turn += (1 if "tr" in held else 0) - (1 if "tl" in held else 0)
        sneak = keys[K.K_LSHIFT] or keys[K.K_RSHIFT] or keys[K.K_c] or "sneak" in held
        inp = {"fwd": max(-1, min(1, fwd)), "strafe": strafe, "turn": max(-1, min(1, turn)),
               "sneak": sneak, "mash": self.mash}
        self.mash = 0
        sim = self.sim
        sim.update(dt, inp)
        if sim.state == "jail":
            self.mode = "jail"
            self.jail_ui = JAIL.JailUI(self.money(), pay_cost=JAIL.PAY_COST)
            sound.play("jail")
        elif sim.state == "won":
            self.mode = "won"
            self.won_t = 0.0
            self.reward = REWARDS[sim.level]
            first = sim.level >= self.done()
            if first:
                self.save[SAVE_KEY] = min(3, sim.level + 1)
            self.save["money"] = self.money() + self.reward
            self.save_fn()
            sound.play("chime")

    # --------------------------------------------------- draw
    def txt(self, surf, s, size, col, pos, center=True):
        img = get_font(size).render(s, True, col)
        sh = get_font(size).render(s, True, (0, 0, 0))
        r = img.get_rect(center=pos) if center else img.get_rect(topleft=pos)
        surf.blit(sh, (r.x + 2, r.y + 2))
        surf.blit(img, r)

    def draw(self, surf):
        if self.mode == "select":
            self.draw_select(surf)
            return
        if self.mode == "jail" and self.jail_ui:
            self.jail_ui.draw(surf)
            return
        sim = self.sim
        self.rend.draw_world(surf, sim)
        self.rend.draw_sprites(surf, sim)
        self.draw_hud(surf, sim)
        if self.mode == "won":
            dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 10, 20, 190))
            surf.blit(dim, (0, 0))
            self.txt(surf, "LEVEL COMPLETE!", 60, (110, 255, 150), (WIDTH // 2, 190))
            self.txt(surf, f"+{self.reward} Tk", 40, (255, 220, 90), (WIDTH // 2, 262))
            if self.done() > sim.level and sim.level < 2:
                self.txt(surf, f"3D LEVEL {sim.level + 2} UNLOCKED", 26, (255, 255, 255), (WIDTH // 2, 320))
            if self.won_t > 1.2:
                self.txt(surf, "tap / press any key", 18, (170, 175, 200), (WIDTH // 2, 400))
        if self.pause:
            dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 160))
            surf.blit(dim, (0, 0))
            self.txt(surf, "PAUSED", 52, (255, 255, 255), (WIDTH // 2, 220))
            for lab, y in (("RESUME  (ESC)", 300), ("EXIT  (P)", 360)):
                r = pygame.Rect(WIDTH // 2 - 120, y, 240, 46)
                pygame.draw.rect(surf, (40, 44, 70), r, border_radius=12)
                pygame.draw.rect(surf, (150, 160, 220), r, 2, border_radius=12)
                self.txt(surf, lab, 20, (255, 255, 255), r.center)

    def draw_hud(self, surf, sim):
        # vignette / alarm wash
        if sim.alarm > 0:
            on = int(self.t * 4) % 2 == 0
            wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            wash.fill((255, 40, 60, 28) if on else (60, 110, 255, 28))
            surf.blit(wash, (0, 0))
        # crosshair-ish
        pygame.draw.circle(surf, (255, 255, 255), (WIDTH // 2, HORIZON), 2)
        # spot meter
        bar = pygame.Rect(WIDTH // 2 - 130, 16, 260, 16)
        pygame.draw.rect(surf, (20, 22, 36), bar, border_radius=8)
        k = sim.spot
        col = (110, 255, 150) if k < 0.4 else ((255, 220, 90) if k < 0.8 else (255, 80, 80))
        pygame.draw.rect(surf, col, (bar.x, bar.y, int(bar.w * k), bar.h), border_radius=8)
        pygame.draw.rect(surf, (220, 225, 245), bar, 2, border_radius=8)
        self.txt(surf, "SPOTTED" if sim.alarm <= 0 else f"ALARM {int(sim.alarm)}s", 14, (255, 255, 255), (WIDTH // 2, 40))
        # catches
        for i in range(CATCHES_MAX):
            c = (255, 70, 70) if i < sim.catches else (60, 62, 84)
            pygame.draw.circle(surf, c, (30 + i * 30, 30), 11)
            pygame.draw.circle(surf, (230, 230, 245), (30 + i * 30, 30), 11, 2)
        self.txt(surf, "CAUGHT", 13, (200, 205, 225), (60, 54))
        # objective
        obj = "Reach the EXIT!" if sim.loot_taken else "Find the DIAMOND (blue)"
        self.txt(surf, obj, 18, (255, 235, 160), (WIDTH // 2, 66))
        if sim.sneak:
            self.txt(surf, "SNEAKING", 16, (150, 255, 190), (WIDTH // 2, 90))
        self.rend.draw_minimap(surf, sim)
        # catch bar
        if sim.catcher is not None and sim.catch > 0:
            r = pygame.Rect(WIDTH // 2 - 160, 300, 320, 26)
            pygame.draw.rect(surf, (30, 12, 16), r, border_radius=10)
            pygame.draw.rect(surf, (255, 80, 80), (r.x, r.y, int(r.w * min(1, sim.catch)), r.h), border_radius=10)
            pygame.draw.rect(surf, (255, 255, 255), r, 2, border_radius=10)
            self.txt(surf, "MASH SPACE / BREAK !", 24, (255, 255, 255), (WIDTH // 2, 270))
        if sim.msg_t > 0:
            self.txt(surf, sim.msg, 24, (255, 255, 255), (WIDTH // 2, 470))
        # touch buttons
        held = self.ptr.held()
        for k, (c, r, lab) in BTN.items():
            on = k in held
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, 70 if on else 30), (r + 2, r + 2), r)
            pygame.draw.circle(s, (255, 255, 255, 140), (r + 2, r + 2), r, 3)
            surf.blit(s, (c[0] - r - 2, c[1] - r - 2))
            self.txt(surf, lab, 14 if len(lab) > 2 else 20, (255, 255, 255), c)

    def draw_select(self, surf):
        surf.fill((10, 12, 26))
        for i in range(0, HEIGHT, 4):
            pygame.draw.line(surf, (10 + i // 30, 12 + i // 40, 26 + i // 18), (0, i), (WIDTH, i))
        self.txt(surf, "3D NINJA", 64, (255, 230, 120), (WIDTH // 2, 80))
        self.txt(surf, "Steal the diamond.  Avoid CCTV.  Don't get caught by the POLICE.", 20, (210, 215, 235), (WIDTH // 2, 134))
        for i, r in enumerate(self.sel_rects):
            open_ = i <= self.done()
            sel = i == self.sel
            rr = r.inflate(14, 14) if sel else r
            pygame.draw.rect(surf, (26, 30, 56) if open_ else (20, 20, 30), rr, border_radius=16)
            pygame.draw.rect(surf, (255, 230, 120) if sel else (96, 102, 138), rr, 3, border_radius=16)
            self.txt(surf, f"3D LEVEL {i + 1}", 26, (255, 255, 255) if open_ else (110, 112, 135), (rr.centerx, rr.y + 40))
            self.txt(surf, LEVEL_NAMES[i], 18, (150, 200, 255) if open_ else (90, 92, 110), (rr.centerx, rr.y + 78))
            ncam, ncop = LEVELS[i][2], LEVELS[i][3]
            self.txt(surf, f"CCTV {ncam}   POLICE {ncop}", 16, (200, 205, 225) if open_ else (90, 92, 110), (rr.centerx, rr.y + 116))
            self.txt(surf, f"+{REWARDS[i]} Tk" if open_ else "LOCKED", 22, (255, 220, 90) if open_ else (200, 90, 90), (rr.centerx, rr.y + 152))
        pygame.draw.rect(surf, (40, 44, 70), (10, 10, 120, 40), border_radius=10)
        self.txt(surf, "< BACK", 18, (255, 255, 255), (70, 30))
        self.txt(surf, "W S A D move   <- ->  turn   SHIFT sneak   SPACE break free", 14, (140, 145, 170), (WIDTH // 2, 470))
        self.txt(surf, "JAIL:  PAY 10000 Tk  /  WAIT 1 MIN  /  BREAK OUT", 16, (255, 150, 130), (WIDTH // 2, 500))


def run(screen, clock, save, save_fn):
    """3D NINJA mode.  Return None."""
    sound.play_music("level1", loops=-1)
    game = Game3D(save, save_fn)
    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        CT.set_ctx(True)
        for e in CT.filter(pygame.event.get()):
            if e.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if game.event(e) == "exit":
                sound.stop_music(300)
                return None
        game.update(dt, pygame.key.get_pressed())
        game.draw(screen)
        pygame.display.flip()
