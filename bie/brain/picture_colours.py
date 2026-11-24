"""Does a drawn picture paint each named part in the colour the film gave it? (r4 of 11.6.3b, 24 November 2026: the
film's look said "CF₀ amber" and the shot's prompt "amber CF₀", and the image model drew CF₀ blue in one picture while
every other picture drew it amber; Navin chose that film's Hybrid look for the films the same day.)

The colour a part should have comes from the film's own words: the shot's image prompt ("amber CF₀", "violet six-lobed
CF₁", "proton pump rust red") first, then the film's look line for the parts the shot's prompt names. Where it is, comes
from the layout checker, which has already put each label on its structure in the drawn picture. Here code looks at the
pixels around that point and in a wider ring around it. A part is reported only when the stated colour is nearly absent
in both, another colour family clearly holds the spot, and that family is not the picture's own background, so a
glowing cofactor inside a protein, a label resting on water, a shadow or a busy background is not taken for a wrong
colour. Tints (pale aqua, ivory-teal) and colourless words (ivory, white, grey) are not checked: hue says nothing there.

Measured on 26 saved runs (55 films, 206 pictures, 347 coloured labels): 4 parts reported, r4's blue CF₀ among them.
Code only (numpy and Pillow); no model call. ``colour_problems`` gives the problems of one picture; the films section
(``tools/vm_studio.py`` ``recolour``) draws that picture once more with the colours written out (``recolour_note``),
places it afresh and keeps the redraw only when fewer parts are wrong."""
from __future__ import annotations

import re
import unicodedata

import numpy as np
from PIL import Image

# hue bands in degrees (0-360) for the colour words film prompts use; several bands where a word spans the 0 line
HUES = {
    "red": [(345, 360), (0, 14)], "crimson": [(340, 360), (0, 10)], "scarlet": [(350, 360), (0, 16)],
    "ruby": [(340, 360), (0, 10)], "burgundy": [(330, 360), (0, 10)], "wine": [(330, 358)],
    "maroon": [(340, 360), (0, 14)], "vermilion": [(0, 16)], "coral": [(0, 22)], "salmon": [(4, 26)],
    "rust": [(0, 28)], "brick": [(0, 24)], "copper": [(8, 34)], "bronze": [(20, 42)], "brown": [(8, 40)],
    "chocolate": [(8, 32)], "tan": [(22, 44)], "peach": [(14, 36)], "orange": [(14, 40)], "saffron": [(28, 46)],
    "amber": [(24, 48)], "ochre": [(30, 52)], "gold": [(36, 58)], "golden": [(36, 58)], "khaki": [(40, 62)],
    "mustard": [(42, 60)], "yellow": [(46, 66)], "lemon": [(50, 64)],
    "olive": [(55, 85)], "chartreuse": [(72, 96)], "lime": [(70, 100)], "moss": [(65, 105)], "sage": [(80, 130)],
    "green": [(75, 160)], "forest": [(95, 145)], "emerald": [(130, 165)], "jade": [(140, 172)],
    "mint": [(130, 170)], "teal": [(160, 200)], "turquoise": [(165, 190)], "cyan": [(180, 200)],
    "aqua": [(170, 200)], "cerulean": [(190, 215)], "sky": [(190, 215)], "blue": [(200, 250)],
    "azure": [(200, 225)], "cobalt": [(210, 235)], "sapphire": [(215, 240)], "navy": [(215, 245)],
    "indigo": [(235, 265)], "violet": [(255, 300)], "purple": [(260, 305)], "lavender": [(250, 290)],
    "lilac": [(260, 300)], "plum": [(280, 320)], "mauve": [(280, 330)], "magenta": [(295, 330)],
    "pink": [(310, 350)], "rose": [(330, 360), (0, 5)],
}
# the colour families a wrong colour is named by in the problem
FAMILIES = {"red": [(345, 360), (0, 14)], "orange": [(14, 40)], "yellow": [(40, 66)], "green": [(66, 160)],
            "teal": [(160, 200)], "blue": [(200, 250)], "violet": [(250, 300)], "pink": [(300, 345)]}
COLOURLESS = {"ivory", "white", "cream", "grey", "gray", "black", "silver", "beige", "pearl", "clear", "transparent",
              "colourless", "colorless", "charcoal", "slate", "bone"}
