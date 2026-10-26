"""The teaching soul (Task 045d; Navin's verdict on the tissue scripts, 24 October 2026).

Navin's verdict: the scripts restated the book ("epithelium absorptive aur secretive surfaces par milta hai")
instead of opening it (what an absorptive surface is, with an everyday example, and why epithelium is found
there). BIE is the link between the learner and the book, like a teacher: the book is the base, and BIE carries
its text, easy or hard, into the learner's mind. Never just read the book line out.

This module holds what every section shares for that:

- the unpack of a teachable item (Section 1): its terms with a plain meaning and an everyday image, a why chain
  that starts from a need and names its basis at every step, an example or place, the consequence, the visual
  verb and the level extra; ``unpack_problems`` is BIE's code check on it;
- the teacher example bank (``rulebook/teacher_examples.json``): the nine methods of real teachers, as fixed
  prefix text for the makers;
- the script checks: "dohraav pakad" (a beat whose words are the book's and that opens nothing goes back),
  clipped verbless sentences, a question before every new topic, no duplicate recaps;
- ``dohraav_share``: the measure Navin asked for, the share of beats that only restate the book;
- the wording rule W-01 (Task 046, Navin, 26 October 2026): the narration never points at the book ("book के अनुसार",
  "किताब कहती है", "book says", "page पर" ...); the word list lives in ``rulebook/visual_grammar.json`` and
  ``book_pointing`` / ``wording_problems`` apply it.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from .common import S, arr as _arr, obj as _obj

TEACHER_PATH = Path(__file__).resolve().parent / "rulebook" / "teacher_examples.json"
GRAMMAR_PATH = Path(__file__).resolve().parent / "rulebook" / "visual_grammar.json"
DEVANAGARI = re.compile(r"[ऀ-ॿ]")

UNPACK_SCHEMA = _obj({
    "terms": _arr(_obj({"term": S, "plain_meaning": S, "everyday_image": S})),
    "why_chain": _arr(_obj({"step": S, "basis": {"type": "string", "enum": ["book", "standard"]}})),
    "example_or_place": S,
    "consequence": S,
    "visual_verb": S,
    "level_extra": S,
})
EMPTY_UNPACK = {"terms": [], "why_chain": [], "example_or_place": "", "consequence": "", "visual_verb": "", "level_extra": ""}

# What opens a book line in a spoken beat: a term opened ("yaani"), a why, an example, a contrast, a memory beat.
YAANI = re.compile(r"यानी|यानि|मतलब|अर्थात|(?<![a-z])(?:yaani|yani|matlab)(?![a-z])", re.IGNORECASE)
WHY = re.compile(r"क्योंकि|क्यूंकि|इसलिए|इसीलिए|इसलिये|ताकि|वजह|कारण|वरना|नहीं तो|क्यों|इससे|इसी से|तभी"
                 r"|(?<![a-z])(?:kyunki|kyonki|isliye|isiliye|taaki|because|varna|kyon|kyun)(?![a-z])", re.IGNORECASE)
EXAMPLE = re.compile(r"जैसे|जैसा|जैसी|की तरह|मिसाल|उदाहरण|मान लो|मान लीजिए|सोचो|सोचिए|ज़रा देखो"
                     r"|(?<![a-z])(?:jaise|jaisa|jaisi|ki tarah|for example|example|maan lo|socho)(?![a-z])", re.IGNORECASE)
# The contrast of Navin's teacher bank is also "what it is not" (job B resume: "यह सिर्फ सख्त ढाँचा नहीं है").
CONTRAST = re.compile(r"लेकिन|जबकि|फ़र्क|फर्क|बल्कि|के उलट|(?<![ऀ-ॿ])(?:न|ना) कि(?![ऀ-ॿ])"
                      r"|(?:सिर्फ|केवल)[^।?!.]{1,60}?नहीं|नहीं[^।?!.]{0,12}(?:सिर्फ|केवल)"
                      r"|(?<![a-z])(?:lekin|jabki|fark|farq|unlike|whereas|not just|not only)(?![a-z])", re.IGNORECASE)
# The memory beat of Navin's teacher bank: the exam's "yaad rakhna", the trick.
MEMORY = re.compile(r"याद\s*रख|ट्रिक|(?<![a-z])(?:yaad\s*rakh\w*|trick|mnemonic)(?![a-z])", re.IGNORECASE)
MARKERS = (("yaani", YAANI), ("why", WHY), ("example", EXAMPLE), ("contrast", CONTRAST), ("memory", MEMORY))

ENGLISH_WORD = re.compile(r"[A-Za-z][A-Za-z\-]{3,}")
STOP = frozenset("""with from that this these those their there where when what which while also into than then them they
have been being other some such each both more most very often only same into about above below under over after before
between through during because called known types kinds type kind like such there here your they them will would could
should shall must might many much even ever just does done make made makes making given gives give take taken takes used
uses using form forms formed found find show shows shown seen sees well within without upon along among across toward
yaani jaise kyunki isliye lekin matlab socho dekho samjho hota hoti hote karta karti karte raha rahi rahe wala wali wale
nahi nahin bhi aur yeh woh kya kyon kaise kahan kaun jisme jisse isme usme unka unki unke iska iski iske""".split())
HINDI_VERB_WORDS = frozenset("""है हैं था थे थी थीं हो हूँ हूं हुआ हुई हुए रहा रही रहे सकता सकती सकते चाहिए लो दो जाओ आओ देखो समझो सोचो रखो
बताओ बनाओ करो कहो पढ़ो लिखो याद गया गई गए किया की किए दिया दी दिए लिया ली लिए मिला मिली मिले होगा होगी होंगे रखना बनता बनती बनते
मिलता मिलती मिलते आता आती आते जाता जाती जाते रहता रहती रहते कहते कहलाता कहलाती कहलाते""".split())
HINDI_VERB_SUFFIXES = ("ता", "ती", "ते", "ना", "ने", "नी", "गा", "गी", "गे", "ें", "िए", "िये", "ाओ", "ो", "ए", "ये", "या", "ई")
SENTENCE_SPLIT = re.compile(r"(?<=[।?!.])\s+")


# ---------------------------------------------------------------- the teacher example bank

@lru_cache(maxsize=2)
def load_teacher(path: str = str(TEACHER_PATH)) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def opening_steps_text(bank: dict | None = None) -> str:
    bank = bank or load_teacher()
    return "\n".join(f"{n}) {step}" for n, step in enumerate(bank["opening_steps"], 1))


def teacher_text(bank: dict | None = None, *, ids=None) -> str:
    """The teacher methods as fixed prefix text: name, when, one paraphrased example each."""
    bank = bank or load_teacher()
    lines = [f"How real teachers open a book line (teacher example bank {bank['version']}; use these ways, in your own words):"]
    for method in bank["methods"]:
        if ids is not None and method["id"] not in ids:
            continue
        lines.append(f"- {method['name']} ({method['when']}): {method['example']}")
    return "\n".join(lines)


# ---------------------------------------------------------------- the unpack (Section 1)

def unpack_elements(unpack: dict | None) -> int:
    """How many opening elements an item's unpack carries (a term, a why step, an example or place, a consequence)."""
    unpack = unpack or {}
    return (len(unpack.get("terms") or []) + len(unpack.get("why_chain") or [])
            + bool((unpack.get("example_or_place") or "").strip()) + bool((unpack.get("consequence") or "").strip()))


