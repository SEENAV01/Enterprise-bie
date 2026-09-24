"""BIE-AUDIO-VO-002: versioned exact-literal pronunciation memory.

Rules have explicit language/domain/meaning, source references and immutable
identity. Longest literal match wins; replacements are never recursively read.
No automatic heteronym, acronym-expansion or IPA correctness inference is made.
"""
from __future__ import annotations
from dataclasses import dataclass
import unicodedata
from .contracts import AudioError, canonical, fingerprint, ids, locale, text


@dataclass(frozen=True, slots=True)
class PronunciationRule:
    rule_id: str
    revision: str
    kind: str
    surface: str
    spoken: str
    language: str
    source_refs: tuple[str, ...]
    domain: str = ""
    role: str = ""
    mode: str = "alias"
    phoneme: str = ""
    alphabet: str = ""

    def validate(self) -> None:
        for key in ("rule_id", "revision", "surface"):
            text(getattr(self, key), key, maximum=512)
        text(self.spoken, "spoken", blank=self.mode == "letters", maximum=2048)
        locale(self.language)
        text(self.domain, "domain", blank=True, maximum=512)
        text(self.role, "role", blank=True, maximum=128)
        ids(self.source_refs, "rule.source_refs")
        if self.kind not in ("term", "symbol", "acronym"):
            raise AudioError("LEXICON_KIND", self.rule_id)
        permitted = {"term": ("alias",), "symbol": ("alias",), "acronym": ("letters", "word", "expansion")}
        if self.mode not in permitted[self.kind]:
            raise AudioError("LEXICON_MODE", self.rule_id)
        if self.mode == "letters" and self.spoken:
            raise AudioError("LETTERS_ALIAS_CONFLICT", self.rule_id)
        text(self.phoneme, "phoneme", blank=True, maximum=2048)
        text(self.alphabet, "alphabet", blank=True, maximum=128)
        if bool(self.phoneme) != bool(self.alphabet) or (self.alphabet and self.alphabet != "ipa"):
            raise AudioError("PHONEME_ALPHABET", self.rule_id)
        if self.mode == "letters" and self.phoneme:
            raise AudioError("LETTERS_PHONEME_CONFLICT", self.rule_id)
        if self.kind == "symbol" and not self.role:
            raise AudioError("SYMBOL_ROLE_REQUIRED", self.rule_id)
        if self.surface != self.surface.strip():
            raise AudioError("LEXICON_SURFACE_WHITESPACE", self.rule_id)

    @property
    def selector(self):
        return self.kind, self.surface, self.language, self.domain, self.role

    @property
    def identity(self) -> str:
        self.validate()
        return fingerprint(self)


@dataclass(frozen=True, slots=True)
class Lexicon:
    lexicon_id: str
    version: str
    rules: tuple[PronunciationRule, ...] = ()

    def validate(self) -> None:
        text(self.lexicon_id, "lexicon_id", maximum=512)
        text(self.version, "version", maximum=128)
        if type(self.rules) is not tuple or len(self.rules) > 10_000:
            raise AudioError("LEXICON_LIMIT")
        rule_ids, selectors = set(), set()
        for rule in self.rules:
            if type(rule) is not PronunciationRule:
                raise AudioError("LEXICON_RULE_TYPE")
            rule.validate()
            if rule.rule_id in rule_ids:
                raise AudioError("DUPLICATE_RULE_ID", rule.rule_id)
            if rule.selector in selectors:
                raise AudioError("AMBIGUOUS_LEXICON_SELECTOR", rule.rule_id)
            rule_ids.add(rule.rule_id)
            selectors.add(rule.selector)

    @property
    def identity(self) -> str:
        self.validate()
        # Ingestion order is immaterial; explicit versions and context are not.
        return fingerprint({"id": self.lexicon_id, "version": self.version,
            "rules": sorted((canonical(r) for r in self.rules))})

    def resolve(self, surface: str, *, kind: str, language: str, domain: str,
                role: str = "", rule_id: str = "", expected_identity: str | None = None):
        self.validate()
        if expected_identity is not None and expected_identity != self.identity:
            raise AudioError("STALE_LEXICON")
        candidates = [r for r in self.rules if r.surface == surface and r.kind == kind and
            r.language == language and r.domain in ("", domain) and (not role or r.role == role)]
        if rule_id:
            selected = [r for r in candidates if r.rule_id == rule_id]
            if len(selected) != 1:
                raise AudioError("EXPLICIT_RULE_MISMATCH", rule_id)
            return selected[0]
        exact = [r for r in candidates if r.domain == domain]
        candidates = exact or candidates
        if len(candidates) > 1:
            raise AudioError("AMBIGUOUS_PRONUNCIATION", surface)
        return candidates[0] if candidates else None


def lexicon_from_dict(raw: dict) -> Lexicon:
    if type(raw) is not dict or set(raw) != {"lexicon_id", "version", "rules"} or type(raw["rules"]) is not list:
        raise AudioError("LEXICON_KEYS")
    rules = []
    for entry in raw["rules"]:
        if type(entry) is not dict or set(entry) != set(PronunciationRule.__dataclass_fields__) or type(entry["source_refs"]) is not list:
            raise AudioError("RULE_KEYS")
        rules.append(PronunciationRule(**{**entry, "source_refs": tuple(entry["source_refs"])}))
    result = Lexicon(raw["lexicon_id"], raw["version"], tuple(rules))
    result.validate()
    return result


def lexical_char(char: str) -> bool:
    return char.isalnum() or char == "_" or unicodedata.category(char).startswith("M") or char in "\u200c\u200d"


def literal_boundary(raw: str, start: int, end: int) -> bool:
    return ((start == 0 or not (lexical_char(raw[start - 1]) and lexical_char(raw[start]))) and
            (end == len(raw) or not (lexical_char(raw[end - 1]) and lexical_char(raw[end]))))


@dataclass(frozen=True, slots=True)
class LexiconMatch:
    start: int
    end: int
    rule: PronunciationRule


def match_lexicon(raw: str, lexicon: Lexicon, *, language: str, domain: str,
                  excluded: tuple[tuple[int, int], ...] = ()) -> tuple[LexiconMatch, ...]:
    text(raw, "text", blank=True)
    lexicon.validate()
    locale(language)
    text(domain, "domain", maximum=512)
    available = [r for r in lexicon.rules if r.language == language and r.domain in ("", domain)]
    trie = {}
    for rule in available:
        node = trie
        for char in rule.surface:
            node = node.setdefault(char, {})
        node.setdefault(None, []).append(rule)
    blocked = set()
    for a, b in excluded:
        blocked.update(range(a, b))
    result, i = [], 0
    while i < len(raw):
        if i in blocked:
            i += 1
            continue
        node, j, matches = trie, i, []
        while j < len(raw) and j not in blocked and raw[j] in node:
            node = node[raw[j]]
            j += 1
            if None in node and literal_boundary(raw, i, j):
                matches = node[None]
        if not matches:
            i += 1
            continue
        length = len(matches[0].surface)
        matches = [r for r in matches if r.domain == domain] or matches
        if len(matches) != 1:
            raise AudioError("AMBIGUOUS_PRONUNCIATION", str(i), raw[i:i + length])
        result.append(LexiconMatch(i, i + length, matches[0]))
        i += length
    return tuple(result)
