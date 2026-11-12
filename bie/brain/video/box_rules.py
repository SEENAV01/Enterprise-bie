"""The box rule (dabba-niyam), Navin 5 November 2026: "v4 abhi ACCEPT nahi. Takraav v2 se ~13 guna."

Every drawn thing knows its box and the boxes of the words inside it (``boxes.py``, measured from the engine's own
drawings), every background knows its reserved zones, and the scene-plan compiler refuses a plan where, for a second or
more while both are on screen:

1. a text sits on a thing (a saancha, an asset, a person, a bubble) — words go beside a thing, or inside it through the
   thing's own label;
2. a thing sits on a face, or on the words inside another thing;
3. anything sits on a reserved zone of the background ("all": a board, a cupboard, a shelf of goods; "text": no words on
   a hut, a stall, a counter — a person may stand in front of it);
4. anything is cut by the frame edge after the camera, or sits under the kicker;
5. a word inside a thing is under the 36 px floor on screen (its saancha label, after the thing's scale and the camera);
6. a caution or fact-check line reaches the screen (D1-06; never on screen, a background check);
7. in a Hindi video, a screen label is English (it is written in Devanagari; an English term may follow in brackets);
8. a text, or any value a text changes to, is on screen for less than 1.5 s (it flashes and cannot be read).

Each problem names the scene, the two things, the second and the way out, for the director to patch. Marks, arrows and
glows point at things on purpose and never count as things here (they still keep to the frame and the zones).

3D models (engine/three, models3d.py): a scene's 3D world is a backdrop like the world saancha, whose parts (machines,
a belt, a ship, a board) are reserved zones that move with its camera; a 3D model item is a thing whose box is its
drawn parts after its camera, at every sampled second. Words and things placed at a model's spot (``at``, marked
``on``) label that part on purpose, so they may sit on that model and its zones.
"""
from __future__ import annotations

import math
import re
import unicodedata

from bie.brain.video import boxes

STAGE_W, STAGE_H = 1920.0, 1080.0
STEP = 0.5                  # the check samples every half second, like the compiler's other checks
HOLD = 1.0                  # held this long it is a collision (a pop-in, a pass-by or a hand-over is not)
SHARE = 0.2                 # of the smaller of the two boxes: that much overlap is "on"
WORD_SHARE = 0.25           # of a word's box (the text audit's own overlap share)
ZONE_SHARE = 0.15
EDGE = 8.0                  # px a box may graze the frame edge
ZOOMED = 1.05               # above this camera zoom a cropped thing is the camera's framing (words never are)
FLOOR_PX = 36.0
MIN_TEXT_S = 1.5            # a text on screen for less cannot be read (Money v5, 5 Nov: two texts 0.7 s before a cut)
KICKER = (46.0, 41.0, 36.0)  # left, top and size of the kicker pill in screen space (engine.mjs)
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
LATIN_WORD = re.compile(r"[A-Za-z]+")
UNITS = {"kg", "g", "km", "cm", "mm", "m", "ml", "l", "x", "rs", "am", "pm", "vs"}
NOT_THINGS = {"glow", "arrow", "map", "mark", "rect"}
BACKDROPS = {"world"}


# ---------------------------------------------------------------- words


def is_symbol(text: str) -> bool:
    """No letter and no digit: a sign drawn as a picture (the text audit's own test)."""
    return not any(unicodedata.category(ch)[0] in "LN" for ch in str(text))


def is_hindi(language) -> bool:
    lang = str(language or "").lower()
    return lang in ("hi", "hin") or "hindi" in lang or "hinglish" in lang


def english_label(text: str) -> bool:
    """An English label (no Devanagari, and a Latin word that is not a short code like RBI, UPI, USD or a unit)."""
    text = str(text)
    if DEVANAGARI.search(text):
        return False
    for word in LATIN_WORD.findall(text):
        if (word.isupper() and len(word) <= 4) or word.lower() in UNITS or maths_token(word):
            continue
        return True
    return False


def label_strings(el, t=None) -> list:
    """The whole labels an element was given (its text, every string of its params at ``t``, split at ; and at the
    name:points colon), so a word wrapped onto its own line is judged with the label it came from."""
    out = []
    if el.get("text") is not None:
        out.append(str(el["text"]))
    stack = [item_p(el, t if t is not None else float("inf"))]
    for m in el.get("group") or []:
        if isinstance(m, dict):
            stack.append(item_p(m, t if t is not None else float("inf")))
            if m.get("text") is not None:
                out.append(str(m["text"]))
    while stack:
        v = stack.pop()
        if isinstance(v, dict):
            stack += list(v.values())
        elif isinstance(v, (list, tuple)):
            stack += list(v)
        elif isinstance(v, str):
            for piece in v.split(";"):
                out.append(piece)
                if ":" in piece:
                    out.append(piece[:piece.rfind(":")])
                    out.append(piece[piece.rfind(":") + 1:])
    return [x.strip() for x in out if x and x.strip()]


