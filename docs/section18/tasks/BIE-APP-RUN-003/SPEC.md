# BIE-APP-RUN-003 — Source validation UI

**Section:** 18 — APP / Product / API / Operator Experience  
**Classification:** ORIGINAL REGISTRY TASK  
**Batch:** 001  
**Canonical baseline:** `47cafba8975061555764c3c579ae6daad696ae64`  
**Implementation status for this ZIP build:** IMPLEMENTED / TESTED LOCALLY IN PACKAGING BRANCH; NOT YET CANONICALLY INTEGRATED OR PRODUCT-ACCEPTED.

## Purpose

Implement the original capability **Source validation UI** as a real operator/product behavior over existing BIE state. The task may add product-facing metadata/read models but MUST NOT replace canonical engine stores, fabricate progress, or silently downgrade missing evidence.

## Owned implementation

- `bie/product_app_v1/source_validation.py`
- `apps/api/section18_operator.py`

Task-specific tests:

- `tests/section18/test_app_run_003.py`

## Completion criteria

- Render the actual validation result, source hash, byte length, media type and signature offset.
- Clearly distinguish basic transport validation from deferred deep document validation.
- Escape untrusted display names and diagnostics.
- Expose accessible heading/table/list semantics and truthful accepted/rejected state.
- Reject empty, oversize, wrong-media-type and missing-PDF-signature inputs.

## Failure / abstention behavior

Malformed input, missing persisted state, invalid state transitions, integrity mismatches and unsupported control states are explicit errors or conflicts. The implementation must not translate those conditions into a green status.

## Security / privacy boundary

Raw PDF bytes stay in the existing canonical CAS/job-service path. Product/operator metadata exposes identifiers, hashes and whitelisted safe diagnostics only. HTML output escapes untrusted labels/names. Batch 001's operator HTTP router is explicit local-development opt-in and does **not** claim authentication.

## Evidence discipline

A task ZIP contains the task spec, owned source files, task-specific tests, a test receipt, immutable manifest/checksums and dependency/preservation metadata. Batch-level integration tests are additional evidence and are not counted again as task-specific tests.

## Explicit non-claim

The UI does not convert a basic PDF-header check into a claim that OCR/layout/semantic ingestion has passed.

Full Section 18 completion still requires the remaining 23 original tasks, completeness audit, justified hardening, re-audit, browser/API/native verification and governed GitHub integration.
