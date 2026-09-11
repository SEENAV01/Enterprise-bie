# BIE Reasoning section quality review 001

Review date: 2026-09-10 UTC. Repository: `SEENAV01/Enterprise-bie`, branch `main`.

**Five demonstrated defects have been fixed in the existing spatial/temporal batch. The integrated gate passes 1,672 tests. The section completion gate remains OPEN and acceptance remains NOT ACCEPTED.**

This is a quality review and revision of existing implementations, not a new numbered roadmap batch. The latest implemented roadmap checkpoint remains **RE-TEMP-003**. No completed Prerequisite, Math or earlier Reasoning task was recreated.

## Scope and dependency check

The starting remote commit was `03f32e193736904a02aac4544d88c0c3b498c4c2`, tree `636596304406b10b03f1c751b43e82f01fe11f76`. Its actual branch ref was checked before work began. The prior forensic audit applies to that immutable snapshot; this review does not retroactively alter its findings.

All five current tasks were inspected: RE-SPATIAL-003/004 and RE-TEMP-001/002/003. Their canonical dependency implementations, specifications and current registry records were present. Hardening changes are limited to `geometry_reasoning.py`, `event_order_reasoning.py` and `periodization_reasoning.py`. Map and chronology production code is unchanged.

The complete Reasoning subsystem and the downstream BIE product are outside this review's acceptance scope. Existing canonical APIs, task IDs, source-evidence contracts, provider neutrality, archive boundaries and original source lineage are retained.

## Reproduced defects and corrections

| Finding | Existing task | Observed before correction | Correction and outcome |
| --- | --- | --- | --- |
| G01 | RE-SPATIAL-004 | Valid triangle evidence supplied as an iterator was consumed during measurement, then rejected as absent during classification. | Materialize the evidence once before both operations. Iterator and tuple inputs now produce the same grounded result ID. |
| G02 | RE-SPATIAL-004 | A containment query could reuse polygon vertex `A` with different coordinates and return a confident `inside` result. | Validate point identity across query and ring together. Conflicting coordinates now raise `ValueError`. |
| G03 | RE-SPATIAL-004 | Two observations of the same segment endpoint at identical coordinates were rejected when they cited different sources. | Point identity compares exact coordinates; independent source citations remain in the inference evidence. A valid shared endpoint returns `touching`. |
| T01 | RE-TEMP-002 | Open Gregorian bounds could produce a supposedly valid strict order before 0001-01-01 or after 9999-12-31. The existing decision adapter then allowed it without review. | Apply the declared Gregorian domain during pair and chain feasibility. Impossible orders now return `CONFLICT`, emit no linear extension and propagate `requires_review=True` through existing decision/artifact contracts. Historical-year open bounds remain unbounded. |
| T02 | RE-TEMP-003 | A half-open period could not include 9999-12-31 because its exclusive end was validated as an included event date. | Validate `start` through `end - 1`. The exclusive boundary may be `date.max.toordinal() + 1`; no included day may exceed the supported calendar. |

G02 and T01 were correctness and QA concerns: contradictory or impossible inputs could receive a resolved result. G01, G03 and T02 rejected valid inputs. All five findings now have executable regression coverage.

## Independent checks and regression evidence

The 18 new quality tests initially produced **4 failures and 4 errors**, with 10 passing. These eight failing checks represent five defects, not eight separately counted defects. The unchanged added test file now passes all **18/18** tests.

| Task or contract | Original tests | Added quality tests | Current count |
| --- | ---: | ---: | ---: |
| RE-SPATIAL-003 | 16 | 1 | 17 |
| RE-SPATIAL-004 | 18 | 5 | 23 |
| RE-TEMP-001 | 15 | 1 | 16 |
| RE-TEMP-002 | 13 | 6 | 19 |
| RE-TEMP-003 | 16 | 4 | 20 |
| Shared integration/contract tests | 13 | 1 | 14 |
| Restored enterprise regression | 1,551 | 0 | 1,551 |
| Repository assembly guards | 12 | 0 | 12 |
| **Total** | **1,654** | **18** | **1,672** |

Four test methods independently enumerate **4,416 finite cases**:

- 4,096 interval/graph combinations, checking order feasibility against explicitly enumerated event-date assignments.
- 256 directed graphs, checking shortest routes against all simple paths; cases include cycles, unreachable goals and equal-cost routes.
- 36 interval pairs, checking chronology relations against every possible pair of dates.
- 28 uncertain event spans across a BCE/CE transition, checking period membership against explicit sets of dates.

