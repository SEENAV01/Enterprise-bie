"""Deterministic text/timeline measurements, not empirical cognitive scores."""
from fractions import Fraction
import re
import unicodedata
from ..release_v2.contracts import ContractError, integer


def merged_text(claims, claim_ids):
    """Union overlapping byte-verified code-point spans without counting them twice.

    Adjacent spans are concatenated; gaps receive a separator so words cannot join.
    A conflicting overlap is rejected even before upstream provenance reporting.
    """
    groups = {}
    for cid in claim_ids:
        c = claims[cid]; groups.setdefault(c.output_id, []).append(c)
    pieces = []
    for oid in sorted(groups):
        end = -1; chars = ''; begin = 0
        for c in sorted(groups[oid], key=lambda x: (x.start, x.end, x.claim_id)):
            if c.start > end:
                if chars: pieces.append(chars)
                begin, end, chars = c.start, c.end, c.text
            else:
                overlap = max(0, min(end, c.end) - c.start)
                if overlap and chars[c.start-begin:c.start-begin+overlap] != c.text[:overlap]:
                    raise ContractError('DIR_CONFLICTING_TEXT_SPANS')
                if c.end > end: chars += c.text[overlap:]; end = c.end
        if chars: pieces.append(chars)
    return '\n'.join(pieces)


def identity(s):
    return ' '.join(unicodedata.normalize('NFC', s).casefold().split())


def codepoints(s): return sum(not ch.isspace() for ch in s)


def rate(count, duration_ms):
    integer(count, 'count', 0, 16_000_000); integer(duration_ms, 'duration_ms', 1, 86_400_000)
    return Fraction(count * 60000, duration_ms)


def ceil_fraction(x): return (x.numerator + x.denominator - 1) // x.denominator


def contains_term(s, form):
    """Conservative Unicode-aware literal matching; not a semantic term detector."""
    hay = unicodedata.normalize('NFC', s).casefold(); needle = unicodedata.normalize('NFC', form).casefold()
    at = 0
    def word(c): return c.isalnum() or c == '_' or unicodedata.category(c).startswith('M')
    while True:
        i = hay.find(needle, at)
        if i < 0: return False
        j = i + len(needle)
        if (i == 0 or not (word(hay[i-1]) and word(needle[0]))) and (j == len(hay) or not (word(hay[j]) and word(needle[-1]))): return True
        at = i + 1


def sentence_lengths(s):
    # A documented guardrail, not a grammar/reading-level classifier.
    return [codepoints(part) for part in re.split(r'[.!?।！？\n]+', s) if part.strip()]


def has_unsafe_controls(s):
    # ZWJ/ZWNJ are valid in several scripts, but directional overrides can hide text.
    return any((unicodedata.category(c) == 'Cc' and c not in '\t\r\n') or c in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069\ufffd' for c in s)


def needs_expanded_readout(s):
    return any(c in s for c in '=∑∫√±≤≥^')


def windows(beats):
    """Half-open intervals: end at t and start at t do not overlap."""
    changes = {}
    for b in beats:
        changes.setdefault(b.start_ms, [[], []])[1].append(b.beat_id)
        changes.setdefault(b.end_ms, [[], []])[0].append(b.beat_id)
    active = set(); previous = None
    for t in sorted(changes):
        if previous is not None and previous < t: yield previous, t, tuple(sorted(active))
        ends, starts = changes[t]; active.difference_update(ends); active.update(starts); previous = t
