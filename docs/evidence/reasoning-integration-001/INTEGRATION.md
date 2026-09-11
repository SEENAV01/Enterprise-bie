# Central Reasoning canonical integration 001

**IMPLEMENTATION-SCOPE COMPLETE — NOT ACCEPTED.** This is integration of the supplied completed tasks into the existing BIE architecture. No new task IDs were created.

## Scope and authority

The exact user prompt is preserved in `USER_INTEGRATION_PROMPT.txt`. The pre-integration remote main commit was `03f32e193736904a02aac4544d88c0c3b498c4c2`, tree `636596304406b10b03f1c751b43e82f01fe11f76`. The original workspace had 29 uncommitted paths from the earlier five-defect quality review. They were preserved, recorded, and applied in an isolated integration worktree. The original workspace was not reset or overwritten.

The 77 original ZIPs were recovered from actual saved artifacts: 56 TEMP-004..059 packages, five original-roadmap RE-QA-001..005 packages, and sixteen enterprise-hardening packages. Every archive and all 483 members were read and hashed. There were zero different-content destination collisions. All declared source hashes matched the supplied source bytes.

## Migration

- Original ZIP bytes reside under `backups/ingested/`; no historical ZIP or original historical ledger was rewritten.
- The 56 incoming `app/bie/reasoning/` modules map to `bie/reasoning/`. The other 21 already use `bie/reasoning/`.
- Forty-one import statements were normalized by inspecting actual Python import nodes. Path literals in migration helpers were retained.
- Ninety-eight empty atomic initializers remain archive evidence. Existing canonical initializers, package identity, and compatibility imports were preserved.
- All 77 task test files are in `tests/reasoning/`. TEMP-014..018 contain 25 plain function tests: the supplied TEMP-055 bridge now exposes them as real unittest methods. Their exception checks use `unittest.TestCase.assertRaises` with the same exception types; original assertions and inputs were retained. No pytest dependency or fake pytest module was introduced.
- Each task has canonical `SPEC.md`, `TASK_RESULT.json`, and `TEST_RESULT.txt`. Exact original task records and logs are retained as `ORIGINAL_TASK_RESULT.json` and `ORIGINAL_TEST_RESULT.txt`, as well as inside the original ZIP.
- `manifests/reasoning_integration_001.json` records each original member, its SHA-256, destination/disposition, transformations and final canonical hash. `RECONCILIATION.csv` has one row per archive.

## Integration findings corrected under existing task IDs

The unmodified supplied assertions passed 323 task tests after namespace/discovery adaptation. The initial complete enterprise run passed 1,995 tests. Required additional cross-contract checks then exposed 11 failing test methods (14 failure entries including subtests, plus two errors). Those tests were retained unchanged after corrections; all 21 now pass.

| Existing task | Correction |
| --- | --- |
| TEMP-013 | Materialize constraints and periods before reuse so synthesized input lineage and fingerprints retain one-shot iterables. |
| TEMP-018 | Materialize events, constraints, periods and evidence once before invoking multiple temporal components. |
| CAUSAL-HARD-004 | Retain contradicting evidence IDs in result evidence and an explicit contradiction field. |
| GRAPH-HARD-001 | Canonicalize directed cycles by rotation, preserving edge direction; retain self-loop witnesses. |
| STATUS-HARD-001 | Normalize the published Temporal `ABSTAIN` spelling to central `ABSTAINED`; retain review semantics. |
| CROSS-HARD-001 | Apply the existing 0.75 critical review boundary to low-confidence arbitration. |
| PROV-HARD-001 | Reject a low-confidence envelope that claims review is unnecessary. |
| E2E-HARD-001 | Fixture gate respects arbitration's review flag. |
| SPATIAL-HARD-001 | Reject nonfinite coordinates before compatibility checks or transformation. |
| UNC-HARD-001 | Reject nonfinite uncertainty bounds before producing an assessment. |
| INTEGRATION-HARD-001 | Detect cyclic derived-parent lineage and report cycle-blocked artifact IDs; such lineage cannot pass. |

Exact source changes are in `INTEGRATION_CORRECTIONS.patch`; failures are in `cross_contract_before.json`. The additional public result fields have backward-compatible defaults. These are documented integration corrections to the supplied tasks, not overwritten archive content or newly invented roadmap tasks.

## Actual verification

| Scope | testsRun | Failures | Errors | Skipped | Failed files |
| --- | ---: | ---: | ---: | ---: | ---: |
| TEMP-004..059 | 253 | 0 | 0 | 0 | 0 |
| RE-QA / hardening | 70 | 0 | 0 | 0 | 0 |
| Additional cross-contract checks | 21 | 0 | 0 | 0 | 0 |
| Complete `tests/reasoning` | 453 | 0 | 0 | 0 | 0 |
| Complete enterprise suite | 2,016 | 0 | 0 | 0 | 0 |

Scopes overlap and must not be summed. All 77 new production modules passed actual canonical import smoke checks. Static inspection found zero production imports from historical, backups or batches; loaded-module inspection likewise found zero archived implementations. Migration helpers retain legitimate staging-path literals and the unittest bridge is a test adapter; neither activates historical production code.

The original 796 archives / 12,439 files remain intact, including Assembly-001's 273 archives / 2,450 files. All 77 additional original ZIPs and 483 members were independently rechecked. The 1,012-file source/test/script fingerprint matches the tested bytes.

Recorded outputs are under `validation/reasoning_integration_001/`. The mandatory runner is `python scripts/test_enterprise.py`; the preservation plus enterprise gate is `python scripts/integrated_check.py`. Standard unittest discovery also executed all 453 Reasoning tests. This is local execution evidence, not a claim of GitHub Actions execution.

## Warnings and acceptance blockers

The five original RE-QA package logs recorded zero executed tests, and some supplied logs contain an unrelated spreadsheet startup warning. Original logs are preserved. Fresh canonical results establish the current executed counts; package reports alone were not trusted.

These checks and source-anchor fixtures are synthetic. They do not demonstrate an actual textbook processed through BI/KI/PR/MATH into RE, downstream PED/DIR/QA consumption, benchmark/product acceptance, a rendered video, or a played revision game. Graph all-cycle enumeration has no enterprise scale benchmark in this batch. Those acceptance limitations remain explicit.

One integration commit is authorized after green verification. Exact final commit/tree/blob readback is written to the delivered report and full backup manifest after committing. The source record does not fabricate a self-referential commit SHA or require a second receipt commit. Any failure to synchronize must be reported separately from local implementation completion.
