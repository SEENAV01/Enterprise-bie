"""Level: how deep the teacher layer opens the book (Task 045d; Navin, 24 October 2026).

BIE is the link between the learner and the book. How much it opens every line (which terms, how many why
steps, which exam beats) follows the level in ``rulebook/level_profiles.json``: school, neet_11_12, upsc_pcs or
revision. The level comes from two places and they must agree:

1. the course setting: ``course.level`` when it is set, else the words of ``learners`` and ``exam``
   ("UPSC", "NEET", "Class 9" ...), else the file's default;
2. the book itself: its text is read for its band (school, senior_secondary, exam_general, advanced) from explicit
   markers ("Class IX", "NEET", "MBBS") and, without markers, from the share of long words. An MBBS text and a
   class 9 text on the same topic differ, and the level must follow the book.

When the book's band is one the setting's profile does not accept, ``choose`` returns a ``disagreement`` and the run
stops with a question for Navin (``tools/run_brain.py``: status "stopped: level"); ``--level <id> --trust-level``
records his answer. The presentation layer never changes with the level (TEACHING_SOUL.md).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).resolve().parent / "rulebook" / "level_profiles.json"
WORD = re.compile(r"[A-Za-z][A-Za-z\-']+")
SENTENCE = re.compile(r"[.!?।]+\s")
LONG, VERY_LONG = 10, 13


@dataclass(frozen=True)
class Profile:
    id: str
    name: str
    learners: str
    accepts_bands: tuple
    setting_words: tuple
    terms: str
    why_steps: tuple
    why_style: str
    where_found: str
    exam_beats: str
    links: str
    one_line_per_item: bool
    new_terms: bool

    def prefix_text(self) -> str:
        """The profile as fixed prefix text (the same bytes for every card of a run)."""
        low, high = self.why_steps
        steps = f"{low}" if low == high else f"{low}-{high}"
        lines = [f"Level profile: {self.name} (level_profiles.json; learners: {self.learners}).",
                 f"- Terms: {self.terms}.",
                 f"- Why: {steps} step(s); {self.why_style}.",
                 f"- Where found: {self.where_found}.",
                 f"- Exam beats: {self.exam_beats}.",
                 f"- Links: {self.links}."]
        if self.one_line_per_item:
            lines.append("- Revision: one line per item, no new terms, one chapter map.")
        return "\n".join(lines)


@dataclass(frozen=True)
class Profiles:
    version: str
    profiles: dict
    default: str
    inference: dict

    def get(self, level_id: str) -> Profile:
        if level_id not in self.profiles:
            raise KeyError(f"unknown level {level_id!r}; known: {', '.join(self.profiles)}")
        return self.profiles[level_id]

    def from_setting(self, course) -> tuple:
        """(profile id or None, evidence): the course setting's own level, from course.level or its words."""
        explicit = (getattr(course, "level", "") or "").strip().lower()
        if explicit:
            return self.get(explicit).id, f"course.level = {explicit}"
        text = f"{getattr(course, 'learners', '')} {getattr(course, 'exam', '')} {getattr(course, 'title', '')}".lower()
        for pid, profile in self.profiles.items():
            for word in profile.setting_words:
                if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", text):
                    return pid, f"the course setting says {word!r}"
        return None, "the course setting names no level"


@lru_cache(maxsize=4)
def load(path: str = str(PATH)) -> Profiles:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    profiles = {}
    for pid, raw in data["profiles"].items():
        profiles[pid] = Profile(id=pid, name=raw["name"], learners=raw["learners"], accepts_bands=tuple(raw["accepts_bands"]),
                                setting_words=tuple(w.lower() for w in raw["setting_words"]), terms=raw["terms"],
                                why_steps=tuple(raw["why_steps"]), why_style=raw["why_style"], where_found=raw["where_found"],
                                exam_beats=raw["exam_beats"], links=raw["links"], one_line_per_item=bool(raw["one_line_per_item"]),
                                new_terms=bool(raw["new_terms"]))
    return Profiles(version=str(data["version"]), profiles=profiles, default=data["default"], inference=data["inference"])


def text_features(text: str) -> dict:
    """What the inference reads from a book's text: words, long-word shares and words a sentence."""
    words = WORD.findall(text or "")
    count = len(words)
    sentences = [s for s in SENTENCE.split(text or "") if s.strip()]
    return {"words": count,
            "long_share": round(sum(1 for w in words if len(w) >= LONG) / count, 4) if count else 0.0,
            "very_long_share": round(sum(1 for w in words if len(w) >= VERY_LONG) / count, 4) if count else 0.0,
            "sentence_words": round(count / len(sentences), 1) if sentences else 0.0}


def infer_band(text: str, profiles: Profiles | None = None) -> tuple:
    """(band or None, evidence): the book's band. Markers win; else the long-word shares; too little text: None."""
    profiles = profiles or load()
    rules = profiles.inference
    low = (text or "").lower()
    features = text_features(text)
    for band, markers in rules["markers"].items():
        for marker in markers:
            match = re.search(marker, low)
            if match:
                return band, dict(features, marker=match.group(0), reason=f"the text says {match.group(0)!r}")
    if features["words"] < rules["min_words"]:
        return None, dict(features, reason=f"only {features['words']} words of text; the level comes from the course setting")
    bands = rules["bands"]
    if features["long_share"] >= bands["advanced"]["long_share_min"]:
        return "advanced", dict(features, reason=f"{features['long_share']:.0%} of the words have {LONG} or more letters")
    if (features["long_share"] <= bands["school"]["long_share_max"]
            and features["very_long_share"] <= bands["school"]["very_long_share_max"]):
        return "school", dict(features, reason=f"{features['long_share']:.0%} long words, {features['very_long_share']:.1%} very long")
    return "senior_secondary", dict(features, reason=f"{features['long_share']:.0%} long words, {features['very_long_share']:.1%} very long")


@dataclass(frozen=True)
class Level:
    profile_id: str
    source: str             # "course" (course.level), "setting" (words of the setting), "inferred" (the text), "default"
    band: str | None
    evidence: dict
    disagreement: str | None

    def as_dict(self) -> dict:
        return {"profile": self.profile_id, "source": self.source, "band": self.band, "evidence": self.evidence,
                "disagreement": self.disagreement}


def choose(course, text: str = "", *, profiles: Profiles | None = None, trust_setting: bool = False) -> Level:
    """The level for a run: the setting's profile, checked against the book's band. A disagreement is Navin's to settle."""
    profiles = profiles or load()
    setting, setting_evidence = profiles.from_setting(course)
    band, evidence = infer_band(text, profiles)
    evidence = dict(evidence, setting=setting_evidence)
    mapped = profiles.inference["band_to_profile"].get(band) if band else None
    if setting:
        profile_id, source = setting, ("course" if (getattr(course, "level", "") or "").strip() else "setting")
    elif mapped:
        profile_id, source = mapped, "inferred"
    else:
        profile_id, source = profiles.default, "default"
    disagreement = None
    if band and not trust_setting:
        profile = profiles.get(profile_id)
        if band == "advanced" and mapped is None:
            disagreement = (f"The book reads deeper than any level profile ({evidence['reason']}); the setting says "
                            f"{profile.name}. Ask Navin which level to teach at, then run with --level <id> --trust-level.")
        elif band not in profile.accepts_bands and source != "inferred":
            disagreement = (f"The book reads as {band} ({evidence['reason']}) but the course setting says {profile.name} "
                            f"({setting_evidence}). Ask Navin which level to teach at, then run with --level <id> --trust-level.")
    return Level(profile_id, source, band, evidence, disagreement)