def unpack_problems(item: dict, *, profile=None, language: str = "Hinglish") -> list:
    """S1-15: every teachable item is opened; every why step names its basis; the plain meaning is for the learner."""
    problems = []
    iid = item.get("item_id", "?")
    unpack = item.get("unpack") or {}
    if unpack_elements(unpack) == 0:
        problems.append(f"item {iid}: unpack is empty; open the book line with at least one of: a term (plain meaning and an "
                        "everyday image), a why step from a need, an example or place, a consequence (S1-15)")
    hindi = language.strip().lower() in ("hinglish", "hindi")
    if hindi:
        from . import hinglish
        texts = [t.get(k) or "" for t in unpack.get("terms") or [] for k in ("plain_meaning", "everyday_image")]
        texts += [unpack.get(k) or "" for k in ("example_or_place", "consequence", "level_extra")]
        found = {}
        for text in texts:
            for word, english in hinglish.technical_words(text):
                found.setdefault(english, word)
        if found:
            pairs = ", ".join(f"{word} → {english}" for english, word in list(found.items())[:5])
            problems.append(f"item {iid}: the unpack uses textbook Hindi for the book's own terms ({pairs}); the learner hears the book's "
                            "English term in Roman, never its Hindi translation (S1-15)")
    for term in unpack.get("terms") or []:
        if not (term.get("term") or "").strip() or not (term.get("plain_meaning") or "").strip():
            problems.append(f"item {iid}: a term needs its term and its plain_meaning (S1-15)")
        elif hindi and not DEVANAGARI.search(term["plain_meaning"]):
            problems.append(f"item {iid}: the plain_meaning of {term['term']!r} is for the learner: write it in simple Hindi "
                            "(Devanagari), with the English term in Roman (S1-15)")
        if (term.get("plain_meaning") or "").strip().lower() == (term.get("term") or "").strip().lower():
            problems.append(f"item {iid}: the plain_meaning of {term['term']!r} only repeats the term (S1-15)")
    for step in unpack.get("why_chain") or []:
        if not (step.get("step") or "").strip():
            problems.append(f"item {iid}: a why step is empty (S1-15)")
        if step.get("basis") not in ("book", "standard"):
            problems.append(f"item {iid}: every why step names its basis, 'book' or 'standard' (S1-15)")
    if profile is not None:
        most = profile.why_steps[1]
        if len(unpack.get("why_chain") or []) > most:
            problems.append(f"item {iid}: the why chain has {len(unpack['why_chain'])} steps; the {profile.name} level opens at most "
                            f"{most} (a longer chain is a side-track; S1-15)")
        if not profile.new_terms and unpack.get("terms"):
            problems.append(f"item {iid}: the {profile.name} level adds no new terms; name them without opening them (S1-15)")
    return problems


