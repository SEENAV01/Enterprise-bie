"""BIE-AUDIO-VO-004: explicit role-based symbol speech, no unit inference."""
from dataclasses import dataclass
from .contracts import AudioError, fingerprint, text
from .pronunciation_lexicon import Lexicon
from .math_pronunciation import UNICODE_GREEK

# These are versioned pronunciation labels, not interpretations of a book.
ROLES = {
    ('−', 'minus'): 'minus', ('-', 'minus'): 'minus', ('-', 'range'): 'to',
    ('–', 'range'): 'to', ('/', 'division'): 'divided by', ('/', 'per'): 'per',
    ('×', 'multiplication'): 'times', ('×', 'dimensions'): 'by',
    ('μ', 'greek_name'): 'mu', ('μ', 'si_prefix'): 'micro',
    ('µ', 'si_prefix'): 'micro', ('π', 'greek_name'): 'pi',
    ('Σ', 'greek_name'): 'capital sigma', ('Δ', 'change'): 'change in',
    ('Δ', 'greek_name'): 'capital delta', ('→', 'direction'): 'to',
    ('→', 'limit'): 'tends to', ('⇒', 'implication'): 'implies',
    ('°', 'degrees'): 'degrees', ('°C', 'temperature'): 'degrees Celsius',
    ('%', 'percentage'): 'percent', ('₹', 'currency'): 'rupees',
    ('$', 'currency'): 'dollars', ('Ω', 'unit'): 'ohms',
    ('Ω', 'greek_name'): 'capital omega', ('+', 'addition'): 'plus',
    ('=', 'equality'): 'equals', ('±', 'plus_minus'): 'plus or minus',
    ('≤', 'comparison'): 'less than or equal to', ('≥', 'comparison'): 'greater than or equal to',
    ('≠', 'comparison'): 'not equal to', ('∞', 'name'): 'infinity',
    ('∂', 'partial_derivative'): 'partial', ('∇', 'operator_name'): 'nabla',
    ('∈', 'membership'): 'is an element of', ('∉', 'membership'): 'is not an element of',
    ('∪', 'set_union'): 'union', ('∩', 'set_intersection'): 'intersection',
}
for char, name in UNICODE_GREEK.items():
    ROLES.setdefault((char, 'greek_name'), name)


@dataclass(frozen=True, slots=True)
class SymbolPronunciation:
    surface: str
    role: str
    spoken_text: str
    language: str
    rule_identity: str
    source_refs: tuple[str, ...]
    phoneme: str = ''
    alphabet: str = ''
    interpretation_verified: bool = False
    audio_generated: bool = False


def pronounce_symbol(surface: str, *, role: str, language: str, domain: str,
                     lexicon: Lexicon | None = None, rule_id: str = '') -> SymbolPronunciation:
    text(surface, 'symbol', maximum=512)
    text(role, 'symbol.role', maximum=128)
    text(domain, 'domain', maximum=512)
    if lexicon is not None:
        rule = lexicon.resolve(surface, kind='symbol', language=language, domain=domain, role=role, rule_id=rule_id)
        if rule:
            return SymbolPronunciation(surface, role, rule.spoken, language, rule.identity, rule.source_refs, rule.phoneme, rule.alphabet)
    elif rule_id:
        raise AudioError('EXPLICIT_RULE_MISMATCH', rule_id)
    if language not in ('en', 'en-US', 'en-GB', 'en-IN'):
        raise AudioError('SYMBOL_LANGUAGE_UNSUPPORTED', language)
    if (surface, role) not in ROLES:
        raise AudioError('SYMBOL_ROLE_UNSUPPORTED', surface, role)
    spoken = ROLES[surface, role]
    return SymbolPronunciation(surface, role, spoken, language,
        fingerprint(('bie-audio-symbols/en/1', surface, role, spoken)), ('policy:bie-audio-symbols/en/1',))
