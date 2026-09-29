# Section 16 recovery — active, not signed off

Authority: current user launch instruction and the complete verified
`BIE_CODEX_SECTIONS_16_17_18_MASTER_PROMPT.txt`. Task 028 stays paused.

## Verified recovery

- Handoff deep verification passed (see `handoff-deep-verification.json`).
  This proves byte integrity only, not implementation or product acceptance.
- Source archive SHA-256:
  `d4a3160e93f47ec510c8162309580b3df4fa3a8346211eb4197905a0399e24f1`.
- Scope supplement SHA-256:
  `fafa9f2e68cb00feadf22fe8b554fcab2377fded64ab4894e7091d8562a24b89`.
- Original checkout `C:\BIE\Enterprise-bie` remains clean on main at
  `dfc1ef9b59bf7d3a8f099a8ad2fb4a93895257e8` as observed before work.
- Fetched canonical main is `a68e054025b8fe7756a71e998d9e9103dad8e0f4`.
- Isolated worktree: `C:\BIE\s16-hard039`, branch
  `codex/section16-hard039-recovery`, initially clean at that canonical commit.
- An initial checkout under the longer OneDrive path failed on Windows path
  length. Git removed that failed worktree registration; no original checkout
  files were altered. The short-path retry with per-command long-path support
  completed successfully.
- Read canonical AGENTS, handoff, current state and global continuation from
  the fetched worktree. Preserve Section 15 and all earlier productization.
- Read original registry PDF pages 17–21 and its supplied navigation extract:
  76 QA, 50 EVAL, 33 APP original tasks. Section implementation sign-off is
  separate from final product acceptance.

## Active work

HARD-039 remains active. No obligation has been closed. The strict read-only
collision plan PASSED: 14,408 entries, 235,455,805 verified bytes, 278 new QA
source paths, 635 support paths, 33 identical native references, two differing
existing files and 13,460 archive/section-metadata paths. The differing native
infrastructure initializer is preserved. No cumulative ZIP overlay was applied.

The metadata-only legacy release source was selectively adopted byte-exact.
It returns CONTRACT_ONLY, not SUCCESS; authorization and product acceptance
remain false. Its current imported assertion is strengthened. Two byte-exact
canonical before-images are preserved. A narrow two-row amendment validates
the original ledger, both predecessors and both replacements; the sealed
lossless ledger is not edited. All other canonical audit checks remain active.
Tracked caller search in bie/apps/scripts/tests found only the imported release
test and Director QA tests, not an additional production consumer.

Fresh actual-worktree tests: 47 unique tests PASS, zero failures/errors/skips:
10 imported release, 8 Director, 15 new fail-closed and 14 preservation tests.
The base had passed the 18 existing tests; the unmigrated caller with candidate
source reproduced exactly one expected SUCCESS/CONTRACT_ONLY failure. Repeated
variants are not additional unique tests.

Separately, 43 existing complete-parser tests passed using candidate QA with
current native math types. This is not source adoption or broad math closure.
H1 on Windows failed: 114 os.geteuid setup errors plus one missing-jsonschema
test-module import. No assertion/security-stub success is claimed. Use the
approved Linux environment; don't weaken POSIX/browser security for Windows.
The QA supplied profile pins pypdf 5.9.0 versus canonical DI 6.19.0; reconcile
and test while preserving the canonical dependency, not downgrading it.

Preserve the full source-grounded, academically correct cinematic video and
meaningful playable-game vision, reusable concept/scene/code memory and governed
improvement. Missing implementation cannot be silently deferred to EVAL, and
final product acceptance is not a prerequisite for implementing downstream work.

## Required continuation

1. Execute the changed candidate through the approved hosted canonical gate.
2. Retain the reviewed release compatibility correction, before-images and 47
   passing scoped tests. Full combined/native regression remains unverified.
3. Selectively adopt verified QA source/tests, never overwrite native dependency
   snapshots, QA initializer, global continuation or Android work.
4. Recheck all 17 historical-local records, resolve 14 capability-review records
   with actual registered implementations, and retain 52 integration / 30 final
   deployment-and-acceptance records with evidence-based dispositions.
5. Complete native integration/regression, audit and re-audit before Section 16
   sign-off/integration, then execute original Section 17 and Section 18 scope.