def unpack_lines(unpack: dict | None, indent: str = "  ") -> list:
    """The unpack as prompt lines for the script maker (what the teacher layer already opened)."""
    unpack = unpack or {}
    lines = []
    for term in unpack.get("terms") or []:
        lines.append(f"{indent}term | {term['term']} | yaani {term['plain_meaning']} | image: {term.get('everyday_image', '')}")
    if unpack.get("why_chain"):
        lines.append(f"{indent}why | " + " → ".join(f"{s['step']} [{s['basis']}]" for s in unpack["why_chain"]))
    for key, label in (("example_or_place", "example or place"), ("consequence", "consequence"), ("visual_verb", "visual"),
                       ("level_extra", "level extra")):
        if (unpack.get(key) or "").strip():
            lines.append(f"{indent}{label} | {unpack[key].strip()}")
    return lines


def unpack_short(unpack: dict | None, limit: int = 90) -> str:
    """One short cell for the naksha: the terms opened and what else the unpack carries."""
    unpack = unpack or {}
    bits = []
    terms = [t["term"] for t in unpack.get("terms") or [] if t.get("term")]
    if terms:
        bits.append("terms: " + ", ".join(terms))
    if unpack.get("why_chain"):
        bits.append(f"why {len(unpack['why_chain'])}")
    for key, tag in (("example_or_place", "eg"), ("consequence", "cons"), ("visual_verb", "visual")):
        if (unpack.get(key) or "").strip():
            bits.append(tag)
    text = "; ".join(bits)
    return text if len(text) <= limit else text[:limit - 1].rstrip(" ,;") + "…"


# ---------------------------------------------------------------- the script checks (Section 2)

def markers(say: str) -> list:
    return [name for name, regex in MARKERS if regex.search(say or "")]


def content_words(text: str) -> set:
    return {w.lower() for w in ENGLISH_WORD.findall(text or "") if w.lower() not in STOP}


def book_words(items_by_id: dict, item_ids) -> set:
    """The content words of the book lines a beat covers (an item and its parent: a table row and its table)."""
    words = set()
    for iid in item_ids or []:
        item = items_by_id.get(iid)
        if not item:
            continue
        words |= content_words(item.get("content", ""))
        parent = items_by_id.get(item.get("parent_item_id") or "")
        if parent:
            words |= content_words(parent.get("content", ""))
    return words


def overlap(say: str, source_words: set) -> tuple:
    """(share, count): the share of the beat's English content words that are the book's, and how many there are."""
    mine = content_words(say)
    if not mine:
        return 0.0, 0
    return round(len(mine & source_words) / len(mine), 3), len(mine)


RESTATING_SHARE = 0.6      # at least this share of the beat's content words are the book's
RESTATING_WORDS = 6        # and the beat has at least this many content words (shorter beats say too little to restate)
JUDGED_PURPOSES = ("explain", "example", "compare", "process_walkthrough", "misconception", "story", "analogy", "exam_tip",
                   "prerequisite", "transition")


def restating_beats(beats, items_by_id: dict) -> list:
    """[(beat id, share, count, markers)] for the beats that only restate the book: the book's words, nothing opened."""
    found = []
    for beat in beats or []:
        if beat.get("purpose") not in JUDGED_PURPOSES or not beat.get("covers_item_ids"):
            continue
        share, count = overlap(beat.get("say", ""), book_words(items_by_id, beat["covers_item_ids"]))
        opened = markers(beat.get("say", ""))
        if share >= RESTATING_SHARE and count >= RESTATING_WORDS and not opened:
            found.append((beat["beat_id"], share, count, opened))
    return found