These are subcases inside four test methods; they are not counted as thousands of additional unit tests. The checks use independent finite reference methods, not copies of the production algorithms. Map and chronology passed their additional checks without implementation changes.

The additional contract integration follows a synthetic calendar-boundary source through event-order reasoning, the existing teaching-order decision contract and an artifact lineage graph. The contradiction reaches the review gate and retains its source locator. This is synthetic contract evidence, not real-book E2E or a rendered/playable product.

Required gate executed: `python -B scripts/integrated_check.py`. Result: **413 test files, 1,672 tests, zero failures, zero errors and zero skips**. Recorded outputs:

- `before.json`: failing pre-fix tests against the original implementation.
- `baseline.json`: original task records, test summary and immutable source commit.
- `after.json`: passing added checks, full-suite summary, source and test SHA-256 hashes.
- `../../../validation/integrated_tests.json`: per-file integrated results.
- `../../../validation/verification_fingerprint.json`: hashes of the tested code/configuration.

## Preservation and canonical integration

The independent canonical integrity gate passes:

- 796 original archives and all 12,439 original member files checked.
- Assembly-001's 273 archives and 2,450 files remain accounted for.
- All 10,942 ledger destination paths match their recorded hashes.
- Migration dispositions remain 824 MIGRATED, 11,226 ARCHIVED_EVIDENCE and 389 DUPLICATE_WITH_PROVENANCE; zero exclusions and zero unavailable archives.

Original archives, historical snapshots, migration ledgers and historical task evidence were not changed. The fixes are in active `bie/reasoning/`; their new tests are in active `tests/reasoning/`. Existing `app.bie` compatibility behavior remains covered by the integrated suite. No archive path or legacy implementation was introduced into production imports.

Task `SPEC.md` and `TASK_RESULT.json` files, the batch registry, continuation state, code fingerprint and current-state documentation were updated. Original primary test counts remain distinguishable from additional quality counts. The three corrected implementations are revision 2; map and chronology remain revision 1.

The stale `docs/bie/REPOSITORY_ASSEMBLY.md` now has an explicit historical-snapshot notice. Its old content is retained and directs readers to the current canonical state. This addresses the forensic audit's documentation warning without rewriting historical evidence.

## Synchronization and reproducibility

The prior actual tiny-write proof is commit `4b35084be062ae17b2b8ac8d99af78030e7c42e4`. This review's actual source commit/tree and readback are recorded separately in `validation/github_sync_quality_001.json` after synchronization. That receipt identifies the source checkpoint; the full downloadable ZIP's `BACKUP_MANIFEST.json` identifies the final commit including its receipt.

No synchronization success should be inferred from this report alone. Use the actual branch ref, commit/tree and receipt readback. The delivery report supplies the exact verified SHA values and full-backup hash. The backup is generated from the committed repository and its member hashes are checked against Git.

No GitHub Actions run was triggered manually. The earlier audit found no CI run proving the 1,654-test result. The 1,672-test result reported here is the executed local canonical integrated gate; it is not a claimed GitHub Actions success.

## Section completion and next development

**Current outcome: HARDENED, IMPLEMENTED, NOT ACCEPTED.** The five demonstrated defects are closed; the overall section completion gate remains OPEN.

| Remaining requirement | Current evidence/status |
| --- | --- |
| Authoritative Reasoning roadmap after RE-TEMP-003 | UNRECOVERED. The repository has `next_task_ids: []`; targeted prior-context and file searches did not recover approved successor IDs/titles/dependencies. No successor was guessed. |
| Diverse real-book integrated Reasoning validation | PENDING. Finite and synthetic contract checks do not establish this. |
| Downstream video compiler, actual render and QA/repair | PENDING acceptance evidence. |
| Playable revision-game runtime and QA/repair | PENDING acceptance evidence. |
| Governed cumulative-learning evaluation | PENDING acceptance evidence. |

The correct next position is **after RE-TEMP-003**, not a reset to Assembly-001, Prerequisite, Math or early Reasoning. A subsequent numbered roadmap batch requires the original authoritative next block. Justified quality hardening may be added under governed records, but it must not be presented as a recovered historical roadmap task or as product acceptance.
