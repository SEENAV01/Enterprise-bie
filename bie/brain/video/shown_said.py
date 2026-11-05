"""Dikhaya-bola, the shown-said check (Navin, 5 November 2026): "jo bola, woh dikhe" — every thing a line names is on
screen during that line.

Navin's choice (decision card, 5 November 2026): "Boli cheez usi line mein" — when a line names a thing, a person's
thing or a place that BIE can draw, that thing is on screen while the line is spoken; when it is not, the compiler
returns the plan naming the line and the word; the target is 95% or more of the lines (agreement of 3 November,
section 5: every line "said = shown").

Which words count: the Hindi and English words of the saancha library (``saanche.json`` tags) that name concrete things
— a sack, a note, a coin, a dollar, a bank, a vault, a phone. Diagrams and marks (a timeline, a graph, a tick, a fork,
a gauge) and abstract words (price, demand, savings, payment) are ways of showing, not things said, so they create no
obligation. A word is matched with its common Hindi endings (नोट → नोटों, रुपया → रुपये) and English plurals.

What shows a word: during the line (at least 1 s of it, or half of a shorter line), an element on screen that is one
of the saanche carrying that word — drawn alone, in a group, held by a person or inside a thought bubble — or a drawn
thing whose own label carries the word (a sack labelled "नमक" shows salt). A word that names a place is also shown by the
place the scene stands in (its background or a world item of that kind: दुकान in the shop). A text alone is not the
thing, and a world never shows an object (a bank hall shows "बैंक" the place, not a coin).
"""
from __future__ import annotations

import re

from bie.brain import saanche

STEP = 0.5
MIN_SHOWN = 1.0                 # seconds of the line the thing must be on screen (half of a shorter line)
TARGET = 0.95                   # agreement: every line said = shown, 95% or more

# Saanche that are a way of showing (diagrams, marks, scales, metaphors, the place itself), not a thing that is named.
NOT_THINGS = {"mark", "disc", "segmentedBar", "ruler", "pillars", "podium", "staircase", "rope", "world", "flow", "bands",
              "fork", "gapBars", "timeline", "table", "graph", "funnel", "roadmap", "gauge", "hands", "sweat", "priceTag",
              "crowd", "plant", "barrier", "chair"}
# Words too general to oblige a drawing on every line that says them (a money lesson says पैसा in every line), or that
# name an idea rather than a thing.
ABSTRACT = {"पैसा", "पैसे", "धन", "money", "cash", "funds", "fund", "wealth", "currency", "भुगतान", "payment", "बचत",
            "savings", "भंडार", "आरक्षित", "reserve", "reserves", "संस्था", "institution", "इमारत", "building", "ढेर",
            "heap", "pile", "stack", "डिब्बा", "can", "box", "जगह", "place", "स्थान", "मूल्य", "दाम", "क़ीमत", "price",
            "cost", "पद", "आसन", "seat", "post", "निवेश", "invest", "फंड", "गाड़ी", "ईंट", "brick", "पत्ते", "leaves",
            "रेटिंग", "rating", "पैमाना", "scale", "मीटर", "meter", "सूचकांक", "index", "रुकावट", "बाधा", "प्रतिबंध",
            "ban", "मेहनत", "पसीना", "effort", "बैठक", "deal", "case", "card", "tag", "bar", "line", "share", "check",
            "bill", "tie", "block", "branch", "शाखा", "port", "mark", "rate", "split", "parts", "types", "real", "public",
            "people", "लोग", "जनता", "भीड़", "आबादी", "crowd", "population", "sick unit", "small lender", "lender",
            "bundle", "notes", "note", "roll", "packet", "पैकेट", "bag", "bowl", "pot", "jar", "safe", "lock", "ताला",
            "chain", "rod", "rope", "seed", "grow", "tree", "tool", "औज़ार", "exchange", "market", "financial market",
            "bond", "act", "law", "report", "licence", "contract", "proposal", "document", "balance", "balances"}