# a tint is not a hue: "pale aqua", "faint amber", "ivory-teal" may be drawn nearly white, so they are not judged
PALE = {"pale", "faint", "light", "pastel", "soft", "translucent", "transparent", "muted", "dusty", "washed",
        "ghost", "ghostly", "dim", "smoky", "milky", "frosted"} | COLOURLESS
SHADE = {"deep", "dark", "bright", "rich", "vivid", "strong", "warm", "cool", "saturated", "glowing", "metallic"}
# words that end the run from a colour to its name: "gold proton spheres in lumen" does not make the lumen gold
STOP = {"in", "at", "of", "inside", "with", "on", "beside", "near", "into", "to", "from", "around", "over", "under",
        "below", "above", "between", "through", "across", "along", "within", "and", "aur", "or", "is", "are", "ka",
        "ki", "ke", "mein", "par", "encloses", "enclosing", "surrounds", "spans", "connects", "binds", "reveals",
        "contains", "retains", "holds", "carries", "facing", "leading", "bound", "embedded", "beyond", "outside",
        "behind", "toward", "towards", "against", "via", "while", "where", "which", "that", "then", "than", "like"}
NOUNS_ING = {"string", "spring", "ceiling", "building", "lining", "opening", "coating", "casing", "housing", "filling",
             "ending", "heading", "wiring", "tubing", "binding", "pudding", "railing"}
SLACK = 12           # degrees allowed outside a word's band (image models shade and light)
RADIUS = 2.4         # percent of the picture's width around the label point
MIN_SAT, MIN_VAL = 0.28, 0.22
NEAR_ABSENT = 0.15   # at most this share of the coloured pixels in the stated colour ...
CLEAR_OTHER = 0.55   # ... while one other family holds at least this share
MIN_COLOURED = 0.25  # and enough of the spot is coloured at all to judge
WIDE = 6.0           # percent of the width: the ring that holds the whole part around its label point
WIDE_ABSENT = 0.08   # the stated colour may hold at most this share of the ring's coloured pixels

_SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁺⁻", "0123456789+-")
_WORD = re.compile(r"[\w₀-₉⁺⁻+-]+")
_SEGMENT = re.compile(r"[,;:.](?=\s|$)|[()|\n]")


def norm(name: str) -> str:
    text = unicodedata.normalize("NFKC", str(name or "")).translate(_SUB).lower()
    return " ".join(re.findall(r"[a-z0-9+-]+", text))


def _parts(word: str) -> list:
    return [p for p in re.split(r"[-/]", word.lower()) if p]


def _hues(word: str) -> list:
    return [p for p in _parts(word) if p in HUES]


def _pale(word: str) -> bool:
    return any(p in PALE for p in _parts(word))


def _shade(word: str) -> bool:
    return bool(_parts(word)) and all(p in SHADE or p in PALE for p in _parts(word))


def _blocked(word: str) -> bool:
    w = word.lower()
    verb = w.endswith("ing") and "-" not in w and len(w) > 5 and w not in NOUNS_ING
    return w in STOP or bool(_hues(w)) or w.replace(",", "").isdigit() or verb


def bands(colour: str) -> list:
    """The hue bands of a stated colour; a two-hue colour ("blue-green", "yellow-green") spans the arc between them."""
    words = [w for w in colour.split("-") if w in HUES]
    if len(words) == 1:
        return HUES[words[0]]
    if not words:
        return []

    def centre(w):
        lo, hi = HUES[w][0] if len(HUES[w]) == 1 else (HUES[w][0][0] - 360, HUES[w][-1][1])
        return ((lo + hi) / 2) % 360
    a, b = sorted(centre(w) for w in words[:2])
    if b - a <= 180:
        arc = [(a, b)]
    else:
        arc = [(b, 360), (0, a)]
    return arc + [band for w in words for band in HUES[w]]


