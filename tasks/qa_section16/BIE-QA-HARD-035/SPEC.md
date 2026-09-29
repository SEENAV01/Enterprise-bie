# BIE-QA-HARD-035 — Operational authority, attestation and trusted time

## Original scope
Provision real out-of-band evaluator/issuer authority, capture attestation, trusted clocks and revocation distribution.

## Dependencies
BIE-QA-HARD-004, BIE-QA-HARD-030, BIE-QA-HARD-034

## Implemented local contract
Public-key verification of independently configured Ed25519 identities, nonce-bound signed clock intervals and revocation status. Private SQLite replay/rollback watermarks, bounded sessions, disjoint authority roles, and an optional wrapper around the actual inherited publication/certificate verifier.

## Original closure criteria (preserved)
- Test-only credentials cannot authorize production.
- Independent review and issuer roles are enforced across adapters.
- Expired/revoked evidence is invalid at assessment, issuance and serving time.

## Remaining closure requirements
- No live time/authority service, independent operator enrollment, KMS, hardware attestation, remote revocation distribution or trusted hardware clock was provisioned. Positive signed evidence is diagnostic.
- The new wrapper is exercised but canonical/direct H7 publication callers are not migrated. Session freshness is bounded by explicit TTL, not instantaneous revocation polling. Local database state is not resistant to administrator rollback.

## Evidence
Code: bie/qa/assurance_quality_v2/authority.py
Shared suite: tests/qa_hardening_h8 (155 unique methods; do not multiply per task).
Executed receipt: hardening/section16_h8/evidence/final_source_suites/TEST_RESULT.json
Mutations: hardening/section16_h8/evidence/mutations/MUTATION_RESULT.json
Diagnostics: hardening/section16_h8/evidence/diagnostics/EXECUTION_RESULT.json

## Authority and acceptance
Inputs, identities and authority are operator configuration, not permissions granted by a source document. Failures and missing native/rights/assessment evidence block or require review. No inherited policy or acceptance floor is relaxed. No GitHub, Section15, global continuation, credential service or live memory mutation. Local implementation is not operational closure.
