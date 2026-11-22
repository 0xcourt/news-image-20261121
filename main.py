#!/usr/bin/env python3
"""news-image-20261121: one broadsheet PNG summing up Saturday 21 Nov 2026.

Pure Python 3 stdlib (struct, zlib, os, hashlib). Deterministic: no clock,
no randomness, no network. Draws with a hand-built 5x7 bitmap font and a
hand-built PNG encoder, then writes $MAKEFUN_OUTPUT_DIR/entry.png (1024x1024).

Layout (1024x1024 broadsheet, warm paper):
  masthead (navy band, title + date + mini world map with story dots)
  8 lead cards in a 2x4 grid (number, region kicker, headline, 2-line deck)
  "THE REST OF THE WORLD" — 42 compact one-liners in 3 regional columns
  UTC timeline strip + sources footer
Stories: 50 verified for 21 Nov 2026, see ../VERIFIED-STORIES.md.
"""

import hashlib
import os
import struct
import zlib

W, H = 1024, 1024

# ---- palette ------------------------------------------------------------
PAPER = (247, 243, 234)      # warm newsprint
CARD = (255, 253, 247)       # card paper
INK = (22, 22, 22)
GREY = (88, 84, 76)
NAVY = (15, 42, 74)
NAVY_LT = (214, 224, 236)
RED = (179, 32, 44)
GOLD = (232, 196, 106)
GREEN = (34, 110, 60)
BORDER = (198, 188, 172)
MAP_LAND = (120, 140, 160)
MAP_SEA = (16, 46, 80)

# ---- 5x7 bitmap font (own design, capitals + digits + punctuation) -----
# Each glyph: 7 rows of 5 bits, written as strings, '1' = ink.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ";": ["00000", "01100", "01100", "00000", "01100", "00100", "01000"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    '"': ["01010", "01010", "01010", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    "\u2014": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    "@": ["01110", "10001", "10111", "10101", "10110", "10000", "01110"],
    "*": ["00000", "00100", "10101", "01110", "10101", "00100", "00000"],
    "#": ["01010", "01010", "11111", "01010", "11111", "01010", "01010"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "[": ["01110", "01000", "01000", "01000", "01000", "01000", "01110"],
    "]": ["01110", "00010", "00010", "00010", "00010", "00010", "01110"],
    "<": ["00010", "00100", "01000", "10000", "01000", "00100", "00010"],
    ">": ["01000", "00100", "00010", "00001", "00010", "00100", "01000"],
    "\u00b7": ["00000", "00000", "00000", "01100", "01100", "00000", "00000"],
    "x": ["00000", "10001", "01010", "00100", "01010", "10001", "00000"],
}


def _advance(scale):
    return 5 * scale + max(1, scale // 2)


def text_w(s, scale):
    if not s:
        return 0
    return len(s) * _advance(scale) - max(1, scale // 2)


def wrap(s, scale, max_w):
    """Greedy word wrap; returns list of lines, each fitting max_w."""
    words = s.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---- canvas ----------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, color):
        self.fill_rect(x, y, w, 1, color)
        self.fill_rect(x, y + h - 1, w, 1, color)
        self.fill_rect(x, y, 1, h, color)
        self.fill_rect(x + w - 1, y, 1, h, color)

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    self.set(cx + dx, cy + dy, color)

    def text(self, x, y, s, scale, color):
        """Draw all-caps text; lowercase is upper-cased, unknown -> '?'."""
        cx = x
        adv = _advance(scale)
        for ch in s:
            g = FONT.get(ch.upper(), FONT["?"])
            for row_i, row in enumerate(g):
                for col_i, bit in enumerate(row):
                    if bit == "1":
                        self.fill_rect(cx + col_i * scale, y + row_i * scale,
                                       scale, scale, color)
            cx += adv
        return cx

    def text_center(self, cx, y, s, scale, color):
        self.text(cx - text_w(s, scale) // 2, y, s, scale, color)


# ---- PNG encoder (own code: zlib + chunk framing) ---------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: None
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))