def stated_colours(prompt: str, look: str, names: list) -> dict:
    """{normalised part name: colour} for the names this picture labels, from the shot's prompt first, then the look.

    Both ways films write it count: a colour, at most two describing words, then the name ("amber CF₀", "violet
    six-lobed CF₁"), or a name that ends its phrase with its colour ("proton pump rust red", "thylakoid membrane deep
    teal"). A place word, a verb, a number or another colour between them ends the run, and a tint ("pale aqua",
    "ivory-teal", "faint amber") is left out: such a part can be drawn nearly white."""
    wanted = {norm(n): n for n in names if norm(n)}

    def match(tokens: list) -> str | None:
        if not tokens or any(_blocked(t) for t in tokens):
            return None
        p = norm(" ".join(tokens))
        if not p:
            return None
        for key in sorted(wanted, key=len, reverse=True):
            if p == key or p.endswith(" " + key) or (key.endswith(" " + p) and len(p) > 3):
                return key
        return None

    def read(text: str) -> dict:
        out: dict = {}
        for segment in _SEGMENT.split(text or ""):
            words = _WORD.findall(segment or "")
            i = 0
            while i < len(words):
                if not _hues(words[i]):
                    i += 1
                    continue
                j, hues, pale = i, [], i > 0 and _pale(words[i - 1])
                while j < len(words) and j - i < 3 and (_hues(words[j]) or (j > i and _shade(words[j]))):
                    hues += [h for h in _hues(words[j]) if h not in hues]
                    pale = pale or _pale(words[j])
                    j += 1
                colour = "-".join(hues[:2])
                key = None
                for start in range(j, min(j + 3, len(words))):
                    if any(_blocked(t) for t in words[j:start]):
                        break
                    for span in (3, 2, 1):
                        key = match(words[start:start + span])
                        if key:
                            break
                    if key:
                        break
                ends = j >= len(words) or _blocked(words[j])
                if not key and ends:
                    back = i
                    while back > 0 and _shade(words[back - 1]):
                        back -= 1
                    for span in (3, 2, 1):
                        if back - span >= 0:
                            key = match(words[back - span:back])
                            if key:
                                break
                if key and key not in out:
                    out[key] = None if pale else colour
                i = j
        return out

    # the look names the film's colours, but one picture may not draw a part at all (a molecule the film adds later
    # as a moving overlay): a look colour is checked only for a part this shot's own prompt names
    said = f" {norm(prompt)} "
    found = {k: v for k, v in read(look).items() if not prompt or f" {k} " in said}
    found.update(read(prompt))           # the shot's own prompt wins over the film's look
    return {k: v for k, v in found.items() if v}


def _in(h: np.ndarray, bands_, slack: float = 0) -> np.ndarray:
    hit = np.zeros(h.shape, bool)
    for lo, hi in bands_:
        hit |= (h >= lo - slack) & (h <= hi + slack)
        if lo - slack < 0:
            hit |= h >= 360 + lo - slack
        if hi + slack > 360:
            hit |= h <= hi + slack - 360
    return hit


def _overlap(a, b) -> bool:
    """Do two sets of hue bands share any degrees?"""
    deg = np.arange(0, 360, 1.0) + 0.5
    return bool((_in(deg, a) & _in(deg, b)).any())


def spot(image: Image.Image, x: float, y: float, radius: float = RADIUS) -> dict:
    """The colours around a point (x, y in percent of the picture): coloured share, and each family's share of it."""
    rgb = image.convert("RGB")
    w, h = rgb.size
    r = max(3, int(radius / 100 * w))
    cx, cy = int(x / 100 * w), int(y / 100 * h)
    box = (max(0, cx - r), max(0, cy - r), min(w, cx + r + 1), min(h, cy + r + 1))
    if box[2] <= box[0] or box[3] <= box[1]:
        return {"coloured": 0.0, "hues": np.zeros(0), "families": {}}
    a = np.asarray(rgb.crop(box), np.float32) / 255.0
    yy, xx = np.mgrid[box[1]:box[3], box[0]:box[2]]
    disc = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    px = a[disc]
    mx, mn = px.max(1), px.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    keep = (sat >= MIN_SAT) & (mx >= MIN_VAL)
    c = px[keep]
    if not len(c):
        return {"coloured": 0.0, "hues": np.zeros(0), "families": {}}
    rr, gg, bb = c[:, 0], c[:, 1], c[:, 2]
    cmax, cmin = c.max(1), c.min(1)
    d = np.maximum(cmax - cmin, 1e-6)
    hue = np.where(cmax == rr, ((gg - bb) / d) % 6, np.where(cmax == gg, (bb - rr) / d + 2, (rr - gg) / d + 4)) * 60
    fam = {name: float(_in(hue, fb).mean()) for name, fb in FAMILIES.items()}
    return {"coloured": float(keep.mean()), "hues": hue, "families": fam}