def restatement_problems(beats, items_by_id: dict) -> list:
    """Dohraav pakad (S2-07): a beat whose English words are the book line's and that opens nothing goes back."""
    return [f"beat {bid}: {share:.0%} of its {count} content words are the book's own and it opens nothing: after a book line, "
            "open a term (yaani + an everyday image), give the why from a need, or an example; never just read the line out (S2-07)"
            for bid, share, count, _ in restating_beats(beats, items_by_id)]


def dohraav_share(beats, items_by_id: dict) -> dict:
    """Navin's measure: of the beats that teach book items, the share that only restate the book."""
    judged = [b for b in beats or [] if b.get("purpose") in JUDGED_PURPOSES and b.get("covers_item_ids")]
    restating = restating_beats(judged, items_by_id)
    opened = sum(1 for b in judged if markers(b.get("say", "")))
    return {"beats": len(beats or []), "judged": len(judged), "restating": len(restating),
            "share": round(len(restating) / len(judged), 3) if judged else 0.0,
            "opened": opened, "opened_share": round(opened / len(judged), 3) if judged else 0.0,
            "restating_beats": [bid for bid, _, _, _ in restating]}


HINDI_LETTERS = re.compile(r"[\u0900-\u0963\u0970-\u097f]+")     # Devanagari without the danda (।, ॥) and the digits


NEGATION_END = re.compile(r"नहीं\s*[।.!]*\s*$")       # "पूरा bundle 1 cell नहीं।": the dropped copula is spoken Hindi, not a note


def _has_verb(sentence: str) -> bool:
    if NEGATION_END.search(sentence):
        return True
    for token in HINDI_LETTERS.findall(sentence):
        if token in HINDI_VERB_WORDS or token.endswith(HINDI_VERB_SUFFIXES):
            return True
    return bool(re.search(r"(?<![a-z])(?:is|are|was|were|has|have|had|can|does|do|means?)(?![a-z])", sentence, re.IGNORECASE))


def clipped_sentences(say: str, min_words: int = 5) -> list:
    """Sentences spoken like notes, not like a teacher: five words or more, in Hindi, no verb, not a question and not the
    short repeat after one ("Irregular walls. Kaisi? Irregular." is a teacher's beat and stays)."""
    found, previous_question = [], False
    for sentence in SENTENCE_SPLIT.split((say or "").strip()):
        words = sentence.split()
        question = "?" in sentence
        if (len(words) >= min_words and HINDI_LETTERS.search(sentence) and not question and not previous_question
                and not YAANI.search(sentence) and not _has_verb(sentence)):      # "X matlab Y nahin" opens a term; it stays
            found.append(sentence.strip())
        previous_question = question
    return found


def clipped_problems(beats) -> list:
    problems = []
    for beat in beats or []:
        for sentence in clipped_sentences(beat.get("say", ""))[:2]:
            problems.append(f"beat {beat['beat_id']}: \"{sentence[:70]}\" is a clipped note without a verb; speak complete sentences "
                            "like a teacher (S2-07)")
    return problems


def concept_groups(card_parts) -> dict:
    """{concept or prerequisite id: [part ids]} in card order ("c07.1", "c07.q" → "c07"; "pre2" → "pre2")."""
    groups = {}
    for part in card_parts or []:
        pid = part["part_id"]
        groups.setdefault(pid.split(".")[0], []).append(pid)
    return groups


def opening_problems(beats, card_parts) -> list:
    """S2-07: a new topic opens with a question about something the learner can see, then the name."""
    problems = []
    beats = list(beats or [])
    for group, parts in concept_groups(card_parts).items():
        first = next((i for i, b in enumerate(beats) if b.get("part_id") in parts), None)
        if first is None:
            continue
        if "?" in beats[first].get("say", "") or (first > 0 and "?" in beats[first - 1].get("say", "")):
            continue
        problems.append(f"beat {beats[first]['beat_id']}: the topic {group} opens without a question; start it with a question about "
                        "something the learner can see, then the name (S2-07)")
    return problems