# ---- world map (own coarse equirectangular sketch, 64 x 32 cells) ---------
# Columns run lon -180..+180, rows run lat ~+84..-60. Rows are padded to 64.
MAP_ROWS = [
    "        ####          ####        #         ###############    ",
    "      ########       #######     #####  ####################    ",
    "    ##########      #########   ####### ##################     ",
    "   ############     ########    #####   ################       ",
    "    ##########       ######    ####     #############  ###     ",
    "     ########        #####    #####     ##########    ####     ",
    "      ######         ####     ####      ########      ###      ",
    "       ####          ###      ###       #######       ##       ",
    "       ###           ##       ##        ######       #        ",
    "        ##           #        #         #####                ",
    "        ##                    #         ####        ##       ",
    "        ##                   ##        #####       ###       ",
    "         #                  ###       #######      ###        ",
    "         ##                ####      ########     ###         ",
    "          #               #####      ########     ##          ",
    "          ##             ######      #######      #           ",
    "           ##           #######       #####      ##           ",
    "            #          ########        ####      #            ",
    "            ##        #########         ###     ##            ",
    "             #       ##########          ##     ###           ",
    "             ##     ###########          #      ####          ",
    "              #    ############                ######         ",
    "              ##  #############                ######         ",
    "               #  ############                  ####          ",
    "                  ##########                     ##           ",
    "                   ########                      #            ",
    "                    ######                                   ",
    "                     ####                                    ",
    "                      ##                                     ",
    "                                                             ",
    "                                                             ",
    "                                                             ",
]
MAP_ROWS = [(r + " " * 64)[:64] for r in MAP_ROWS]

# (lon, lat, is_lead, number) — plotted on the masthead map
DOTS = [
    (50.5, 26.2, True, 1),    # Bahrain
    (30.7, 36.9, True, 2),    # Antalya
    (-75.9, -11.0, True, 3),  # Junin, Peru
    (-108.0, 25.6, True, 4),  # Sinaloa
    (33.4, 47.9, True, 5),    # Kryvyi Rih
    (114.1, 22.5, True, 6),   # Shenzhen
    (-74.0, 40.7, True, 7),   # New York
    (24.0, 59.8, True, 8),    # Gulf of Finland
    (56.5, 26.5, False, 0),   # Hormuz
    (46.7, 24.6, False, 0),   # Riyadh
    (34.5, 31.5, False, 0),   # Gaza
    (4.4, 50.8, False, 0),    # Brussels
    (12.6, 55.7, False, 0),   # Copenhagen
    (2.4, 48.9, False, 0),    # Paris
    (-77.0, 38.9, False, 0),  # Washington
    (-47.9, -15.8, False, 0), # Brasilia
    (-72.3, 18.5, False, 0),  # Port-au-Prince
    (121.5, 31.2, False, 0),  # Shanghai
    (77.2, 28.6, False, 0),   # New Delhi
    (127.0, 37.5, False, 0),  # Seoul
    (135.5, 34.7, False, 0),  # Osaka
    (6.0, 4.8, False, 0),     # Bayelsa, Nigeria
    (32.6, 0.3, False, 0),    # Kampala
    (39.3, -6.8, False, 0),   # Dar es Salaam
    (38.0, 6.0, False, 0),    # S Ethiopia
    (18.4, -33.9, False, 0),  # Cape Town
    (-46.6, -23.5, False, 0), # Sao Paulo
    (-80.2, 25.8, False, 0),  # Miami (GTA VI)
    (-121.9, 37.4, False, 0), # Santa Clara (Nvidia)
    (7.7, 45.1, False, 0),    # Turin
    (-3.2, 51.5, False, 0),   # Cardiff
    (103.8, 1.35, False, 0),  # Singapore strait side (Timor proxy east)
]

# ---- stories ---------------------------------------------------------------
# Leads: (kicker, headline, deck). Decks wrap to 2 lines at scale 2.
LEADS = [
    ("MIDDLE EAST",
     "IRAN STRIKES BAHRAIN",
     "IRGC MISSILES AND DRONES HIT TWO US BASES; A CIVILIAN PLANT BURNS. NO INJURIES."),
    ("CLIMATE \u00b7 TURKEY",
     "COP31 IN OVERTIME",
     "ANTALYA TALKS INTO A 2ND EXTRA DAY, DEADLOCKED ON FOSSIL FUELS AND FINANCE."),
    ("SOUTH AMERICA",
     "PERU QUAKE M6.7",
     "JUNIN, 00:09 UTC, 129 KM DEEP. LIMA SHAKEN; 1 DEAD, 16 HURT, 93,000 CUT OFF."),
    ("MEXICO",
     "MEXICO NABS 'CHAPO ISIDRO'",
     "FBI MOST-WANTED CARTEL BOSS SEIZED IN SINALOA; 11 KILLED IN THE BACKLASH."),
    ("UKRAINE",
     "KRYVYI RIH HIT",
     "RUSSIAN MISSILE KILLS 2, INCLUDING A BOY, 7; ABOUT 60 HURT IN ZELENSKY'S HOMETOWN."),
    ("CHINA",
     "TRUMP, XI AND PUTIN MEET",
     "SHENZHEN SUMMIT AGREES NUCLEAR RISK TALKS. ZELENSKY CALLS PUTIN A KILLER."),
    ("MARKETS",
     "MARKETS IN AI ROUT",
     "S&P 500 -3.7% IN FRIDAY'S SELL-OFF; NASDAQ ERASES ITS 2026 GAINS. NIKKEI -5.1%."),
    ("BALTIC SEA",
     "SPARTA II ABLAZE",
     "DRONES HIT A RUSSIAN CARGO SHIP IN THE GULF OF FINLAND; IT DRIFTS TO FINLAND."),
]