def background(image: Image.Image) -> str | None:
    """The colour family that fills most of the picture (water, stroma, sky): a label point on it says nothing."""
    small = image.convert("RGB").copy()
    small.thumbnail((240, 240))
    w, h = small.size
    s = spot(small, 50, 50, radius=150 * max(w, h) / w)
    fam = s["families"]
    return max(fam, key=fam.get) if fam and s["coloured"] >= MIN_COLOURED else None


def judge(image: Image.Image, x: float, y: float, colour: str, ground: str | None = None) -> dict | None:
    """None when the part is the stated colour or cannot be judged; else {"seen": family, "share": its share}.

    Three things must all hold before a part is called wrongly coloured: around the label point the stated colour is
    nearly absent and one other family clearly holds the spot; in the wider ring around it (the whole protein, not one
    glowing cofactor inside it) the stated colour is nearly absent too; and the colour seen is not simply the
    picture's background (a label point that rests on water or stroma)."""
    stated_bands = bands(colour)
    if not stated_bands:
        return None
    s = spot(image, x, y)
    if s["coloured"] < MIN_COLOURED or not len(s["hues"]):
        return None
    stated = float(_in(s["hues"], stated_bands, SLACK).mean())
    if stated > NEAR_ABSENT:
        return None
    own = {f for f, fb in FAMILIES.items() if _overlap(fb, stated_bands)}   # jade is a green, amber an orange
    others = {f: v for f, v in s["families"].items() if f not in own}
    seen, share = max(others.items(), key=lambda kv: kv[1]) if others else (None, 0.0)
    if share < CLEAR_OTHER or seen == ground:
        return None
    wide = spot(image, x, y, radius=WIDE)
    wide_stated = float(_in(wide["hues"], stated_bands, SLACK).mean()) if len(wide["hues"]) else 0.0
    if wide_stated > WIDE_ABSENT:
        return None
    return {"seen": seen, "share": round(share, 2), "stated_share": round(stated, 2),
            "wide_share": round(wide_stated, 2)}


def _labels(shot: dict) -> list:
    """Every label point drawn on this shot's picture: [(label, x, y)], first place each label stands."""
    out, seen = [], set()
    for sentence in shot.get("sentences") or []:
        for pin in sentence.get("pins") or []:
            label = str(pin.get("label") or "")
            if label and norm(label) not in seen and "=" not in label:
                seen.add(norm(label))
                out.append((label, float(pin.get("x", 50)), float(pin.get("y", 50))))
    return out


def colour_problems(shot: dict, image_path, look: str = "") -> list:
    """The parts this picture paints in another colour than the film gave them, as problems for the report."""
    visual = shot.get("visual") or {}
    if (visual.get("library") or "").strip() or visual.get("type") not in ("cutaway",):
        return []                       # a kept picture was chosen as it is; an everyday photo has no colour key
    labels = _labels(shot)
    colours = stated_colours(visual.get("image_prompt") or "", look, [l for l, _, _ in labels])
    if not colours:
        return []
    image = Image.open(image_path)
    ground = background(image)
    out = []
    for label, x, y in labels:
        colour = colours.get(norm(label))
        if not colour:
            continue
        wrong = judge(image, x, y, colour, ground)
        if wrong:
            out.append({"label": label, "stated": colour, "seen": wrong["seen"], "share": wrong["share"],
                        "text": f"{shot.get('id')}: the picture paints '{label}' {wrong['seen']}, but the film gives it "
                                f"{colour}; the picture is drawn again with its colours written out"})
    return out


def recolour_note(problems: list) -> str:
    """The sentence added to the picture's prompt for its one redraw."""
    said = "; ".join(f"{p['label']} is {p['stated']}, never {p['seen']}" for p in problems)
    return f" Colour key, kept exactly: {said}."
