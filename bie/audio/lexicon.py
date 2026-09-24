"""AUDIO-VO-002: scoped, versioned pronunciation decisions with exact spans.

Source/domain/sense declarations are evidence identifiers, not an acoustic proof.
PLS export is a local alias/IPA subset, with no remote fetch or XML import.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import xml.etree.ElementTree as ET
from .common import AudioError, Reading, fingerprint, is_word, locale, refs, text


@dataclass(frozen=True)
class Lexeme:
    entry_id: str
    surface: str
    language: str
    pronunciation: str
    evidence_refs: tuple[str, ...]
    domain: str = "*"
    sense: str = "*"
    mode: str = "ALIAS"
    alphabet: str | None = None
    case_sensitive: bool = True

    def __post_init__(self):
        for name, maximum in (("entry_id",512),("surface",256),("pronunciation",2048),("domain",128),("sense",128)):
            text(getattr(self,name),name,maximum)
        locale(self.language)
        refs(self.evidence_refs,"lexicon evidence")
        if self.surface != self.surface.strip() or type(self.case_sensitive) is not bool:
            raise AudioError("INVALID_LEXEME")
        if self.mode not in ("ALIAS","PHONEME"):
            raise AudioError("INVALID_LEXEME_MODE")
        if self.mode == "PHONEME" and self.alphabet != "ipa":
            raise AudioError("UNSUPPORTED_PHONEME_ALPHABET")
        if self.mode == "ALIAS" and self.alphabet is not None:
            raise AudioError("ALIAS_WITH_ALPHABET")


@dataclass(frozen=True)
class Lexicon:
    version: str
    entries: tuple[Lexeme, ...]

    def __post_init__(self):
        text(self.version,"lexicon version",256)
        if type(self.entries) is not tuple or len(self.entries)>10000 or any(type(x) is not Lexeme for x in self.entries):
            raise AudioError("INVALID_LEXICON_ENTRIES")
        if tuple(sorted(self.entries,key=lambda x:x.entry_id)) != self.entries:
            raise AudioError("LEXICON_NOT_CANONICAL")
        if len({e.entry_id for e in self.entries}) != len(self.entries):
            raise AudioError("DUPLICATE_LEXICON_ID")
        keys=set()
        for e in self.entries:
            key=(e.surface if e.case_sensitive else e.surface.casefold(),e.case_sensitive,e.language,e.domain,e.sense)
            if key in keys:
                raise AudioError("DUPLICATE_LEXICON_SCOPE")
            keys.add(key)

    def fingerprint(self):
        return fingerprint(self)


def build_lexicon(version: str, entries: tuple[Lexeme, ...]) -> Lexicon:
    if type(entries) is not tuple or any(type(e) is not Lexeme for e in entries):
        raise AudioError("INVALID_LEXICON_ENTRIES")
    return Lexicon(version,tuple(sorted(entries,key=lambda e:e.entry_id)))


def resolve(lexicon: Lexicon, surface: str, language: str, *, domain: str = "general", sense: str | None = None,
            allow_primary_language: bool = False) -> Reading:
    if type(lexicon) is not Lexicon or type(allow_primary_language) is not bool:
        raise AudioError("INVALID_LEXICON")
    text(surface,"surface",8192);locale(language);text(domain,"domain",128)
    if sense is not None:
        text(sense,"sense",128)
    candidates=[]
    requires_sense=False
    for e in lexicon.entries:
        if not (e.surface==surface if e.case_sensitive else e.surface.casefold()==surface.casefold()):
            continue
        ls=2 if e.language==language else (1 if allow_primary_language and e.language==language.split('-')[0] else 0)
        if not ls or e.domain not in (domain,"*"):
            continue
        if sense is None and e.sense!="*":
            requires_sense=True
            continue
        if e.sense not in (sense,"*"):
            continue
        candidates.append(((ls,e.domain==domain,e.sense==sense),e))
    if not candidates:
        raise AudioError("LEXICON_SENSE_REQUIRED" if requires_sense else "LEXICON_NOT_FOUND",surface)
    best=max(score for score,_ in candidates)
    winners=[e for score,e in candidates if score==best]
    if len(winners)!=1:
        raise AudioError("LEXICON_AMBIGUOUS",surface)
    e=winners[0]
    return Reading(surface,e.pronunciation if e.mode=="ALIAS" else surface,language,"TERM",e.entry_id,
        e.evidence_refs,e.pronunciation if e.mode=="PHONEME" else None,e.alphabet)


def matches(lexicon: Lexicon, value: str, language: str, *, domain="general", allow_primary_language=False):
    """Longest whole-token/phrase match first; original code-point offsets retained."""
    text(value,"text",1000000)
    if len(value)*max(1,len(lexicon.entries))>20000000:
        raise AudioError("LEXICON_SCAN_BUDGET")
    found=[]
    for e in lexicon.entries:
        if e.language not in ((language,language.split('-')[0]) if allow_primary_language else (language,)) or e.domain not in (domain,"*"):
            continue
        for m in re.finditer(re.escape(e.surface),value,flags=0 if e.case_sensitive else re.IGNORECASE):
            a,b=m.span()
            if a and is_word(value[a-1]) and is_word(value[a]):continue
            if b<len(value) and is_word(value[b-1]) and is_word(value[b]):continue
            found.append((a,b))
    occupied=0
    out=[]
    for a,b in sorted(set(found),key=lambda p:(p[0],-(p[1]-p[0]))):
        if a<occupied:continue
        r=resolve(lexicon,value[a:b],language,domain=domain,allow_primary_language=allow_primary_language)
        out.append((a,b,r));occupied=b
    return tuple(out)


def export_pls(lexicon: Lexicon, language: str, *, domain="general") -> str:
    """Export only an unambiguous resolved locale/domain view; all text is escaped."""
    locale(language)
    ns="http://www.w3.org/2005/01/pronunciation-lexicon"
    root=ET.Element("lexicon",{"version":"1.0","xmlns":ns,"alphabet":"ipa","{http://www.w3.org/XML/1998/namespace}lang":language})
    for surface in sorted({e.surface for e in lexicon.entries if e.language==language and e.domain in (domain,"*")}):
        r=resolve(lexicon,surface,language,domain=domain)
        if any(not e.case_sensitive for e in lexicon.entries if e.entry_id==r.rule_id):
            raise AudioError("PLS_CASE_VARIANTS_REQUIRE_EXPLICIT_ENTRIES")
        node=ET.SubElement(root,"lexeme")
        ET.SubElement(node,"grapheme").text=surface
        ET.SubElement(node,"phoneme" if r.phonemes is not None else "alias").text=r.phonemes or r.spoken
    return ET.tostring(root,encoding="unicode",xml_declaration=True)
