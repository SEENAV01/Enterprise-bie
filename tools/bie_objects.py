"""BIE's own drawings of money things (Task 046 Part D2 item F, Navin's brief of 1 November 2026).

Writes flat, friendly SVG icons (viewBox 0 0 512 512, outlined shapes with a light shadow, no external references, text in
a generic sans-serif) into ``bie/toolbox/icons/bie/`` with ``objects.json``, the catalogue the icon index reads
(``python -m bie.toolbox.icons add-sets``). Ids are ``bie:<name>``: Indian coins and notes drawn in BIE's own style with
their denomination (never a replica of a real RBI design; ``docs/bie/BIE_MONEY_OBJECTS.md`` records the rules and how
each drawing keeps them), and the objects of a money lesson: cheque, passbook, QR stand, POS machine, phone, salt sack,
cowrie shells, cattle, grain sack, cloth roll, gold bar, ledger.

    python tools/bie_objects.py                 (writes the SVGs and objects.json)
    python tools/bie_objects.py --check         (exit 1 when the files in git differ from what this script draws)

The drawings are BIE's own work, published as CC0 1.0.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "bie" / "toolbox" / "icons" / "bie"
CATALOGUE = "objects.json"

INK = "#2d3640"                    # the outline colour of every drawing
FONT = "Noto Sans, Noto Sans Devanagari, Arial, sans-serif"
NOT_MONEY = "नमूना · not money"    # on every note: a sample, not money
HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">'
        "<!-- BIE's own drawing (Book Intelligence Engine), CC0 1.0. {note} -->")


def n(v: float) -> str:
    """A coordinate, short: 12, 12.5 (never 12.000)."""
    r = round(v, 1)
    return str(int(r)) if r == int(r) else str(r)


def svg(title: str, body: str, note: str = "") -> str:
    return HEAD.format(note=note or "Not a real object.") + f"<title>{title}</title>" + body + "</svg>\n"


def shadow(cx=256, cy=470, rx=150, ry=16) -> str:
    return f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}" fill="#1b2733" opacity=".14"/>'


def text(x, y, value, size, fill=INK, weight=800, anchor="middle", stroke="", sw=0, extra="") -> str:
    halo = f' stroke="{stroke}" stroke-width="{n(sw)}" stroke-linejoin="round" paint-order="stroke"' if stroke else ""
    return (f'<text x="{n(x)}" y="{n(y)}" font-family="{FONT}" font-size="{n(size)}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill}"{halo}{extra}>{value}</text>')


def poly(points, close=True) -> str:
    return "M" + " L".join(f"{n(x)} {n(y)}" for x, y in points) + (" Z" if close else "")


# ---------------------------------------------------------------- coins

COINS = {   # id: (label, sub-label, radius, face, rim, edge, centre colour for a two-metal coin)
    "coin-25p": ("25", "पैसे", 110, "#d08d5c", "#8e5a34", "dots", None),
    "coin-50p": ("50", "पैसे", 124, "#d9d2ea", "#8c80aa", "milled", None),
    "coin-1": ("₹1", "", 138, "#d5dbe1", "#8d98a5", "plain", None),
    "coin-2": ("₹2", "", 148, "#bfdcd6", "#6e9c93", "scallop", None),
    "coin-5": ("₹5", "", 156, "#f0c24b", "#b5862a", "milled", None),
    "coin-10": ("₹10", "", 166, "#d5dbe1", "#8d98a5", "plain", "#f0c24b"),
    "coin-20": ("₹20", "", 176, "#f0c24b", "#b5862a", "octagon", "#e8a27c"),
}


def outline(edge: str, cx: float, cy: float, r: float) -> str:
    """The coin's outer shape as a path: round, scalloped (BIE's ten-lobed edge) or an eight-sided coin."""
    if edge == "scallop":
        pts = [(cx + (r - 6 + 6 * math.cos(10 * t)) * math.cos(t), cy + (r - 6 + 6 * math.cos(10 * t)) * math.sin(t))
               for t in (2 * math.pi * k / 100 for k in range(100))]
        return poly(pts)
    if edge == "octagon":
        return poly([(cx + r * math.cos(math.pi / 8 + k * math.pi / 4), cy + r * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)])
    return f"M{n(cx - r)} {n(cy)} A{n(r)} {n(r)} 0 1 0 {n(cx + r)} {n(cy)} A{n(r)} {n(r)} 0 1 0 {n(cx - r)} {n(cy)} Z"


def coin(cid: str) -> str:
    label, sub, r, face, rim, edge, centre = COINS[cid]
    cx, cy = 256, 240
    parts = [shadow(cy=cy + r + 30, rx=r * 0.9),
             f'<path d="{outline(edge, cx, cy + 12, r)}" fill="{rim}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>',
             f'<path d="{outline(edge, cx, cy, r)}" fill="{face}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>']
    if edge == "milled":
        ticks = " ".join(f"M{n(cx + (r - 16) * math.cos(t))} {n(cy + (r - 16) * math.sin(t))} L{n(cx + (r - 5) * math.cos(t))} {n(cy + (r - 5) * math.sin(t))}"
                         for t in (2 * math.pi * k / 60 for k in range(60)))
        parts.append(f'<path d="{ticks}" stroke="{rim}" stroke-width="4" stroke-linecap="round"/>')
    ring = r - 30
    if centre:
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{n(r * 0.62)}" fill="{centre}" stroke="{rim}" stroke-width="6"/>')
        ring = r * 0.62 - 12
    dash = ' stroke-dasharray="1 15" stroke-linecap="round" stroke-width="9"' if edge == "dots" else ' stroke-width="5"'
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{n(ring)}" fill="none" stroke="{rim}"{dash} opacity=".8"/>')
    hl = r - 12
    parts.append(f'<path d="M{n(cx - hl * 0.87)} {n(cy - hl * 0.5)} A{n(hl)} {n(hl)} 0 0 1 {n(cx - hl * 0.2)} {n(cy - hl * 0.98)}" '
                 f'fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" opacity=".55"/>')
    dark = "#3e2a12" if face in ("#f0c24b", "#d08d5c") else "#2b3846"
    if sub:
        parts.append(text(cx, cy + 28, label, 90, fill=dark))
        parts.append(text(cx, cy + 72, sub, 38, fill=dark, weight=700))
    else:
        size = 116 if len(label) == 2 else 96 if not centre else 88
        parts.append(text(cx, cy + size * 0.36, label, size, fill=dark))
    parts.append(text(cx, cy - ring + 30 if not centre else cy + r - 18, "BIE", 18, fill=dark, weight=700, extra=' opacity=".75"'))
    name = f"{label} {sub}".strip()
    return svg(f"BIE drawing: {name} coin, not a real coin", "".join(parts), "Not a coin: BIE's own coin picture.")


# ---------------------------------------------------------------- notes

NOTES = {   # BIE's own colours, deliberately not the real notes' colours (docs/bie/BIE_MONEY_OBJECTS.md)
    "10": ("#2fb3a6", "#17695f"), "20": ("#f27c62", "#9a3a24"), "50": ("#4fa35e", "#24622f"), "100": ("#f59e3b", "#8f5300"),
    "200": ("#de5671", "#8a1f36"), "500": ("#8a5cc9", "#48267f"), "2000": ("#3f5698", "#1d2b5e"),
}


def note(denomination: str) -> str:
    face, dark = NOTES[denomination]
    x, y, w, h = 56, 131, 400, 250                      # 1.6 : 1 with round corners; real notes are about 1.95 to 2.5 : 1
    waves = " ".join(f"M{x + 20} {n(y + 162 + 12 * k)} q25 -10 50 0 t50 0 t50 0 t50 0 t50 0 t50 0 t50 0" for k in range(2))
    label = "₹" + denomination
    size = {3: 96, 4: 84, 5: 70}[len(label)]
    parts = [f'<rect x="{x + 8}" y="{y + 14}" width="{w}" height="{h}" rx="30" fill="#1b2733" opacity=".14"/>',
             f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="30" fill="{face}" stroke="{INK}" stroke-width="10"/>',
             f'<rect x="{x + 18}" y="{y + 18}" width="{w - 36}" height="{h - 36}" rx="18" fill="none" stroke="#fff" stroke-width="5" '
             f'stroke-dasharray="14 10" opacity=".6"/>',
             f'<path d="{waves}" fill="none" stroke="#fff" stroke-width="4" opacity=".35"/>',
             f'<circle cx="{x + 88}" cy="{y + 114}" r="52" fill="#fff" opacity=".9" stroke="{dark}" stroke-width="6"/>',
             text(x + 88, y + 127, "BIE", 36, fill=dark),
             text(x + 34, y + 46, denomination, 24, fill="#fff", anchor="start", stroke=dark, sw=5),
             text(x + 262, y + 136, label, size, fill="#fff", stroke=dark, sw=10),
             f'<rect x="{x + 122}" y="{y + 190}" width="236" height="34" rx="17" fill="#fff" opacity=".88"/>',
             text(x + 240, y + 214, NOT_MONEY, 22, fill=dark, weight=700)]
    return svg(f"BIE drawing: a {label} note, not money (नमूना)", "".join(parts), "Not a currency note: BIE's own note picture.")


# ---------------------------------------------------------------- objects

def cheque() -> str:
    boxes = "".join(f'<rect x="{326 + 16 * k}" y="176" width="13" height="20" rx="2" fill="#fff" stroke="#7aa6c4" stroke-width="2"/>'
                    for k in range(8))
    waves = " ".join(f"M50 {214 + 26 * k} q30 -10 60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0" for k in range(5))
    body = (shadow(cy=392, rx=210, ry=14)
            + f'<rect x="36" y="150" width="440" height="214" rx="14" fill="#eaf4fb" stroke="{INK}" stroke-width="8"/>'
            + f'<path d="{waves}" fill="none" stroke="#cfe3f1" stroke-width="3"/>'
            + text(58, 190, "CHEQUE · चेक", 24, fill="#2c5a7a", anchor="start") + boxes
            + text(58, 240, "Pay", 22, fill="#2c5a7a", weight=700, anchor="start")
            + '<path d="M104 242 H454 M58 284 H310" stroke="#7aa6c4" stroke-width="3"/>'
            + text(58, 278, "₹ in words", 16, fill="#7aa6c4", weight=600, anchor="start")
            + f'<rect x="326" y="252" width="128" height="40" rx="6" fill="#fff" stroke="{INK}" stroke-width="4"/>'
            + text(344, 282, "₹", 26, fill=INK, anchor="start")
            + f'<path d="M330 338 c14 -26 24 -26 22 -4 c-2 18 18 -22 30 -14 c10 8 6 18 22 8 c10 -6 18 -10 30 -4" fill="none" '
              f'stroke="#33415c" stroke-width="4" stroke-linecap="round"/>'
            + '<path d="M318 348 H462" stroke="#7aa6c4" stroke-width="3"/>'
            + text(58, 346, "BIE", 18, fill="#7aa6c4", anchor="start"))
    return svg("BIE drawing: a cheque (चेक), not a real cheque", body)


def passbook() -> str:
    rows = [("+500", "1,500", "#2e8b57"), ("−200", "1,300", "#c0392b"), ("+1,000", "2,300", "#2e8b57"), ("−300", "2,000", "#c0392b")]
    lines = "".join(text(282, 238 + 38 * k, a, 22, fill=c, weight=700, anchor="start") + text(438, 238 + 38 * k, b, 22, fill=INK, weight=700, anchor="end")
                    for k, (a, b, c) in enumerate(rows))
    body = (shadow(cy=430, rx=220, ry=16)
            + f'<rect x="34" y="124" width="444" height="286" rx="20" fill="#2f5d8a" stroke="{INK}" stroke-width="10"/>'
            + f'<path d="M56 144 H248 Q256 150 264 144 H456 V388 H264 Q256 394 248 388 H56 Z" fill="#fffdf6" stroke="{INK}" stroke-width="6" '
              f'stroke-linejoin="round"/>'
            + f'<path d="M256 148 V388" stroke="{INK}" stroke-width="4" opacity=".5"/>'
            + text(152, 214, "पासबुक", 34, fill="#2f5d8a") + text(152, 246, "PASSBOOK", 20, fill="#2f5d8a", weight=700)
            + '<path d="M84 286 H222 M84 318 H222 M84 350 H190" stroke="#c9d6e2" stroke-width="6" stroke-linecap="round"/>'
            + text(282, 190, "जमा / निकासी", 16, fill="#6b7c8f", weight=700, anchor="start")
            + text(438, 190, "बाकी", 16, fill="#6b7c8f", weight=700, anchor="end")
            + '<path d="M278 202 H440" stroke="#c9d6e2" stroke-width="3"/>' + lines
            + text(152, 380, "BIE", 16, fill="#9fb3c6"))
    return svg("BIE drawing: an open bank passbook (पासबुक) with balance lines", body)


def qr_modules(size: int = 19, seed: int = 46) -> list:
    """A decorative QR-like pattern: three finder squares and pseudo-random dots on a 19 × 19 grid (no QR version has 19
    modules, so nothing can be decoded from it)."""
    grid = [[False] * size for _ in range(size)]
    state = seed
    for r in range(size):
        for c in range(size):
            state = (state * 1103515245 + 12345) % 2 ** 31
            grid[r][c] = (state >> 16) % 5 < 2
    for fr, fc in ((0, 0), (0, size - 7), (size - 7, 0)):
        for r in range(-1, 8):
            for c in range(-1, 8):
                rr, cc = fr + r, fc + c
                if 0 <= rr < size and 0 <= cc < size:
                    ring = max(abs(r - 3), abs(c - 3))
                    grid[rr][cc] = ring in (0, 1, 3) and 0 <= r <= 6 and 0 <= c <= 6
    return [(r, c) for r in range(size) for c in range(size) if grid[r][c]]


def qr_stand() -> str:
    cell, x0, y0 = 9, 170, 156
    dots = "".join(f"M{x0 + c * cell} {y0 + r * cell}h{cell}v{cell}h-{cell}z" for r, c in qr_modules())
    body = (shadow(cy=458, rx=170, ry=16)
            + f'<path d="M120 452 L392 452 L364 400 L148 400 Z" fill="#9b7653" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
            + f'<rect x="136" y="66" width="240" height="340" rx="22" fill="#fff" stroke="{INK}" stroke-width="10"/>'
            + f'<path d="M141 88 Q141 71 158 71 H354 Q371 71 371 88 V128 H141 Z" fill="#3c8dde"/>'
            + text(256, 110, "SCAN · PAY", 26, fill="#fff")
            + f'<rect x="{x0 - 8}" y="{y0 - 8}" width="{19 * cell + 16}" height="{19 * cell + 16}" rx="8" fill="#fff" stroke="#c9d6e2" stroke-width="3"/>'
            + f'<path d="{dots}" fill="{INK}"/>'
            + text(256, 378, "स्कैन करें", 24, fill="#3c8dde", weight=700) + text(352, 394, "BIE", 12, fill="#9fb3c6", anchor="end"))
    return svg("BIE drawing: a QR code stand on a shop counter (decorative pattern, cannot be scanned)", body)


def pos_machine() -> str:
    keys = "".join(f'<rect x="{184 + 52 * c}" y="{252 + 40 * r}" width="40" height="28" rx="8" fill="{"#e9edf2" if (r, c) != (3, 2) else "#58c48a"}"/>'
                   for r in range(4) for c in range(3))
    body = (shadow(cy=488, rx=130, ry=14)
            + f'<rect x="196" y="38" width="120" height="80" rx="4" fill="#fff" stroke="{INK}" stroke-width="6"/>'
            + '<path d="M212 58 H300 M212 76 H284 M212 94 H296" stroke="#c9d6e2" stroke-width="5" stroke-linecap="round"/>'
            + f'<rect x="190" y="398" width="132" height="76" rx="8" fill="#f5b13d" stroke="{INK}" stroke-width="8"/>'
            + f'<rect x="210" y="440" width="30" height="22" rx="4" fill="#e3c16f" stroke="{INK}" stroke-width="3"/>'
            + f'<rect x="150" y="94" width="212" height="336" rx="36" fill="#3a4654" stroke="{INK}" stroke-width="10"/>'
            + '<rect x="172" y="122" width="168" height="104" rx="12" fill="#cff3e4"/>'
            + text(190, 186, "₹", 40, fill="#1f6b4a", anchor="start") + keys
            + '<rect x="196" y="408" width="120" height="8" rx="4" fill="#232b34"/>'
            + text(256, 244, "BIE", 12, fill="#8e9bab"))
    return svg("BIE drawing: a card machine (POS) with a card in it", body)


def phone() -> str:
    body = (shadow(cy=490, rx=130, ry=14)
            + f'<rect x="146" y="38" width="220" height="436" rx="40" fill="#2e3440" stroke="{INK}" stroke-width="10"/>'
            + '<rect x="364" y="132" width="10" height="56" rx="4" fill="#2e3440"/>'
            + '<rect x="162" y="82" width="188" height="346" rx="14" fill="#f5f8fb"/>'
            + '<rect x="226" y="58" width="60" height="9" rx="4.5" fill="#55606e"/><circle cx="304" cy="62.5" r="6" fill="#55606e"/>'
            + '<rect x="222" y="444" width="68" height="9" rx="4.5" fill="#55606e"/>')
    return svg("BIE drawing: a smartphone with a plain light screen", body)


def sack(heap: str, label: str, word: str, cloth: str, dark: str, bits: str) -> str:
    weave = " ".join(f"M{140 + 4 * k} {260 + 34 * k} Q256 {272 + 34 * k} {372 - 4 * k} {260 + 34 * k}" for k in range(5))
    return (shadow(cy=470, rx=160, ry=16)
            + f'<path d="M150 190 C118 262 102 360 118 420 Q128 456 170 458 H342 Q384 456 394 420 C410 360 394 262 362 190 Z" fill="{cloth}" '
              f'stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
            + f'<path d="{weave}" fill="none" stroke="{dark}" stroke-width="3" stroke-dasharray="10 8" opacity=".55"/>'
            + f'<ellipse cx="256" cy="188" rx="118" ry="34" fill="{dark}" stroke="{INK}" stroke-width="8"/>'
            + f'<path d="M156 192 Q196 112 256 106 Q316 112 356 192 Z" fill="{heap}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>' + bits
            + f'<path d="M138 188 Q256 238 374 188 L376 204 Q256 256 136 204 Z" fill="{cloth}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
            + f'<rect x="180" y="292" width="152" height="92" rx="14" fill="#fff" stroke="{INK}" stroke-width="6"/>'
            + text(256, 342, label, 46, fill=INK) + text(256, 370, word, 20, fill="#6b7c8f", weight=700)
            + text(256, 446, "BIE", 14, fill=dark))


def salt_sack() -> str:
    bits = "".join(f'<rect x="{x}" y="{y}" width="12" height="12" rx="2" fill="#d9ecf7" transform="rotate(20 {x + 6} {y + 6})"/>'
                   for x, y in ((206, 160), (246, 132), (288, 152), (230, 176), (318, 176)))
    return svg("BIE drawing: a jute sack of salt (नमक)", sack("#fff", "नमक", "SALT", "#d7b07a", "#b48e57", bits))


def grain_sack() -> str:
    bits = "".join(f'<ellipse cx="{x}" cy="{y}" rx="7" ry="4.5" fill="#c98a1c" transform="rotate({a} {x} {y})"/>'
                   for x, y, a in ((200, 168, 20), (226, 146, -30), (252, 128, 10), (280, 144, 40), (308, 162, -15), (240, 172, 60),
                                   (272, 170, -50), (330, 182, 25), (186, 184, -20)))
    ears = (f'<path d="M300 140 Q318 80 346 52" fill="none" stroke="#b5862a" stroke-width="6" stroke-linecap="round"/>'
            + "".join(f'<ellipse cx="{x}" cy="{y}" rx="9" ry="5" fill="#f0c24b" stroke="{INK}" stroke-width="2.5" transform="rotate(-50 {x} {y})"/>'
                      for x, y in ((322, 94), (334, 76), (344, 60), (312, 110))))
    return svg("BIE drawing: a sack of grain (अनाज)", sack("#f2c14e", "अनाज", "GRAIN", "#cdb27c", "#a98d55", bits + ears))


def cowrie_shells() -> str:
    def front(x, y, a, s=1.0):
        teeth = " ".join(f"M{n(t)} {n(-4 * s)} V{n(-11 * s)} M{n(t)} {n(4 * s)} V{n(11 * s)}" for t in range(int(-40 * s), int(44 * s), int(10 * s) or 1))
        return (f'<g transform="translate({x} {y}) rotate({a})">'
                f'<ellipse rx="{n(74 * s)}" ry="{n(50 * s)}" fill="#f6ebd9" stroke="{INK}" stroke-width="8"/>'
                f'<path d="M{n(-56 * s)} 0 Q0 {n(-12 * s)} {n(56 * s)} 0 Q0 {n(12 * s)} {n(-56 * s)} 0 Z" fill="#7a5230"/>'
                f'<path d="{teeth}" stroke="#c8a37a" stroke-width="3" stroke-linecap="round"/></g>')

    def back(x, y, a, s=1.0):
        spots = "".join(f'<circle cx="{n(cx * s)}" cy="{n(cy * s)}" r="{n(r * s)}" fill="#b8875a" opacity=".7"/>'
                        for cx, cy, r in ((-30, -10, 6), (-8, -24, 5), (14, -6, 7), (34, -20, 5), (-20, 14, 5), (24, 16, 6), (2, 6, 4)))
        return (f'<g transform="translate({x} {y}) rotate({a})">'
                f'<ellipse rx="{n(70 * s)}" ry="{n(48 * s)}" fill="#e9cfa3" stroke="{INK}" stroke-width="8"/>{spots}'
                f'<ellipse cx="{n(-14 * s)}" cy="{n(-22 * s)}" rx="{n(34 * s)}" ry="{n(12 * s)}" fill="#fff" opacity=".5"/></g>')

    body = (shadow(cy=410, rx=190, ry=18) + back(160, 300, -25, 0.95) + back(356, 304, 20, 0.95) + front(258, 236, -8, 1.1)
            + front(262, 360, 6, 0.9))
    return svg("BIE drawing: cowrie shells (कौड़ी), old money", body)


def cattle() -> str:
    leg = lambda x: (f'<rect x="{x}" y="296" width="32" height="136" rx="12" fill="#faf7f2" stroke="{INK}" stroke-width="8"/>'
                     f'<path d="M{x + 4} 414 H{x + 28} V426 Q{x + 28} 432 {x + 22} 432 H{x + 10} Q{x + 4} 432 {x + 4} 426 Z" fill="#4a3b33"/>')
    body = (shadow(cy=446, rx=180, ry=16)
            + leg(338) + leg(378) + leg(178) + leg(218)
            + f'<path d="M404 222 C434 250 436 300 424 344" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
            + f'<ellipse cx="424" cy="352" rx="11" ry="17" fill="#6b4a3a" stroke="{INK}" stroke-width="5"/>'
            + f'<ellipse cx="346" cy="334" rx="28" ry="17" fill="#f4a7b0" stroke="{INK}" stroke-width="6"/>'
            + '<clipPath id="bie-cow-body"><rect x="150" y="192" width="266" height="136" rx="64"/></clipPath>'
            + f'<rect x="150" y="192" width="266" height="136" rx="64" fill="#faf7f2" stroke="{INK}" stroke-width="10"/>'
            + '<g clip-path="url(#bie-cow-body)" fill="#8b5e3c"><path d="M270 186 C300 200 342 196 352 226 C362 262 318 270 296 252 C276 236 252 226 270 186 Z"/>'
              '<path d="M366 270 C392 262 420 276 420 330 H360 C352 306 350 280 366 270 Z"/><path d="M196 262 C214 252 236 264 232 288 C228 306 204 310 192 296 C182 284 184 270 196 262 Z"/></g>'
            + f'<rect x="150" y="192" width="266" height="136" rx="64" fill="none" stroke="{INK}" stroke-width="10"/>'
            + f'<path d="M98 146 Q84 118 100 100 M160 146 Q174 118 158 100" fill="none" stroke="#efe3c2" stroke-width="13" stroke-linecap="round"/>'
            + f'<path d="M98 146 Q84 118 100 100 M160 146 Q174 118 158 100" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round" opacity=".5"/>'
            + f'<ellipse cx="66" cy="174" rx="28" ry="14" fill="#faf7f2" stroke="{INK}" stroke-width="7" transform="rotate(-20 66 174)"/>'
            + f'<ellipse cx="192" cy="174" rx="28" ry="14" fill="#faf7f2" stroke="{INK}" stroke-width="7" transform="rotate(20 192 174)"/>'
            + f'<rect x="78" y="140" width="102" height="124" rx="48" fill="#faf7f2" stroke="{INK}" stroke-width="10"/>'
            + '<path d="M112 142 C132 160 150 150 160 168 C150 186 126 178 112 142 Z" fill="#8b5e3c"/>'
            + f'<rect x="70" y="222" width="118" height="62" rx="30" fill="#f4b8b0" stroke="{INK}" stroke-width="8"/>'
            + f'<ellipse cx="108" cy="252" rx="7" ry="10" fill="{INK}"/><ellipse cx="150" cy="252" rx="7" ry="10" fill="{INK}"/>'
            + f'<circle cx="106" cy="196" r="9" fill="{INK}"/><circle cx="152" cy="196" r="9" fill="{INK}"/>'
            + '<circle cx="109" cy="193" r="3" fill="#fff"/><circle cx="155" cy="193" r="3" fill="#fff"/>')
    return svg("BIE drawing: a cow (गाय), cattle as old money", body)


def cloth_roll() -> str:
    stripes = " ".join(f"M{x} 134 V266" for x in range(150, 400, 34))
    body = (shadow(cy=446, rx=190, ry=16)
            + f'<path d="M150 252 H410 L440 404 Q392 424 340 408 Q290 394 236 416 Q186 434 160 418 Z" fill="#e8657a" stroke="{INK}" '
              f'stroke-width="10" stroke-linejoin="round"/>'
            + f'<path d="M168 396 Q190 410 236 394 Q290 374 340 388 Q390 402 434 384" fill="none" stroke="#f2c14e" stroke-width="12"/>'
            + '<path d="M210 300 l10 10 l-10 10 l-10 -10 Z M290 310 l10 10 l-10 10 l-10 -10 Z M370 304 l10 10 l-10 10 l-10 -10 Z" fill="#f7c2cb"/>'
            + f'<rect x="110" y="130" width="300" height="140" rx="10" fill="#d9485f" stroke="{INK}" stroke-width="10"/>'
            + f'<path d="{stripes}" stroke="#f08a9b" stroke-width="5" opacity=".7"/>'
            + '<path d="M120 252 H404" stroke="#f2c14e" stroke-width="10"/>'
            + f'<ellipse cx="410" cy="200" rx="34" ry="70" fill="#b23349" stroke="{INK}" stroke-width="10"/>'
            + f'<ellipse cx="410" cy="200" rx="20" ry="44" fill="none" stroke="#e8657a" stroke-width="5"/>'
            + f'<ellipse cx="410" cy="200" rx="8" ry="18" fill="#fff4e0" stroke="{INK}" stroke-width="5"/>'
            + f'<ellipse cx="110" cy="200" rx="34" ry="70" fill="#c43b53" stroke="{INK}" stroke-width="10"/>'
            + '<ellipse cx="110" cy="200" rx="20" ry="44" fill="none" stroke="#e8657a" stroke-width="5"/>')
    return svg("BIE drawing: a roll of cloth (कपड़े का थान)", body)


def gold_bar() -> str:
    body = (shadow(cy=372, rx=200, ry=18)
            + f'<path d="M132 240 H380 L424 342 H88 Z" fill="#f2b632" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
            + f'<path d="M168 162 H344 L380 240 H132 Z" fill="#ffe08a" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
            + '<path d="M150 262 H196 L176 324 H124 Z" fill="#fff" opacity=".4"/><path d="M188 178 H216 L196 226 H168 Z" fill="#fff" opacity=".55"/>'
            + f'<rect x="218" y="184" width="76" height="38" rx="8" fill="none" stroke="#c9901e" stroke-width="5"/>'
            + text(256, 214, "Au", 24, fill="#9a6a10")
            + '<path d="M392 104 l9 25 l25 9 l-25 9 l-9 25 l-9 -25 l-25 -9 l25 -9 Z" fill="#ffe08a" stroke="#c9901e" stroke-width="4" stroke-linejoin="round"/>')
    return svg("BIE drawing: a gold bar (सोने की ईंट)", body)


def ledger() -> str:
    pages = " ".join(f"M362 {96 + 26 * k} H372" for k in range(13))
    body = (shadow(cy=470, rx=150, ry=14)
            + f'<rect x="352" y="80" width="30" height="356" rx="6" fill="#fff6e0" stroke="{INK}" stroke-width="8"/>'
            + f'<path d="{pages}" stroke="#d9c8a2" stroke-width="3"/>'
            + f'<rect x="140" y="64" width="226" height="388" rx="16" fill="#c8323b" stroke="{INK}" stroke-width="10"/>'
            + '<rect x="160" y="84" width="186" height="348" rx="10" fill="none" stroke="#f2c14e" stroke-width="4" opacity=".8"/>'
            + f'<rect x="178" y="138" width="150" height="72" rx="10" fill="#fff6e0" stroke="{INK}" stroke-width="6"/>'
            + text(253, 188, "खाता", 40, fill="#8e1f27")
            + '<path d="M136 300 H386" stroke="#f2c14e" stroke-width="12"/>'
            + f'<path d="M256 300 q-22 30 -10 64 M256 300 q22 30 10 64" fill="none" stroke="#f2c14e" stroke-width="8" stroke-linecap="round"/>'
            + f'<circle cx="256" cy="300" r="13" fill="#f2c14e" stroke="{INK}" stroke-width="5"/>'
            + text(253, 410, "BIE", 14, fill="#f2c14e"))
    return svg("BIE drawing: an old account book (बही-खाता), a ledger", body)


# ---------------------------------------------------------------- the catalogue the icon index reads

def _coin_entry(cid: str) -> dict:
    label, sub, *_ = COINS[cid]
    if sub:
        hi = {"25": "पच्चीस", "50": "पचास"}[label]
        return {"name": f"{label} paise coin · {label} पैसे का सिक्का",
                "terms": ["coin", "paise", f"{label} paise", f"{label} p", "money", "सिक्का", "पैसे", f"{label} पैसे", f"{hi} पैसे",
                          {"25": "चवन्नी", "50": "अठन्नी"}[label]]}
    d = label[1:]
    hi = {"1": "एक", "2": "दो", "5": "पाँच", "10": "दस", "20": "बीस"}[d]
    return {"name": f"₹{d} coin · {d} रुपये का सिक्का",
            "terms": ["coin", "rupee", f"₹{d}", f"{d} rupee coin", "money", "सिक्का", "रुपये", f"{hi} रुपये का सिक्का"]}


def _note_entry(d: str) -> dict:
    hi = {"10": "दस", "20": "बीस", "50": "पचास", "100": "सौ", "200": "दो सौ", "500": "पाँच सौ", "2000": "दो हज़ार"}[d]
    return {"name": f"₹{d} note · {d} रुपये का नोट",
            "terms": ["note", "banknote", "currency note", "rupee", f"₹{d}", f"{d} rupee note", "money", "नोट", "रुपये", f"{hi} का नोट"]}


OBJECTS = {   # id: (draw, name, terms)
    "cheque": (cheque, "cheque · चेक", ["cheque", "check", "cheque book", "bank", "payment", "चेक", "चेकबुक", "बैंक"]),
    "passbook": (passbook, "bank passbook · पासबुक", ["passbook", "bank book", "balance", "deposit", "account", "पासबुक", "खाता", "जमा", "बैंक"]),
    "qr-stand": (qr_stand, "QR code stand · क्यूआर कोड स्टैंड", ["qr", "qr code", "scan", "upi", "digital payment", "shop counter", "क्यूआर", "स्कैन",
                                                               "डिजिटल भुगतान"]),
    "pos-machine": (pos_machine, "card machine (POS) · कार्ड मशीन", ["pos", "pos machine", "card machine", "swipe machine", "card payment",
                                                                    "debit card", "कार्ड मशीन", "स्वाइप मशीन"]),
    "phone": (phone, "smartphone with a plain screen · मोबाइल फ़ोन", ["phone", "mobile", "smartphone", "payment screen", "upi payment",
                                                                      "मोबाइल", "फ़ोन", "फोन"]),
    "salt-sack": (salt_sack, "sack of salt · नमक की बोरी", ["salt", "sack", "commodity money", "goods", "नमक", "बोरी"]),
    "cowrie-shells": (cowrie_shells, "cowrie shells · कौड़ियाँ", ["cowrie", "cowries", "shell", "shells", "commodity money", "old money",
                                                                "कौड़ी", "कौड़ियाँ"]),
    "cattle": (cattle, "cow · गाय", ["cow", "cattle", "livestock", "commodity money", "गाय", "मवेशी", "पशु"]),
    "grain-sack": (grain_sack, "sack of grain · अनाज की बोरी", ["grain", "sack", "wheat", "rice", "commodity money", "अनाज", "बोरी", "गेहूँ"]),
    "cloth-roll": (cloth_roll, "roll of cloth · कपड़े का थान", ["cloth", "fabric", "cloth roll", "bolt of cloth", "textile", "कपड़ा", "थान"]),
    "gold-bar": (gold_bar, "gold bar · सोने की ईंट", ["gold", "gold bar", "ingot", "bullion", "gold standard", "सोना", "सोने की ईंट"]),
    "ledger": (ledger, "account book (ledger) · बही-खाता", ["ledger", "account book", "accounts", "bahi khata", "बही", "खाता", "हिसाब"]),
}


def drawings() -> dict:
    """{bie id (without the prefix): (svg text, catalogue entry)} for every drawing, in the catalogue's order."""
    out = {}
    for cid in COINS:
        out[cid] = (coin(cid), _coin_entry(cid))
    for d in NOTES:
        out[f"note-{d}"] = (note(d), _note_entry(d))
    for oid, (draw, name, terms) in OBJECTS.items():
        out[oid] = (draw(), {"name": name, "terms": terms})
    return out


