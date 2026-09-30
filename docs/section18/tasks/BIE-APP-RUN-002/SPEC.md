# BIE-APP-RUN-002 — Upload/import source

**Section:** 18 — APP / Product / API / Operator Experience  
**Classification:** ORIGINAL REGISTRY TASK  
**Batch:** 001  
**Canonical baseline:** `47cafba8975061555764c3c579ae6daad696ae64`  
**Implementation status for this ZIP build:** IMPLEMENTED / TESTED LOCALLY IN PACKAGING BRANCH; NOT YET CANONICALLY INTEGRATED OR PRODUCT-ACCEPTED.

## Purpose

Implement the original capability **Upload/import source** as a real operator/product behavior over existing BIE state. The task may add product-facing metadata/read models but MUST NOT replace canonical engine stores, fabricate progress, or silently downgrade missing evidence.

## Owned implementation

- `bie/product_app_v1/source_validation.py`
- `bie/product_app_v1/source_import.py`

Task-specific tests:

- `tests/section18/test_app_run_002.py`

## Completion criteria

- Accept a bounded PDF source only after basic transport validation.
- Delegate durable source storage, idempotency, queueing and canonical job identity to the existing PdfInspectionJobService, SQLitePersistence, SQLiteDurableTaskQueue and FileSystemCAS.
- Bind the operator run to the actual canonical job and exact SHA-256 source identity.
- Keep raw source bytes out of the operator metadata database.
- Reject duplicate initial imports and invalid source signatures without creating a fake job.

## Failure / abstention behavior

Malformed input, missing persisted state, invalid state transitions, integrity mismatches and unsupported control states are explicit errors or conflicts. The implementation must not translate those conditions into a green status.

## Security / privacy boundary

Raw PDF bytes stay in the existing canonical CAS/job-service path. Product/operator metadata exposes identifiers, hashes and whitelisted safe diagnostics only. HTML output escapes untrusted labels/names. Batch 001's operator HTTP router is explicit local-development opt-in and does **not** claim authentication.

## Evidence discipline

A task ZIP contains the task spec, owned source files, task-specific tests, a test receipt, immutable manifest/checksums and dependency/preservation metadata. Batch-level integration tests are additional evidence and are not counted again as task-specific tests.

## Explicit non-claim

Basic source import does not claim deep document validity; deep inspection remains the canonical document-intelligence runtime's responsibility.

Full Section 18 completion still requires the remaining 23 original tasks, completeness audit, justified hardening, re-audit, browser/API/native verification and governed GitHub integration.
