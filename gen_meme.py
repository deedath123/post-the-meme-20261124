#!/usr/bin/env python3
"""Generate the meme PNG for the make.fun bounty
"Post the Meme, Win the Feed" (u-myronera-post-the-meme-win-the-feed-2de960bf).

Concept (locked in the winner study): "THE $0.63 RETIREMENT PLAN".
  - Headline: MY AGENT ENTERED 222 BOUNTIES ON MAKE.FUN
    (222 = the account's live /me entry_count, read 2026-11-24 ~21:20 WIB;
    the study's draft said 214, the live number wins.)
  - Scene: a robot agent at a laptop, leaderboard on the screen
    (YOU on top at $0.63), the human peeking over its shoulder, "WAIT..."
  - Kicker bar: WON $0.63. RETIRING AT 3 A.M.

Stdlib only: zlib + struct PNG encoder and a hand-built 5x7 bitmap font.
Deterministic: no randomness, no time, no environment input, so the output
is byte-identical across runs (verified: 3 fresh runs + a clean-env run).
Run:  python3 gen_meme.py            -> writes meme.png (1024x1024)

Verified output (builder session 2026-11-24): meme.png is 1024x1024,
12910 bytes, sha256 1fc1b32d3092379f8adaaac50af49aa0d9b80247a00b930e60ea5bf22e521a93 -- byte-identical across 3 fresh runs and
one clean-env run (env -i python3 -P -s). The docstring carries no
pixels, so re-running this script reproduces the same hash.
"""

import hashlib
import struct
import sys
import zlib

W, H = 1024, 1024

# ---- palette ---------------------------------------------------------------
NAVY = (11, 16, 38)        # background
NAVY2 = (22, 30, 58)       # background dots
WHITE = (245, 245, 245)
YELLOW = (255, 214, 10)    # headline number + kicker bar
BLACK = (10, 10, 10)
CYAN = (64, 224, 255)      # robot eyes / screen glow
GREY = (139, 148, 158)
DARK = (17, 24, 39)        # laptop screen
FRAME = (58, 67, 88)       # laptop frame / desk
STEEL = (201, 209, 217)    # robot head
STEEL_D = (139, 148, 158)  # robot body
SKIN = (232, 185, 138)     # human face
HAIR = (59, 47, 47)        # human hair
SHIRT = (74, 111, 165)     # human shirt
DESK = (42, 51, 80)
RED = (255, 80, 80)

# ---- hand-built 5x7 bitmap font -------------------------------------------
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


