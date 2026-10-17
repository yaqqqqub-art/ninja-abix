"""
intro.py - Game cholar age eta prothome chole.
Run korar jonno:  python intro.py

Logo + "ABIX NINJA" + niche "ABIX GAMES" + 10 second loading bar + sound.
Loading 100% hole main_game.py open hoy.
"""
import sys
import pygame

import os
import sound
import trailer
from animation import (
    WIDTH, HEIGHT, BG, RED, WHITE, GOLD,
    Starfield, Embers, FadeText, LoadingBar,
    draw_logo, logo_available, fade_overlay,
)

LOADING_SECONDS = 10.0
FADE_OUT_SECONDS = 0.8

# (shomoy, sound) - intro er sound events
SOUND_EVENTS = [
    (0.2, "whoosh"),   # logo ashche
    (1.8, "chime"),    # ABIX GAMES
    (2.5, "pop"),      # loading 25%
    (5.0, "pop"),      # loading 50%
    (7.5, "pop"),      # loading 75%
    (LOADING_SECONDS, "ding"),  # loading shesh
]


def run_intro(screen, clock):
    stars = Starfield()
    embers = Embers()

    title = FadeText("ABIX NINJA", 72, WHITE, (WIDTH // 2, 320), start=0.8, fade=1.0, glow=RED)
    studio = FadeText("BY ABU BAKKAR", 36, GOLD, (WIDTH // 2, 358), start=1.8, fade=1.0, glow=RED)
    studio2 = FadeText("ABIX GAMES", 20, (170, 160, 130), (WIDTH // 2, 398), start=2.4, fade=1.0)
    bar = LoadingBar((WIDTH // 2, 465))

    sound.play_music("intro")      # taiko + melody (11 second)
    pending = list(SOUND_EVENTS)
    music_faded = False

    t = 0.0
    while True:
        t += min(clock.tick(60) / 1000.0, 0.1)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        while pending and t >= pending[0][0]:
            sound.play(pending.pop(0)[1])

        stars.update()
        embers.update()

        screen.fill(BG)
        stars.draw(screen, t)
        embers.draw(screen, t)

        if logo_available():                         # stars er upore ABIX NINJA logo
            draw_logo(screen, (WIDTH // 2, 175), t, scale=1.0, appear=min(1.0, t / 1.2))
        else:
            draw_logo(screen, (WIDTH // 2, 140), t, scale=1.0, appear=min(1.0, t / 1.2))
            title.draw(screen, t)
        studio.draw(screen, t)
        studio2.draw(screen, t)

        progress = min(1.0, t / LOADING_SECONDS)
        bar.draw(screen, progress, t)

        # loading shesh hole screen kalo hoye jay
        if t > LOADING_SECONDS:
            if not music_faded:
                sound.stop_music(700)
                music_faded = True
            fade_overlay(screen, (t - LOADING_SECONDS) / FADE_OUT_SECONDS)
            if t > LOADING_SECONDS + FADE_OUT_SECONDS:
                return

        pygame.display.flip()


def main():
    pygame.init()
    pygame.display.set_caption("Abix Ninja - by Abu Bakkar")
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
    sound.init()                      # sound toiri (1-2 second lagte pare)
    clock = pygame.time.Clock()       # sound toiri'r por clock, jate shomoy na lafay

    run_intro(screen, clock)

    # intro shesh -> main_game.py
    import main_game
    main_game.run(screen, clock)


if __name__ == "__main__":
    main()