# The place a scene stands in (its background, or a world item's kind) shows a word that names that place: a line that
# says दुकान while the scene stands in the shop shows the shop. The names are the engine's own backgrounds and world kinds.
PLACES = {"village": {"गाँव", "village"}, "haat": {"हाट", "बाज़ार", "market"}, "shop": {"दुकान", "shop"},
          "store": {"दुकान", "गोदाम", "shop", "store", "warehouse"}, "market": {"बाज़ार", "market"},
          "bankHall": {"बैंक", "bank"}, "centralBank": {"केंद्रीय बैंक", "रिज़र्व बैंक", "आरबीआई", "central bank",
          "reserve bank", "rbi", "बैंक", "bank"}, "exchangeFloor": {"शेयर बाज़ार", "बाज़ार"}, "port": {"बंदरगाह"},
          "factory": {"कारख़ाना", "उद्योग", "factory", "industry"}, "office": {"दफ़्तर", "office"},
          "court": {"अदालत", "न्यायालय", "court"}, "city": {"शहर", "city"}, "assembly": {"संसद", "सभा", "parliament",
          "assembly"}, "twoCountries": {"दो देश", "border"}, "forexCounter": {"विदेशी मुद्रा", "मुद्रा विनिमय", "forex",
          "foreign currency", "काउंटर", "counter"}}
SUFFIXES = ("ों", "ो", "ें", "े", "ियों", "ियाँ", "यों", "एँ", "ाओं", "ाएँ")   # plural and oblique endings only: जार + ी is जारी
STEM_ENDINGS = ("ा", "े", "ों", "ें", "ी", "ियाँ", "ियों")                             # रुपया -> रुपये, सिक्का -> सिक्कों
TOKEN = re.compile(r"[\wऀ-ॿ][\wऀ-ॿ़ँ-ःा-्'-]*")


def lexicon() -> dict:
    """word (lower case) -> the thing-saanche that carry it; multi-word tags kept as phrases."""
    out: dict = {}
    for name, entry in saanche.manifest()["saanche"].items():
        if name in NOT_THINGS:
            continue
        for tag in entry.get("tags") or []:
            word = tag.strip().lower()
            if not word or word in ABSTRACT or len(word) < 2:
                continue
            out.setdefault(word, set()).add(name)
    return out


def _stem_match(token: str, word: str) -> bool:
    if token == word:
        return True
    if re.fullmatch(r"[a-z][a-z .-]*", word):
        return token in (word + "s", word + "es")
    if len(word) >= 2 and token.startswith(word) and token[len(word):] in SUFFIXES:
        return True
    if word[-1] in "ाी" and len(word) >= 3:
        stem = word[:-1]
        return token.startswith(stem) and token[len(stem):] in STEM_ENDINGS
    return False


def named_things(text: str, lex: dict | None = None) -> list:
    """The thing-words a line names, in order: [(word as said, tag, saanche)]; phrases before single words."""
    lex = lex if lex is not None else lexicon()
    low = str(text or "").lower()
    found, used = [], set()
    for tag in sorted((t for t in lex if " " in t), key=len, reverse=True):
        at = low.find(tag)
        if at >= 0 and not any(at <= u < at + len(tag) for u in used):
            found.append((text[at:at + len(tag)], tag, sorted(lex[tag])))
            used.update(range(at, at + len(tag)))
    for m in TOKEN.finditer(low):
        if any(m.start() <= u < m.end() for u in used):
            continue
        token = m.group(0).strip("'-")
        for tag, names in lex.items():
            if " " not in tag and _stem_match(token, tag):
                found.append((text[m.start():m.end()], tag, sorted(names)))
                break
    seen, out = set(), []
    for said, tag, names in found:
        if tag not in seen:
            seen.add(tag)
            out.append((said, tag, names))
    return out


def _labels(item: dict) -> str:
    p = item.get("p") or {}
    return " ".join(str(v) for k, v in p.items() if isinstance(v, str)).lower()


