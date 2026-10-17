"""
sound.py - Abix Ninja er shob sound ekhane.
Kono mp3/wav file lage na: sound gulo code diye nijei toiri hoy.

Use:
    import sound
    sound.init()                     # ekbar, game shuru te
    sound.play("click")              # effect
    sound.play_music("intro")        # music
    sound.stop_music(600)            # fade out (ms)

Sound list:
    click, hover, back, pop, whoosh, chime, ding, lock, roar   (effects)
    jump, throw, hit, hurt, die, star, checkpoint, punch,
    hide, alert, win, gameover                                 (game effects)
    gunshot, stab, beep, hack, laser, zap, cash, siren, alarm,
    key, unlock, jail                                          (bank heist effects)
    intro, menu, level1                            (music)
"""
import array
import math
import random
import pygame

RATE = 22050
TWO_PI = 2 * math.pi

_sounds = {}
_enabled = False
_music_channel = None


# ------------------------------------------------------------------
# Sound toiri-r chhoto chhoto helper
# ------------------------------------------------------------------
def _sweep(f0, f1, dur, vol=0.5, decay=0.0):
    n = int(RATE * dur)
    out, ph = [], 0.0
    for i in range(n):
        x = i / n
        ph += TWO_PI * (f0 + (f1 - f0) * x) / RATE
        env = min(1.0, i / (RATE * 0.004)) * (1 - x) ** 1.2
        if decay:
            env *= math.exp(-decay * x)
        out.append(math.sin(ph) * vol * env)
    return out


def _noise(dur, vol, lp0, lp1, shape):
    n = int(RATE * dur)
    out, y = [], 0.0
    for i in range(n):
        x = i / n
        a = lp0 + (lp1 - lp0) * x
        y += a * (random.uniform(-1, 1) - y)
        out.append(y * vol * shape(x))
    return out


def _pluck(freq, dur=1.2, vol=0.5):
    n = int(RATE * dur)
    out = []
    for i in range(n):
        t = i / RATE
        env = min(1.0, t / 0.004) * math.exp(-4.5 * t)
        s = (math.sin(TWO_PI * freq * t)
             + 0.5 * math.sin(TWO_PI * freq * 2 * t)
             + 0.25 * math.sin(TWO_PI * freq * 3 * t))
        out.append(s * env * vol / 1.75)
    return out


def _bell(freq, dur=1.4, vol=0.5):
    n = int(RATE * dur)
    parts = ((1.0, 1.0), (2.76, 0.5), (5.4, 0.25))
    out = []
    for i in range(n):
        t = i / RATE
        env = min(1.0, t / 0.003) * math.exp(-3.2 * t)
        s = sum(a * math.sin(TWO_PI * freq * m * t) for m, a in parts)
        out.append(s * env * vol / 1.75)
    return out


def _taiko(vol=1.0):
    body = _sweep(150, 48, 0.55, vol * 0.9, decay=3.0)
    hit = _noise(0.12, vol * 0.8, 0.25, 0.05, lambda x: (1 - x) ** 2)
    return _mix(body, hit, 0.0)


def _mix(dst, src, at=0.0, gain=1.0):
    start = int(at * RATE)
    for i, v in enumerate(src):
        j = start + i
        if j >= len(dst):
            break
        dst[j] += v * gain
    return dst


def _drone(length, vol=0.10):
    n = int(length * RATE)
    out = []
    for i in range(n):
        t = i / RATE
        fade = min(1.0, t / 1.5) * min(1.0, (length - t) / 0.8)
        trem = 0.65 + 0.35 * math.sin(TWO_PI * t / 4.0)
        s = math.sin(TWO_PI * 110 * t) + 0.5 * math.sin(TWO_PI * 165 * t)
        out.append(s * vol * trem * fade)
    return out


def _to_sound(samples, volume=1.0, peak=0.9):
    m = max(1e-6, max(abs(s) for s in samples))
    k = min(1.0, peak / m) if m > peak else 1.0
    buf = array.array("h", (int(max(-1.0, min(1.0, s * k)) * 32767) for s in samples))
    snd = pygame.mixer.Sound(buffer=buf.tobytes())
    snd.set_volume(volume)
    return snd


# ------------------------------------------------------------------
# Music
# ------------------------------------------------------------------
def _make_intro_music():
    length = 11.0
    track = _drone(length)
    melody = [(0.9, 440.0), (1.4, 523.25), (2.0, 659.25), (2.8, 523.25),
              (3.4, 493.88), (4.0, 440.0), (4.8, 349.23), (5.6, 440.0),
              (6.2, 523.25), (6.8, 659.25), (7.4, 698.46), (8.0, 659.25),
              (8.6, 523.25), (9.2, 659.25), (9.8, 880.0)]
    for t, f in melody:
        _mix(track, _pluck(f, 1.2, 0.35), t)
    drums = [(0.8, 1.0), (2.0, 0.55), (3.2, 0.55), (4.4, 0.6), (5.6, 0.65),
             (6.2, 0.65), (6.8, 0.7), (7.4, 0.75), (8.0, 0.8), (8.6, 0.8),
             (9.2, 0.9), (9.5, 0.9), (9.8, 0.95), (10.0, 1.0)]
    for t, v in drums:
        _mix(track, _taiko(v), t, 0.9)
    return track


