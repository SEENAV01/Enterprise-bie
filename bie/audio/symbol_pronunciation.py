"""AUDIO-VO-004: exact context-bound symbol reading, not dimensional inference."""
from __future__ import annotations
from dataclasses import dataclass
from .common import AudioError, Reading, fingerprint, locale, refs, text


@dataclass(frozen=True)
class SymbolRule:
    symbol: str
    language: str
    sense: str
    spoken: str
    evidence_refs: tuple[str, ...]
    domain: str = "*"

    def __post_init__(self):
        for name,maxlen in (("symbol",64),("sense",128),("spoken",512),("domain",128)):
            text(getattr(self,name),name,maxlen)
        locale(self.language);refs(self.evidence_refs,"symbol evidence")


@dataclass(frozen=True)
class SymbolTable:
    version: str
    rules: tuple[SymbolRule, ...]

    def __post_init__(self):
        text(self.version,"symbol table version",256)
        if type(self.rules) is not tuple or len(self.rules)>4096 or any(type(x)is not SymbolRule for x in self.rules):
            raise AudioError("INVALID_SYMBOL_RULES")
        keys=[(r.symbol,r.language,r.domain,r.sense) for r in self.rules]
        if len(set(keys))!=len(keys):raise AudioError("DUPLICATE_SYMBOL_SCOPE")
        if keys!=sorted(keys):raise AudioError("SYMBOL_TABLE_NOT_CANONICAL")

    def fingerprint(self):return fingerprint(self)


def make_table(version, rules):
    if type(rules) is not tuple or any(type(r)is not SymbolRule for r in rules):raise AudioError("INVALID_SYMBOL_RULES")
    return SymbolTable(version,tuple(sorted(rules,key=lambda r:(r.symbol,r.language,r.domain,r.sense))))


def pronounce_symbol(symbol: str, language: str, table: SymbolTable, *, domain="general", sense: str|None=None) -> Reading:
    text(symbol,"symbol",64);locale(language);text(domain,"domain",128)
    if type(table) is not SymbolTable:raise AudioError("SYMBOL_TABLE_REQUIRED")
    if sense is not None:text(sense,"sense",128)
    candidates=[r for r in table.rules if r.symbol==symbol and r.language==language and r.domain in (domain,"*") and (sense is None or r.sense==sense)]
    if not candidates:raise AudioError("SYMBOL_NOT_FOUND",symbol)
    best=[r for r in candidates if r.domain==domain] or candidates
    if len(best)!=1:raise AudioError("SYMBOL_SENSE_REQUIRED",symbol)
    r=best[0]
    return Reading(symbol,r.spoken,language,"SYMBOL","symbol:"+fingerprint(r)[7:],r.evidence_refs)


def standard_symbols(language="en") -> SymbolTable:
    """Small versioned reading convention, not a science inference engine."""
    names={"en":("less than or equal to","greater than or equal to","not equal to","approximately equal to","plus or minus","percent"),
           "hi":("से छोटा या बराबर","से बड़ा या बराबर","के बराबर नहीं","लगभग बराबर","धन या ऋण","प्रतिशत")}
    if language not in names:raise AudioError("SYMBOL_LANGUAGE_NOT_SUPPORTED",language)
    rules=tuple(SymbolRule(s,language,"comparison" if i<4 else ("uncertainty" if i==4 else "percent"),name,
                          ("bie:audio:reading-conventions:1",)) for i,(s,name) in enumerate(zip(("≤","≥","≠","≈","±","%"),names[language])))
    return make_table("bie-symbols/1",rules)
