"""Compose VO-001..005 without altering narration/captions or inventing audio.

Speech is a separate source-mapped channel. An unresolved interpretation returns
review evidence, not a falsely ready TTS request. No replacement is rescanned.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import re
import unicodedata
from .contracts import AudioError, ENGINE_VERSION, Issue, NarrationDocument, fingerprint, canonical
from .narration_segmentation import SegmentationPolicy, delimited_math, segment_narration, verify_segments
from .pronunciation_lexicon import Lexicon, match_lexicon
from .math_pronunciation import pronounce_math, UNICODE_GREEK
from .symbol_pronunciation import pronounce_symbol
from .acronym_pronunciation import pronounce_acronym, acronym_candidates


@dataclass(frozen=True, slots=True)
class SpeechPiece:
    block_id: str
    start_char: int
    end_char: int
    original_text: str
    spoken_text: str
    kind: str
    decision_identity: str
    source_refs: tuple[str, ...]
    phoneme: str = ''
    alphabet: str = ''


@dataclass(frozen=True, slots=True)
class PreparedSegment:
    segment_id: str
    block_id: str
    scene_id: str
    voice_id: str
    language: str
    start_char: int
    end_char: int
    original_text: str
    spoken_text: str
    pieces: tuple[SpeechPiece, ...]
    evidence_ids: tuple[str, ...]
    objective_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class VoiceoverPreparation:
    document_fingerprint: str
    script_fingerprint: str
    lexicon_fingerprint: str
    engine_version: str
    policy: SegmentationPolicy
    segments: tuple[PreparedSegment, ...]
    issues: tuple[Issue, ...]
    source_map_offset_unit: str = 'UNICODE_CODEPOINT_HALF_OPEN'
    audio_generated: bool = False
    audio_alignment_verified: bool = False
    product_accepted: bool = False

    @property
    def requires_review(self) -> bool:
        return bool(self.issues)

    @property
    def status(self) -> str:
        return 'REVIEW_REQUIRED' if self.requires_review else 'PRONUNCIATION_PREPARED_NO_AUDIO'

    @property
    def identity(self) -> str:
        return fingerprint(self)

    def to_dict(self) -> dict:
        return {**asdict(self), 'status': self.status, 'identity': self.identity}


def _math_body(surface: str) -> str:
    for opening, closing in ((r'\(', r'\)'), (r'\[', r'\]'), ('$$', '$$'), ('$', '$')):
        if surface.startswith(opening) and surface.endswith(closing) and len(surface) > len(opening) + len(closing):
            return surface[len(opening):-len(closing)]
    return surface


def _atoms(block, lexicon):
    raw, occupied, atoms, issues = block.raw_text, [], [], []

    def add(start, end, spoken, kind, identity, refs, phoneme='', alphabet=''):
        occupied.append((start, end))
        atoms.append(SpeechPiece(block.block_id, start, end, raw[start:end], spoken,
            kind, identity, tuple(dict.fromkeys((*block.evidence_ids, *refs))), phoneme, alphabet))

    def unresolved(start, end, exc, task):
        issues.append(Issue(exc.code, block.block_id, start, end, exc.detail or str(exc), task))
        add(start, end, raw[start:end], 'unresolved', fingerprint(('unresolved', exc.code, start, end)), ())

    def lower(start, end, kind, role='', rule_id='', annotation_refs=()):
        surface = raw[start:end]
        try:
            if kind == 'verbatim':
                add(start, end, surface, kind, fingerprint(('verbatim/1', surface)), annotation_refs)
            elif kind == 'math':
                if role not in ('', 'latex') or rule_id:
                    raise AudioError('MATH_ANNOTATION_FORMAT', str(start))
                p = pronounce_math(_math_body(surface), language=block.language)
                add(start, end, p.spoken_text, kind, p.identity, annotation_refs)
            elif kind == 'symbol':
                p = pronounce_symbol(surface, role=role, language=block.language,
                    domain=block.domain, lexicon=lexicon, rule_id=rule_id)
                add(start, end, p.spoken_text, kind, p.rule_identity, (*annotation_refs, *p.source_refs), p.phoneme, p.alphabet)
            elif kind == 'acronym':
                p = pronounce_acronym(surface, language=block.language, domain=block.domain,
                    lexicon=lexicon, rule_id=rule_id)
                add(start, end, p.spoken_text, kind, p.rule_identity,
                    (*annotation_refs, *p.source_refs), p.phoneme, p.alphabet)
            else:
                p = lexicon.resolve(surface, kind=kind, language=block.language,
                    domain=block.domain, role=role, rule_id=rule_id)
                if p is None:
                    raise AudioError('PRONUNCIATION_RULE_MISSING', surface)
                add(start, end, p.spoken, kind, p.identity, (*annotation_refs, *p.source_refs), p.phoneme, p.alphabet)
        except AudioError as exc:
            task = {'math': 'BIE-AUDIO-VO-003', 'symbol': 'BIE-AUDIO-VO-004', 'acronym': 'BIE-AUDIO-VO-005'}.get(kind, 'BIE-AUDIO-VO-002')
            unresolved(start, end, exc, task)

    for annotation in block.annotations:
        lower(annotation.start, annotation.end, annotation.kind, annotation.role,
              annotation.rule_id, annotation.source_refs)
    masked = list(raw)
    for start, end in occupied:
        masked[start:end] = ' ' * (end - start)
    for start, end, _ in delimited_math(''.join(masked)):
        lower(start, end, 'math')
    for match in match_lexicon(raw, lexicon, language=block.language, domain=block.domain, excluded=tuple(occupied)):
        lower(match.start, match.end, match.rule.kind, match.rule.role, match.rule.rule_id)

    def outside(start, end):
        return not any(start < b and end > a for a, b in occupied)

    for start, end, surface in acronym_candidates(raw):
        if outside(start, end):
            unresolved(start, end, AudioError('ACRONYM_OR_CAPS_NEEDS_RULE', surface,
                'Choose letters/word/expansion or explicitly annotate verbatim'), 'BIE-AUDIO-VO-005')
    for match in re.finditer(r'°C|[%₹$±∞≤≥≠⇒→∈∉∂∇ΩΔ]|[αβγδεζηθικλμνξοπρστυφχψω]|[=+*/^_<>\\]', raw):
        if outside(match.start(), match.end()):
            unresolved(match.start(), match.end(), AudioError('SYMBOL_ROLE_REQUIRED', match.group(),
                'Bind a mathematical expression or a source-specific symbol role'), 'BIE-AUDIO-VO-004')
    # Catch other Unicode mathematical/currency/standalone pictographic marks;
    # a small allowlist must not silently certify unhandled symbolic notation.
    for index, char in enumerate(raw):
        if outside(index, index + 1) and (unicodedata.category(char).startswith('S') or
                (char.isnumeric() and not char.isdecimal())):
            unresolved(index, index + 1, AudioError('UNHANDLED_SYMBOLIC_NOTATION', char,
                'Provide a source-bound role, pronunciation rule, math expression, or verbatim intent'), 'BIE-AUDIO-VO-004')

    # Raw prose numbers are not silently assigned ordinal/date/currency meaning.
    for match in re.finditer(r'\d+(?:\.\d+)?', raw):
        if outside(match.start(), match.end()):
            issues.append(Issue('NUMERIC_READING_UNSPECIFIED', block.block_id, match.start(), match.end(),
                'Annotate math or supply explicit term realization for number/date/version meaning.', 'BIE-AUDIO-VO-003'))
    for reason in block.review_reasons:
        issues.append(Issue('UPSTREAM_REVIEW', block.block_id, 0, len(raw), reason, 'DIR'))
    if block.language not in ('en', 'en-US', 'en-GB', 'en-IN'):
        issues.append(Issue('LANGUAGE_ADOPTION_PENDING_VO006', block.block_id, 0, len(raw),
            'Source and exact-locale rules preserved; mixed-language/provider behavior not yet verified.', 'BIE-AUDIO-VO-006'))
    atoms.sort(key=lambda atom: atom.start_char)
    for left, right in zip(atoms, atoms[1:]):
        if left.end_char > right.start_char:
            raise AudioError('PRONUNCIATION_OVERLAP', block.block_id)
    return tuple(atoms), tuple(issues)


def prepare_voiceover(document: NarrationDocument, lexicon: Lexicon,
                      policy=SegmentationPolicy(), *, expected_document: str | None = None,
                      expected_lexicon: str | None = None) -> VoiceoverPreparation:
    document.validate()
    lexicon.validate()
    if expected_document is not None and expected_document != document.identity:
        raise AudioError('STALE_DOCUMENT')
    if expected_lexicon is not None and expected_lexicon != lexicon.identity:
        raise AudioError('STALE_LEXICON')
    atoms, issues = {}, []
    for block in document.blocks:
        atoms[block.block_id], found = _atoms(block, lexicon)
        issues.extend(found)
    segmentation = segment_narration(document, policy, protected={key: tuple((x.start_char, x.end_char) for x in value) for key, value in atoms.items()})
    verify_segments(segmentation, document)
    prepared = []
    for segment in segmentation.segments:
        pieces, cursor = [], segment.start_char
        for atom in atoms[segment.block_id]:
            if atom.start_char < segment.start_char or atom.end_char > segment.end_char:
                continue
            if atom.start_char > cursor:
                literal = segment.raw_text[cursor - segment.start_char:atom.start_char - segment.start_char]
                pieces.append(SpeechPiece(segment.block_id, cursor, atom.start_char, literal, literal,
                    'literal', fingerprint(('literal/1', literal)), segment.evidence_ids))
            pieces.append(atom)
            cursor = atom.end_char
        if cursor < segment.end_char:
            literal = segment.raw_text[cursor - segment.start_char:]
            pieces.append(SpeechPiece(segment.block_id, cursor, segment.end_char, literal, literal,
                'literal', fingerprint(('literal/1', literal)), segment.evidence_ids))
        if ''.join(p.original_text for p in pieces) != segment.raw_text:
            raise AudioError('SPEECH_SOURCE_COVERAGE', segment.block_id)
        spoken = ''.join(p.spoken_text for p in pieces)
        if len(spoken.encode('utf-8')) > 32_000:
            raise AudioError('SPOKEN_SEGMENT_LIMIT', segment.block_id)
        prepared.append(PreparedSegment(segment.segment_id, segment.block_id, segment.scene_id,
            segment.voice_id, segment.language, segment.start_char, segment.end_char,
            segment.raw_text, spoken, tuple(pieces), segment.evidence_ids, segment.objective_ids))
    order = {block.block_id: i for i, block in enumerate(document.blocks)}
    issues.sort(key=lambda issue: (order[issue.block_id], issue.start, issue.end, issue.code, issue.detail))
    return VoiceoverPreparation(document.identity, document.script_fingerprint, lexicon.identity,
        ENGINE_VERSION, policy, tuple(prepared), tuple(issues))


def verify_preparation(plan: VoiceoverPreparation, document: NarrationDocument, lexicon: Lexicon) -> None:
    if type(plan) is not VoiceoverPreparation or canonical(plan) != canonical(prepare_voiceover(document, lexicon, plan.policy)):
        raise AudioError('PREPARATION_MISMATCH', detail='Edited/stale inputs, speech, source map, review or acceptance fields')
