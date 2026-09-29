"""Small, auditable entailment kernel for reviewed, explicitly scoped atoms.

This does not parse language or decide whether a reference is true. It compares
normalized propositions only after the orchestrating evaluator checks authority.
"""
from __future__ import annotations
from .models import Proposition, PredicateRule, number
from ..release_v2.contracts import ContractError


def validate_rule(p: Proposition, rule: PredicateRule) -> None:
    if type(p) is not Proposition or type(rule) is not PredicateRule:
        raise ContractError('INVALID_LOGIC_INPUT')
    if p.predicate_id != rule.predicate_id: raise ContractError('PREDICATE_RULE_MISMATCH')
    if p.value.kind != rule.value_kind: raise ContractError('PREDICATE_VALUE_KIND_MISMATCH')
    if p.value.unit != rule.unit: raise ContractError('PREDICATE_UNIT_MISMATCH')
    if tuple(k for k, _ in p.context) != rule.context_keys:
        raise ContractError('INCOMPLETE_OR_EXTRA_CONTEXT')


def compare(reference: Proposition, candidate: Proposition, rule: PredicateRule) -> str:
    """Return ENTAILS, CONTRADICTS, UNKNOWN or DIFFERENT_SCOPE.

    Numeric intervals are closed. A reference interval entails a candidate only
    when all reference values lie within the candidate interval. Overlap alone
    is not entailment; a precise candidate cannot erase reference uncertainty.
    Multi-valued predicates do not make differing positive symbols exclusive.
    """
    validate_rule(reference, rule); validate_rule(candidate, rule)
    if (reference.entity_id, reference.context) != (candidate.entity_id, candidate.context):
        return 'DIFFERENT_SCOPE'
    r, c = reference.value, candidate.value
    if r.kind == 'quantity':
        rlo, rhi, clo, chi = number(r.lower), number(r.upper), number(c.lower), number(c.upper)
        if rhi < clo or chi < rlo: return 'CONTRADICTS'
        if clo <= rlo and rhi <= chi: return 'ENTAILS'
        return 'UNKNOWN'
    same_value = r.symbol == c.symbol
    same_sign = reference.polarity == candidate.polarity
    if same_value: return 'ENTAILS' if same_sign else 'CONTRADICTS'
    if rule.cardinality == 'single' and reference.polarity == 'positive':
        return 'CONTRADICTS' if candidate.polarity == 'positive' else 'ENTAILS'
    return 'UNKNOWN'


def conflict(a: Proposition, b: Proposition, rule: PredicateRule) -> bool:
    # The kernel's conflict relation must remain symmetric even though
    # entailment and open-world negative information are directional.
    return compare(a, b, rule) == 'CONTRADICTS' or compare(b, a, rule) == 'CONTRADICTS'