def catalogue(made: dict) -> dict:
    return {"schema": "bie.icons.bie-objects/1", "licence": "CC0 1.0",
            "about": "BIE's own drawings of money things (tools/bie_objects.py); the rules they keep: docs/bie/BIE_MONEY_OBJECTS.md",
            "objects": [{"id": "bie:" + k, "file": k + ".svg", "name": e["name"], "terms": e["terms"]} for k, (_, e) in made.items()]}


def write(out: Path = OUT) -> list:
    made = drawings()
    out.mkdir(parents=True, exist_ok=True)
    for k, (text_, _) in made.items():
        (out / f"{k}.svg").write_text(text_, encoding="utf-8")
    (out / CATALOGUE).write_text(json.dumps(catalogue(made), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return sorted(made)


def check(out: Path = OUT) -> list:
    """The drawings whose committed file differs from what this script draws (empty when the folder is up to date)."""
    made = drawings()
    bad = [f"{k}.svg" for k, (t, _) in made.items() if not (out / f"{k}.svg").is_file() or (out / f"{k}.svg").read_text(encoding="utf-8") != t]
    cat = json.dumps(catalogue(made), ensure_ascii=False, indent=1) + "\n"
    if not (out / CATALOGUE).is_file() or (out / CATALOGUE).read_text(encoding="utf-8") != cat:
        bad.append(CATALOGUE)
    extra = sorted(p.name for p in out.glob("*.svg") if p.stem not in made) if out.is_dir() else []
    return bad + [f"{e} (not drawn by this script)" for e in extra]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    if a.check:
        bad = check(a.out)
        print(json.dumps({"out_of_date": bad}, ensure_ascii=False))
        return 1 if bad else 0
    ids = write(a.out)
    print(f"{len(ids)} drawings -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
