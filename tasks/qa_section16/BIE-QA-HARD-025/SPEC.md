# BIE-QA-HARD-025 — Native source-extraction repair adapter

Owner: BI.QA.REPAIR. Local namespace: `bie/qa/lifecycle_quality_v2`.

## Original scope (preserved)
Repair derived extraction/anchors through approved native providers while preserving original bytes and meaning.

## Required full-closure evidence (preserved)
- Multiregion/scanned defects generate bounded proposals with unchanged original sources.
- Ambiguous extraction escalates rather than fabricating a quote.
- Every repaired source change invalidates downstream meaning/media evidence.

## Local implementation
Reruns the native PDF ingestion/provenance adapter and proposes a regenerated multi-region derived snapshot; original source bytes and extraction policy remain unchanged. Actual source-pixel/text verification is repeated.

## Inputs, outputs and trust
All mutable target paths, required validators, policies, source/fixture inventories and authority are operator inputs. Candidate/document text cannot grant privileges, weaken gates or authorize its own changes. Reports/receipts identify exact artifact bytes, run, revision, candidate and policy. Proposed fixes do not modify the original and cannot inherit old signatures.

## Executed test/evidence locations
- `tests/qa_hardening_h6/test_repairs.py`
- `tests/qa_hardening_h6/test_handoff.py`
- `hardening/section16_h6/evidence/final_source_suites/TEST_RESULT.json`
- `hardening/section16_h6/evidence/mutations/MUTATION_RESULT.json`
- `hardening/section16_h6/evidence/diagnostics/EXECUTION_RESULT.json`

The 137-case H6 suite is shared, not an independent count per task. Positive review credentials and human/model observations are explicitly synthetic.

## Remaining requirements
- Scanned repair with independently valid OCR and reading-order/figure interpretation remains open; no OCR process was executed in this batch.
- Only proposed derived extraction is produced; semantic assessment, canonical downstream invalidation/adoption and real-book proof remain required.

No historical obligation is closed here. Section15, GitHub and global continuation are unchanged. Final section audit and canonical real-book gates remain required.