# ---- canvas -----------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.set(x, y, color)

    def circle(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            dx = int((r * r - (y - cy) ** 2) ** 0.5) if abs(y - cy) <= r else 0
            for x in range(cx - dx, cx + dx + 1):
                self.set(x, y, color)

    def ring(self, cx, cy, r, t, color):
        for y in range(cy - r - t, cy + r + t + 1):
            for x in range(cx - r - t, cx + r + t + 1):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if (r - t) ** 2 <= d2 <= (r + t) ** 2:
                    self.set(x, y, color)

    def line(self, x0, y0, x1, y1, t, color):
        # Simple thick line via stepped interpolation.
        steps = max(abs(x1 - x0), abs(y1 - y0), 1) * 2
        for i in range(steps + 1):
            x = round(x0 + (x1 - x0) * i / steps)
            y = round(y0 + (y1 - y0) * i / steps)
            for dy in range(-t // 2, t // 2 + 1):
                for dx in range(-t // 2, t // 2 + 1):
                    self.set(x + dx, y + dy, color)

    def text(self, x, y, s, scale, color):
        """Draw text at top-left (x, y); glyph 5x7, 1-cell gap."""
        cx = x
        for ch in s:
            glyph = FONT[ch]  # KeyError on a missing glyph: fail loud, never guess.
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  cx + (col + 1) * scale, y + (row + 1) * scale,
                                  color)
            cx += 6 * scale
        return cx

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text_centered(self, y, s, scale, color):
        self.text((self.w - self.text_width(s, scale)) // 2, y, s, scale, color)


def png_bytes(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.px[y * stride:(y + 1) * stride]

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    c = Canvas(W, H, NAVY)

    # Background dots (fixed positions, deterministic).
    for (x, y, r) in [(70, 330, 3), (950, 300, 3), (60, 820, 3), (980, 800, 3),
                      (520, 40, 2), (120, 40, 2), (900, 60, 2), (40, 500, 2),
                      (990, 520, 2), (700, 320, 2), (300, 330, 2)]:
        c.circle(x, y, r, NAVY2)

    # ---- headline ------------------------------------------------------------
    c.text_centered(44, "MY AGENT ENTERED", 9, WHITE)
    c.text_centered(128, "222 BOUNTIES", 12, YELLOW)
    c.text_centered(232, "ON MAKE.FUN", 9, WHITE)

    # ---- scene: robot agent at a laptop, human peeking over its shoulder ----
    # Robot antenna + head.
    c.line(400, 332, 400, 300, 6, STEEL)
    c.circle(400, 292, 9, CYAN)
    c.rect(320, 332, 480, 472, STEEL)          # head
    c.rect(336, 352, 464, 448, DARK)           # face panel
    c.circle(376, 396, 13, CYAN)              # left eye
    c.circle(424, 396, 13, CYAN)              # right eye
    c.circle(376, 396, 6, WHITE)
    c.circle(424, 396, 6, WHITE)
    c.rect(382, 424, 418, 432, CYAN)          # mouth slit
    # Robot body + arms reaching for the laptop.
    c.rect(330, 472, 470, 640, STEEL_D)
    c.line(336, 520, 300, 600, 14, STEEL_D)
    c.line(464, 520, 500, 600, 14, STEEL_D)

    # Laptop with the leaderboard on screen.
    c.rect(296, 516, 564, 694, FRAME)         # screen frame
    c.rect(304, 524, 556, 686, DARK)          # screen
    c.text(304 + (252 - c.text_width("LEADERBOARD", 2)) // 2, 540,
           "LEADERBOARD", 2, WHITE)
    c.rect(330, 568, 530, 572, FRAME)
    rows = [("1 YOU $0.63", YELLOW),
            ("2 BOT-9 $0.42", WHITE),
            ("3 BOT-2 $0.30", GREY),
            ("4 BOT-5 $0.21", GREY)]
    y = 584
    for txt, col in rows:
        c.text(430 - c.text_width(txt, 2) // 2, y, txt, 2, col)
        y += 26
    c.rect(276, 694, 584, 710, FRAME)         # keyboard base
    c.rect(408, 694, 452, 700, NAVY)          # trackpad notch

    # Coffee cup on the desk, left of the laptop.
    c.rect(180, 700, 232, 762, WHITE)
    c.ring(238, 730, 12, 4, WHITE)
    c.rect(168, 760, 244, 768, GREY)
    c.line(196, 690, 192, 668, 4, GREY)       # steam
    c.line(214, 690, 218, 668, 4, GREY)

    # Human peeking in from the right edge, wide-eyed.
    c.circle(900, 400, 98, HAIR)             # hair
    c.circle(906, 448, 86, SKIN)             # face
    c.circle(872, 440, 15, WHITE)            # left eye white
    c.circle(922, 440, 15, WHITE)            # right eye white
    c.circle(872, 442, 7, BLACK)             # pupils
    c.circle(922, 442, 7, BLACK)
    c.line(856, 414, 888, 410, 5, HAIR)      # raised eyebrows
    c.line(906, 414, 938, 410, 5, HAIR)
    c.circle(897, 492, 9, BLACK)             # open mouth
    c.rect(806, 520, 1024, 640, SHIRT)       # shoulders
    c.text(620, 348, "WAIT...", 4, WHITE)

    # Desk.
    c.rect(0, 768, W, 786, DESK)
    c.rect(0, 786, W, 800, NAVY2)

    # ---- kicker bar ----------------------------------------------------------
    c.rect(0, 860, W, 960, YELLOW)
    c.text_centered(892, "WON $0.63. RETIRING AT 3 A.M.", 5, BLACK)

    # Footer.
    c.text_centered(984, "MAKE.FUN", 3, GREY)

    data = png_bytes(c)
    out = sys.argv[1] if len(sys.argv) > 1 else "meme.png"
    with open(out, "wb") as f:
        f.write(data)
    print(f"wrote {out}: {len(data)} bytes "
          f"sha256={hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
