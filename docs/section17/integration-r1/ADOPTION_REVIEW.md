# Section 17 R1 controlled adoption review

This is a source-integration candidate, not Section 17 sign-off or product
acceptance. Task 028 remains paused; Section 18 is unchanged.

- Canonical comparison main: `8b8e500bf7b83addfcecce41c3fca08563eceb41`.
  This main includes the Section 16 QA implementation merge, but its own
  recovery ledger still records HARD-039/HARD-040 and operational acceptance
  obligations as open. A merge alone is not Section 16 sign-off.
- Source master: `Section17_R1_Master_RESTORED.zip`, 383,934,041 bytes,
  SHA-256 `03043839a2290672a4b672cbb39952846e77ff99572a791bf0ca89cf14a51f4e`.
  `VERIFY_MASTER.py` verified all 2,517 manifest payload files. The 103
  atomic ZIPs remain in that external master; they were not overlaid on Git.
- Read-only R1 preflight: 2,029 mapped paths; 0 direct collisions, 780 absent
  adoption candidates, 277 identical dependencies, 36 differing dependency
  checkout bytes, 920 historical-only paths, 15 generated caches, and one
  reviewed QA CLI route patch. The JSON plan is retained outside this checkout.
- Of the 36 differing dependencies, 34 normalize exactly to the same LF bytes
  and hashes recorded in the master. The remaining two are the canonical
  Section 16 `bie/infrastructure/__init__.py` and hardened
  `bie/math_intelligence/expression_ast.py`; both are preserved. No native
  dependency file was copied from the master.
- The 780 new files consist of 175 `bie/evaluation/benchmarks` files, 127
  Section 17 test/support files and 478 scoped docs/metadata/tools/examples.
  Each source file was SHA-256 checked against the preflight map before
  copying into an absent target. No `__pycache__` or `.pyc` was adopted.
  `SOURCE_INTEGRATION_MAP.json` and `ADOPTION_AMENDMENTS.json` are retained
  in this directory; `scripts/verify_section17_adoption.py` verifies all
  780 adopted paths, 13 reviewed amendments (three integration adaptations and
  ten EOF-only test formatting fixes), the original CLI route patch,
  and the absence of 15 generated caches. Its local result passed.
- The existing QA lifecycle CLI's Git blob SHA matched the package's stated
  predecessor. The two explicit `eval-api` and `eval-campaign` routes were
  applied by review; the original journal-inspection route remains present.
  The new CLI's LF-normalized SHA-256 matches the package's published
  `7bc0c5b937d14a4918349f377716d213e9447812aac2f8d5f443bda0b7f6ee0e`.
- The canonical `BenchmarkAPI` Git blob matches the package pin. Windows Git
  materializes it with CRLF, so the Section 17 caller accepts only an exact
  CRLF-to-LF reconstruction that still matches both pinned SHA-256 and Git
  blob SHA-1. Altered content remains rejected. The canonical API source is
  not changed.

The canonical integrated gate now runs the adopted Section 17 suite with an
exact 2,023-method census: 2,018 recovered methods plus five new checkout-pin
controls. Missing, duplicate, failed or skipped methods fail closed. The
existing 37 native durable-worker tests are already present byte-identically
in canonical Section 16 tests; they are not counted again as new tests.
Local targeted checks passed: 20/20 Metric 001 methods, 5/5 checkout-pin
methods, and 10/10 adoption/gate-control methods. The inherited preflight
test file has a Windows symlink-privilege setup error (`WinError 1314`), so
its combined local run was not a clean pass; its hosted Linux run remains
required. The complete Section 17/native/browser suite has not yet passed
against this exact repository candidate.

The adopted `native_api.Service` composes the canonical `BenchmarkAPI` with a
fixed PlanRegistry, Campaign and operator-owned Admission registry. Its
operator CLI is a local library/command route, **not** an HTTP service,
distributed authorization, or a general job-host integration. Actual
book-to-native-video/game production and independent full-metric evaluation
remain unexecuted and cannot be inferred from authored fixtures.

Historical master-only gaps are carried forward from the R1 master: exact H3,
H5, Native Campaign and Native API master containers, two old H5 helper
scripts, and other stated fingerprints have not been fabricated or relabelled.
The complete archive and original gap ledger remain in external preservation.

