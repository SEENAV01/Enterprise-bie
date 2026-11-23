"""Aatma ki almaari: what a passed film's way of teaching was, kept without its subject's words (Navin, 23 November 2026).

Navin: "bie ke code mein ek memory unit daalna jisme passed output ke features, wo kin general baaton se bana tha jo
subject specific words par depend nahi karti, matlab har passed output ki aatma na ki keval structure", and, after
Claude's example: "kisi passed output ke yeh niyam bhi ki yaha process samjhayi thi to yeh kyu behtar samajh aayi: step by
step cheezen huyi, hilte huye hisse; jaise economics mein scene mein gaay chalti huyi, paise ka len den, vyakti chalte
huye, counter khulta hua, asli sikke, kahani chalti huyi, baat karti huyi". He agreed it works like a form: the soul is
a form with blanks, and each subject fills the blanks with its own words ("ek form ki tarah hai jisme us subject ke words
aa jaayenge").

So for a film this module finds, by code, how each part was taught and shown, as **forms** in five drawers (kinds):
process, structure, scene, story and reason. A form is a sentence with blanks in brackets ("[chalti cheez] khud chale,
thik jab awaaz uska naam le") and the film's own filling of the blanks ("chalti cheez: H⁺"), plus the film's measures
(how often the camera moved, how many things moved in a line, how many lines asked a question ...). Nothing here asks an
AI. Navin sees a film's soul on its review page (``page``); only after his yes does ``tools/lock_aatma.py`` put the
forms into ``rulebook/aatma.json``, with his words on why the film worked. A locked form then goes to every new film's
maker in any subject, its blanks filled from that subject's kit (``prompt_part``), and the new film's measures are
compared with the locked films' range (``aatma_problems``). Claude's demos never enter the almaari: only a BIE film
Navin passed.
"""
from __future__ import annotations

import copy
import html
import json
import math
import re
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).resolve().parent / "rulebook" / "aatma.json"
SCHEMA = "bie.brain.aatma/1"

KINDS = {"process": "Process / mechanism", "structure": "Structure / jagah", "scene": "Duniya / scene",
         "story": "Kahani / len-den", "reason": "Kaaran (kyun)"}

# the blanks a form may have, in words of no subject (the subject's kit gives the examples)
SLOTS = {"chalti cheez": "the thing that moves or is passed on",
         "machine": "the part, machine or institution it goes through",
         "hissa": "a part of the picture that moves itself",
         "kaam": "what that part does",
         "jagah": "the whole place first seen",
         "andar ki jagah": "the place the camera goes into next",
         "misaal": "an everyday example, in its own picture",
         "sawaal": "the small question asked before the answer",
         "kirdaar": "the people of the scene"}

# a line that names an amount on two sides ("zyada", "kam", "high", "low", "bheed", "khaali")
TWO_SIDES = re.compile(r"(?i)\b(zyada|jyada|kam|high|low|higher|lower|bheed|khaali|khali|gradient|difference)\b")


def _roman(sentence: dict) -> str:
    return sentence.get("roman") or sentence.get("text") or ""


def _lines(film: dict):
    for shot in film.get("shots") or []:
        for k, sentence in enumerate(shot.get("sentences") or []):
            yield shot, k, sentence


def _where(shot: dict, k: int) -> str:
    return f"{shot.get('id')}.{k + 1}"


def _name_of_move(move: dict) -> str:
    return str(move.get("label") or move.get("what") or "").strip()


def _near(point, pin, gap=8.0) -> bool:
    return math.hypot(float(point[0]) - float(pin["x"]), float(point[1]) - float(pin["y"])) <= gap


