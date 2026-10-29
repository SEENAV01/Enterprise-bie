"""On-screen text that a learner can read and that the narration explains (Task 046 Part C, Navin's verdict of 29 October 2026).

Navin on v1: "thoda kaam hume explain krne ke jo text lines screen par dikh rahi hai us par karna padega ... teacher ki
naration uske sentence aise poore ho ki banawati na lage". The first real plans put codes on the boards ("Exchange ✓ · Account
✓ / Store · Deferred", "EMI amount agreed ≠", "1–3 ✓, 4 Future payment →") and nothing checked that a board was complete, in the
learner's language or spoken. Rules CV-13 … CV-16 (``canvas_profile.json``): an on-screen text is a short COMPLETE phrase or
sentence in the learner's language, one idea per board or box; no symbol codes (✓ ✗ ≠ never; → = · + only inside a phrase
whose words and numbers the narration says); a caveat ("imagined market") once per part; every text is explained: its key
words and every number occur in the narration of the beat it appears in.

``problems(texts, beats)`` is the code check both compilers run (``canvas.compile_plan``, ``world.compile_world``); ``texts``
come from ``canvas_texts(plan)`` / ``world_texts(plan)``: one row per on-screen text with its element id, its cue beat and its
role (``label`` for a short heading or icon label, exempt from the spoken check; ``text`` for everything the learner reads).
"""
from __future__ import annotations

import re

NEVER = "✓✔✗✘≠"                                       # never spoken; a code
CONNECTORS = "→=+:/-–—|·"                              # allowed only inside a spoken phrase; never at the end
DEVANAGARI = re.compile(r"[ऀ-ॿ]{2,}")
LATIN = re.compile(r"[A-Za-z][A-Za-z'’-]{2,}")
NUMBER = re.compile(r"(?<![A-Za-z\d])\d[\d,]*(?:\.\d+)?(?![A-Za-z\d])")      # an amount, not an id like c01.1 or b2
CAVEAT = re.compile(r"illustrative|imagined|hypothetical|काल्पनिक|मान\s*लीजिए|actual data|not (?:a )?forecast|forecast नहीं|असली data", re.I)
STOP = {"the", "and", "aur", "for", "with", "from", "into", "that", "this", "its", "are", "was", "not", "but", "per",
        "के", "की", "का", "को", "से", "में", "पर", "है", "हैं", "और", "या", "एक", "यह", "वह", "भी", "ही", "तो", "ने", "था", "थे", "थी"}
SPOKEN_SHARE = 0.6                                     # at least this share of a text's key words is said in its beat


def words_of(text: str) -> list:
    """The key words of a text: Devanagari words of 2+ letters and Latin words of 3+ letters, stop words out, lower-case."""
    out = []
    for w in DEVANAGARI.findall(text) + LATIN.findall(text):
        w = w.lower().strip("'’-")
        if w and w not in STOP:
            out.append(w)
    return out


def numbers_of(text: str) -> set:
    return {n.replace(",", "") for n in NUMBER.findall(text or "")}


def _said(word: str, say: str) -> bool:
    """A key word counts as said when the narration carries it (Latin: the word, a plural or a possessive; Devanagari: the
    first four letters, so हुईं matches हुई and खरीदार matches खरीदारों)."""
    low = say.lower()
    if DEVANAGARI.match(word):
        return word[:4] in low
    return re.search(r"(?<![a-z])" + re.escape(word) + r"(?:e?s|'s)?(?![a-z])", low) is not None


def code_list(text: str) -> bool:
    """Three or more bare tokens separated by · / | on one line: a code list, not a phrase."""
    for line in text.split("\n"):
        parts = [p.strip() for p in re.split(r"\s*[·/|]\s*", line) if p.strip()]
        if len(parts) >= 3 and all(len(p.split()) <= 2 for p in parts):
            return True
    return False


def text_problems(text: str, say: str, *, where: str, role: str = "text", beat_id: str = "") -> list:
    """The problems of one on-screen text against the narration of its cue beat (CV-13, CV-14, CV-16)."""
    problems = []
    clean = (text or "").strip()
    if not clean:
        return problems
    bad = sorted({c for c in clean if c in NEVER})
    if bad:
        problems.append(f"{where}: '{clean[:40]}' uses the symbol code{'s' if len(bad) > 1 else ''} {' '.join(bad)}; write the idea in "
                        "words the learner reads, or leave it to the narration (CV-13)")
    lines = [ln.strip() for ln in clean.split("\n") if ln.strip()]
    if any(ln[-1] in CONNECTORS for ln in lines) or any(not (DEVANAGARI.search(ln) or LATIN.search(ln) or NUMBER.search(ln)) for ln in lines):
        problems.append(f"{where}: '{clean[:40]}' is unfinished (a line ends on a connector or is only symbols); write a complete "
                        "phrase or sentence (CV-13)")
    if code_list(clean):
        problems.append(f"{where}: '{clean[:40]}' is a list of codes; one idea per board or box, as a phrase the learner can read (CV-13)")
    if role == "text":
        key = words_of(clean)
        said = [w for w in key if _said(w, say)]
        if key and (not said or len(said) < SPOKEN_SHARE * len(key)):
            missing = [w for w in key if w not in said]
            problems.append(f"{where}: '{clean[:40]}' is not explained by the narration of {beat_id or 'its beat'}: the words "
                            f"{missing[:5]} are not said there; say them in that beat or move the cue to the beat that says them (CV-14)")
    unsaid = sorted(n for n in numbers_of(clean) if n not in numbers_of(say))
    if unsaid:
        problems.append(f"{where}: the number{'s' if len(unsaid) > 1 else ''} {', '.join(unsaid)} on screen {'are' if len(unsaid) > 1 else 'is'} "
                        f"not said in {beat_id or 'its beat'}; write numbers the way the narration says them (CV-16)")
    return problems


