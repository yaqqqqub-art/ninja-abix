"""Android / mobile entry point for Abix Ninja (buildozer uses main.py)."""
import os
import pygame

import sound
import main_game
from animation import WIDTH, HEIGHT

if __name__ == "__main__":
    pygame.init()
    flags = pygame.SCALED | (pygame.FULLSCREEN if "ANDROID_ARGUMENT" in os.environ else 0)
    scr = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    sound.init()
    try:
        sound.set_master(main_game.load_save()["laptop"]["volume"])
    except Exception:
        pass
    main_game.run(scr, pygame.time.Clock())