def wrapped_hindi(text: str, labels) -> bool:
    """``text`` is one wrapped line of a whole label that is not English (Sloman workers, Nov 2026: "45 डिग्री (degree)"
    drew "(degree)" on its own line, and that line alone was refused as English)."""
    t = str(text).strip()
    return bool(t) and any(t != lab and t in lab and DEVANAGARI.search(lab) and not english_label(lab) for lab in labels)


def moving_at(el, t) -> bool:
    """The element is moving at ``t`` (a key that changes x or y is running): an item or a person walking or sliding in
    from off-screen is not "cut by the frame" while it moves; only where it settles must be inside."""
    for k in el.get("keys") or []:
        if k.get("t") is None or (k.get("x") is None and k.get("y") is None):
            continue
        if float(k["t"]) <= t < float(k["t"]) + float(k.get("d") or 0.6):
            return True
    return False


def bracket_term(text: str, siblings) -> bool:
    """``text`` is (part of) an English term in brackets after a Hindi word of the same label, wrapped onto its own line
    (Sloman workers, Nov 2026: a graph line "माँग (demand)" draws "माँग" over "(demand)", "आपूर्ति (supply" over "curve)")."""
    t = str(text).strip()
    if not t:
        return False
    joined = " ".join(str(x) for x in siblings)
    for m in re.finditer(r"\([^()]*\)", joined):
        if t.strip("()") and t in m.group(0) and DEVANAGARI.search(joined[max(0, m.start() - 40):m.start()]):
            return True
    return False


# two-letter English words: never read as maths symbols
ENGLISH_2 = {"is", "of", "to", "in", "on", "at", "an", "be", "by", "or", "if", "it", "no", "so", "up", "we", "he", "me", "my",
             "do", "go", "as", "us", "am", "ok", "hi", "oh"}


def maths_token(word: str) -> bool:
    """A Latin token used as maths, not English (Sloman scene plans: a, b, Qd, Ps, Pe, d/dQ in formula, table and graph
    labels): one letter, or two letters that are not an English word (Qd, Pe, dQ, MC)."""
    w = str(word)
    return w.isalpha() and (len(w) == 1 or (len(w) == 2 and w.lower() not in ENGLISH_2))


def letter_width(ch: str) -> float:
    """A letter's advance as a share of the font size (bold Noto Sans / Devanagari) — boxes.mjs letterWidth, same table."""
    c = ord(ch)
    if 0x0900 <= c <= 0x097F:
        if (0x0900 <= c <= 0x0903) or (0x093A <= c <= 0x094F) or (0x0951 <= c <= 0x0957) or c in (0x0962, 0x0963):
            return 0.28 if c in (0x093E, 0x0940, 0x0949, 0x094A, 0x094B, 0x094C) else 0.04
        return 0.66
    if ch == " ":
        return 0.27
    if ch.isdigit():
        return 0.6
    if "A" <= ch <= "Z":
        return 0.7
    if "a" <= ch <= "z":
        return 0.32 if ch in "iljft" else 0.92 if ch in "mw" else 0.58
    if ch in "₹$€£¥":
        return 0.6
    return 0.42


def text_width(text, px) -> float:
    return sum(letter_width(ch) for ch in str(text)) * float(px)


# ---------------------------------------------------------------- geometry


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def prop_at(el, t):
    """x, y, s, r of an element at ``t`` through its keys (engine.mjs propAt)."""
    st = {"x": float(el.get("x") or 0), "y": float(el.get("y") or 0), "s": float(el.get("s") if el.get("s") is not None else 1),
          "r": float(el.get("r") or 0)}
    for k in el.get("keys") or []:
        if k.get("t") is None or t <= k["t"]:
            break
        p = ease((t - k["t"]) / (k.get("d") or 0.6))
        for f in st:
            if k.get(f) is not None:
                st[f] += (float(k[f]) - st[f]) * p
    return st


def cam_at(scene, t):
    st = {"x": 960.0, "y": 540.0, "z": 1.0}
    for k in sorted(scene.get("cam") or [], key=lambda k: k.get("t") or 0):
        if t <= (k.get("t") or 0):
            break
        p = ease((t - k["t"]) / (k.get("d") or 1.0))
        for f in st:
            if k.get(f) is not None:
                st[f] += (float(k[f]) - st[f]) * p
    return st


def to_screen(box, cam):
    z = cam["z"]
    return ((box[0] - cam["x"]) * z + 960, (box[1] - cam["y"]) * z + 540, (box[2] - cam["x"]) * z + 960, (box[3] - cam["y"]) * z + 540)


def place(box, x, y, s=1.0, r=0.0):
    """A local box drawn at translate(x,y) scale(s) rotate(r) (engine order) -> its stage box."""
    if not box:
        return None
    a = math.radians(r or 0)
    c, sn = math.cos(a), math.sin(a)
    pts = [(box[0], box[1]), (box[2], box[1]), (box[0], box[3]), (box[2], box[3])]
    xs = [x + s * (px * c - py * sn) for px, py in pts]
    ys = [y + s * (px * sn + py * c) for px, py in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def mirror(box):
    return (-box[2], box[1], -box[0], box[3]) if box else None


def area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1]) if b else 0.0


