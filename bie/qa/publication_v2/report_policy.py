"""HARD-001/002: out-of-band closed-world terminal report requirements.

Not populated by PublicationRequest. Each native adapter must provision its exact
schema, evaluator-policy digest and mandatory check identities. Empty configuration
fails closed. Additional native formats need code, tests, and explicit registration.
"""
from dataclasses import dataclass, asdict
from ..release_v2.contracts import ContractError, token, sha256, choice, tuple_tokens

TERMINAL_SCHEMA = 'bie.qa.terminal-report/1'
FACT_SCHEMA = 'bie.qa.immutable-fact/1'
LEDGER_SCHEMA = 'bie.qa.obligation-ledger/1'
REGISTRY_VERSION = 'bie.qa.terminal-registry/h1-1'

@dataclass(frozen=True, slots=True)
class TerminalRequirement:
    subject_type: str
    subject_id: str
    evaluator_policy_digest: str
    required_check_ids: tuple[str, ...]
    allowed_schemas: tuple[str, ...] = (TERMINAL_SCHEMA,)

    def __post_init__(self):
        choice(self.subject_type, ('gate', 'section_exit', 'obligation'), 'terminal.subject_type')
        token(self.subject_id, 'terminal.subject_id')
        sha256(self.evaluator_policy_digest, 'terminal.evaluator_policy_digest')
        tuple_tokens(self.required_check_ids, 'required_check_ids', 1, 4096)
        if self.allowed_schemas != (TERMINAL_SCHEMA,):
            raise ContractError('UNREGISTERED_TERMINAL_POLICY_SCHEMA')

    def to_dict(self):
        d=asdict(self);d['required_check_ids']=sorted(self.required_check_ids)
        return d