def recap_problems(beats) -> list:
    """S2-07: no duplicate recaps: at most one recap beat per part and one closing recap for the video."""
    problems = []
    per_part = {}
    for beat in beats or []:
        if beat.get("purpose") == "recap":
            per_part.setdefault(beat.get("part_id") or "", []).append(beat["beat_id"])
    for pid, ids in per_part.items():
        if len(ids) > 1:
            where = f"part {pid}" if pid else "the video's closing"
            problems.append(f"beats {', '.join(ids[:6])} are all recaps of {where}; one recap is enough, say the rest once (S2-07)")
    return problems


def skipped_step_problems(parts, card_parts, types) -> tuple:
    """(problems, {part id: {step: why}}): the steps a script skips with a reason (a flexible pattern, S2-07)."""
    problems, skipped = [], {}
    kinds = {p["part_id"]: p["type"] for p in card_parts or []}
    for part in parts or []:
        pid = part.get("part_id")
        pattern = types.pattern(kinds.get(pid, ""))
        entries = part.get("skipped_steps") or []
        if not entries:
            continue
        if len(entries) > len(pattern) // 2:
            problems.append(f"part {pid}: {len(entries)} of {len(pattern)} pattern steps skipped; a part may skip at most half, each "
                            "with a real reason (S2-07)")
        for entry in entries:
            step, why = entry.get("step"), (entry.get("why") or "").strip()
            if not isinstance(step, int) or not 1 <= step <= len(pattern):
                problems.append(f"part {pid}: skipped step {step!r} is not a step of its pattern (1-{len(pattern)})")
                continue
            if len(why.split()) < 3:
                problems.append(f"part {pid}: skipping step {step} needs a real reason, not {why!r} (S2-07)")
                continue
            skipped.setdefault(pid, {})[step] = why
    return problems, skipped


# ---------------------------------------------------------------- the wording rule W-01 (Task 046)

WORDING_GROUPS = ("hindi", "hinglish", "english", "mixed")


@lru_cache(maxsize=2)
def load_wording(path: str = str(GRAMMAR_PATH)) -> dict:
    """The W-01 word list of the visual grammar rulebook: {"version", "groups": {group: [compiled regex, ...]}}."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    words = data["wording"]["W-01"]
    groups = {}
    for group in WORDING_GROUPS:
        groups[group] = [re.compile(_bounded(pattern), re.IGNORECASE) for pattern in words.get(group) or []]
    return {"version": data["version"], "groups": groups, "decided": words.get("decided", "")}


def _bounded(pattern: str) -> str:
    """A word-list pattern bounded by letters of its own script: Devanagari letters around a Devanagari start or end,
    Roman letters around a Roman one, so "kitaab" is not found inside "kitaabghar" and "पृष्ठ" not inside "पृष्ठभूमि"."""
    first, last = pattern[0], pattern[-1]
    letters = r"\u0900-\u0963\u0970-\u097f"            # Devanagari letters and signs, not the danda (।) or the digits
    head = f"(?<![{letters}])" if DEVANAGARI.match(first) else (r"(?<![a-z])" if first.isalpha() else "")
    tail = f"(?![{letters}])" if DEVANAGARI.match(last) else (r"(?![a-z])" if last.isalpha() else "")
    return head + pattern + tail


def book_pointing(say: str, wording: dict | None = None) -> list:
    """[(sentence, matched words, group)] for every sentence of ``say`` that points at the book (W-01)."""
    wording = wording or load_wording()
    found = []
    for sentence in SENTENCE_SPLIT.split((say or "").strip()):
        for group, patterns in wording["groups"].items():
            hit = next((m for p in patterns for m in [p.search(sentence)] if m), None)
            if hit:
                found.append((sentence.strip(), hit.group(0), group))
                break
    return found


def wording_problems(beats, wording: dict | None = None) -> list:
    """W-01: a beat whose sentence points at the book goes back; BIE says the fact itself, like a teacher."""
    problems = []
    for beat in beats or []:
        for sentence, words, _ in book_pointing(beat.get("say", ""), wording)[:2]:
            problems.append(f"beat {beat['beat_id']}: \"{sentence[:80]}\" points at the book ({words!r}); BIE teaches as a teacher: "
                            "say the fact itself, never 'book ke anusar', 'kitaab kehti hai', 'page par' or the like (W-01)")
    return problems


def wording_hits(beats, wording: dict | None = None) -> list:
    """Every W-01 hit of a script as rows for a report: {beat_id, sentence, words, group}."""
    return [{"beat_id": beat["beat_id"], "sentence": sentence, "words": words, "group": group}
            for beat in beats or [] for sentence, words, group in book_pointing(beat.get("say", ""), wording)]

