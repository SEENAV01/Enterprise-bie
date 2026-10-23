"""Navin's mixed-script narration (rule S2-04, decided 23 October 2026).

A script beat is written in mixed script: Hindi words in Devanagari, English words (above all the book's
technical terms) in Roman, as in "आज हम tissue के बारे में पढ़ेंगे". A Hindi word that is not a simple everyday
word (``rulebook/simple_hindi.json``, versioned; Navin adds words) gets its English word in brackets right
after it: "सतह (surface)". Subtitles and the screen show the bracket; the voice says "सतह, यानी surface".

The checks here never ask for an English term in Devanagari or a Hindi word in Roman; they only ask for the
bracket after a difficult Hindi word, and for common Hindi words written in Roman ("hai", "aur") to be
written in Devanagari.
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
# Common Hindi words that belong in Devanagari when they appear in Roman. Words that are also English
# ("to", "me", "is") are left out on purpose.
ROMAN_HINDI = {"hai", "hain", "ka", "ki", "ke", "ko", "se", "mein", "aur", "yeh", "kya", "kyun", "kyon", "kaise", "nahi",
               "nahin", "hum", "aap", "tum", "toh", "bhi", "jab", "tab", "phir", "lekin", "kyunki", "matlab", "yani"}


def normal(word: str) -> str:
    """Spelling variants compare equal: no nukta, chandrabindu as anusvara."""
    return word.replace("़", "").replace("ँ", "ं")


@dataclass(frozen=True)
class SimpleHindi:
    version: str
    words: frozenset
    suffixes: tuple

    def is_simple(self, word: str) -> bool:
        w = normal(word)
        if w in self.words:
            return True
        for suffix in self.suffixes:
            if w.endswith(suffix) and len(w) > len(suffix):
                stem = w[:-len(suffix)]
                if stem in self.words or stem + "ना" in self.words or stem + "ा" in self.words:
                    return True
        return False


@lru_cache(maxsize=2)
def load(path: str = str(PATH)) -> SimpleHindi:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    suffixes = sorted({normal(s) for s in data["suffixes"]}, key=len, reverse=True)
    return SimpleHindi(str(data["version"]), frozenset(normal(w) for w in data["words"]), tuple(suffixes))


def difficult_words(say: str, simple: SimpleHindi | None = None) -> list:
    """Hindi words of a beat that are not simple and have no English word in brackets right after them."""
    simple = simple or load()
    glossed = {m.start(1) for m in GLOSS.finditer(say)}
    inside = [(m.start(), m.end()) for m in re.finditer(r"\([^()]*\)", say)]
    found = []
    for m in WORD.finditer(say):
        if m.start() in glossed or any(a < m.start() < b for a, b in inside):
            continue
        if not simple.is_simple(m.group(0)) and m.group(0) not in found:
            found.append(m.group(0))
    return found


def bracket_problems(say: str) -> list:
    """A bracket must follow a Hindi word and hold its English word in Roman."""
    problems = []
    for m in re.finditer(r"\(([^()]*)\)", say):
        before = say[:m.start()].rstrip()
        inner = m.group(1).strip()
        if not ROMAN_GLOSS.match(inner):
            problems.append(f"({inner}) must hold the English word in Roman letters")
        elif not before or not WORD.search(before[-1]):
            problems.append(f"({inner}) must come right after the Hindi word it explains")
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
    """The rule and the word list for a fixed task prefix (the same bytes for every card of a run)."""
    simple = simple or load()
    return (f"Simple everyday Hindi words (list {simple.version}); any other Hindi word gets its English word in brackets "
            f"right after it, for example \"सतह (surface)\":\n" + " ".join(sorted(simple.words)))
