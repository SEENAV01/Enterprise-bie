"""AUDIO-VO-005: explicit acronym/initialism/expansion policies, no guessed names."""
from __future__ import annotations
from dataclasses import dataclass
import re
from .common import AudioError, Reading, fingerprint, locale, refs, text

from .common import EN, HI



@dataclass(frozen=True)
class AcronymRule:
    surface: str
    language: str
    mode: str
    evidence_refs: tuple[str, ...]
    reading: str | None = None
    domain: str = "*"

    def __post_init__(self):
        text(self.surface,"acronym",64);locale(self.language);text(self.domain,"domain",128)
        refs(self.evidence_refs,"acronym evidence")
        if not re.fullmatch(r"(?:[A-Z]{2,16}|(?:[A-Z]\.){2,16})",self.surface):
            raise AudioError("ACRONYM_SURFACE_REQUIRED")
        if self.mode not in ("LETTERS","WORD","EXPANSION"):raise AudioError("INVALID_ACRONYM_MODE")
        if self.mode=="LETTERS":
            if self.reading is not None:raise AudioError("LETTERS_WITH_OVERRIDE")
        else:text(self.reading,"acronym reading",2048)


@dataclass(frozen=True)
class AcronymTable:
    version: str
    rules: tuple[AcronymRule,...]
    def __post_init__(self):
        text(self.version,"acronym version",256)
        if type(self.rules) is not tuple or len(self.rules)>4096 or any(type(x)is not AcronymRule for x in self.rules):
            raise AudioError("INVALID_ACRONYM_RULES")
        keys=[(r.surface,r.language,r.domain) for r in self.rules]
        if len(set(keys))!=len(keys):raise AudioError("CONFLICTING_ACRONYM_RULES")
        if keys!=sorted(keys):raise AudioError("ACRONYM_TABLE_NOT_CANONICAL")
    def fingerprint(self):return fingerprint(self)


def make_acronyms(version,rules):
    if type(rules)is not tuple or any(type(r)is not AcronymRule for r in rules):raise AudioError("INVALID_ACRONYM_RULES")
    return AcronymTable(version,tuple(sorted(rules,key=lambda r:(r.surface,r.language,r.domain))))


def pronounce_acronym(surface,language,table:AcronymTable,*,domain="general") -> Reading:
    text(surface,"acronym",64);locale(language);text(domain,"domain",128)
    if type(table)is not AcronymTable:raise AudioError("ACRONYM_TABLE_REQUIRED")
    candidates=[r for r in table.rules if r.surface==surface and r.language==language and r.domain in (domain,"*")]
    candidates=[r for r in candidates if r.domain==domain] or candidates
    if len(candidates)!=1:raise AudioError("ACRONYM_NOT_FOUND" if not candidates else "ACRONYM_AMBIGUOUS",surface)
    r=candidates[0]
    if r.mode=="LETTERS":
        alphabet=EN if language.split('-')[0]=="en" else HI if language.split('-')[0]=="hi" else None
        if alphabet is None:raise AudioError("LETTER_LANGUAGE_NOT_SUPPORTED",language)
        spoken=" ".join(alphabet[ord(c)-65] for c in surface.replace('.',''))
    else:spoken=r.reading
    return Reading(surface,spoken,language,"ACRONYM","acronym:"+fingerprint(r)[7:],r.evidence_refs)