# Compact: (column 0..2, one line, max 29 chars at scale 2)
COMPACT = [
    (0, "HORMUZ: 2 MORE TANKERS HIT"),
    (0, "HOUTHIS FIRE ON RIYADH"),
    (0, "GAZA FOOD-TRUCK HIT: 3 DEAD"),
    (0, "BASRA POWER FIRE: 4 DEAD"),
    (0, "SAUDI OIL STORED IN JAPAN X3"),
    (0, "UK-EU SIGN 3 BREXIT DEALS"),
    (0, "EU-INDONESIA TRADE DEAL DONE"),
    (0, "DENMARK EXPELS RUSSIAN ENVOY"),
    (0, "ESTONIA SHUTS RUSSIA BORDER"),
    (0, "FRANCE: 6TH SATURDAY PROTEST"),
    (0, "PARIS POLICE GUILTY: BEATING"),
    (0, "TURKEY SEIZES SOZCU TV"),
    (0, "IRAQ-KATAIB BASE DEAL AGREED"),
    (0, "JAPAN SIDELINED AT SHENZHEN"),
    (1, "FBI CRIME DATABASE HACKED"),
    (1, "TRUMP DATA CENTRE TAX THREAT"),
    (1, "BOLSONARO IN INTENSIVE CARE"),
    (1, "HAITI: TROOPS FIGHT GANGS"),
    (1, "VIRGINIA CHILD MEASLES DEATH"),
    (1, "PALISADES FIRE ARSON VERDICT"),
    (1, "MAMDANI: CLOSE RIKERS 2032"),
    (1, "NIGERIA BOAT SINKS: 24 DEAD"),
    (1, "UGANDA EBOLA CURBS"),
    (1, "TANZANIA'S LISSU CONVICTED"),
    (1, "ETHIOPIA: 700,000 DISPLACED"),
    (1, "MLAMBO-NGCUKA DIES, 71"),
    (1, "WOLBACHIA CUTS DENGUE 69%"),
    (1, "KENYA STARTS OIL DRILLING"),
    (2, "CHINA AI STOCKS SHED $1.7TN"),
    (2, "NEPAL PM'S FIRST INDIA VISIT"),
    (2, "SEOUL MOVES TO IMPEACH JUDGE"),
    (2, "BTS WIN FIVE MAMA AWARDS"),
    (2, "M6.8 QUAKE OFF TIMOR-LESTE"),
    (2, "BEPICOLOMBO REACHES MERCURY"),
    (2, "GTA VI: $3.8BN IN ONE DAY"),
    (2, "NVIDIA CHIEF HUANG OUSTED"),
    (2, "ALCARAZ V ZVEREV: ATP FINAL"),
    (2, "ENGLAND 37-12 ALL BLACKS"),
    (2, "WALLABIES EDGE WALES 29-26"),
    (2, "HARDEN 51 PASSES KOBE BRYANT"),
    (2, "VERSTAPPEN ON POLE IN VEGAS"),
    (2, "CERN FINDS ULTRA-RARE DECAY"),
]

COL_HEADERS = ["MIDDLE EAST & EUROPE", "AMERICAS & AFRICA",
               "ASIA, OCEANIA & BEYOND"]
COL_COLORS = [RED, NAVY, GREEN]