def cover(a, b):
    if not a or not b:
        return 0.0
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def share(a, b):
    """Overlap as a share of the smaller box."""
    small = min(area(a), area(b))
    return cover(a, b) / small if small > 0 else 0.0


def union(bs):
    bs = [b for b in bs if b]
    if not bs:
        return None
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))


STYLE_PAD = {"tag": (0.62, 0.42), "pill": (0.72, 0.42)}


def text_lines(text, size, wrap_w):
    if not wrap_w:
        return [str(text)]
    lines, cur = [], ""
    for word in str(text).split():
        nxt = (cur + " " + word).strip()
        if cur and text_width(nxt, size) > wrap_w:
            lines.append(cur)
            cur = word
        else:
            cur = nxt
    return lines + ([cur] if cur else []) or [""]


def text_at(el, t):
    text = el.get("text")
    for s in el.get("steps") or []:
        if s.get("t") is not None and t >= s["t"] and s.get("text"):
            text = s["text"]
    return str(text if text is not None else "")


def text_local(el, t, style_default="tag"):
    """A text's box around its own origin, as engine.mjs textSvg draws it (style pad, 1.28 line height, wrap at w)."""
    size = float(el.get("size") or 46)
    style = el.get("style") or style_default
    lines = text_lines(text_at(el, t), size, el.get("w"))
    px, py = STYLE_PAD.get(style, (0.0, 0.0))
    w = max(text_width(l, size) for l in lines) + 2 * px * size
    h = len(lines) * 1.28 * size + 2 * py * size
    return (-w / 2, -h / 2, w / 2, h / 2)


def item_p(el, t):
    p = dict(el.get("p") or {})
    for s in el.get("steps") or []:
        if s.get("t") is not None and t >= s["t"] and isinstance(s.get("p"), dict):
            p.update(s["p"])
    return p


def item_local(spec, t):
    """(box, words, faces, name) of an item drawn at its own origin; words are (text, px, box)."""
    if spec.get("group"):
        bs, words, faces = [], [], []
        for m in spec["group"]:
            b, w, f, _ = item_local(m, t)
            mx, my, ms = float(m.get("x") or 0), float(m.get("y") or 0), float(m.get("s") if m.get("s") is not None else 1)
            bs.append(place(b, mx, my, ms))
            words += [(tx, px * ms, place(wb, mx, my, ms)) for tx, px, wb in w]
            faces += [place(fb, mx, my, ms) for fb in f]
        names = [item_local(m, t)[3] for m in spec["group"]]
        return union(bs), words, faces, "group of " + " + ".join(names[:3])
    if spec.get("asset"):
        w = float(spec.get("w") or 160)
        return (-w / 2, -w / 2, w / 2, w / 2), [], [], f"asset '{spec['asset']}'"
    if spec.get("draw") == "__person__":
        h = float(spec.get("h") or 200)
        pb = boxes.person(h, spec.get("look"))
        flip = (lambda b: mirror(b)) if (spec.get("facing") or 1) < 0 else (lambda b: b)
        box, face = flip(tuple(pb["box"])), flip(tuple(pb["face"]))
        return place(box, 0, h / 2), [], [place(face, 0, h / 2)], "mini person"
    if spec.get("draw"):
        p = {k: v for k, v in item_p(spec, t).items() if not str(k).startswith("_")}
        got = boxes.item(spec["draw"], p)
        box = tuple(got["box"]) if got.get("box") else None
        words = [(w["t"], float(w["px"]), tuple(w["box"])) for w in got.get("texts") or []]
        label = next((str(p[k]) for k in ("label", "title", "name", "text", "value") if p.get(k) not in (None, "")), "")
        return box, words, [], f"'{spec['draw']}'" + (f" ({label[:24]})" if label else "")
    if spec.get("text") is not None:
        b = text_local(spec, t, "plain")
        return b, [(text_at(spec, t), float(spec.get("size") or 46), b)], [], f"text '{text_at(spec, t)[:24]}'"
    return None, [], [], "thing"


def _min_px(got) -> float | None:
    px = [float(w["px"]) for w in (got or {}).get("texts") or [] if not is_symbol(w.get("t", ""))]
    return min(px) if px else None


_MIN_W: dict = {}
MIN_W_TABLE = __import__("pathlib").Path(__file__).resolve().parent / "engine" / "min_readable_w.json"


def min_w_table() -> dict:
    """name -> {w_default, min_w, px_at_default, sample}: the readable-width table (tools/saancha_min_w.py), {} if absent."""
    import json as _json
    try:
        return _json.loads(MIN_W_TABLE.read_text(encoding="utf-8")).get("saanche") or {}
    except (OSError, ValueError):
        return {}


