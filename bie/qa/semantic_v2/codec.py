"""Exact wire shapes; reuse existing bounded UTF-8/integer-only JSON parser."""
from dataclasses import fields
from ..release_v2.contracts import ContractError
from ..source_v2.codec import loads, request_from_dict as source_from_dict
from ..source_v2.models import Policy as SourcePolicy
from .models import (Value, PredicateRule, Proposition, Normalization, ReferenceFact,
    Requirement, CoverageLink, SemanticRequest, SemanticPolicy)
from .attestation import SemanticAssessment


def shape(data, cls):
    if type(data) is not dict or set(data) != {f.name for f in fields(cls)}:
        raise ContractError('SEMANTIC_OBJECT_FIELDS_MISMATCH', cls.__name__)
    return dict(data)


def array(data, limit=4096):
    if type(data) is not list or len(data) > limit: raise ContractError('INVALID_SEMANTIC_ARRAY')
    return tuple(data)


def proposition_from_dict(value):
    d = shape(value, Proposition)
    d['value'] = Value(**shape(d['value'], Value))
    d['context'] = tuple(array(row, 2) for row in array(d['context'], 32))
    return Proposition(**d)


def request_from_dict(value):
    d = shape(value, SemanticRequest)
    d['source'] = source_from_dict(d['source'])
    ns, rs, ls = [], [], []
    for raw in array(d['normalizations']):
        n = shape(raw, Normalization)
        n['propositions'] = tuple(proposition_from_dict(p) for p in array(n['propositions'], 64))
        ns.append(Normalization(**n))
    for raw in array(d['references']):
        r = shape(raw, ReferenceFact); r['proposition'] = proposition_from_dict(r['proposition'])
        r['citation_ids'] = array(r['citation_ids'], 128); rs.append(ReferenceFact(**r))
    for raw in array(d['coverage_links']):
        l = shape(raw, CoverageLink); l['claim_ids'] = array(l['claim_ids'], 128); ls.append(CoverageLink(**l))
    d.update(normalizations=tuple(ns), references=tuple(rs), coverage_links=tuple(ls))
    return SemanticRequest(**d)


def policy_from_dict(value):
    # This function decodes data; it does not confer authority. CLI/API callers
    # must provision this independently, never read it from generated content.
    d = shape(value, SemanticPolicy); s = shape(d['source'], SourcePolicy)
    s['expected_output_ids'] = array(s['expected_output_ids']); d['source'] = SourcePolicy(**s)
    for f in ('expected_reference_ids', 'reference_source_ids'): d[f] = array(d[f])
    ps, rs = [], []
    for raw in array(d['predicates']):
        p = shape(raw, PredicateRule); p['context_keys'] = array(p['context_keys'], 32); ps.append(PredicateRule(**p))
    for raw in array(d['requirements']):
        r = shape(raw, Requirement); r['allowed_channels'] = array(r['allowed_channels'], 6); rs.append(Requirement(**r))
    d.update(predicates=tuple(ps), requirements=tuple(rs)); return SemanticPolicy(**d)


def load_request(data: bytes): return request_from_dict(loads(data))

def load_policy(data: bytes): return policy_from_dict(loads(data))

def load_assessments(data: bytes):
    result = []
    for raw in array(loads(data), 8192):
        a = shape(raw, SemanticAssessment); a['evidence_ids'] = array(a['evidence_ids'])
        result.append(SemanticAssessment(**a))
    return tuple(result)