No section completion, production deployment, merge, or product acceptance is
claimed by this recovery checkpoint. HARD-039 is active and HARD-040 integration
is incomplete. See the containing Git commit and subsequent CI receipt for
remote state; this record grants no merge authorization.

## Controlled adoption checkpoint (2026-09-29)

Recovery commit 0efcb1599880dbabf7eb8ac196515b45364a46e1 passed hosted run
36506727442: 9,327 tests / 1,245 files, zero failures/errors/skips. Downloaded
artifact 11007774576 was independently hash-, count- and preservation-verified;
see `docs/evidence/qa-section16/recovery-001/HOSTED_CI_VERIFIED_001.json`.
That result does not cover the following newly staged QA additions.

Read `CONTROLLED_ADOPTION.md`, `manifests/qa_section16_adoption.json` and
`scripts/section16_gate.py` for the 817 hash-bound addition-only candidate.
The new combined workflow retains the approved canonical gate and executes all
32 supplied QA suites explicitly. Its complete current-candidate result remains
pending until actual hosted evidence is checked. Do not reuse recovery CI as
this candidate's pass. The 14 capability reviews and 17 historical rechecks
remain open; source adoption is not obligation closure or section sign-off.

## Combined candidate run 36518073587 — failed, evidence retained

The exact candidate 1e8022138597771b75450ac1766c2ce0d9447cfd
passed the complete canonical gate: 9,351 tests across 1,246 files with
zero failures, errors or skips. All 4,856 explicitly selected Section 16
tests executed on Linux. Two positive synthetic full-chain checks failed:
qa_hardening_h8 completed 0 of 15 diagnostic stages (154/155 passed),
and qa_reaudit_002 observed the same 0 of 15 (89/90 passed).
Other 30 suites passed their expected counts. This is a genuine candidate
gate failure; no section completion or obligation closure follows from it.

The hosted failure artifact is section16-combined-candidate-evidence,
ID 11012670386, SHA-256
6f528458028cf91b835d1e03f07b1c775a0d21e6628acae4e15c4e4a7595c607.
Both inherited assertions are unchanged. The focused script
scripts/diagnose_section16_pipeline.py will record bounded synthetic
first-stage process errors on a failed rerun. It grants no acceptance,
relaxes no test, and contains no real document input.

## Confirmed synthetic fixture defect — follow-up candidate pending CI

Run 36521339502 on diagnostic commit 37c5a780ae54fc1ebe2d86fb62ef378bb3042cd0
again failed the Section 16 gate after the canonical gate. Its artifact
11013603923 has SHA-256
951f4824c06cae1c9893726464c0c13b5a50de313c340dba7f39471082811990.
The bounded H8 diagnostic recorded the two-stage fixture completing BI and KI,
while the 15-stage fixture exited at BI before any completion. The actual
stderr shows Python importing the generated `re.py` stage instead of its
standard-library `re` module; `json`/`glob` then fails on missing `re.compile`.

This is a synthetic fixture import collision, not evidence of a production
pipeline defect. The scoped repair runs fixture scripts with Python `-I` so
other generated stage names cannot shadow standard-library imports. Neither
inherited full-chain assertion nor production engine source was altered.
The original 817-path adoption manifest remains byte-identical. A separate
`qa_section16_amendments.json` records the one changed fixture's original and
new hashes, byte lengths, reason, failed run and artifact digest; the gate
rejects any unrecorded addition or byte drift. Local amendment verification
and 28 seeded positive/negative gate tests pass. Full hosted QA remains
unverified for this new candidate, and no capability/section signoff follows.

Run 36524548405 on repair commit eb17b170a85d038ad2d18318e25903a83cd2b55c
passed the canonical 9,355-test gate and every explicit Section 16 candidate
suite (4,856/4,856 unique test IDs; H8 155/155 and Re-audit 002 90/90).
The workflow itself still concluded FAILURE at the final combined-receipt step:
that unprivileged step attempted to write into `section16-evidence`, a directory
created by the approved root supervisor. The traceback was `PermissionError`
for `COMBINED_RESULT.json`; no test or preservation check failed. The CI-only
repair writes this final receipt into the already runner-owned
`canonical-evidence` directory, which the same workflow uploads. This is not
an acceptance decision until a fresh exact-commit workflow succeeds and its
artifact is independently inspected.