def measures(film: dict) -> dict:
    """The film's numbers that carry no subject: lines, how often the camera moved (after BIE's steady camera), things
    moving per line, the share of lines that ask, that add a step, that move something, words per line, everyday asides."""
    from . import studio_film
    lines = [s for _, _, s in _lines(film)]
    n = max(1, len(lines))
    moved_camera = 0
    for shot in film.get("shots") or []:
        last = (50.0, 50.0, 1.0)
        for zoom in studio_film.steady_camera(shot.get("sentences") or []):
            now = (zoom["x"], zoom["y"], zoom["scale"])
            if abs(now[2] - last[2]) >= 0.15 or (now[2] > 1 and math.hypot(now[0] - last[0], now[1] - last[1]) >= 5):
                moved_camera += 1
            last = now
    words = [len(_roman(s).split()) for s in lines] or [0]
    movers = [sum(int(m.get("count") or 1) for m in s.get("moves") or []) for s in lines]
    return {"lines": len(lines), "shots": len(film.get("shots") or []),
            "camera_moves": round(moved_camera / n, 2),
            "movers_per_line": round(sum(movers) / n, 2),
            "questions": round(sum(1 for s in lines if _roman(s).rstrip().endswith("?")) / n, 2),
            "steps": round(sum(1 for s in lines if s.get("step")) / n, 2),
            "moving_lines": round(sum(1 for s in lines if s.get("moves") or s.get("reacts") or s.get("acts")) / n, 2),
            "words_avg": round(sum(words) / len(words), 1), "words_max": max(words),
            "asides": sum(1 for shot in film.get("shots") or [] if shot.get("aside"))}


def _form(fid: str, kind: str, form: str, why: str, slots: dict, where: list) -> dict:
    return {"id": fid, "kind": kind, "form": form, "why": why, "filled": slots, "where": where[:6], "seen": len(where)}


def forms(film: dict) -> list:
    """The ways this film taught and showed, found by code, each as a form with blanks and this film's filling."""
    from . import studio_film
    out, found = [], {}

    def add(fid, kind, form, why, slots, where):
        if fid in found:
            if where not in found[fid]["where"]:
                found[fid]["where"] = (found[fid]["where"] + [where])[:6]
            found[fid]["seen"] += 1
            for key, value in slots.items():
                found[fid]["filled"].setdefault(key, value)
            return
        found[fid] = _form(fid, kind, form, why, dict(slots), [where])
        out.append(found[fid])

    shots = film.get("shots") or []
    for number, shot in enumerate(shots):
        sentences = shot.get("sentences") or []
        pins = [p for s in sentences for p in s.get("pins") or [] if isinstance(p, dict) and "x" in p]
        parts = {p.get("id"): p.get("name") or p.get("id") for p in (shot.get("visual") or {}).get("parts") or []
                 if isinstance(p, dict)}
        steps = [k for k, s in enumerate(sentences) if s.get("step")]
        if len(steps) >= 3:
            add("ek_ek_step", "process", "Ek hi tasveer par ek-ek step jude; naya step chamke, pichhle step dheeme rahein",
                "dimaag mein tasveer diagram ki tarah step by step banti hai", {}, _where(shot, steps[0]))
        two_sides_at = next((k for k, s in enumerate(sentences) if TWO_SIDES.search(_roman(s)) or (s.get("count") or {}).get("groups")), None)
        for k, sentence in enumerate(sentences):
            roman = _roman(sentence)
            for move in sentence.get("moves") or []:
                name = _name_of_move(move)
                if name and studio_film.said_at([name, move.get("what") or ""], roman, max(2.5, 0.075 * len(roman))) is not None:
                    add("naam_par_chale", "process", "[chalti cheez] khud chale, thik jab awaaz uska naam le",
                        "nazar usi cheez par jaati hai jo abhi boli gayi", {"chalti cheez": name}, _where(shot, k))
                points = move.get("points") or []
                inner = points[1:-1] if len(points) > 2 else []
                ends = points[:1] + points[-1:]
                # a machine sits on the way, not where the thing starts or ends (those are places), and is never a mapping
                through = next((p for p in pins if "=" not in str(p.get("label") or "") and any(_near(q, p) for q in inner)
                                and not any(_near(q, p, 10.0) for q in ends)), None)
                if through and len(points) >= 2:
                    add("andar_se_raasta", "process", "[chalti cheez] [machine] ke andar se guzre, bahar se nahi",
                        "raasta saaf dikhta hai; bahar ghoomti cheez galat tasveer banati hai",
                        {"chalti cheez": name or move.get("what"), "machine": through.get("label")}, _where(shot, k))
                if two_sides_at is not None and k in (two_sides_at, two_sides_at + 1) and name:
                    add("pehle_zyada_kam", "process", "Chalne se pehle dikhao ki [chalti cheez] kahan zyada hai aur kahan kam",
                        "chalne ka kaaran pehle aankh se dikhta hai", {"chalti cheez": name},
                        _where(shot, two_sides_at))
            for act in sentence.get("acts") or []:
                words = {"turn": "ghoomta hai", "spin": "ghoomta rehta hai", "open": "khulta hai", "tight": "kasta hai",
                         "stick": "judta hai", "leave": "chhoot jaata hai", "arrive": "aata hai", "glow": "chamakta hai"}
                if act.get("do") in words:
                    add("hissa_hile", "process", "[hissa] usi pal [kaam] jab line kahe",
                        "machine kaam karti dikhti hai, sirf likhi nahi jaati",
                        {"hissa": parts.get(act.get("part")) or act.get("part"), "kaam": words[act["do"]]}, _where(shot, k))
            if roman.rstrip().endswith("?") and k + 1 < len(sentences):
                add("sawaal_phir_jawab", "reason", "Kaaran se pehle ek chhota sawaal ('[sawaal]'), phir ek bahte vakya mein jawab",
                    "soch jaagti hai, phir jawab baith jaata hai", {"sawaal": roman.strip()}, _where(shot, k))
        dive = shot.get("dive") or {}
        if number and dive.get("x", -1) != -1:
            before = shots[number - 1]
            add("poora_phir_zoom", "structure", "Pehle poori [jagah] dikhe, phir camera [andar ki jagah] mein jaaye",
                "dimaag mein naksha banta hai: kahan hain, phir andar kya hai",
                {"jagah": before.get("title") or before.get("id"), "andar ki jagah": shot.get("title") or shot.get("id")},
                _where(shot, 0))
        if shot.get("aside"):
            mapping = [p.get("label") for s in sentences for p in s.get("pins") or [] if "=" in str(p.get("label") or "")]
            add("rozmarra_misaal", "story", "Rozmarra ki [misaal] apni asli tasveer mein, mapping saaf shabdon mein",
                "anjaani cheez jaani-pehchaani cheez se jud jaati hai",
                {"misaal": shot.get("title") or shot.get("id"), "mapping": "; ".join(m for m in mapping if m)}, _where(shot, 0))
    if measures(film)["camera_moves"] <= 0.55:
        add("camera_tika", "process", "Camera tab tak ek jagah tike jab tak ek step poora na ho",
            "aankh ko thehrav milta hai, step poora dikhta hai", {}, "film")
    return out