def _min_w_cached(draw, p, scale):
    import json as _json
    key = (draw, _json.dumps(p, sort_keys=True, ensure_ascii=False, default=str), round(scale, 3))
    if key not in _MIN_W:
        try:
            _MIN_W[key] = min_readable_w(draw, p, scale)
        except boxes.BoxesUnavailable:
            raise
        except Exception as exc:  # noqa: BLE001  - a helper's hint never hides the problem itself
            _MIN_W[key] = {"w": None, "reason": f"could not be measured ({type(exc).__name__})"}
    return _MIN_W[key]


def min_readable_w(draw: str, p: dict | None = None, scale: float = 1.0, floor: float = FLOOR_PX) -> dict:
    """The smallest ``w`` at which every word inside this saancha, drawn with these exact ``p`` at ``scale`` (the item's
    s times the camera), reaches the floor on screen; measured by the engine's own drawing, not guessed.

    Returns {"w": the width or None (no words, no w parameter, or never readable up to the manifest's max),
    "w_now", "px_now" (smallest word px at w_now and scale 1), "box" (the box at w_now), "reason"}."""
    from bie.brain import saanche
    entry = saanche.get(draw) or {}
    spec = (entry.get("params") or {}).get("w")
    p = {k: v for k, v in dict(p or {}).items() if not str(k).startswith("_")}
    now = boxes.item(draw, p)
    out = {"w": None, "w_now": None, "px_now": _min_px(now), "box": now.get("box"), "reason": ""}
    if spec is None:
        out["reason"] = f"{draw} has no w parameter (make it bigger with s)"
        return out
    w_now = float(p.get("w", spec.get("default") or 0) or 0)
    out["w_now"] = w_now
    if out["px_now"] is None:
        out["reason"] = "no words inside it"
        return out
    lo, hi = float(spec.get("min", 10) or 10), float(spec.get("max", 1900) or 1900)
    lo = max(lo, 10.0)
    need = floor / max(scale, 1e-6) - 0.5

    def ok(w):
        got = _min_px(boxes.item(draw, dict(p, w=w)))
        return got is not None and got >= need

    grid = [round(lo * (hi / lo) ** (k / 39.0), 1) for k in range(40)]
    boxes.measure(items=[{"draw": draw, "p": dict(p, w=w)} for w in grid])          # one Node call for the whole grid
    passing = [k for k, w in enumerate(grid) if ok(w)]
    if not passing:
        out["reason"] = f"its words stay under {floor:.0f}px up to w {hi:.0f} at scale {scale:.2f} (shorten the words)"
        return out
    k = passing[0]
    a, b = (grid[k - 1] if k else lo), grid[k]
    fine = [round(a + (b - a) * j / 16.0, 1) for j in range(1, 17)]
    boxes.measure(items=[{"draw": draw, "p": dict(p, w=w)} for w in fine])
    best = next((w for w in fine if ok(w)), b)
    out["w"] = int(math.ceil(best / 10.0) * 10) if ok(math.ceil(best / 10.0) * 10) or best >= hi else int(math.ceil(best))
    return out


class Geo:
    """One element at one moment, on the stage: its box, its words, its faces, what it is."""

    __slots__ = ("el", "kind", "box", "words", "faces", "name", "scale", "loose")

    def __init__(self, el, kind, box, words=(), faces=(), name="", scale=1.0, loose=()):
        self.el, self.kind, self.box, self.words, self.faces, self.name, self.scale = el, kind, box, list(words), list(faces), name, scale
        self.loose = list(loose)         # words drawn outside the thing's own body (a crowd's caption, a label under a board)


def loose_local(spec, t) -> list:
    """The words of a drawn saancha that lie mostly outside its body (the shapes without the words), at its origin."""
    if not spec.get("draw") or spec.get("group") or spec.get("draw") in BACKDROPS:
        return []
    p = {k: v for k, v in item_p(spec, t).items() if not str(k).startswith("_")}
    got = boxes.item(spec["draw"], p)
    body = got.get("body")
    if not body:
        return []
    out = []
    for w in got.get("texts") or []:
        wb = tuple(w["box"])
        if area(wb) > 0 and cover(tuple(body), wb) < area(wb) * 0.5:
            out.append((w["t"], float(w["px"]), wb))
    return out


def person_pos(el, t):
    return prop_at(el, t)


def facing_at(el, t):
    s = el.get("facing", 1)
    for f in el.get("facings") or []:
        if f.get("t") is not None and t >= f["t"]:
            s = f["s"]
    return s


