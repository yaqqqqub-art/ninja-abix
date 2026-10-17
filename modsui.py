"""modsui.py - ABIX MODS panel (main menu: MODS button / M key)."""
import pygame

from animation import WIDTH, HEIGHT, WHITE, GOLD, get_font, rgb_color

COL = {"loaded": (110, 240, 150), "disabled": (255, 190, 80), "blocked": (255, 110, 110),
       "error": (255, 110, 110), "checking": (150, 190, 255), "gone": (150, 150, 170)}


class ModsPanel:
    def __init__(self, mgr):
        self.mgr = mgr
        self.active = False
        self.t = 0.0
        self.box = pygame.Rect(0, 0, 720, 440)
        self.box.center = (WIDTH // 2, HEIGHT // 2)
        b = self.box
        self.b_open = pygame.Rect(b.x + 24, b.bottom - 62, 250, 42)
        self.b_chk = pygame.Rect(b.x + 288, b.bottom - 62, 190, 42)
        self.b_close = pygame.Rect(b.right - 194, b.bottom - 62, 170, 42)

    def open(self):
        self.active = True
        self.mgr.recheck()

    def update(self, dt):
        self.t += dt

    def event(self, e):
        if not self.active:
            return False
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_m):
            self.active = False
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            p = e.pos
            if self.b_open.collidepoint(p):
                self.mgr.open_folder()
            elif self.b_chk.collidepoint(p):
                self.mgr.recheck()
            elif self.b_close.collidepoint(p) or not self.box.collidepoint(p):
                self.active = False
        return True

    def _btn(self, surf, r, label, mouse):
        hot = r.collidepoint(mouse)
        pygame.draw.rect(surf, rgb_color(self.t, offset=0.3) if hot else (34, 34, 58), r, border_radius=12)
        pygame.draw.rect(surf, WHITE if hot else (95, 95, 125), r, 3, border_radius=12)
        img = get_font(17).render(label, True, (15, 15, 25) if hot else WHITE)
        surf.blit(img, img.get_rect(center=r.center))

    def draw(self, surf, mouse):
        if not self.active:
            return
        m = self.mgr
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surf.blit(dim, (0, 0))
        pygame.draw.rect(surf, (18, 20, 40), self.box, border_radius=18)
        pygame.draw.rect(surf, rgb_color(self.t), self.box, 4, border_radius=18)
        b = self.box
        t = get_font(28).render("ABIX MODS", True, GOLD)
        surf.blit(t, t.get_rect(center=(b.centerx, b.y + 34)))
        img = get_font(20).render("MOD CHECKER: REMOVED  -  every mod runs, nothing is blocked", True, (110, 240, 150))
        surf.blit(img, img.get_rect(center=(b.centerx, b.y + 70)))
        y = b.y + 112
        ents = list(m.entries.values())
        if not ents:
            n = get_font(18, False).render("No mods yet. Put mod folders in the AbixMods folder.", True, (170, 170, 195))
            surf.blit(n, n.get_rect(center=(b.centerx, y + 70)))
        for e in ents[:6]:
            row = pygame.Rect(b.x + 24, y, b.w - 48, 48)
            pygame.draw.rect(surf, (28, 30, 56), row, border_radius=10)
            nm = get_font(18).render(f"{e.name}  v{e.version}  by {e.author}"[:60], True, WHITE)
            surf.blit(nm, (row.x + 12, row.y + 5))
            st = get_font(15).render(e.status.upper(), True, COL.get(e.status, WHITE))
            surf.blit(st, st.get_rect(topright=(row.right - 12, row.y + 7)))
            if e.reason:
                rs = get_font(13, False).render(e.reason[:92], True, (200, 160, 160))
                surf.blit(rs, (row.x + 12, row.y + 28))
            y += 54
        if len(ents) > 6:
            more = get_font(14, False).render(f"+ {len(ents) - 6} more", True, (170, 170, 195))
            surf.blit(more, (b.x + 28, y))
        self._btn(surf, self.b_open, "OPEN MODS FOLDER", mouse)
        self._btn(surf, self.b_chk, "RE-CHECK", mouse)
        self._btn(surf, self.b_close, "CLOSE (ESC)", mouse)
