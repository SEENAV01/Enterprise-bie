# Task036 Step 4 — operation-local Director span validation

Status: **STEP4_BLOCKED at compatibility verification**. The bounded local repair and preservation records are implemented, but the retained Scene suite is non-green on this Windows execution. Independent review and exact-candidate governed Linux verification remain required. This is not Task036 completion or evidence that the historical Scene termination is fixed.

## Baseline and scope

Baseline commit: `ed9f845859a32107c021ff826761ae2350cd3125`.
Baseline tree: `249065d3a5c748de7a52f5188c06ac194e3ecec1`.
Isolated branch: `codex/task036-step4-director-span`.
The old handoff, Step 1 and Step 2 checkouts are preserved. No Codespaces changes were imported.

Only two native sources change: `bie/director/qa_contract.py` and `bie/director/narration_annotations.py`. No worker, workflow, renderer, producer, model, dependency, security policy or execution budget changes.

## Confirmed source path and correction

Completed Scene status reaches `_completed_status_bundle`, `_verified_scene_bundle`, native motion ENTRY/EXIT verification, `verified_director`, `DirectorConsumers._director`, `verify_persisted_annotation_bundle`, `verify_production`, `validate_annotations`, and `selection`.

Previously a default `selection` called `validate_snapshot`, then public `bind_span` called it again. Each validation reconstructs the entire snapshot through `snapshot_script`. This duplicated work is measured, not inferred from the last worker checkpoint.

Public `bind_span` still performs fresh full validation. A private `_bind_validated_span` contains its unchanged binding/word-boundary/revision validation body. `selection` performs one fresh full validation and uses only that operation's index for binding and exact quote checks. An optional caller index is checked against the complete fresh index and cannot confer authority. Invalid index types, missing/extra/foreign entries and equality-spoofing mapping/value objects are rejected. The valid public signature is unchanged. No index or PASS result survives the operation.

All surrounding source, semantic, assessment, coverage, currentness, authorization and native ENTRY/EXIT checks remain unchanged. In particular this does not implement window/batch-wide or cross-operation caching.

## Separate fresh-process measurements

Windows, Python 3.13.5; original repository synthetic fixtures, outside all budgeted workers. Reconstruction counting used a temporary wrapping counter only in the external local experiment. CPU measurements ran without that counter and have no timing-threshold assertions.

| Operation | Baseline reconstructions | Candidate reconstructions | Repetitions timed | Baseline CPU ms | Candidate CPU ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Default selection, 16-utterance fixture | 2 | 1 | 100 | 906.250 | 484.375 |
| Public bind_span | 1 | 1 | 100 | 546.875 | 343.750 |
| Selection with equivalent caller index | 1 | 1 | 100 | 421.875 | 468.750 |
| Annotation production revalidation | 56 | 33 | 5 | 593.750 | 421.875 |
| Actual persisted Director consumer revalidation | 66 | 43 | 3 | 2750.000 | 2359.375 |

The unchanged public bind operation's varying timing and the caller-index row illustrate measurement variability; these numbers are fixture observations, not production throughput or causal proof about a killed child.

Matching identities:

- 16-utterance input: `9af803d65915b97f913ac13a1b928ac4248e95ee4e977feed1db0135a6005c9c`.
- Selected span: `cb273272e8af062ecabeeec948830b281c9befda18457ce0822b5bd0a3eeecde`.
- Annotation fixture: `365ef35127c6042e096a05aa531110f2c24aa7b2fce1cca9ba1336637d391a32`.
- Annotation result: `b815b23ff52fb0793ea57dbd3b5894bfa4601d9cdaa86a711911338292dd16bb`.
- Persisted consumer execution: `801a23ff972350ae5c152057fb022b61f551c52012066f70db21125dec20df6c`.
- Persisted consumer snapshot: `2ad073ba65e5230d19a7a36bec36043fba157a14f02396d42a9087be15ea29c2`.

Both processes rejected the ten compared stale/index/span/quote invalid cases with ValueError. Revalidation made no provider calls. The Director code identity legitimately changes from `5413fa723286a52b1f5824736179f70efcdfe17f54c42fd0db8b41214ef05a90` to `5d02f6927598da5d10dd1bcdcca2b7fa01d7294f5f384f0e98c41cffc324b8df`; it is not frozen to the old receipt.

## Exact preservation amendment, not an approval

`director-span-step4-amendment/AMENDMENT.json` has SHA256 `422853c8718e2f996497bae5c2060cb2b409a721ddea5187ed581fcadd1ee6cb`.

The amendment binds exact Git preimages and active replacements for both native sources, the original 71-file Director census, and the narrowly changed audit entry point. The fixed resolver authenticates raw bytes; it does not generate expected identities from current contents during verification. It rejects unrelated changes, unlisted native paths, altered expectations, preimage tampering, rollback, missing/extra caller rows and modified contributors.

