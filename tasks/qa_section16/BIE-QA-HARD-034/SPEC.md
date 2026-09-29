# BIE-QA-HARD-034 — Immutable publication and artifact transaction

## Preserved registered scope
Use content-addressed immutable release inputs and atomic verified publication so later bytes match the assessed candidate.

## Required closure evidence
- A post-audit mutation cannot publish under an older certificate.
- Release retries cannot produce mixed-version artifacts.
- Rollback/revocation behavior is checked without claiming deployment from local SQLite.

## Local implementation
Actual existing certificate assessment/verification before copying and after restoring content-addressed release bytes. Local transactional activation, immutable version identity, compare-and-swap head, idempotent retry, read-time expiry/revocation verification and deactivation. Mutable source files are never hardlinked as published blobs.

## Still required
- Publication exercised the existing certificate verifier using synthetic diagnostic-only authorities and artifacts. No production certificate, distributed store, deployed endpoint or real product release was issued.
- Private local SQLite/CAS does not resist an administrator replacing all database/history, deliver distributed transactions/trusted time/KMS, or revoke already downloaded bytes. Native caller integration and production approval remain open.

## Trust, execution and acceptance
All generation/execution configuration is operator-owned, never taken from book instructions. Synthetic approvals are explicitly diagnostic. This task cannot issue a terminal production PASS and does not close the historical gap ledger. No GitHub, global continuation, Section15 or Codex/Android modification occurs.

## Verification
Shared suite: tests/qa_hardening_h7. Actual suite-qualified results: hardening/section16_h7/evidence/final_source_suites/TEST_RESULT.json. Selected mutation controls: hardening/section16_h7/evidence/mutations/MUTATION_RESULT.json. Diagnostics: hardening/section16_h7/evidence/diagnostics/EXECUTION_RESULT.json. Do not multiply shared tests across task packages.
