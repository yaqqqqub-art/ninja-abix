"""
bust_ursina.py - game theke REAL 3D (Ursina) arrest animation chalano.

  pip install ursina          (PC: Windows / Mac / Linux)

ursina_bust.py ke alada process e chalay (Ursina nijer window khole), game er pygame window "3D ARREST" screen dekhay.
Shesh hole game jail e jay.  Ursina nei / Android / exe build / error  ->  game nijer bust3d.py (pygame 3D) chalay.
Bondho korte:  ABIX_NO_URSINA=1
"""
import importlib.util
import math
import os
import subprocess
import sys
import time

import pygame

from animation import WIDTH, HEIGHT, get_font

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "ursina_bust.py")


def available():
    if os.environ.get("ABIX_NO_URSINA") or "ANDROID_ARGUMENT" in os.environ or getattr(sys, "frozen", False):
        return False
    if not os.path.isfile(SCRIPT):
        return False
    try:
        return importlib.util.find_spec("ursina") is not None
    except Exception:
        return False


class UrsinaBust:
    DURATION = 10.4

    def __init__(self, rounds=3):
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.proc = subprocess.Popen([sys.executable, SCRIPT, "--duration", str(self.DURATION),
                                      "--rounds", str(rounds)], cwd=HERE, creationflags=flags,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.t = 0.0
        self.done = False
        self.failed = False

    def update(self, dt):
        self.t += dt
        rc = self.proc.poll()
        if rc is not None:
            if rc == 0 or self.t > 4.0:
                self.done = True                 # shesh holo (ba user skip korlo)
            else:
                self.failed = True               # shuru e-i crash -> pygame fallback
        elif self.t > self.DURATION + 12.0:      # atke gele zor kore bondho
            try:
                self.proc.kill()
            except Exception:
                pass
            self.done = True

    def draw(self, surf):
        surf.fill((6, 8, 18))
        t = self.t
        on = int(t * 5) % 2 == 0
        for i in range(8):                       # police light sweep
            a = t * 1.5 + i * 0.8
            col = (255, 40, 60) if (i % 2 == 0) == on else (60, 110, 255)
            x = WIDTH / 2 + math.cos(a) * 340
            pygame.draw.circle(surf, col, (int(x), HEIGHT // 2 + int(math.sin(a * 1.7) * 130)), 18)
        f = get_font(34, True).render("3D ARREST ANIMATION", True, (255, 230, 150))
        surf.blit(f, f.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        g = get_font(18, False).render("Ursina 3D window e dekho  (ESC / SPACE = skip)", True, (190, 190, 215))
        surf.blit(g, g.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 24)))

    def close(self):
        try:
            if self.proc.poll() is None:
                self.proc.kill()
        except Exception:
            pass