def geo_of(el, t, persons):
    kind = el.get("kind")
    if kind == "model3d":
        from bie.brain.video import models3d
        name = f"the 3D {'world' if el.get('place') else 'model'} '{el.get('id')}' ({el.get('model')})"
        if el.get("place"):
            return Geo(el, "backdrop", None, [], [], name)
        got = models3d.measure(el, t)
        return Geo(el, "thing", tuple(got["box"]) if got.get("box") else None, [], [], name)
    if kind == "person":
        pos = person_pos(el, t)
        h = float(el.get("h") or 440)
        pb = boxes.person(h, el.get("look"))
        box, face = tuple(pb["box"]), tuple(pb["face"])
        if facing_at(el, t) < 0:
            box, face = mirror(box), mirror(face)
        return Geo(el, "person", place(box, pos["x"], pos["y"]), [], [place(face, pos["x"], pos["y"])], f"person '{el.get('id')}'")
    if kind == "bubble":
        of = persons.get(el.get("of"))
        base = person_pos(of, t) if of else {"x": float(el.get("x") or 0), "y": float(el.get("y") or 0)}
        bx, by = base["x"] + float(el.get("dx", 200)), base["y"] + float(el.get("dy", -560))
        w = float(el.get("w") or 260)
        h = w * 0.74
        words = []
        if isinstance(el.get("content"), dict):
            spec = dict(el["content"])
            if spec.get("text") is not None and not spec.get("style"):
                spec["style"] = "plain"
            b, ws, _, _ = item_local(spec, t)
            words = [(tx, px, place(wb, bx, by + h * 0.06)) for tx, px, wb in ws]
        return Geo(el, "bubble", (bx - w / 2, by - h / 2, bx + w / 2, by + h * 0.9), words, [], f"the bubble of '{el.get('of')}'")
    if kind in ("mark", "glow", "rect", "arrow", "map"):
        if kind == "arrow":
            xs, ys, wd = (el.get("x1", 0), el.get("x2", 0)), (el.get("y1", 0), el.get("y2", 0)), float(el.get("width") or 8)
            return Geo(el, kind, (min(xs) - wd, min(ys) - wd, max(xs) + wd, max(ys) + wd), name="an arrow")
        if kind == "rect":
            x, y, w, h = float(el["x"]), float(el["y"]), float(el["w"]), float(el["h"])
            return Geo(el, kind, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), name="a panel")
        if kind == "mark":
            w = float(el.get("w") or 120)
            return Geo(el, kind, (el["x"] - w / 2, el["y"] - w / 2, el["x"] + w / 2, el["y"] + w / 2), name=f"the mark '{el.get('mark')}'")
        if kind == "glow":
            w = float(el.get("w") or 0)
            return Geo(el, kind, (el["x"] - w / 2, el["y"] - w / 2, el["x"] + w / 2, el["y"] + w / 2), name="a glow")
        return Geo(el, kind, None, name="the map")
    pos = prop_at(el, t)
    if el.get("text") is not None and not (el.get("draw") or el.get("asset") or el.get("group")):
        b = place(text_local(el, t), pos["x"], pos["y"], pos["s"])
        return Geo(el, "text", b, [(text_at(el, t), float(el.get("size") or 46) * pos["s"], b)], [], f"text '{text_at(el, t)[:30]}'", pos["s"])
    if el.get("draw") in BACKDROPS:
        b, ws, _, _ = item_local(el, t)
        return Geo(el, "backdrop", place(b, pos["x"], pos["y"], pos["s"]), [(tx, px * pos["s"], place(wb, pos["x"], pos["y"], pos["s"])) for tx, px, wb in ws],
                   [], "the world", pos["s"])
    b, ws, fs, name = item_local(el, t)
    kind = "mark" if el.get("draw") == "mark" else "thing"
    return Geo(el, kind, place(b, pos["x"], pos["y"], pos["s"], pos["r"]),
               [(tx, px * pos["s"], place(wb, pos["x"], pos["y"], pos["s"], pos["r"])) for tx, px, wb in ws],
               [place(f, pos["x"], pos["y"], pos["s"], pos["r"]) for f in fs], name, pos["s"],
               [(tx, px * pos["s"], place(wb, pos["x"], pos["y"], pos["s"], pos["r"])) for tx, px, wb in loose_local(el, t)])


def held_words(person, t):
    """The words on the item a person holds at ``t`` (for the floor and the word rules), scaled by the hold."""
    held = None
    for h in person.get("holds") or []:
        if h.get("t") is not None and t >= h["t"]:
            held = h.get("item")
    if not isinstance(held, dict):
        return []
    _, ws, _, name = item_local(held, t)
    s = float(held.get("s") if held.get("s") is not None else 1)
    return [(tx, px * s, None, name) for tx, px, _ in ws]


# ---------------------------------------------------------------- the rules


def visible(el, t, scene):
    t0 = el.get("t0") if el.get("t0") is not None else scene["t0"]
    t1 = el.get("t1") if el.get("t1") is not None else scene["t1"]
    return t0 <= t < min(t1, scene["t1"])