def soul(film: dict) -> dict:
    """A film's aatma: its forms by drawer, and its measures."""
    found = forms(film)
    return {"schema": SCHEMA, "drawers": {kind: [f for f in found if f["kind"] == kind] for kind in KINDS},
            "measures": measures(film)}


# --- the almaari: locked forms, the subject kits, and their use -----------------------------------------------------------

@lru_cache(maxsize=1)
def _load(path: str = str(PATH)) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema": SCHEMA, "version": 1, "films": [], "kits": {}}


def almaari(path: Path | None = None) -> dict:
    return copy.deepcopy(_load(str(path or PATH)))


SUBJECTS = {"biology": r"\bbio", "economics": r"\becono|\bcommerce", "physics": r"\bphysic", "chemistry": r"\bchemi",
            "geography": r"\bgeogra", "history": r"\bhistor", "polity": r"\bpolit"}


def subject_of(course: str) -> str:
    low = (course or "").lower()
    return next((name for name, pattern in SUBJECTS.items() if re.search(pattern, low)), "")


def locked_forms(book: dict | None = None) -> dict:
    """Every locked form once, by id, with the films that showed it."""
    book = book if book is not None else almaari()
    out = {}
    for film in book.get("films") or []:
        for form in film.get("forms") or []:
            entry = out.setdefault(form["id"], {"id": form["id"], "kind": form["kind"], "form": form["form"],
                                               "why": form.get("why", ""), "films": []})
            entry["films"].append(film.get("qid"))
    return out


