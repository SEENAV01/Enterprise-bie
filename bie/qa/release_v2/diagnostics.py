"""HARD-003: legacy diagnostic strings are blocking; typed advisories are explicit.

Severity is never inferred from a score, substring, or outer PASS. An unknown
severity or malformed diagnostic is a contract error, not an ignored warning.
"""
from dataclasses import dataclass
from .contracts import ContractError, token, choice

@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: str = 'BLOCKING'

    def __post_init__(self):
        token(self.code, 'diagnostic.code')
        choice(self.severity, ('BLOCKING', 'ADVISORY'), 'diagnostic.severity')

    @classmethod
    def from_dict(cls, value):
        if type(value) is not dict or set(value) != {'code', 'severity'}:
            raise ContractError('INVALID_TYPED_DIAGNOSTIC')
        return cls(**value)


def legacy_blockers(values):
    """No caller-controlled string prefix can downgrade a legacy diagnostic."""
    return tuple(Diagnostic(value) for value in values)
