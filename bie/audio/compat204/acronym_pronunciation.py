"""BIE-AUDIO-VO-005: explicit initialism/word/expansion choices.

Never expands unknown uppercase tokens from model memory. Letter-name defaults
are versioned English policies; ambiguous names (US, MS, AI) need lexicon intent.
"""
from dataclasses import dataclass
import re
from .contracts import AudioError, fingerprint
from .pronunciation_lexicon import Lexicon, literal_boundary

LETTER_NAMES = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    ('ay bee see dee ee ef gee aitch eye jay kay el em en oh pee cue ar ess tee you vee double-you ex why zed').split()))
DIGIT_NAMES = dict(zip('0123456789', 'zero one two three four five six seven eight nine'.split()))


@dataclass(frozen=True, slots=True)
class AcronymPronunciation:
    surface: str
    mode: str
    spoken_text: str
    language: str
    rule_identity: str
    source_refs: tuple[str, ...]
    phoneme: str = ''
    alphabet: str = ''
    audio_generated: bool = False


def spell_initialism(surface: str, language: str, *, explicit_mixed_case: bool = False) -> str:
    if language not in ('en', 'en-US', 'en-GB', 'en-IN'):
        raise AudioError('ACRONYM_LANGUAGE_UNSUPPORTED', language)
    pattern = r'[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*\.?' if explicit_mixed_case else r'[A-Z0-9]+(?:\.[A-Z0-9]+)*\.?'
    if type(surface) is not str or len(surface) > 128 or not re.fullmatch(pattern, surface):
        raise AudioError('INITIALISM_SHAPE', str(surface))
    letters = {**LETTER_NAMES, **DIGIT_NAMES}
    if language == 'en-US':
        letters['Z'] = 'zee'
    return ' '.join(letters[char.upper()] for char in surface if char != '.')


def pronounce_acronym(surface: str, *, language: str, domain: str, lexicon: Lexicon,
                      rule_id: str = '') -> AcronymPronunciation:
    rule = lexicon.resolve(surface, kind='acronym', language=language, domain=domain, rule_id=rule_id)
    if rule is None:
        raise AudioError('UNKNOWN_ACRONYM', surface, 'Explicit letters, word, or expansion rule required')
    spoken = spell_initialism(surface, language, explicit_mixed_case=True) if rule.mode == 'letters' else rule.spoken
    return AcronymPronunciation(surface, rule.mode, spoken, language,
        rule.identity, rule.source_refs, rule.phoneme, rule.alphabet)


def acronym_candidates(raw: str) -> tuple[tuple[int, int, str], ...]:
    # Candidates, not assertions that every all-caps word is an acronym.
    result = []
    pattern = r'(?:[A-Z]\.){2,}[A-Z]?|[A-Z][A-Z0-9]{1,}'
    for match in re.finditer(pattern, raw):
        if literal_boundary(raw, match.start(), match.end()):
            result.append((match.start(), match.end(), match.group()))
    return tuple(result)
