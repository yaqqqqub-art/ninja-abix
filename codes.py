"""codes.py - SECRET CODE box (main menu er CODE button / C key).

Code gulo sha256 hash hishebe rakha - file khule dekhleo code dekha jabe na.
"""
import hashlib
import math

import pygame

from animation import WIDTH, HEIGHT, WHITE, GOLD, get_font, rgb_color

CHAPTERS, LEVELS = 5, 20
BIG = 99_999_999
SALT = "abix.v5::"

H = {
    "b1272d55cd6d8f37d631964f74f3aa57753dfc1a4e8758e289cee80b08ad63e5": "god",
    "9079e28e7b2efa3e2e7af7dba814873268217a8e8540a31226097210ede145c5": "unlock",
    "6a2185eeeb03e80801995a783de0f1c57749d623be29180e3d078ee3ffe9fdf7": "stars",
    "9446624d0747407c6681e337df00bfd20e0bd379599e7049c1bfd94877c9329f": "tools",
    "0920d843e85a28f069cca55b25f0c17a7514a20484ce1c76988695e96a638994": "diamond",
    "54745ad22c0e7cd4ac6624577dcbc3c96d558162e840cdefdec652f93e40b04c": "rich",
    "0889a34fa7edcd20621d97fb7fa061a44c7bdabddaed6575952b9c405375e475": "normal",
    "bc410691ac7f3b76a8d309c0c22c02f922e6a4908f263ecf48f5726c02fa29e3": "unlimited",
}


def top_up(save):
    """UNLIMITED chalu thakle taka / dollar / diamond sob shomoy bhora thake."""
    if save.get("unlimited"):
        for k in ("money", "dollars", "diamonds"):
            if save.get(k, 0) < BIG:
                save[k] = BIG


def apply_code(text, save):
    """-> (ok, message)"""
    key = H.get(hashlib.sha256((SALT + text.strip()).encode("utf-8")).hexdigest())
    if key is None:
        return False, "WRONG CODE"
    if key == "unlimited":
        save["unlimited"] = True
        top_up(save)
        return True, "UNLIMITED MONEY ON!"
    if key == "normal":
        save["unlimited"] = False
        return True, "Unlimited money OFF (normal mode)"
    if key == "god":
        save["god"] = not save.get("god", False)
        return True, "GOD MODE " + ("ON" if save["god"] else "OFF")
    if key == "unlock":
        for i in range(CHAPTERS):
            save["done"][i] = LEVELS
        return True, "ALL LEVELS UNLOCKED!"
    if key == "stars":
        for i in range(CHAPTERS):
            for j in range(LEVELS):
                save["stars"][i][j] = 3
        return True, "ALL STARS = 3!"
    if key == "tools":
        for k in ("star", "code", "electric"):
            save["special"][k] = True
        return True, "ALL SPECIAL TOOLS UNLOCKED!"
    if key == "diamond":
        save["diamonds"] = save.get("diamonds", 0) + 100
        return True, "+100 DIAMOND!"
    if key == "rich":
        save["money"] = save.get("money", 0) + 1_000_000
        return True, "+1,000,000 Tk!"
    return False, "WRONG CODE"


class CodeBox:
    def __init__(self):
        self.active = False
        self.text = ""
        self.msg, self.msg_ok, self.msg_t = "", False, 0.0
        self.box = pygame.Rect(0, 0, 560, 230)
        self.box.center = (WIDTH // 2, HEIGHT // 2)
        self.field = pygame.Rect(self.box.x + 30, self.box.y + 95, self.box.w - 60, 52)
        self.t = 0.0
        self.fails, self.lock_t = 0, 0.0

    def open(self):
        self.active, self.text, self.msg, self.msg_t = True, "", "", 0.0

    def update(self, dt):
        self.t += dt
        self.msg_t = max(0.0, self.msg_t - dt)
        self.lock_t = max(0.0, self.lock_t - dt)

    def event(self, e, save, save_fn, sound=None):
        """True = event use hoyeche."""
        if not self.active:
            return False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.active = False
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.lock_t > 0:
                    self.msg, self.msg_ok, self.msg_t = "TOO MANY TRIES - wait %ds" % (int(self.lock_t) + 1), False, 2.0
                    return True
                ok, self.msg = apply_code(self.text, save)
                self.msg_ok, self.msg_t = ok, 3.0
                if ok:
                    self.fails = 0
                else:
                    self.fails += 1
                    if self.fails >= 5:
                        self.fails, self.lock_t = 0, 30.0
                        self.msg = "TOO MANY TRIES - locked 30s"
                if ok:
                    save_fn()
                    self.text = ""
                if sound:
                    sound.play("chime" if ok else "back")
            elif e.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif e.key == pygame.K_v and (e.mod & pygame.KMOD_CTRL):
                try:
                    pygame.scrap.init()
                    raw = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if raw:
                        self.text = (self.text + raw.decode("utf-8", "ignore").replace("\x00", "").strip())[:40]
                except Exception:
                    pass
            elif e.unicode and e.unicode.isprintable() and len(self.text) < 40:
                self.text += e.unicode
            return True
        if e.type == pygame.MOUSEBUTTONDOWN:
            if not self.box.collidepoint(getattr(e, "pos", (0, 0))):
                self.active = False
            return True
        return e.type in (pygame.KEYUP, pygame.TEXTINPUT)

    def draw(self, surf):
        if not self.active:
            return
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        surf.blit(dim, (0, 0))
        pygame.draw.rect(surf, (18, 20, 40), self.box, border_radius=18)
        pygame.draw.rect(surf, rgb_color(self.t), self.box, 4, border_radius=18)
        t1 = get_font(28).render("ENTER SECRET CODE", True, GOLD)
        surf.blit(t1, t1.get_rect(center=(self.box.centerx, self.box.y + 45)))
        pygame.draw.rect(surf, (8, 8, 18), self.field, border_radius=10)
        pygame.draw.rect(surf, WHITE, self.field, 2, border_radius=10)
        shown = self.text + ("|" if int(self.t * 2) % 2 == 0 else " ")
        f = 26
        while f > 12 and get_font(f).size(shown)[0] > self.field.w - 24:
            f -= 2
        img = get_font(f).render(shown, True, WHITE)
        surf.blit(img, img.get_rect(midleft=(self.field.x + 12, self.field.centery)))
        if self.msg_t > 0:
            m = get_font(22).render(self.msg, True, (110, 240, 150) if self.msg_ok else (255, 110, 110))
            surf.blit(m, m.get_rect(center=(self.box.centerx, self.box.y + 175)))
        h = get_font(15).render("ENTER = OK     ESC = close     Ctrl+V = paste", True, (150, 150, 175))
        surf.blit(h, h.get_rect(center=(self.box.centerx, self.box.bottom - 18)))
