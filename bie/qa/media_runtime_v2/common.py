"""Shared exact contracts. Policy and authority are operator objects, not source data."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from fractions import Fraction
import re
from ..native_quality_v2.common import (Binding, Finding, Report, report, require, fields,
    items, unique, approved, Review, ReviewVerifier, SnapshotStore, ArtifactRef,
    ContractError, canonical_bytes, digest, integer, token, text, binding_matches)
from ..release_v2.contracts import safe_relative_path, sha256
from ..publication_v2.contracts import strict_json

SCHEMA = 'bie.qa.media-runtime/1'


def q(value):
    """Bounded canonical rational; no float/coercion/NaN or implicit booleans."""
    require(type(value) in (str, int), 'H5_RATIONAL_TYPE')
    if type(value) is str:
        require(len(value) <= 80 and re.fullmatch(r'-?[0-9]+(?:/[1-9][0-9]*)?', value) is not None, 'H5_RATIONAL_SYNTAX')
    v = Fraction(value)
    require(v.numerator.bit_length() <= 192 and v.denominator.bit_length() <= 192, 'H5_RATIONAL_BUDGET')
    return v


def qt(v):
    return str(Fraction(v))


def checked_ids(values, name, minimum=1, maximum=4096):
    require(type(values) in (tuple, list) and minimum <= len(values) <= maximum, name + '_COUNT')
    for x in values: token(x, name)
    require(len(set(values)) == len(values), name + '_DUPLICATE')
    return tuple(values)


def findings_report(task, binding, findings, details, inspected=()):
    # Healthy technical results do not establish native provenance, scientific
    # teaching meaning, acoustic truth, operational authority or product acceptance.
    findings.append(Finding('NATIVE_OPERATIONAL_AND_CONTEXTUAL_REVIEW_REQUIRED', task))
    r = report(task, binding, findings, inspected, details)
    return {'schema_version': SCHEMA, 'report': r.to_dict(), 'details': details,
            'technical_checks_clear': not any(f.severity == 'BLOCKER' for f in findings),
            'production_authorized': False, 'product_accepted': False}


def fail(findings, code, subject='candidate'):
    findings.append(Finding(code, subject, 'BLOCKER'))


def policy_binding(binding, policy):
    require(type(binding) is Binding and binding.policy_digest == digest(asdict(policy)), 'H5_POLICY_BINDING')


@dataclass(frozen=True)
class Tool:
    path: str
    sha256: str
    def __post_init__(self):
        from pathlib import Path
        require(type(self.path) is str and Path(self.path).is_absolute(), 'H5_TOOL_PATH')
        sha256(self.sha256, 'tool')
    def verify(self):
        from pathlib import Path
        import hashlib
        p = Path(self.path).resolve(strict=True)
        require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == self.sha256, 'H5_TOOL_IDENTITY')
        return str(p)
