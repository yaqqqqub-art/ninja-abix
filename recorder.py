"""
recorder.py - ABIX SCREEN RECORDER  (V12)

  F9   = recording shuru / shesh         F10 = screenshot (PNG)
  Mobile:  uporer  REC  button (touch.py)

Video kothay jay:   <AbixNinja folder>/Recordings/abix_2026-10-17_21-30-05.mp4
  (Windows: %APPDATA%\\AbixNinja\\Recordings,  ABIX_HOME set thakle shekhane)

Kibhabe kaj kore:
  1) ffmpeg thakle  ->  shorashori MP4 (H.264, 30 fps)   [ffmpeg PATH e thakle ba  pip install imageio-ffmpeg]
  2) ffmpeg na thakle -> frame gulo JPG hishabe folder e (15 fps).  Pore ffmpeg diye jure nao:
         ffmpeg -framerate 15 -i frame_%05d.jpg -pix_fmt yuv420p out.mp4
Note: game er sound record hoy na (shudhu chobi).

Game e ekbar  recorder.install()  chalate hoy (main_game.run e kora ache).  Shob level / menu / 3D jail e kaj kore,
karon pygame.display.flip ke hook kore.
"""
import os
import queue
import shutil
import subprocess
import threading
import time

import pygame

VIDEO_FPS = 30
FRAME_FPS = 15                  # ffmpeg na thakle
MAX_FRAME_SECONDS = 120         # frame-folder mode e max koto second (storage bachate)

_state = {
    "on": False, "installed": False, "orig_flip": None, "orig_get": None,
    "next_t": 0.0, "t0": 0.0, "mode": "", "path": "", "proc": None, "q": None, "thread": None,
    "frames": 0, "dropped": 0, "toast": "", "toast_t": 0.0, "size": (0, 0), "font": None,
}


# ------------------------------------------------------------------
def home_dir():
    base = os.environ.get("ABIX_HOME") or os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "AbixNinja") if not os.environ.get("ABIX_HOME") else base
    return d


def rec_dir():
    d = os.path.join(home_dir(), "Recordings")
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        d = os.path.join(os.path.expanduser("~"), "AbixRecordings")
        os.makedirs(d, exist_ok=True)
    return d


def find_ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg                       # pip install imageio-ffmpeg  (ffmpeg binary soho ashe)
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _stamp():
    return time.strftime("%Y-%m-%d_%H-%M-%S")


def _toast(msg, secs=4.0):
    _state["toast"], _state["toast_t"] = msg, time.time() + secs
    print("[recorder]", msg)


def is_recording():
    return bool(_state["on"])


# ------------------------------------------------------------------
def _to_bytes(surf):
    try:
        return pygame.image.tobytes(surf, "RGB")
    except AttributeError:
        return pygame.image.tostring(surf, "RGB")


def _writer_ffmpeg(q, proc):
    try:
        while True:
            data = q.get()
            if data is None:
                break
            try:
                proc.stdin.write(data)
            except (BrokenPipeError, OSError, ValueError):
                break
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=60)
        except Exception:
            pass


def _writer_frames(q, folder, ext):
    n = 0
    while True:
        item = q.get()
        if item is None:
            break
        size, raw = item
        try:
            s = pygame.image.frombuffer(raw, size, "RGB")
            pygame.image.save(s, os.path.join(folder, "frame_%05d.%s" % (n, ext)))
        except Exception:
            pass
        n += 1


def start():
    if _state["on"]:
        return
    surf = pygame.display.get_surface()
    if surf is None:
        return
    size = surf.get_size()
    base = os.path.join(rec_dir(), "abix_" + _stamp())
    ff = find_ffmpeg()
    _state.update(frames=0, dropped=0, size=size, t0=time.time(), next_t=0.0)
    q = queue.Queue(maxsize=90)
    _state["q"] = q
    if ff:
        path = base + ".mp4"
        cmd = [ff, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % size,
               "-r", str(VIDEO_FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
               "-pix_fmt", "yuv420p", path]
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, creationflags=flags)
            th = threading.Thread(target=_writer_ffmpeg, args=(q, proc), daemon=True)
            th.start()
            _state.update(mode="mp4", path=path, proc=proc, thread=th, on=True)
            _toast("REC started  (F9 = stop)")
            return
        except Exception as ex:
            print("[recorder] ffmpeg failed:", ex)
    # fallback: frame folder
    os.makedirs(base, exist_ok=True)
    ext = "jpg"
    th = threading.Thread(target=_writer_frames, args=(q, base, ext), daemon=True)
    th.start()
    _state.update(mode="frames", path=base, proc=None, thread=th, on=True)
    _toast("REC started (frames mode - ffmpeg nei)  F9 = stop")


