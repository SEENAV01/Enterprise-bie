# BIE-APP-GRAPH-002 — Prerequisite graph viewer

**Section:** 18 — APP / Product / API / Operator Experience  
**Classification:** ORIGINAL REGISTRY TASK  
**Batch:** 001  
**Canonical baseline:** `47cafba8975061555764c3c579ae6daad696ae64`  
**Implementation status for this ZIP build:** IMPLEMENTED / TESTED LOCALLY IN PACKAGING BRANCH; NOT YET CANONICALLY INTEGRATED OR PRODUCT-ACCEPTED.

## Purpose

Implement the original capability **Prerequisite graph viewer** as a real operator/product behavior over existing BIE state. The task may add product-facing metadata/read models but MUST NOT replace canonical engine stores, fabricate progress, or silently downgrade missing evidence.

## Owned implementation

- `bie/product_app_v1/prerequisite_graph_viewer.py`

Task-specific tests:

- `tests/section18/test_app_graph_002.py`

## Completion criteria

- Consume the canonical PrerequisiteGraph representation.
- Verify incoming/outgoing symmetry, node coverage, graph size and cycle freedom.
- Compute deterministic dependency levels and a topological teaching order.
- Preserve caller-supplied labels/source refs without inventing provenance.
- Render deterministic layered SVG plus an accessible textual fallback and fail closed on cycles/asymmetry.

## Failure / abstention behavior

Malformed input, missing persisted state, invalid state transitions, integrity mismatches and unsupported control states are explicit errors or conflicts. The implementation must not translate those conditions into a green status.

## Security / privacy boundary

Raw PDF bytes stay in the existing canonical CAS/job-service path. Product/operator metadata exposes identifiers, hashes and whitelisted safe diagnostics only. HTML output escapes untrusted labels/names. Batch 001's operator HTTP router is explicit local-development opt-in and does **not** claim authentication.

## Evidence discipline

A task ZIP contains the task spec, owned source files, task-specific tests, a test receipt, immutable manifest/checksums and dependency/preservation metadata. Batch-level integration tests are additional evidence and are not counted again as task-specific tests.

## Explicit non-claim

The viewer does not decide prerequisites; it displays a validated prerequisite graph produced elsewhere in BIE.

Full Section 18 completion still requires the remaining 23 original tasks, completeness audit, justified hardening, re-audit, browser/API/native verification and governed GitHub integration.