def draw_map(cv, x0, y0, cw, ch):
    """Mini world map: land cells + story dots. cw/ch = box size."""
    cell_w, cell_h = cw // 64, ch // 32
    for r, row in enumerate(MAP_ROWS):
        for c, bit in enumerate(row):
            if bit == "#":
                cv.fill_rect(x0 + c * cell_w, y0 + r * cell_h,
                             cell_w, cell_h, MAP_LAND)
    for lon, lat, lead, num in DOTS:
        px = x0 + int((lon + 180.0) / 360.0 * cw)
        py = y0 + int((84.0 - lat) / 144.0 * ch)
        if lead:
            cv.disc(px, py, 5, RED)
            cv.disc(px, py, 2, (255, 255, 255))
        else:
            cv.disc(px, py, 2, GOLD)


def draw_lead_card(cv, x, y, w, h, num, kicker, headline, deck):
    accent = RED if num == 1 else NAVY
    cv.fill_rect(x, y, w, h, CARD)
    cv.rect(x, y, w, h, BORDER)
    cv.fill_rect(x, y, 6, h, accent)
    # number box
    cv.fill_rect(x + 16, y + 10, 40, 32, accent)
    cv.text_center(x + 36, y + 15, str(num), 3, (255, 255, 255))
    # kicker
    cv.text(x + 64, y + 18, kicker, 2, RED)
    # headline (up to 2 lines, scale 3)
    hl = wrap(headline, 3, w - 32)[:2]
    hy = y + 50
    for line in hl:
        cv.text(x + 16, hy, line, 3, INK)
        hy += 21
    # deck (up to 2 lines, scale 2)
    dl = wrap(deck, 2, w - 32)[:2]
    dy = hy + 6
    for line in dl:
        cv.text(x + 16, dy, line, 2, GREY)
        dy += 15


def draw():
    cv = Canvas(W, H, PAPER)

    # ---- masthead ---------------------------------------------------------
    cv.fill_rect(0, 0, W, 92, NAVY)
    cv.fill_rect(0, 92, W, 4, RED)
    cv.text(16, 12, "THE WORLD IN ONE DAY", 5, (255, 255, 255))
    cv.text(16, 56, "SATURDAY, 21 NOVEMBER 2026", 3, GOLD)
    draw_map(cv, 724, 8, 256, 64)
    cv.text(724, 76, "50 STORIES \u00b7 9 REGIONS", 2, GOLD)

    # ---- 8 lead cards, 2 cols x 4 rows ------------------------------------
    cw, ch, gap = 502, 130, 8
    for i, (kicker, headline, deck) in enumerate(LEADS):
        cx = 10 + (i % 2) * (cw + gap)
        cy = 104 + (i // 2) * (ch + gap)
        draw_lead_card(cv, cx, cy, cw, ch, i + 1, kicker, headline, deck)

    # ---- compact section ---------------------------------------------------
    cv.text(10, 652, "THE REST OF THE WORLD", 3, NAVY)
    cv.text(10 + text_w("THE REST OF THE WORLD", 3) + 12, 652,
            "\u2014 42 MORE STORIES", 3, RED)
    cv.fill_rect(10, 678, W - 20, 2, RED)
    col_w = 328
    for col in range(3):
        cx = 10 + col * (col_w + 8)
        cv.text(cx, 688, COL_HEADERS[col], 2, COL_COLORS[col])
        cv.fill_rect(cx, 706, col_w, 1, BORDER)
        items = [t for (c, t) in COMPACT if c == col]
        for j, item in enumerate(items):
            iy = 714 + j * 17
            cv.fill_rect(cx, iy + 3, 8, 8, COL_COLORS[col])
            cv.text(cx + 14, iy, item, 2, INK)

    # ---- footer ------------------------------------------------------------
    cv.fill_rect(10, 954, W - 20, 2, NAVY)
    cv.text_center(W // 2, 962,
                   "00:09 PERU QUAKE \u00b7 COP31 OVERTIME \u00b7 KRYVYI RIH "
                   "\u00b7 SHENZHEN SUMMIT \u00b7 IRAN STRIKES BAHRAIN",
                   2, NAVY)
    cv.text_center(W // 2, 980,
                   "EVERY STORY ABOVE HAPPENED OR WAS FIRST REPORTED ON "
                   "SATURDAY 21 NOVEMBER 2026.", 2, INK)
    cv.text_center(W // 2, 998,
                   "SOURCES: AFP \u00b7 AP \u00b7 REUTERS \u00b7 BBC \u00b7 AL "
                   "JAZEERA \u00b7 EURONEWS \u00b7 USGS \u00b7 YONHAP",
                   2, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    digest = hashlib.sha256(data).hexdigest()
    print("wrote %s (%d bytes) sha256=%s" % (path, len(data), digest))


if __name__ == "__main__":
    main()
