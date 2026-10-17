"""trailer.py - ABIX NINJA TRAILER: full screen e video chole (ESC / SPACE / ENTER / click = skip)."""
import os
import sys
import time

import pygame

import sound
from animation import WIDTH, HEIGHT


def asset(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", name)


def _external(path):
    """cv2 na thakle default player e khule."""
    try:
        os.startfile(path)          # Windows
    except Exception:
        pass


def play(screen, clock):
    video = asset("trailer.mp4")
    if not os.path.exists(video):
        return
    try:
        import cv2
    except Exception:
        _external(video)
        return

    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        _external(video)
        return
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0

    was_full = bool(screen.get_flags() & pygame.FULLSCREEN)
    if not was_full:
        try:
            pygame.display.toggle_fullscreen()
        except Exception:
            pass
    pygame.mouse.set_visible(False)

    try:
        sound.stop_music(250)
    except Exception:
        pass
    snd = None
    try:
        snd = pygame.mixer.Sound(asset("trailer.wav"))
        snd.play()
    except Exception:
        snd = None

    surf, idx = None, -1
    start = time.perf_counter()
    running = True
    while running:
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                running = False
            if e.type == pygame.MOUSEBUTTONDOWN:
                running = False
            if e.type == pygame.JOYBUTTONDOWN:
                running = False

        want = int((time.perf_counter() - start) * fps)
        while idx < want:                         # frame skip kore audio'r shathe mil rakhe
            ok, frame = cap.read()
            if not ok:
                running = False
                break
            idx += 1
            if idx >= want or idx == 0:
                frame = cv2.resize(frame, (WIDTH, HEIGHT))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                surf = pygame.image.frombuffer(frame.tobytes(), (WIDTH, HEIGHT), "RGB")
        if surf is not None:
            screen.blit(surf, (0, 0))
        pygame.display.flip()

    cap.release()
    if snd:
        snd.stop()
    pygame.mouse.set_visible(True)
    if not was_full:
        try:
            pygame.display.toggle_fullscreen()
        except Exception:
            pass
    try:
        sound.play_music("menu", loops=-1)
    except Exception:
        pass