def kits(book: dict | None = None) -> dict:
    """Each subject's own things to fill the blanks with, from BIE's own resources, never written by hand: the molecules
    of the film kit for the sciences, and the places, people and goods of the examples Navin locked
    (``rulebook/explanations.json``) for their subject; the almaari's own ``kits`` add to them."""
    from . import studio_film
    out = {}
    molecules = [str(v.get("name") or k) for k, v in (studio_film.KIT.get("molecules") or {}).items()]
    for science in ("biology", "chemistry"):
        out[science] = {"chalti cheez": molecules[:16]}
    try:
        locked = json.loads((PATH.parent / "explanations.json").read_text(encoding="utf-8")).get("examples") or []
    except (FileNotFoundError, ValueError):
        locked = []
    for entry in locked:
        subject = subject_of(f"{entry.get('subject', '')} {entry.get('family', '')}")
        example = entry.get("example") or {}
        if not subject or not example:
            continue
        kit = out.setdefault(subject, {})
        place = str(example.get("place") or "").split(";")[0].strip()
        for slot, values in (("jagah", [place] if place else []), ("kirdaar", example.get("actors") or []),
                             ("chalti cheez", example.get("goods") or [])):
            have = kit.setdefault(slot, [])
            have += [v for v in values if v and v not in have]
    for subject, more in ((book or {}).get("kits") or {}).items():
        kit = out.setdefault(subject, {})
        for slot, values in more.items():
            have = kit.setdefault(slot, [])
            have += [v for v in values if v and v not in have]
    return out


def prompt_part(course: str, book: dict | None = None) -> str:
    """What passed films did, for a new film's maker in any subject: each locked form with its blanks, the meaning of
    each blank, and this subject's own things to fill them with (its kit). Empty while the almaari is empty."""
    book = book if book is not None else almaari()
    found = locked_forms(book)
    if not found:
        return ""
    subject = subject_of(course)
    kit = kits(book).get(subject) or {}
    lines = ["", "", "WHAT FILMS NAVIN PASSED DID (aatma ki almaari, Navin, 23 November 2026). These are ways of teaching and",
             "showing, not this subject's content. Fill every [blank] with this film's own things of this subject, never with",
             "another subject's words:"]
    for kind, title in KINDS.items():
        rows = [f for f in found.values() if f["kind"] == kind]
        if rows:
            lines.append(f"- {title}: " + "; ".join(f"{f['form']} (why: {f['why']})" for f in rows))
    used = sorted({m for f in found.values() for m in re.findall(r"\[([^\]]+)\]", f["form"])})
    lines.append("- The blanks: " + "; ".join(f"[{s}] = {SLOTS.get(s, s)}" for s in used))
    if kit:
        lines.append(f"- This subject's own things ({subject}): " + "; ".join(f"{k}: {', '.join(v)}" for k, v in kit.items() if v))
    return "\n".join(lines)


def aatma_problems(film: dict, book: dict | None = None) -> list:
    """A new film measured against the films Navin passed: its camera moves no more often than theirs did, it moves no
    more things in a line, and it asks no less often (a little room either way)."""
    book = book if book is not None else almaari()
    passed = [f.get("measures") or {} for f in book.get("films") or [] if f.get("measures")]
    if not passed:
        return []
    now, out = measures(film), []
    most = lambda key: max(p.get(key, 0) for p in passed)
    least = lambda key: min(p.get(key, 0) for p in passed)
    if now["camera_moves"] > most("camera_moves") + 0.1:
        out.append(f"the camera moves on {now['camera_moves']:.0%} of lines; the films Navin passed moved it on at most "
                   f"{most('camera_moves'):.0%}: keep it still until a step is done")
    if now["movers_per_line"] > most("movers_per_line") + 0.75:
        out.append(f"{now['movers_per_line']} things move in a line on average; the passed films moved at most "
                   f"{most('movers_per_line')}: one thing at a time")
    if now["questions"] < least("questions") - 0.05:
        out.append(f"{now['questions']:.0%} of lines ask a question; the passed films asked in at least "
                   f"{least('questions'):.0%}: ask before the answer")
    return out


