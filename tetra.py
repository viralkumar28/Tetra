"""
Tetra - a Tetris-style falling block game.

Run:
    pip install "pygame>=2.0"
    python tetra.py

Controls:
    Left / Right ....... move
    Down ............... soft drop
    Up or X ............ rotate clockwise
    Z .................. rotate counter-clockwise
    Space .............. hard drop
    C or Shift ......... hold
    P or Esc ........... pause
    R .................. restart

The whole window scales from the CELL constant below - change it and
every panel, font and margin follows.
"""

import os
import random
import sys

import pygame

# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------
COLS, ROWS = 10, 20
CELL = 28                      # size of one block in pixels

PAD = 16                       # margin between window edge and cabinet
CAB_PAD = 14                   # cabinet inner padding
GAP = 12                       # gap between cabinet columns
RAIL_W = 132                   # width of the left / right side rails
WELL_PAD = 6                   # padding inside the playfield housing
MODULE_PAD = 9

BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
WELL_W, WELL_H = BOARD_W + WELL_PAD * 2, BOARD_H + WELL_PAD * 2

MASTHEAD_H = 62
KEYS_H = 66

CAB_W = CAB_PAD * 2 + RAIL_W + GAP + WELL_W + GAP + RAIL_W
CAB_H = CAB_PAD * 2 + WELL_H
WIN_W = CAB_W + PAD * 2
WIN_H = PAD + MASTHEAD_H + CAB_H + KEYS_H + PAD

# --------------------------------------------------------------------------
# palette
# --------------------------------------------------------------------------
PAGE = (16, 17, 21)
PAGE_INK = (227, 229, 234)
PAGE_MUTE = (139, 143, 153)
SHELL_HI = (38, 42, 51)
SHELL_LO = (20, 22, 27)
RULE = (45, 50, 61)
WELL_BG = (10, 12, 16)
GRID_LINE = (22, 25, 31)
CHROME = (140, 147, 163)
CHROME_HI = (230, 233, 240)
FLASH = (242, 244, 248)

COLORS = {
    "I": (46, 196, 216),
    "J": (79, 127, 224),
    "L": (224, 138, 60),
    "O": (220, 179, 60),
    "S": (75, 179, 95),
    "T": (155, 106, 214),
    "Z": (217, 87, 87),
}