def problems(spec, language=None) -> list:
    """Every box-rule problem of a compiled show-spec (see the module text)."""
    from bie.brain.visual_thinking import CAUTION

    out = []
    hindi = is_hindi(language)
    plan_items, persons_req, bgs, worlds = [], [], set(), []
    for scene in spec.get("scenes") or []:
        bgs.add(scene.get("bg") or "paper")
        stack = list(scene.get("els") or [])
        while stack:
            el = stack.pop()
            if not isinstance(el, dict):
                continue
            if el.get("kind") == "person":
                persons_req.append({"h": el.get("h") or 440, "look": el.get("look") or "villager"})
                stack += [h.get("item") for h in el.get("holds") or []]
            if el.get("draw") == "__person__":
                persons_req.append({"h": el.get("h") or 200, "look": el.get("look") or "villager"})
            elif el.get("draw") and el.get("draw") != "__person__":
                variants = [dict(el.get("p") or {})]
                acc = dict(el.get("p") or {})
                for s in el.get("steps") or []:
                    if isinstance(s.get("p"), dict):
                        acc = {**acc, **s["p"]}
                        variants.append(dict(acc))
                for v in variants:
                    plan_items.append({"draw": el["draw"], "p": {k: x for k, x in v.items() if not str(k).startswith("_")}})
                if el["draw"] == "world":
                    worlds.append(dict(el.get("p") or {}))
            stack += list(el.get("group") or [])
            if isinstance(el.get("content"), dict):
                stack.append(el["content"])
    try:
        boxes.measure(items=plan_items, persons=persons_req, bgs=sorted(bgs), worlds=worlds)
    except boxes.BoxesUnavailable as exc:
        return [f"box rule not checked: {exc}"]
    pairs = []                                   # every 3D model at every sampled second, measured in one Node call
    for scene in spec.get("scenes") or []:
        models = [el for el in scene.get("els") or [] if el.get("kind") == "model3d"]
        t = float(scene["t0"])
        while models and t < scene["t1"]:
            pairs += [(el, t) for el in models if visible(el, t, scene)]
            t += STEP
    if pairs:
        from bie.brain.video import models3d
        try:
            got = models3d.measure_many(pairs)
        except models3d.ModelsUnavailable as exc:
            return [f"box rule not checked: {exc}"]
        bad = {f"the 3D model '{el.get('id')}': {g['error']}" for (el, _), g in zip(pairs, got) if g.get("error")}
        if bad:
            return [f"box rule not checked: {b}" for b in sorted(bad)]

    def word_rules(sid, text, where, siblings=(), labels=()):
        m = CAUTION.search(text)
        if m:
            out.append(f"scene {sid}: '{text[:50]}' ({where}) is a caution or fact-check line ('{m.group(0)}'); it stays a background "
                       "check, never on screen: show the thing itself (D1-06)")
        if hindi and english_label(text) and not bracket_term(text, siblings) and not wrapped_hindi(text, labels):
            out.append(f"scene {sid}: '{text[:50]}' ({where}) is English on a Hindi video's screen: write it in Hindi (Devanagari); an "
                       "English term may follow in brackets")

    for scene in spec.get("scenes") or []:
        sid = scene.get("id", "?")
        els = list(scene.get("els") or [])
        persons = {el.get("id"): el for el in els if el.get("kind") == "person"}
        zones = list(boxes.zones(scene.get("bg") or "paper"))
        bg_name = scene.get("bg") or "paper"
        for el in els:
            if el.get("draw") == "world":
                pos = prop_at(el, scene["t0"])
                for z in boxes.world_zones(el.get("p") or {}):      # held only while the world is on screen
                    zones.append({**z, "box": list(place(tuple(z["box"]), pos["x"], pos["y"], pos["s"])), "_el": el})
        panels = [el for el in els if el.get("kind") == "rect" and el.get("fill") and (el.get("alpha") if el.get("alpha") is not None else 1.0) >= 0.85]
        if scene.get("kicker"):
            word_rules(sid, str(scene["kicker"]), "the kicker")
        kicker_box = None
        if scene.get("kicker"):
            kw = text_width(scene["kicker"], KICKER[2]) + 52
            kicker_box = (KICKER[0], KICKER[1], KICKER[0] + kw, KICKER[1] + 66)
        # 8. a text is on screen long enough to be read (a text that flashes before a cut is caught mid pop-in by the audit)
        for el in els:
            if el.get("text") is None or el.get("draw") or el.get("asset") or el.get("group") or el.get("kind") not in (None, "text"):
                continue
            t0 = float(el.get("t0") if el.get("t0") is not None else scene["t0"])
            t1 = min(float(el.get("t1") if el.get("t1") is not None else scene["t1"]), float(scene["t1"]))
            if 0 < t1 - t0 < MIN_TEXT_S:
                out.append(f"scene {sid}: text '{str(el['text'])[:40]}' is on screen for only {t1 - t0:.1f}s (from {t0:.1f}s, "
                           f"{'the scene ends' if t1 >= float(scene['t1']) - 1e-6 else 'it leaves'} at {t1:.1f}s): a text needs at "
                           f"least {MIN_TEXT_S:.1f}s to be read - start it earlier, keep it longer, or show it in the next scene "
                           "(box rule)")
                continue
            # each value a text shows (its first words and every step that changes them) stays long enough to be read too:
            # Money v4, 5 Nov, run b: one text ran ₹10 -> ₹20 -> ₹50 -> ₹100 every 0.5 s and the audit caught ₹10 mid pop-in
            values = [(t0, str(el["text"]))] + sorted((float(st["t"]), str(st["text"])) for st in el.get("steps") or []
                                                      if st.get("t") is not None and st.get("text") is not None and t0 < float(st["t"]) < t1)
            for (a, words), (b, _) in zip(values, values[1:] + [(t1, "")]):
                if 0 < b - a < MIN_TEXT_S:
                    out.append(f"scene {sid}: text '{words[:40]}' shows for only {b - a:.1f}s (from {a:.1f}s) before it changes "
                               f"or leaves: each value needs at least {MIN_TEXT_S:.1f}s to be read - show the values side by side, "
                               "or give each its own longer moment (box rule)")
                    break
        seen_words = set()
        floor = {}
        runs = {}

        def hit(key, t, msg):
            r = runs.setdefault(key, [t, t, msg])
            r[1] = t

        def close(now, t_end=None):
            for key in list(runs):
                if key in now and t_end is None:
                    continue
                f, l, msg = runs[key]
                if l - f + STEP >= HOLD:
                    out.append(msg.replace("§F", f"{f:.1f}").replace("§D", f"{l - f + STEP:.1f}"))
                del runs[key]

        t = float(scene["t0"])
        while t < scene["t1"]:
            cam = cam_at(scene, t)
            on = []
            for el in els:
                if not visible(el, t, scene):
                    continue
                g = geo_of(el, t, persons)
                if g.kind == "text":
                    # a text fully behind an opaque, higher panel is not on screen
                    if any(visible(pn, t, scene) and (pn.get("z") or 1) > (el.get("z") or 40) and
                           cover(g.box, geo_of(pn, t, persons).box) >= area(g.box) * 0.98 for pn in panels):
                        continue
                on.append(g)
            now = set()
            # a world's zones count only during the world's own time (a world that arrives mid-scene does not block the
            # lines before it)
            zones_now = [z for z in zones if "_el" not in z or visible(z["_el"], t, scene)]
            for el in els:                       # a 3D world's parts move with its camera: its zones at this second
                if el.get("kind") == "model3d" and el.get("place") and visible(el, t, scene):
                    from bie.brain.video import models3d
                    zones_now += [{**z, "name": f"{z['name']} (3D world '{el.get('id')}')", "of": el.get("id")}
                                  for z in models3d.measure(el, t).get("zones") or []]
            texts = [g for g in on if g.kind == "text"]
            things = [g for g in on if g.kind in ("thing", "person", "bubble")]
            # the words on screen: caution and language (once per scene and text), and the floor for words inside things
            for g in on:
                for tx, px, _ in g.words:
                    if (sid, tx) not in seen_words:
                        seen_words.add((sid, tx))
                        word_rules(sid, tx, g.name if g.kind != "text" else "a text", [w[0] for w in g.words],
                                   label_strings(g.el, t) if g.el else ())
                    if g.kind != "text" and not is_symbol(tx):
                        key = (g.name, tx)
                        screen = px * cam["z"]
                        if key not in floor or screen < floor[key][0]:
                            src = g.el if (g.el.get("draw") and not g.el.get("group")) else None
                            floor[key] = (screen, px, cam["z"], g.scale,
                                          (src["draw"], item_p(src, t)) if src else None)
                if g.kind == "person":
                    for tx, px, _, name in held_words(g.el, t):
                        if (sid, tx) not in seen_words:
                            seen_words.add((sid, tx))
                            word_rules(sid, tx, f"held by {g.name}")
                        if not is_symbol(tx):
                            key = (f"{name} held by {g.name}", tx)
                            screen = px * cam["z"]
                            if key not in floor or screen < floor[key][0]:
                                floor[key] = (screen, px, cam["z"], 1.0, None)
            # 1. a text on a thing
            for a in texts:
                for b in things:
                    if b.el.get("kind") == "model3d" and a.el.get("on") == b.el.get("id"):
                        continue                 # a label placed at this model's spot
                    if share(a.box, b.box) > SHARE:
                        key = ("text-thing", a.name, b.name)
                        now.add(key)
                        hit(key, t, f"scene {sid}: {a.name} sits on {b.name} from §Fs for §Ds (box rule: words never sit on a "
                                    "thing; move the text clear of it, or put the words inside it through the thing's own label)")
            # 2. a thing on a face, or on the words inside another thing
            for a in things:
                for b in things:
                    if a is b:
                        continue
                    for face in b.faces:
                        if face and cover(a.box, face) > area(face) * SHARE:
                            key = ("thing-face", a.name, b.name)
                            now.add(key)
                            hit(key, t, f"scene {sid}: {a.name} covers the face of {b.name} from §Fs for §Ds (box rule: "
                                        "nothing on a face; move it beside the person)")
                    for tx, _, wb in b.words:
                        if wb and cover(a.box, wb) > area(wb) * WORD_SHARE and (a.el.get("z") or 20) >= (b.el.get("z") or 20):
                            key = ("thing-words", a.name, b.name, tx)
                            now.add(key)
                            hit(key, t, f"scene {sid}: {a.name} sits on the words '{tx[:30]}' of {b.name} from §Fs for "
                                        "§Ds (box rule: nothing on another thing's words)")
                    # 2b. words a thing draws outside its own body (a crowd's caption, a tag under a sign) that land on
                    # another thing: the whole-box test above lets them through when the other thing is drawn first
                    for tx, _, wb in a.loose:
                        if b.box and cover(b.box, wb) > area(wb) * WORD_SHARE and (a.el.get("z") or 20) >= (b.el.get("z") or 20):
                            key = ("loose-words", a.name, b.name, tx)
                            now.add(key)
                            hit(key, t, f"scene {sid}: the words '{tx[:30]}' of {a.name} sit on {b.name} from §Fs for §Ds "
                                        "(box rule: a thing's caption never sits on another thing; move one of them)")
            # 3. reserved zones of the background
            for g in on:
                if g.kind in ("glow", "map", "backdrop") or not g.box:
                    continue
                for z in zones_now:
                    if z.get("of") is not None and g.el.get("on") == z["of"]:
                        continue                 # placed at a spot of this 3D world: it labels that part
                    zb = tuple(z["box"])
                    if z.get("keep") == "text" and g.kind != "text":
                        continue
                    c = cover(g.box, zb)
                    if c > 0 and max(c / max(area(g.box), 1.0), c / max(area(zb), 1.0)) > ZONE_SHARE:
                        key = ("zone", g.name, z["name"])
                        now.add(key)
                        keep = "everything" if z.get("keep") == "all" else "words"
                        hit(key, t, f"scene {sid}: {g.name} sits on the background's {z['name']} ({bg_name}) from §Fs for "
                                    f"§Ds (box rule: the {z['name']} is reserved — keep {keep} off it, at x {zb[0]:.0f}-{zb[2]:.0f}, "
                                    f"y {zb[1]:.0f}-{zb[3]:.0f})")
            # 4. the frame edge and the kicker (screen space, after the camera)
            for g in on:
                if g.kind in ("glow", "map", "backdrop", "rect") or not g.box:
                    continue
                sb = to_screen(g.box, cam)
                inside = sb[2] > 0 and sb[0] < STAGE_W and sb[3] > 0 and sb[1] < STAGE_H
                cut = [side for side, v in (("left", -sb[0]), ("top", -sb[1]), ("right", sb[2] - STAGE_W), ("bottom", sb[3] - STAGE_H)) if v > EDGE]
                # words are always whole; a thing cropped while the camera is zoomed in is framing, not layout
                if inside and cut and not (g.el and moving_at(g.el, t)) and (g.kind == "text" or cam["z"] <= ZOOMED):
                    key = ("edge", g.name)
                    now.add(key)
                    hit(key, t, f"scene {sid}: {g.name} is cut by the frame's {'/'.join(cut)} edge from §Fs for §Ds "
                                "(box rule: everything stays inside the frame after the camera)")
                if kicker_box and g.kind != "backdrop" and cover(sb, kicker_box) > 0.15 * min(area(sb), area(kicker_box)):
                    key = ("kicker", g.name)
                    now.add(key)
                    hit(key, t, f"scene {sid}: {g.name} sits under the kicker from §Fs for §Ds (box rule: the kicker "
                                "pill at the top left is reserved)")
            close(now)
            t += STEP
        close(set(), t_end=t)
        for (name, tx), (screen, px, z, s, src) in sorted(floor.items(), key=lambda kv: kv[0]):
            if screen < FLOOR_PX - 0.5:
                need = s * (FLOOR_PX / screen) if screen > 0 else 0
                way = f"make the thing bigger (s at least {need:.2f})"
                if src:
                    mw = _min_w_cached(src[0], src[1], s * z)
                    if mw.get("w"):
                        way = (f"give it w {mw['w']} (now {mw['w_now']:.0f}; at s {s:.2f} and camera {z:.2f} all its words reach "
                               f"{FLOOR_PX:.0f}px from w {mw['w']}) or s at least {need:.2f}")
                    elif mw.get("reason"):
                        way += f" - w alone will not do: {mw['reason']}"
                out.append(f"scene {sid}: the words '{tx[:30]}' inside {name} are {screen:.0f}px on screen (scale {s:.2f}, camera "
                           f"{z:.2f}), under the {FLOOR_PX:.0f}px floor: {way}, or its words shorter (box rule)")
    return out
