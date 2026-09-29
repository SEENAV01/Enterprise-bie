# BIE-QA-HARD-004 — Evaluator independence and key lifecycle

Add out-of-band principal/independence-group identity and validity/revocation rules at the evidence verifier, not caller-supplied names.

Shared implementation and contracts: docs/qa_section16/hardening_h1/SPEC.md

Closure checks:
- Two aliases sharing a secret/principal cannot meet an independence floor of two.
- Distinct valid independent principals can meet a strengthened floor.
- Expired/revoked rotated identities fail; evidence cannot choose its own trust store.
- Do not confuse local HMAC identity with remote attestation.

No section exit or production acceptance.