def problems(texts: list, beats: list) -> list:
    """All screen-text problems of a plan: ``texts`` rows {"id", "cue", "text", "role"}; ``beats`` the plan's beats (beat_id, say)."""
    says = {b["beat_id"]: b.get("say", "") for b in beats}
    first = beats[0]["beat_id"] if beats else ""
    out = []
    caveats = []
    for row in texts:
        cue = row.get("cue")
        beat_id = cue[0] if isinstance(cue, (list, tuple)) and cue else first
        say = says.get(beat_id, "")
        out += text_problems(row["text"], say, where=row["id"], role=row.get("role", "text"), beat_id=beat_id)
        if CAVEAT.search(row["text"] or ""):
            caveats.append(row["id"])
    if len(caveats) > 1:
        out.append(f"the caveat ('imagined market', 'illustrative') is on {len(caveats)} texts ({', '.join(caveats[:4])}); show it once "
                   "per part on its own small note, not on every board (CV-15)")
    return out


def canvas_texts(plan: dict) -> list:
    """The on-screen texts of a canvas (B) plan: text and callout bodies, value steps, table cells, tree roots and children,
    arrow labels (text); icon labels and tags (label)."""
    rows = []
    for n in plan.get("nodes", []) or []:
        kind, nid, cue = n.get("kind"), n.get("id", "?"), n.get("cue")
        if kind in ("text", "callout"):
            rows.append({"id": nid, "cue": cue, "text": n.get("text", ""), "role": "label" if n.get("style") in ("tag", "title") else "text"})
        elif kind == "value":
            rows += [{"id": f"{nid}.step{i + 1}", "cue": s.get("cue", cue), "text": s.get("text", ""), "role": "text"} for i, s in enumerate(n.get("steps") or [])]
        elif kind == "table":
            rows.append({"id": f"{nid}.columns", "cue": cue, "text": " · ".join(str(c) for c in n.get("columns") or []), "role": "label"})
            rows += [{"id": f"{nid}.row{i + 1}", "cue": r.get("cue", cue), "text": "\n".join(str(c) for c in r.get("cells") or []), "role": "text"}
                     for i, r in enumerate(n.get("rows") or [])]
        elif kind == "tree":
            rows.append({"id": f"{nid}.root", "cue": cue, "text": str(n.get("root", "")), "role": "label"})
            for i, c in enumerate(n.get("children") or []):
                text, ccue = (c.get("text", ""), c.get("cue", cue)) if isinstance(c, dict) else (str(c), cue)
                rows.append({"id": f"{nid}.child{i + 1}", "cue": ccue, "text": text, "role": "label" if len(text.split()) <= 2 else "text"})
        elif kind == "icon" and n.get("label"):
            rows.append({"id": f"{nid}.label", "cue": cue, "text": str(n.get("label", "")), "role": "label"})
        elif kind == "arrow" and n.get("label"):
            rows.append({"id": f"{nid}.label", "cue": cue, "text": str(n.get("label", "")), "role": "label" if len(str(n["label"]).split()) <= 2 else "text"})
    return rows


def world_texts(plan: dict) -> list:
    """The on-screen texts of a world (C) plan: board steps and their titles, price tags, labels, pull arrows and the title."""
    rows = []
    for n in plan.get("elements", []) or []:
        kind, nid, cue = n.get("kind"), n.get("id", "?"), n.get("cue")
        if kind == "board":
            if n.get("text"):
                rows.append({"id": f"{nid}.title", "cue": cue, "text": str(n["text"]), "role": "label"})
            rows += [{"id": f"{nid}.step{i + 1}", "cue": s.get("cue", cue), "text": str(s.get("text", "")), "role": "text"} for i, s in enumerate(n.get("steps") or [])]
        elif kind == "price_tag":
            rows += [{"id": f"{nid}.step{i + 1}", "cue": s.get("cue", cue), "text": str(s.get("text", "")), "role": "label"} for i, s in enumerate(n.get("steps") or [])]
        elif kind in ("label", "pull_arrow"):
            text = str(n.get("text", ""))
            rows.append({"id": nid, "cue": cue, "text": text, "role": "label" if len(text.split()) <= 2 else "text"})
        elif kind == "title":
            rows.append({"id": nid, "cue": cue, "text": str(n.get("text", "")), "role": "label"})
    return rows