def page(film: dict, *, question: dict | None = None, chapter: str = "") -> str:
    """Navin's review page "Is film ki aatma": each drawer's forms in general words, this film's filling, why it works,
    where it happens, and the film's measures. A review page: it never reaches the learner's screen."""
    e = html.escape
    found = soul(film)
    m = found["measures"]
    rows = []
    for kind, title in KINDS.items():
        items = found["drawers"][kind]
        if not items:
            continue
        rows.append(f"<h2>{e(title)}</h2>")
        for f in items:
            filled = ", ".join(f"{e(k)}: <b>{e(str(v))}</b>" for k, v in (f.get("filled") or {}).items() if v)
            rows.append(f"<div class='f'><p class='g'>{e(f['form'])}</p><p class='w'>Kyun: {e(f['why'])}</p>"
                        + (f"<p class='b'>Is film mein: {filled}</p>" if filled else "")
                        + f"<p class='at'>{f['seen']} jagah: {e(', '.join(f['where']))}</p></div>")
    numbers = (f"<table><tr><td>Lines</td><td>{m['lines']}</td></tr><tr><td>Camera kitni lines par hila</td>"
               f"<td>{m['camera_moves']:.0%}</td></tr><tr><td>Har line par chalti cheezein</td><td>{m['movers_per_line']}</td></tr>"
               f"<tr><td>Sawaal wali lines</td><td>{m['questions']:.0%}</td></tr><tr><td>Naya step jodne wali lines</td>"
               f"<td>{m['steps']:.0%}</td></tr><tr><td>Vakya ke shabd (ausat / sabse lamba)</td><td>{m['words_avg']} / "
               f"{m['words_max']}</td></tr><tr><td>Rozmarra ki misaal wale shot</td><td>{m['asides']}</td></tr></table>")
    title = (question or {}).get("question") or film.get("title") or ""
    return f"""<!doctype html><html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Is film ki aatma</title><style>
:root{{--bg:#f7f5f0;--ink:#1f2428;--mut:#5d666d;--line:#d9d4c8;--ok:#2e6b45}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif;padding:16px;max-width:860px;margin:auto}}
h1{{font-size:1.3rem;margin:.2em 0}}h2{{font-size:1.05rem;margin:1.2em 0 .4em;color:var(--ok)}}
.f{{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:8px 0;background:#fff}}
.g{{font-weight:700;margin:0}}.w,.b,.at{{margin:.2em 0 0;font-size:.92rem}}.w{{color:var(--mut)}}.at{{color:var(--mut);font-size:.82rem}}
table{{border-collapse:collapse;margin-top:8px}}td{{border:1px solid var(--line);padding:5px 10px;background:#fff}}
.n{{color:var(--mut);font-size:.9rem}}</style></head><body>
<p class="n">{e(chapter)} · review page (learner ko nahi dikhta)</p>
<h1>Is film ki aatma: {e(str(title))}</h1>
<p class="n">Ye tareeke BIE ke code ne film se nikaale hain, subject ke shabd hata kar. Aap film pass karein aur haan kahein, tabhi ye
aatma ki almaari mein jayenge aur har subject ki nayi film mein lagenge. Kyun achhi lagi, apne shabdon mein bata dein; wo bhi saath jayega.</p>
{''.join(rows)}<h2>Film ka naap</h2>{numbers}</body></html>"""


def lock(book: dict, film: dict, *, qid: str, run: str, by: str, words: str = "", only: list | None = None) -> dict:
    """The almaari with this film's forms locked after Navin's yes (``tools/lock_aatma.py``): its forms in general words
    (blanks, no subject word), why each works, his own words, the film's measures, the run and who locked it."""
    book = copy.deepcopy(book)
    found = forms(film)
    if only:
        found = [f for f in found if f["id"] in only]
    entry = {"qid": qid, "run": run, "by": by, "words": words, "measures": measures(film),
             "forms": [{"id": f["id"], "kind": f["kind"], "form": f["form"], "why": f["why"],
                        "example": {k: v for k, v in (f.get("filled") or {}).items() if v}} for f in found]}
    book["films"] = [f for f in book.get("films") or [] if not (f.get("qid") == qid and f.get("run") == run)] + [entry]
    book["version"] = int(book.get("version") or 0) + 1
    return book