Local Windows verification boundary: the host Git configuration has
`core.autocrlf=true`. `scripts/verify_assembly.py` hashes working-tree bytes
of historical text snapshots, and this Windows checkout materialized CRLF
where the immutable manifest records LF. Its local run therefore reported
historical `Imported source mismatch` errors (for example
`batches/BIE_AST_001/TASK_RESULT.json`), even though `git hash-object` of
that path matches its committed Git blob. Historical files and the verifier
were not altered to make the check pass. The complete preservation gate must
run in the approved Linux checkout and its exact candidate result must be
inspected before PR/merge readiness is claimed.

The hosted run `36675956256` tested commit
`3910368ad81fab63ce9597d90b7b0209bed241e1`. Its 9,470-method enterprise
run failed in `tests/assembly/test_section16_gate.py`: the Section 16
adoption guard rejected the reviewed two-route QA CLI extension as
`ADOPTION_BYTES:bie/qa/lifecycle_quality_v2/__main__.py`. The downloaded
artifact `11079729909` matched GitHub's SHA-256
`9ffe35161373349681cd5127c237a2dff0149d7e1a992c3575ef39c2d898b1d8`.
The Section 17 suite had not run because the earlier gate failed.

The scoped integration repair preserves the original Section 16 adoption
manifest and adds one explicit cross-section extension to its guard. The
original CLI row must still match its original 1,659-byte hash; the extension
must match the R1 patch-binding document and its exact 2,010-byte candidate
hash. The guard reports this extension separately from Section 16 amendments.
Three seeded-negative controls reject altered original rows, binding data,
and CLI bytes. All 39 guard tests passed on an isolated Git-blob snapshot
exported with `core.autocrlf=false`; the first Windows export used host CRLF
conversion and was invalid for byte-preservation testing. No historical
evidence or guard was normalized to conceal that difference.

The five existing journal CLI behavior tests and the existing structural
schema test passed (6/6) with the pinned `jsonschema==4.26.0` installed in an
external validation directory. The broader 11-method file is not claimed
as a Windows pass: Linux-only secure artifact I/O rejects this host. Hosted
Linux validation remains mandatory. Section 17 adoption verification still
passes for all 780 files and 12 documented amendments.

The shared approved browser setup now exports its regular executable path
for every subsequent combined-gate caller. Section 16 combined CI is also
enabled for this explicit integration branch, retaining its 4,856-method
denominator and the complete enterprise/Section 17 checks. These changes do
not change browser isolation, production algorithms, historical manifests,
or the remaining real-book/independent-assessment acceptance obligations.

Canonical-runner provenance is the third integration adaptation. The recovered
standalone runner could add a sibling `dependency_snapshot` to `sys.path` and
always described that snapshot in its receipt. The canonical runner no longer
imports that location. It records every loaded BIE file/namespace origin and
fails if an origin is missing or outside this checkout's `bie/` tree. The
Section 17 gate requires this origin result and an explicit false value for
external-snapshot use. The amended runner's original and replacement hashes
are recorded without changing the supplied master or original integration map.
Positive and seeded-negative runner/gate/adoption controls passed 16/16 locally.

The exact `b834648ea5bd0631dabe21e8779d675e5a0881fd` hosted runs
`36690026670` and `36690026683` both failed when Section 17's H5-006
Chromium fixture could not start: `chrome_crashpad_handler: --database is
required`. The enterprise run nevertheless completed 9,479 methods with
zero failures/errors/skips, including 1,123 GAME methods. The separate
Section 16 gate completed its unchanged 4,856-method census successfully.
These results do not establish Section 17 completion. The combined artifact
`11087181799` was downloaded outside Git and verified against SHA-256
`de86376b5989cafe92f528818c3a6126328678d2cd8f443fb2da310d37d38f24`.

The recovered recorder then raised a secondary `KeyError` for `setUpClass`,
since unittest fixture failures do not call `startTest`. The repair records
fixture errors/skips separately from executed method identities, continues
the remaining suite, and rejects any such event at the gate. Expected
failures no longer receive a PASS status. Private temporary writable XDG
config/cache directories are scoped to the suite and restored/removed even
on failure; no browser security flag, authored browser assertion, or GAME
isolation policy was weakened. Fresh hosted validation is required to
confirm this addresses the Chromium startup failure. An early eight-method
H5-006 preflight now runs before the expensive enterprise regression.

The previous combined receipt incorrectly considered only enterprise and
Section 16 results even after the Section 17 step failed. Its workflow still
failed, but that receipt must not be reused as complete integration evidence.
The combined receipt now requires the exact Section 17 gate and adds its
2,023 methods only after proving the enterprise file census excludes
`tests/section17/`. The existing ten-method legacy release overlap between
enterprise and Section 16 is still deducted. Positive and seeded-negative
runner/gate/adoption controls passed 23/23 locally after these repairs.
