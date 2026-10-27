"""Navin's mixed-script narration (rule S2-04, decided 23 October 2026).

A script beat is written in mixed script: Hindi words in Devanagari, English words (above all the book's
technical terms) in Roman, as in "आज हम tissue के बारे में पढ़ेंगे". A Hindi word that is not a simple everyday
word (``rulebook/simple_hindi.json``, versioned; Navin adds words) gets its English word in brackets right
after it: "सतह (surface)". Subtitles and the screen show the bracket; the voice says "सतह, यानी surface".

The checks here never ask for an English term in Devanagari or a Hindi word in Roman; they only ask for the
bracket after a difficult Hindi word, and for common Hindi words written in Roman ("hai", "aur") to be
written in Devanagari. Brackets belong only on genuinely difficult words and never inside an idiom or a fixed
phrase (Navin, after the tissue run): ``clean`` removes a bracket after an everyday word or inside a fixed phrase
("आम तौर (usually) पर" becomes "आम तौर पर"), so the maker is never sent back for one.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).resolve().parent / "rulebook" / "simple_hindi.json"
WORD = re.compile(r"[ऀ-ॣ०-ॿ]+")          # Devanagari letters and signs, not the danda
GLOSS = re.compile(r"([ऀ-ॣ०-ॿ]+)\s*\(\s*([^()]*?)\s*\)")
ROMAN_GLOSS = re.compile(r"^[A-Za-z][A-Za-z0-9 '\-/]*$")
ROMAN_WORD = re.compile(r"[A-Za-z]+")
MARKER = re.compile(r"^(?:[a-eA-E]|[ivx]{1,4}|\d{1,2})$")       # "(a)", "(ii)", "(3)": an option or a list mark, not a gloss
# Common Hindi words that belong in Devanagari when they appear in Roman. Words that are also English
# ("to", "me", "is") are left out on purpose.
ROMAN_HINDI = {"hai", "hain", "ka", "ki", "ke", "ko", "se", "mein", "aur", "yeh", "kya", "kyun", "kyon", "kaise", "nahi",
               "nahin", "hum", "aap", "tum", "toh", "bhi", "jab", "tab", "phir", "lekin", "kyunki", "matlab", "yani"}


# The oblique forms whose dictionary form changes its last vowel (Task 045d job B2): पहिए / पहियों → पहिया, झाड़ुओं → झाड़ू.
REWRITES = (("ियों", "िया"), ("िए", "िया"), ("िये", "िया"), ("ुओं", "ू"), ("ुएं", "ू"), ("ुए", "ू"), ("ुओ", "ू"))
# An ordinal ending written after a digit ("10वाँ", "2री"): part of the number, not a Hindi word.
ORDINAL = frozenset({"वां", "वीं", "वें", "वा", "वी", "वे", "रा", "री", "रे", "था", "थी", "थे", "ला", "ली", "ले"})


def normal(word: str) -> str:
    """Spelling variants compare equal: no nukta, chandrabindu as anusvara."""
    return word.replace("़", "").replace("ँ", "ं")


def _stems(stem: str):
    """The dictionary forms a stem may come from: itself, the verb (+ना), the noun or adjective (+ा, +ी, +े), and the
    plain verb of a causative (पहुंचा → पहुंच, रखवा → रख)."""
    yield from (stem, stem + "ना", stem + "ा", stem + "ी", stem + "े")
    if stem.endswith("वा") and len(stem) > 3:
        yield from (stem[:-2], stem[:-2] + "ना")
    if stem.endswith("ा") and len(stem) > 2:
        yield from (stem[:-1], stem[:-1] + "ना")


@dataclass(frozen=True)
class SimpleHindi:
    version: str
    words: frozenset
    suffixes: tuple
    phrases: tuple = ()
    technical: tuple = ()      # ((textbook Hindi word, the book's English term), ...), longest first

    def is_simple(self, word: str) -> bool:
        w = normal(word)
        if w in self.words or w + "ना" in self.words:      # a word, or a bare verb stem (रुक, हट, घुमा)
            return True
        for end, base in REWRITES:
            if w.endswith(end) and len(w) > len(end) and w[:-len(end)] + base in self.words:
                return True
        for suffix in self.suffixes:
            if w.endswith(suffix) and len(w) > len(suffix):
                if any(stem in self.words for stem in _stems(w[:-len(suffix)])):
                    return True
        return False

    @property
    def phrase_regex(self):
        return _phrase_regex(self.phrases)


@lru_cache(maxsize=4)
def _phrase_regex(phrases: tuple):
    """One pattern for every fixed phrase, tolerant of nukta, chandrabindu, a hyphen or space between its words and a
    bracket wrongly put inside it ("आम तौर (usually) पर")."""
    def letters(word):
        return "".join("[ंँ]" if ch == "ं" else re.escape(ch) + "़?" for ch in word)
    alternatives = []
    for phrase in sorted(phrases, key=len, reverse=True):
        parts = [letters(w) for w in re.split(r"[\s\-]+", phrase) if w]
        alternatives.append(r"(?:\s*\([^()]*\))?[\s\-]+".join(parts))
    return re.compile("(?<![ऀ-ॿ])(?:" + "|".join(alternatives) + ")(?![ऀ-ॣ०-ॿ])") if alternatives else None


@lru_cache(maxsize=2)
def load(path: str = str(PATH)) -> SimpleHindi:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    suffixes = sorted({normal(s) for s in data["suffixes"]}, key=len, reverse=True)
    technical = sorted(((normal(k), v) for k, v in (data.get("technical") or {}).items()), key=lambda kv: -len(kv[0]))
    return SimpleHindi(str(data["version"]), frozenset(normal(w) for w in data["words"]), tuple(suffixes),
                       tuple(normal(p) for p in data.get("fixed_phrases") or []), tuple(technical))


def term_stem(word: str) -> str:
    """One stem for an English term and its plural ("cells" → "cell", "glands" → "gland", "tissues" → "tissue")."""
    w = (word or "").lower()
    if w.endswith("ies") and len(w) >= 5:
        return w[:-3] + "y"
    if w.endswith(("ses", "xes", "zes", "ches", "shes")) and len(w) >= 5:
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) >= 4:
        return w[:-1]
    return w


def english_terms(text: str) -> frozenset:
    """The stems of the English words of a book text (the terms the learner must hear in Roman; S1-15, S2-04)."""
    return frozenset(term_stem(w) for w in ROMAN_WORD.findall(text or "") if len(w) >= 3)


def technical_words(say: str, simple: SimpleHindi | None = None, book_terms=None) -> list:
    """[(Hindi word as written, the book's English term)] for the textbook translations in ``say`` (ऊतक → tissue): the
    learner hears the book's own English term in Roman, so these go back whether or not a bracket follows (Task 045d).
    With ``book_terms`` (``english_terms`` of the book's text) only the translations of terms the book itself uses count:
    the Money chapter's पदार्थ (substance) is plain Hindi where the book never says "substance" (27 October 2026)."""
    simple = simple or load()
    found, seen = [], set()
    text = normal(say or "")
    for hindi, english in simple.technical:
        if book_terms is not None and not any(term_stem(w) in book_terms for w in ROMAN_WORD.findall(english)):
            continue
        if " " in hindi:
            if hindi in text and hindi not in seen:
                found.append((hindi, english)); seen.add(hindi); seen.update(hindi.split())   # its words are not counted again
            continue
        for word in WORD.findall(say or ""):
            w = normal(word)
            if (w == hindi or (w.startswith(hindi) and w[len(hindi):] in simple.suffixes)) and w not in seen:
                found.append((word, english)); seen.add(w)
    return found


def phrase_spans(say: str, simple: SimpleHindi | None = None) -> list:
    """(start, end) of every fixed phrase in a beat."""
    simple = simple or load()
    regex = simple.phrase_regex
    return [(m.start(), m.end()) for m in regex.finditer(say)] if regex else []


def difficult_words(say: str, simple: SimpleHindi | None = None) -> list:
    """Hindi words of a beat that are not simple, not inside a fixed phrase, and have no English word in brackets right
    after them."""
    simple = simple or load()
    glossed = {m.start(1) for m in GLOSS.finditer(say)}
    skip = [(m.start(), m.end()) for m in re.finditer(r"\([^()]*\)", say)] + phrase_spans(say, simple)
    found = []
    for m in WORD.finditer(say):
        if m.start() in glossed or any(a <= m.start() < b for a, b in skip):
            continue
        if m.start() > 0 and say[m.start() - 1].isdigit() and normal(m.group(0)) in ORDINAL:
            continue                                      # "10वाँ": the number's ending
        if not simple.is_simple(m.group(0)) and m.group(0) not in found:
            found.append(m.group(0))
    return found


def clean(say: str, simple: SimpleHindi | None = None) -> tuple:
    """(say, removed): the beat without brackets inside a fixed phrase or after an everyday word ("मुख्य (main)" →
    "मुख्य"), and the brackets removed. A bracket after a difficult word stays."""
    simple = simple or load()
    removed = []
    spans = phrase_spans(say, simple)

    def drop(m):
        word, inner = m.group(1), m.group(2)
        inside = any(a <= m.start(1) and m.end() <= b for a, b in spans)
        if ROMAN_GLOSS.match(inner) and not MARKER.match(inner) and (inside or simple.is_simple(word)):
            removed.append(f"{word} ({inner})")
            return word
        return m.group(0)

    out = GLOSS.sub(drop, say)
    if len(out) != len(say):                    # a bracket inside a phrase that does not follow its last word
        for a, b in sorted(phrase_spans(out, simple), reverse=True):
            inner = re.findall(r"\s*\(([^()]*)\)", out[a:b])
            if inner:
                removed += [f"({x})" for x in inner]
                out = out[:a] + re.sub(r"\s*\([^()]*\)", "", out[a:b]) + out[b:]
    else:
        for a, b in sorted(spans, reverse=True):
            inner = re.findall(r"\s*\(([^()]*)\)", out[a:b])
            if inner:
                removed += [f"({x})" for x in inner]
                out = out[:a] + re.sub(r"\s*\([^()]*\)", "", out[a:b]) + out[b:]
    return re.sub(r" {2,}", " ", out), removed


def bracket_problems(say: str) -> list:
    """A bracket after a Hindi word must hold its English word in Roman. Option and list marks ("(a)", "(ii)") and
    brackets after English words are not glosses and are left alone."""
    problems = []
    for m in re.finditer(r"\(([^()]*)\)", say):
        before = say[:m.start()].rstrip()
        inner = m.group(1).strip()
        if MARKER.match(inner) or not before or not WORD.search(before[-1]):
            continue
        if not ROMAN_GLOSS.match(inner):
            problems.append(f"({inner}) must hold the English word in Roman letters")
    return problems


def roman_hindi(say: str) -> list:
    return sorted({w for w in ROMAN_WORD.findall(say) if w.lower() in ROMAN_HINDI})


def voice_text(say: str) -> str:
    """What the voice says: "सतह (surface)" becomes "सतह, यानी surface"."""
    return GLOSS.sub(lambda m: f"{m.group(1)}, यानी {m.group(2)}" if ROMAN_GLOSS.match(m.group(2)) else m.group(0), say)


def subtitle_text(say: str) -> str:
    """What the screen and the subtitles show: the beat as written, brackets included."""
    return say


def prefix_text(simple: SimpleHindi | None = None) -> str:
    """The bracket rule for a fixed task prefix (the same bytes for every card of a run). The word list itself stays in
    code: it has thousands of words and the maker does not need it to write natural Hinglish."""
    simple = simple or load()
    return (f"Brackets (word list {simple.version}): use everyday spoken Hindi freely, without brackets (मुख्य, वापस, बराबर, "
            "आसपास, इस्तेमाल, करके, जिससे ...). Only a genuinely difficult Hindi word (formal, literary or technical) gets its "
            "English word in brackets right after it, for example \"सतह (surface)\", \"घर्षण (friction)\", \"सघन (dense)\"; better "
            "still, use the book's English term or a simpler Hindi word. Never put a bracket inside an idiom or a fixed phrase: "
            "\"आम तौर पर\", not \"आम तौर (usually) पर\"; \"नहीं के बराबर\", not \"नहीं के बराबर (equal to)\". BIE's code removes a "
            "bracket after an everyday word and asks for one only after a Hindi word it does not know as everyday.")