The immutable `director_integration_003.json` SHA256 remains `02733513b9cca98b1255c7e615890ecd7e25726135a0d590a77b40ea5dba0285`. All seven original mappings (one qa_contract and six narration_annotations), the six contributor references and original archive hashes remain intact. Only an authenticated in-memory audit view redirects the historical canonical references to preserved preimages. The audit authenticates the replacement separately.

The original M1 amendment SHA256 remains `b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c`. No sealed review, ledger, archive, M1 source or previous amendment is edited. The new record explicitly says `PENDING_NOT_SELF_APPROVED`; its integrity PASS is not independent reviewer approval. The changed audit reader is preserved with its own exact preimage and replacement pin.

## Verification record

37 new controls (20 span/freshness and 17 preservation/tamper): 37 selected, executed and passed; zero failures, errors, skips or collection errors. The retained 683 Director identities were independently collected from the baseline; their identity SHA256 is `87d8b7917941f170c2ce29e95c1f1ec382d463ceb4bcfd7bfe8c8ad9dfd11802`. The unchanged 440 Scene inventory and retained safety controls are executed separately, with no repeated probes counted as authored tests.

Final local results (Windows/Python 3.13.5):

| Inventory | Selected | Executed | Passed methods | Failed methods | Method errors | Setup errors | Skips |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Retained Director | 683 | 683 | 682 | 0 | 1 | 0 | 0 |
| Added span/amendment controls | 37 | 37 | 37 | 0 | 0 | 0 | 0 |
| Unchanged Scene | 440 | 374 | 355 | 15 | 4 | 2 | 0 |
| Runner/evidence/safety, owner account | 62 | 62 | 62 | 0 | 0 | 0 | 0 |

All collection-error counts are zero. Scene's six reported errors comprise four method errors and two setup errors, not six errored executed methods. Those setup errors prevented 66 selected methods from executing. The Scene identity hash remains `8db0c676408303693a4c96716c5db8b7e77b1ded5e787c047de0787350980fcb`, matching the baseline 440-case inventory. No existing test/assertion was edited, omitted, skipped or replaced.

Director's `DurableRecoveryTests.test_catalog_rejects_corrupt_journal_and_missing_cas` raises Windows `PermissionError` (winerror 32) during temporary-directory cleanup on both unchanged baseline and candidate, including owner-account checks. It is retained, not fixed here.

The first sandbox-account safety run had 61 passes and one error in `StrictAfterReceipt.test_complete_six_probe_comparison_and_bound_runtime_are_required`. Fresh comparison observed a Git `CalledProcessError` on the baseline; a direct Git read established the sandbox-account/checkout ownership mismatch. Both isolated owner-account checks and the complete owner-account 62-test suite passed with no Git trust-setting or BIE security-policy change. The original non-green attempt remains evidence; its unsaved detailed exception is not retroactively reconstructed.

Scene's three positive `RealSourceCases` failed, along with recovery and real-native status controls. Conservation/currentness class setup errors blocked 66 methods. A separate unchanged quantitative service fixture reached ten SUCCEEDED upstream stages, then `SCENE_IR=FAILED` with `scene_ir_execution_failed` on both baseline and candidate. This is a generic diagnostic, not an internal cause or proof that every failure is inherited. These comparisons do not replace real-child or Linux verification. No unrelated Scene repair was attempted.

Ingested-source audit PASS: 387 archives, 74,518 original members, 7,806 canonical targets and seven exact Director amendment member mappings. Post-DIR audit PASS: 386 supplied files, 6,014 mappings and 435 nested ZIP identities. Canonical audit PASS under Python `-X utf8`: 796 archives and 12,439 original member/ledger rows. Its preceding default-Windows-decoding attempt raised `UnicodeDecodeError`; no source, expected hash or validator was normalized or changed to address that environment setting.

The source-set identity, exact local commands, complete failure-method lists, receipt hashes, local commit/tree and backup verification are recorded in the external Step4 continuation report. Comparison probes and repeated environment checks are not additional authored tests. An equivalent byte-exact checkout requires command-scoped `core.autocrlf=false`, `core.eol=lf`, and Windows `core.longpaths=true`; no global setting or tracked attributes change is part of this repair.

## Limits and continuation boundary

The historical push run 38770111999 had two children exit -9 near 30 seconds after eleven SUCCEEDED stages and eleven ACKs. PR run 38770118027 passed on an equal-source-tree synthetic merge. Neither the last checkpoint nor this local improvement establishes the exact historical kill cause.

CPU 30 seconds, wall 45 seconds and every security/render/supervision limit remain unchanged. Required next work is independent review of this exact local amendment and later explicitly authorized exact-candidate hosted validation. No push, hosted run, PR modification, merge, acceptance promotion or Task037 is part of this step. Audio reconciliation stays open and all review/acceptance boundaries are unchanged.