def _make_menu_music():
    length = 8.0
    track = _drone(length, 0.08)
    melody = [(0.0, 440.0), (1.0, 523.25), (2.0, 659.25), (3.0, 523.25),
              (4.0, 493.88), (5.0, 440.0), (6.0, 349.23), (7.0, 440.0)]
    for t, f in melody:
        _mix(track, _pluck(f, 1.4, 0.30), t)
    for t in (0.0, 4.0):
        _mix(track, _taiko(0.5), t)
    return track


def _make_level_music():
    """Bank heist - tense, dhire (16 second loop)."""
    length = 16.0
    track = _drone(length, 0.08)
    # niche-r heartbeat / tick
    for i in range(int(length)):
        _mix(track, _sweep(110, 70, 0.12, 0.35), i + 0.0)
        if i % 2 == 1:
            _mix(track, _sweep(1800, 1600, 0.03, 0.12), i + 0.5)
    # tense minor melody (kom note)
    melody = [(0.0, 220.0), (2.0, 261.63), (3.0, 233.08), (4.0, 220.0), (6.0, 207.65), (8.0, 220.0),
              (10.0, 261.63), (11.0, 329.63), (12.0, 311.13), (14.0, 220.0)]
    for t, f in melody:
        _mix(track, _bell(f, 1.6, 0.20), t)
    for t in (0.0, 8.0):
        _mix(track, _taiko(0.4), t)
    return track


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def init():
    """Shob sound banay. Audio device na thakle game sound chara cholbe."""
    global _enabled, _music_channel
    try:
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=512, allowedchanges=0)
        pygame.mixer.set_num_channels(16)
        pygame.mixer.set_reserved(1)          # channel 0 = music
        _music_channel = pygame.mixer.Channel(0)
    except pygame.error:
        _enabled = False
        return False

    _sounds["click"] = _to_sound(_sweep(950, 550, 0.08, 0.6), 0.8)
    _sounds["hover"] = _to_sound(_sweep(1500, 1700, 0.04, 0.4), 0.35)
    _sounds["back"] = _to_sound(_sweep(650, 300, 0.12, 0.55), 0.7)
    _sounds["pop"] = _to_sound(_sweep(420, 950, 0.12, 0.55), 0.7)
    _sounds["whoosh"] = _to_sound(
        _noise(0.9, 2.2, 0.03, 0.55, lambda x: math.sin(math.pi * x) ** 2), 0.7)
    _sounds["chime"] = _to_sound(
        _mix(_bell(659.25, 1.4, 0.5), _bell(988.0, 1.4, 0.35), 0.12), 0.7)
    done = _bell(440.0, 1.6, 0.5)
    _mix(done, _bell(659.25, 1.6, 0.4), 0.08)
    _mix(done, _bell(880.0, 1.6, 0.4), 0.16)
    _sounds["ding"] = _to_sound(done, 0.9)
    _sounds["lock"] = _to_sound(_sweep(230, 130, 0.16, 0.6), 0.7)
    roar = _noise(0.9, 1.6, 0.08, 0.2, lambda x: math.sin(math.pi * x) ** 1.5)
    _mix(roar, _sweep(130, 55, 0.9, 0.5), 0.0)
    _sounds["roar"] = _to_sound(roar, 0.9)
    _sounds["intro"] = _to_sound(_make_intro_music(), 0.8)
    _sounds["menu"] = _to_sound(_make_menu_music(), 0.45)

    # ---- game (level) sound ----
    _sounds["jump"] = _to_sound(_sweep(300, 640, 0.13, 0.5), 0.55)
    thr = _noise(0.16, 1.0, 0.5, 0.08, lambda x: (1 - x) ** 1.5)
    _mix(thr, _sweep(1500, 700, 0.12, 0.3), 0.0)
    _sounds["throw"] = _to_sound(thr, 0.6)
    hit = _sweep(760, 180, 0.12, 0.6)
    _mix(hit, _noise(0.08, 0.9, 0.3, 0.1, lambda x: (1 - x) ** 2), 0.0)
    _sounds["hit"] = _to_sound(hit, 0.8)
    _sounds["hurt"] = _to_sound(_sweep(280, 90, 0.28, 0.75), 0.85)
    die = _sweep(520, 55, 0.75, 0.7, decay=1.5)
    _mix(die, _noise(0.3, 0.8, 0.2, 0.03, lambda x: (1 - x)), 0.0)
    _sounds["die"] = _to_sound(die, 0.9)
    star = _bell(880.0, 0.7, 0.45)
    _mix(star, _bell(1318.5, 0.7, 0.4), 0.09)
    _sounds["star"] = _to_sound(star, 0.8)
    cp = _bell(523.25, 1.2, 0.45)
    _mix(cp, _bell(659.25, 1.2, 0.4), 0.10)
    _mix(cp, _bell(783.99, 1.2, 0.4), 0.20)
    _sounds["checkpoint"] = _to_sound(cp, 0.85)
    pun = _taiko(1.0)
    _mix(pun, _noise(0.3, 1.4, 0.15, 0.02, lambda x: (1 - x) ** 1.5), 0.0)
    _sounds["punch"] = _to_sound(pun, 1.0)
    _sounds["hide"] = _to_sound(_noise(0.35, 1.3, 0.02, 0.22, lambda x: math.sin(math.pi * x) ** 2), 0.5)
    al = _sweep(950, 1250, 0.07, 0.5)
    _mix(al, _sweep(950, 1250, 0.07, 0.5), 0.1)
    _sounds["alert"] = _to_sound(al, 0.7)
    win = _bell(523.25, 2.0, 0.45)
    for i, f in enumerate((659.25, 783.99, 1046.5)):
        _mix(win, _bell(f, 2.0 - 0.15 * (i + 1), 0.4), 0.14 * (i + 1))
    _sounds["win"] = _to_sound(win, 0.9)
    over = _sweep(420, 70, 1.0, 0.7, decay=1.0)
    _mix(over, _taiko(0.9), 0.0)
    _sounds["gameover"] = _to_sound(over, 0.9)
    _sounds["level1"] = _to_sound(_make_level_music(), 0.5)
    gun = _noise(0.28, 1.8, 0.6, 0.04, lambda x: (1 - x) ** 2)
    _mix(gun, _sweep(260, 50, 0.22, 0.8), 0.0)
    _sounds["gunshot"] = _to_sound(gun, 0.85)
    stab = _noise(0.14, 1.0, 0.45, 0.08, lambda x: (1 - x))
    _mix(stab, _sweep(950, 280, 0.1, 0.45), 0.0)
    _sounds["stab"] = _to_sound(stab, 0.7)
    _sounds["beep"] = _to_sound(_sweep(1100, 1100, 0.07, 0.35), 0.5)
    hk = _sweep(500, 900, 0.08, 0.35)
    _mix(hk, _sweep(700, 1200, 0.08, 0.35), 0.09)
    _mix(hk, _sweep(900, 1500, 0.10, 0.35), 0.18)
    _sounds["hack"] = _to_sound(hk, 0.7)
    lz = _noise(0.35, 1.0, 0.7, 0.2, lambda x: (1 - x) ** 0.5)
    _mix(lz, _sweep(2400, 1500, 0.3, 0.3), 0.0)
    _sounds["laser"] = _to_sound(lz, 0.55)
    zap = _noise(0.25, 1.4, 0.8, 0.3, lambda x: (1 - x))
    _mix(zap, _sweep(200, 1400, 0.2, 0.5), 0.0)
    _sounds["zap"] = _to_sound(zap, 0.8)
    cash = _bell(1568.0, 0.5, 0.35)
    _mix(cash, _bell(2093.0, 0.5, 0.3), 0.07)
    _sounds["cash"] = _to_sound(cash, 0.7)
    sir = _sweep(650, 1050, 0.5, 0.45)
    _mix(sir, _sweep(1050, 650, 0.5, 0.45), 0.5)
    _mix(sir, _sweep(650, 1050, 0.5, 0.45), 1.0)
    _sounds["siren"] = _to_sound(sir, 0.55)
    alarm = _sweep(880, 880, 0.18, 0.4)
    _mix(alarm, _sweep(660, 660, 0.18, 0.4), 0.2)
    _mix(alarm, _sweep(880, 880, 0.18, 0.4), 0.4)
    _mix(alarm, _sweep(660, 660, 0.18, 0.4), 0.6)
    _sounds["alarm"] = _to_sound(alarm, 0.6)
    _sounds["key"] = _to_sound(_sweep(1300, 900, 0.03, 0.3), 0.5)
    unl = _bell(392.0, 1.2, 0.4)
    _mix(unl, _bell(523.25, 1.2, 0.4), 0.12)
    _mix(unl, _bell(783.99, 1.2, 0.4), 0.24)
    _mix(unl, _taiko(0.5), 0.0)
    _sounds["unlock"] = _to_sound(unl, 0.85)
    _sounds["jail"] = _to_sound(_sweep(200, 90, 0.5, 0.7, decay=1.0), 0.8)

    _enabled = True
    return True


MASTER = 0.8          # laptop Settings er volume slider ei number ta bodlay (0.0 - 1.0)


def set_master(v):
    """Pura game er volume. Laptop > Settings > Sound slider eta call kore."""
    global MASTER
    MASTER = max(0.0, min(1.0, float(v)))
    if _enabled and _music_channel is not None:
        _music_channel.set_volume(MASTER)


def get_master():
    return MASTER


def play(name, volume=1.0):
    if not _enabled or name not in _sounds:
        return
    ch = _sounds[name].play()
    if ch:
        ch.set_volume(volume * MASTER)


def play_music(name, loops=0, volume=1.0):
    if not _enabled or name not in _sounds:
        return
    _music_channel.set_volume(volume * MASTER)
    _music_channel.play(_sounds[name], loops=loops)


def stop_music(fade_ms=600):
    if _enabled and _music_channel is not None:
        _music_channel.fadeout(fade_ms)