def _things(el: dict, t: float) -> list:
    """(draw name, label words) of every drawn thing an element shows at ``t`` (groups, holds, bubble content)."""
    out = []
    if el.get("draw") and el["draw"] not in ("world", "__person__"):
        out.append((el["draw"], _labels(el)))
    for m in el.get("group") or []:
        if isinstance(m, dict):
            out += _things(m, t)
    if el.get("kind") == "person":
        held = None
        for h in el.get("holds") or []:
            if h.get("t") is not None and h["t"] <= t:
                held = h.get("item")
        if isinstance(held, dict):
            out += _things(held, t)
    if el.get("kind") == "bubble" and isinstance(el.get("content"), dict):
        out += _things(el["content"], t)
    return out


def _places(scene: dict, t: float) -> set:
    """The place words of where the scene stands at ``t``: its background and any world item on screen."""
    words = set(PLACES.get(scene.get("bg") or "", ()))
    for el in scene.get("els") or []:
        if el.get("draw") == "world" and _visible(el, t, scene):
            words |= PLACES.get((el.get("p") or {}).get("kind") or "", set())
    return words


def _visible(el, t, scene) -> bool:
    t0 = el.get("t0") if el.get("t0") is not None else scene["t0"]
    t1 = el.get("t1") if el.get("t1") is not None else scene["t1"]
    return t0 <= t < min(t1, scene["t1"])


def _shown_seconds(spec: dict, t0: float, t1: float, tag: str, names: list) -> float:
    hits = 0
    t = t0
    while t < t1:
        for scene in spec.get("scenes") or []:
            if not (scene["t0"] <= t < scene["t1"]):
                continue
            if tag in _places(scene, t) or any(name in names or tag in label
                                               for el in scene.get("els") or [] if _visible(el, t, scene)
                                               for name, label in _things(el, t)):
                hits += 1
                break
        t += STEP
    return hits * STEP


def rows(spec: dict, T, only=None) -> list:
    """Per line (of ``only`` when given: the lines the plan places in scenes): what it names and whether each named
    thing is on screen long enough during the line."""
    lex = lexicon()
    out = []
    for lid in T.line_ids():
        if only is not None and lid not in only:
            continue
        line = T.L(lid)
        t0, t1 = float(line["t0"]), float(line["t1"])
        need = min(MIN_SHOWN, (t1 - t0) / 2)
        named = []
        for said, tag, names in named_things(line.get("sub") or "", lex):
            secs = _shown_seconds(spec, t0, t1, tag, names)
            named.append({"word": said, "tag": tag, "saanche": names, "shown_s": round(secs, 1), "shown": secs + 1e-6 >= need})
        out.append({"line": lid, "t0": round(t0, 2), "t1": round(t1, 2), "named": named,
                    "ok": all(n["shown"] for n in named)})
    return out


def summary(rows_: list) -> dict:
    named = [r for r in rows_ if r["named"]]
    ok = sum(1 for r in named if r["ok"])
    return {"lines": len(rows_), "lines_naming_things": len(named), "lines_shown": ok,
            "said_shown_pct": round(100.0 * ok / len(named), 1) if named else 100.0,
            "target_pct": TARGET * 100,
            "missing": [{"line": r["line"], "word": n["word"], "saanche": n["saanche"]}
                        for r in named for n in r["named"] if not n["shown"]]}


def problems(spec: dict, T, only=None) -> list:
    out = []
    for r in rows(spec, T, only):
        for n in r["named"]:
            if not n["shown"]:
                show = " or ".join(n["saanche"][:3])
                out.append(f"line {r['line']} ({r['t0']:.1f}-{r['t1']:.1f}s) names '{n['word']}' but nothing showing it is on "
                           f"screen during the line ({n['shown_s']:.1f}s): show {show} (or a thing labelled "
                           f"'{n['tag']}') while that line is spoken (dikhaya-bola: jo bola, woh dikhe)")
    return out