def stop():
    if not _state["on"]:
        return
    _state["on"] = False
    q, th = _state["q"], _state["thread"]
    try:
        q.put(None, timeout=2)
    except Exception:
        pass
    secs = time.time() - _state["t0"]
    if _state["mode"] == "mp4":
        _toast("Saved: %s  (%.0fs)" % (os.path.basename(_state["path"]), secs), 6.0)
    else:
        _toast("Saved frames: %s  (%d)" % (os.path.basename(_state["path"]), _state["frames"]), 6.0)


def toggle():
    stop() if _state["on"] else start()


def screenshot():
    surf = pygame.display.get_surface()
    if surf is None:
        return
    path = os.path.join(rec_dir(), "abix_" + _stamp() + ".png")
    try:
        pygame.image.save(surf, path)
        _toast("Screenshot: " + os.path.basename(path), 3.0)
    except Exception as ex:
        _toast("Screenshot failed: %s" % ex, 3.0)


# ------------------------------------------------------------------
def _capture(surf):
    now = time.time()
    fps = VIDEO_FPS if _state["mode"] == "mp4" else FRAME_FPS
    if now < _state["next_t"]:
        return
    step = 1.0 / fps
    # mp4: wall-clock e frame dubar kore dei jate video er speed thik thake
    reps = 1
    if _state["mode"] == "mp4":
        if _state["next_t"] == 0.0:
            _state["next_t"] = now
        reps = max(1, min(4, int((now - _state["next_t"]) / step) + 1))
        _state["next_t"] += step * reps
    else:
        _state["next_t"] = now + step
        if now - _state["t0"] > MAX_FRAME_SECONDS:
            stop()
            return
    raw = _to_bytes(surf)
    q = _state["q"]
    for _ in range(reps):
        try:
            q.put_nowait(raw if _state["mode"] == "mp4" else (_state["size"], raw))
            _state["frames"] += 1
        except queue.Full:
            _state["dropped"] += 1
            break


def _overlay(surf):
    now = time.time()
    if _state["font"] is None:
        _state["font"] = pygame.font.SysFont(None, 24, bold=True)
    f = _state["font"]
    if _state["on"]:
        if int(now * 2) % 2 == 0:
            pygame.draw.circle(surf, (255, 40, 50), (surf.get_width() - 118, 20), 8)
        el = int(now - _state["t0"])
        img = f.render("REC %02d:%02d" % (el // 60, el % 60), True, (255, 255, 255))
        surf.blit(img, (surf.get_width() - 104, 11))
    if now < _state["toast_t"] and _state["toast"]:
        img = f.render(_state["toast"], True, (255, 255, 255))
        r = img.get_rect(midbottom=(surf.get_width() // 2, surf.get_height() - 8))
        bg = pygame.Surface((r.w + 20, r.h + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 170))
        surf.blit(bg, (r.x - 10, r.y - 4))
        surf.blit(img, r)


def _flip():
    surf = pygame.display.get_surface()
    if surf is not None:
        try:
            if _state["on"]:
                _capture(surf)                     # overlay chara capture (REC badge video te jabe na)
            _overlay(surf)
        except Exception as ex:
            _state["on"] = False
            print("[recorder] error:", ex)
    _state["orig_flip"]()


def _get(*a, **k):
    evs = _state["orig_get"](*a, **k)
    try:
        for e in evs:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_F9:
                    toggle()
                elif e.key == pygame.K_F10:
                    screenshot()
    except Exception:
        pass
    return evs


def install():
    """Ekbar chalao.  F9 / F10 shob jaygay kaj korbe."""
    if _state["installed"]:
        return
    _state["installed"] = True
    _state["orig_flip"] = pygame.display.flip
    _state["orig_get"] = pygame.event.get
    pygame.display.flip = _flip
    pygame.event.get = _get


def shutdown():
    stop()