# --------------------------------------------------------------------------
# tetrominoes
# --------------------------------------------------------------------------
SHAPES = {
    "I": [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    "J": [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
    "L": [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
    "O": [[1, 1], [1, 1]],
    "S": [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
    "T": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
    "Z": [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
}
SPAWN = {"I": (3, -1), "O": (4, 0), "J": (3, 0), "L": (3, 0),
         "S": (3, 0), "T": (3, 0), "Z": (3, 0)}

# Super Rotation System wall kicks. y is written in the standard
# "up is positive" form and negated when applied to the screen grid.
KICKS_JLSTZ = {
    (0, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (1, 0): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (1, 2): [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
    (2, 1): [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    (2, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
    (3, 2): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (3, 0): [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
    (0, 3): [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
}
KICKS_I = {
    (0, 1): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (1, 0): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (1, 2): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
    (2, 1): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (2, 3): [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
    (3, 2): [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
    (3, 0): [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
    (0, 3): [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
}

# milliseconds per row, by level
GRAVITY = [1000, 793, 618, 473, 355, 262, 190, 135, 94, 64, 43, 28, 18, 11, 7]
LINE_SCORE = [0, 100, 300, 500, 800]

DAS_MS = 165        # delay before a held move key repeats
ARR_MS = 42         # repeat interval once it does
SOFT_MS = 45        # soft drop repeat interval
LOCK_MS = 480       # grace period before a grounded piece locks
LOCK_RESETS = 15
FLASH_MS = 130

BEST_FILE = os.path.join(os.path.expanduser("~"), ".tetra_best")
FOCUS_LOST = getattr(pygame, "WINDOWFOCUSLOST", -1)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def rotate_matrix(m, clockwise=True):
    n = len(m)
    if clockwise:
        return [[m[n - 1 - x][y] for x in range(n)] for y in range(n)]
    return [[m[x][n - 1 - y] for x in range(n)] for y in range(n)]


def mix(a, b, t):
    """Blend colour a toward b by t (0..1)."""
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def load_font(size, bold=False):
    path = pygame.font.match_font(
        "chakrapetch,bahnschrift,dejavusans,verdana,arial,freesans"
    )
    font = pygame.font.Font(path, size) if path else pygame.font.SysFont(None, size)
    font.set_bold(bold)
    return font


def draw_block(surface, x, y, size, color, alpha=255):
    """A block with a light top-left edge and a dark bottom-right edge."""
    gap = max(1, round(size * 0.07))
    s = size - gap
    edge = max(1, int(s * 0.16))

    if alpha < 255:
        tile = pygame.Surface((s, s), pygame.SRCALPHA)
        _bevel(tile, 0, 0, s, edge, color)
        tile.set_alpha(alpha)
        surface.blit(tile, (x, y))
    else:
        _bevel(surface, x, y, s, edge, color)


def _bevel(surface, x, y, s, edge, color):
    pygame.draw.rect(surface, color, (x, y, s, s))
    hi = mix(color, (255, 255, 255), 0.22)
    lo = mix(color, (0, 0, 0), 0.28)
    pygame.draw.rect(surface, hi, (x, y, s, edge))
    pygame.draw.rect(surface, hi, (x, y, edge, s))
    pygame.draw.rect(surface, lo, (x, y + s - edge, s, edge))
    pygame.draw.rect(surface, lo, (x + s - edge, y, edge, s))


def panel(surface, rect, radius=8):
    pygame.draw.rect(surface, SHELL_LO, rect, border_radius=radius)
    pygame.draw.rect(surface, RULE, rect, width=1, border_radius=radius)


def shape_bounds(matrix):
    cells = [(x, y) for y, row in enumerate(matrix)
             for x, v in enumerate(row) if v]
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return min(xs), min(ys), max(xs), max(ys)


# --------------------------------------------------------------------------
# pieces
# --------------------------------------------------------------------------
class Piece:
    __slots__ = ("kind", "m", "x", "y", "r")

    def __init__(self, kind):
        self.kind = kind
        self.m = [row[:] for row in SHAPES[kind]]
        self.x, self.y = SPAWN[kind]
        self.r = 0

    def cells(self):
        for y, row in enumerate(self.m):
            for x, v in enumerate(row):
                if v:
                    yield self.x + x, self.y + y


class Bag:
    """Seven-bag randomiser - every piece appears once per cycle."""

    def __init__(self):
        self._items = []

    def pull(self):
        if not self._items:
            self._items = list(SHAPES)
            random.shuffle(self._items)
        return self._items.pop()


# --------------------------------------------------------------------------
# game
# --------------------------------------------------------------------------
class Tetra:
    READY, PLAYING, PAUSED, OVER = "ready", "playing", "paused", "over"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tetra")
        self.win = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.key.set_repeat(0)
        self.clock = pygame.time.Clock()

        self.f_title = load_font(26, bold=True)
        self.f_sub = load_font(14)
        self.f_label = load_font(13)
        self.f_big = load_font(22, bold=True)
        self.f_mid = load_font(17, bold=True)
        self.f_key = load_font(13)
        self.f_veil = load_font(20, bold=True)
        self.f_veil_sub = load_font(14)

        # cabinet rectangles, all derived from the constants above
        cab_x, cab_y = PAD, PAD + MASTHEAD_H
        self.cabinet = pygame.Rect(cab_x, cab_y, CAB_W, CAB_H)
        inner_x, inner_y = cab_x + CAB_PAD, cab_y + CAB_PAD
        self.well = pygame.Rect(inner_x + RAIL_W + GAP, inner_y, WELL_W, WELL_H)
        self.board_origin = (self.well.x + WELL_PAD, self.well.y + WELL_PAD)

        mini_h = CELL * 2 + 14
        self.hold_box = pygame.Rect(inner_x, inner_y, RAIL_W, mini_h + 26)
        self.stats_box = pygame.Rect(
            inner_x, self.hold_box.bottom + 10, RAIL_W, 0)
        self.stats_box.height = WELL_H - self.hold_box.height - 10

        nx = self.well.right + GAP
        self.next_box = pygame.Rect(nx, inner_y, RAIL_W, mini_h * 3 + 26 + 14)

        self.best = self._load_best()
        self.reset()

    # -- persistence -------------------------------------------------------
    @staticmethod
    def _load_best():
        try:
            with open(BEST_FILE, "r", encoding="utf-8") as fh:
                return int(fh.read().strip() or 0)
        except (OSError, ValueError):
            return 0

    def _save_best(self):
        try:
            with open(BEST_FILE, "w", encoding="utf-8") as fh:
                fh.write(str(self.best))
        except OSError:
            pass

    # -- state -------------------------------------------------------------
    def reset(self):
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.bag = Bag()
        self.queue = [self.bag.pull() for _ in range(3)]
        self.piece = None
        self.held = None
        self.can_hold = True

        self.score = 0
        self.level = 1
        self.lines = 0

        self.phase = self.READY
        self.drop_timer = 0
        self.lock_timer = None
        self.lock_resets = 0
        self.clearing = None
        self.clear_timer = 0
        self.jolt = 0

        self.das_dir = 0
        self.das_timer = 0
        self.das_ready = False
        self.soft_held = False
        self.soft_timer = 0

    def start(self):
        self.reset()
        self.phase = self.PLAYING
        self.spawn()

    def spawn(self):
        self.piece = Piece(self.queue.pop(0))
        self.queue.append(self.bag.pull())
        self.can_hold = True
        self.drop_timer = 0
        self.lock_timer = None
        self.lock_resets = 0
        if self.collides(self.piece.m, self.piece.x, self.piece.y):
            self.game_over()

    def game_over(self):
        self.phase = self.OVER
        self.piece = None
        if self.score > self.best:
            self.best = self.score
            self._save_best()

    def toggle_pause(self):
        if self.phase == self.PLAYING:
            self.phase = self.PAUSED
        elif self.phase == self.PAUSED:
            self.phase = self.PLAYING

    # -- collision ---------------------------------------------------------
    def collides(self, matrix, px, py):
        for y, row in enumerate(matrix):
            for x, v in enumerate(row):
                if not v:
                    continue
                gx, gy = px + x, py + y
                if gx < 0 or gx >= COLS or gy >= ROWS:
                    return True
                if gy >= 0 and self.grid[gy][gx]:
                    return True
        return False

    def ghost_y(self):
        y = self.piece.y
        while not self.collides(self.piece.m, self.piece.x, y + 1):
            y += 1
        return y

    def touch_lock(self):
        if self.lock_timer is not None and self.lock_resets < LOCK_RESETS:
            self.lock_timer = 0
            self.lock_resets += 1

    # -- actions -----------------------------------------------------------
    def move(self, dx):
        if self.phase != self.PLAYING or not self.piece:
            return False
        if self.collides(self.piece.m, self.piece.x + dx, self.piece.y):
            return False
        self.piece.x += dx
        self.touch_lock()
        return True

    def rotate(self, clockwise=True):
        if self.phase != self.PLAYING or not self.piece:
            return
        if self.piece.kind == "O":
            return
        old = self.piece.r
        new = (old + (1 if clockwise else 3)) % 4
        matrix = rotate_matrix(self.piece.m, clockwise)
        table = KICKS_I if self.piece.kind == "I" else KICKS_JLSTZ
        for kx, ky in table.get((old, new), [(0, 0)]):
            nx, ny = self.piece.x + kx, self.piece.y - ky
            if not self.collides(matrix, nx, ny):
                self.piece.m, self.piece.x, self.piece.y, self.piece.r = \
                    matrix, nx, ny, new
                self.touch_lock()
                return

    def soft_drop(self):
        if self.phase != self.PLAYING or not self.piece:
            return
        if self.collides(self.piece.m, self.piece.x, self.piece.y + 1):
            self.lock_piece()
        else:
            self.piece.y += 1
            self.score += 1
            self.drop_timer = 0

    def hard_drop(self):
        if self.phase != self.PLAYING or not self.piece:
            return
        dist = 0
        while not self.collides(self.piece.m, self.piece.x, self.piece.y + 1):
            self.piece.y += 1
            dist += 1
        self.score += dist * 2
        self.jolt = 110
        self.lock_piece()

    def hold(self):
        if self.phase != self.PLAYING or not self.piece or not self.can_hold:
            return
        incoming, self.held = self.held, self.piece.kind
        if incoming:
            self.piece = Piece(incoming)
        else:
            self.piece = Piece(self.queue.pop(0))
            self.queue.append(self.bag.pull())
        self.can_hold = False
        self.drop_timer = 0
        self.lock_timer = None
        self.lock_resets = 0
        if self.collides(self.piece.m, self.piece.x, self.piece.y):
            self.game_over()

    # -- locking and clearing ---------------------------------------------
    def lock_piece(self):
        for gx, gy in self.piece.cells():
            if gy < 0:
                self.game_over()
                return
            self.grid[gy][gx] = self.piece.kind
        self.piece = None
        self.lock_timer = None
        self.lock_resets = 0

        full = [y for y in range(ROWS) if all(self.grid[y])]
        if full:
            self.clearing = full
            self.clear_timer = 0
        else:
            self.spawn()

    def finish_clear(self):
        n = len(self.clearing)
        for y in sorted(self.clearing):
            del self.grid[y]
            self.grid.insert(0, [None] * COLS)
        self.lines += n
        self.score += LINE_SCORE[n] * self.level
        self.level = min(len(GRAVITY), self.lines // 10 + 1)
        self.clearing = None
        self.spawn()

    # -- per-frame ---------------------------------------------------------
    def update(self, dt):
        if self.jolt > 0:
            self.jolt -= dt
        if self.phase != self.PLAYING:
            return

        if self.clearing:
            self.clear_timer += dt
            if self.clear_timer >= FLASH_MS:
                self.finish_clear()
        elif self.piece:
            grounded = self.collides(self.piece.m, self.piece.x, self.piece.y + 1)
            if grounded:
                self.lock_timer = (self.lock_timer or 0) + dt
                if self.lock_timer >= LOCK_MS:
                    self.lock_piece()
            else:
                self.lock_timer = None
                self.drop_timer += dt
                if self.drop_timer >= GRAVITY[self.level - 1]:
                    self.drop_timer = 0
                    self.piece.y += 1

        if self.das_dir:
            self.das_timer += dt
            if not self.das_ready and self.das_timer >= DAS_MS:
                self.das_ready = True
                self.das_timer = 0
                self.move(self.das_dir)
            elif self.das_ready and self.das_timer >= ARR_MS:
                self.das_timer = 0
                self.move(self.das_dir)

        if self.soft_held:
            self.soft_timer += dt
            if self.soft_timer >= SOFT_MS:
                self.soft_timer = 0
                self.soft_drop()

    # -- input -------------------------------------------------------------
    def on_keydown(self, key):
        if self.phase in (self.READY, self.OVER):
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r,
                       pygame.K_UP, pygame.K_x):
                self.start()
            return

        if key in (pygame.K_p, pygame.K_ESCAPE):
            self.toggle_pause()
            return
        if key == pygame.K_r:
            self.start()
            return
        if self.phase != self.PLAYING:
            return

        if key == pygame.K_LEFT:
            self.move(-1)
            self.das_dir, self.das_timer, self.das_ready = -1, 0, False
        elif key == pygame.K_RIGHT:
            self.move(1)
            self.das_dir, self.das_timer, self.das_ready = 1, 0, False
        elif key == pygame.K_DOWN:
            self.soft_held, self.soft_timer = True, 0
            self.soft_drop()
        elif key in (pygame.K_UP, pygame.K_x):
            self.rotate(True)
        elif key == pygame.K_z:
            self.rotate(False)
        elif key == pygame.K_SPACE:
            self.hard_drop()
        elif key in (pygame.K_c, pygame.K_LSHIFT, pygame.K_RSHIFT):
            self.hold()

    def on_keyup(self, key):
        if key == pygame.K_LEFT and self.das_dir == -1:
            self.das_dir = 0
        elif key == pygame.K_RIGHT and self.das_dir == 1:
            self.das_dir = 0
        elif key == pygame.K_DOWN:
            self.soft_held = False

    # -- drawing -----------------------------------------------------------
    def draw(self):
        self.win.fill(PAGE)
        self.draw_masthead()

        pygame.draw.rect(self.win, SHELL_HI, self.cabinet, border_radius=16)
        inner = self.cabinet.inflate(-2, -2)
        pygame.draw.rect(self.win, mix(SHELL_HI, SHELL_LO, 0.45), inner,
                         border_radius=15)

        self.draw_hold()
        self.draw_stats()
        self.draw_next()
        self.draw_well()
        self.draw_keys()
        pygame.display.flip()

    def draw_masthead(self):
        self.win.blit(self.f_title.render("TETRA", True, PAGE_INK), (PAD, PAD))
        sub = "Clear full rows. The stack rises when you do not."
        self.win.blit(self.f_sub.render(sub, True, PAGE_MUTE), (PAD, PAD + 32))

    def draw_module_label(self, rect, label):
        panel(self.win, rect)
        self.win.blit(self.f_label.render(label, True, CHROME),
                      (rect.x + MODULE_PAD, rect.y + 7))

    def draw_hold(self):
        self.draw_module_label(self.hold_box, "Hold")
        area = pygame.Rect(self.hold_box.x + MODULE_PAD,
                           self.hold_box.y + 26,
                           self.hold_box.width - MODULE_PAD * 2,
                           self.hold_box.height - 34)
        self.draw_mini(self.held, area, 255 if self.can_hold else 90)

    def draw_next(self):
        self.draw_module_label(self.next_box, "Next")
        slot_h = (self.next_box.height - 33) // 3
        for i, kind in enumerate(self.queue[:3]):
            area = pygame.Rect(self.next_box.x + MODULE_PAD,
                               self.next_box.y + 26 + i * slot_h,
                               self.next_box.width - MODULE_PAD * 2,
                               slot_h - 4)
            self.draw_mini(kind, area)

    def draw_mini(self, kind, area, alpha=255):
        if not kind:
            return
        matrix = SHAPES[kind]
        x0, y0, x1, y1 = shape_bounds(matrix)
        pw, ph = x1 - x0 + 1, y1 - y0 + 1
        size = max(6, min(area.width // 4, area.height // 2))
        ox = area.x + (area.width - pw * size) // 2
        oy = area.y + (area.height - ph * size) // 2
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if matrix[y][x]:
                    draw_block(self.win, ox + (x - x0) * size,
                               oy + (y - y0) * size, size, COLORS[kind], alpha)

    def draw_stats(self):
        panel(self.win, self.stats_box)
        rows = [("Score", f"{self.score:,}", self.f_big),
                ("Level", str(self.level), self.f_mid),
                ("Lines", str(self.lines), self.f_mid),
                ("Best", f"{self.best:,}", self.f_mid)]
        y = self.stats_box.y + 10
        x = self.stats_box.x + MODULE_PAD
        for label, value, font in rows:
            self.win.blit(self.f_label.render(label, True, CHROME), (x, y))
            self.win.blit(font.render(value, True, CHROME_HI), (x, y + 17))
            y += 17 + font.get_height() + 10

    def draw_well(self):
        offset = 3 if self.jolt > 0 else 0
        well = self.well.move(0, offset)
        panel(self.win, well)
        bx, by = self.board_origin[0], self.board_origin[1] + offset

        pygame.draw.rect(self.win, WELL_BG, (bx, by, BOARD_W, BOARD_H))
        for x in range(1, COLS):
            pygame.draw.line(self.win, GRID_LINE,
                             (bx + x * CELL, by), (bx + x * CELL, by + BOARD_H))
        for y in range(1, ROWS):
            pygame.draw.line(self.win, GRID_LINE,
                             (bx, by + y * CELL), (bx + BOARD_W, by + y * CELL))

        for y in range(ROWS):
            for x in range(COLS):
                kind = self.grid[y][x]
                if not kind:
                    continue
                if self.clearing and y in self.clearing:
                    pygame.draw.rect(self.win, FLASH,
                                     (bx + x * CELL, by + y * CELL,
                                      CELL - 1, CELL - 1))
                else:
                    draw_block(self.win, bx + x * CELL, by + y * CELL,
                               CELL, COLORS[kind])

        if self.piece and self.phase == self.PLAYING:
            gy = self.ghost_y()
            ghost = mix(COLORS[self.piece.kind], WELL_BG, 0.58)
            for y, row in enumerate(self.piece.m):
                for x, v in enumerate(row):
                    if not v or gy + y < 0:
                        continue
                    pygame.draw.rect(
                        self.win, ghost,
                        (bx + (self.piece.x + x) * CELL + 1,
                         by + (gy + y) * CELL + 1, CELL - 3, CELL - 3),
                        width=2)
            for gx, gy2 in self.piece.cells():
                if gy2 < 0:
                    continue
                draw_block(self.win, bx + gx * CELL, by + gy2 * CELL,
                           CELL, COLORS[self.piece.kind])

        if self.phase != self.PLAYING:
            self.draw_veil(well)

    def draw_veil(self, well):
        veil = pygame.Surface(well.size, pygame.SRCALPHA)
        veil.fill((13, 15, 19, 232))
        self.win.blit(veil, well.topleft)

        if self.phase == self.READY:
            title, sub, hint = "Ready", "Stack the blocks, clear the rows.", \
                "Press space to start"
        elif self.phase == self.PAUSED:
            title, sub, hint = "Paused", "", "Press P to resume"
        else:
            noun = "line" if self.lines == 1 else "lines"
            title = "Game over"
            sub = f"You cleared {self.lines} {noun}."
            hint = "Press R to play again"

        cy = well.centery - 26
        for text, font, color in ((title, self.f_veil, CHROME_HI),
                                  (sub, self.f_veil_sub, CHROME),
                                  (hint, self.f_veil_sub, CHROME_HI)):
            if not text:
                continue
            img = font.render(text, True, color)
            self.win.blit(img, img.get_rect(center=(well.centerx, cy)))
            cy += font.get_height() + 10

    def draw_keys(self):
        pairs = [("Move", "Left / Right"), ("Soft drop", "Down"),
                 ("Rotate", "Up or X"), ("Rotate back", "Z"),
                 ("Hard drop", "Space"), ("Hold", "C"),
                 ("Pause", "P"), ("Restart", "R")]
        top = self.cabinet.bottom + 14
        col_w = (CAB_W - 24) // 4
        for i, (name, keys) in enumerate(pairs):
            x = PAD + (i % 4) * col_w
            y = top + (i // 4) * 22
            self.win.blit(self.f_key.render(name, True, PAGE_MUTE), (x, y))
            img = self.f_key.render(keys, True, PAGE_INK)
            self.win.blit(img, (x + col_w - img.get_width() - 24, y))

    # -- loop --------------------------------------------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q and (
                            event.mod & pygame.KMOD_CTRL):
                        running = False
                    else:
                        self.on_keydown(event.key)
                elif event.type == pygame.KEYUP:
                    self.on_keyup(event.key)
                elif event.type == FOCUS_LOST:
                    if self.phase == self.PLAYING:
                        self.toggle_pause()
            self.update(dt)
            self.draw()
        pygame.quit()


def main():
    try:
        Tetra().run()
    except KeyboardInterrupt:
        pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
