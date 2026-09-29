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

## Parser preservation and native-PDF math linkage checkpoint (2026-09-29)

The current isolated branch remains `codex/section16-hard039-recovery` on
canonical base `a68e054025b8fe7756a71e998d9e9103dad8e0f4`; the separate
original checkout has not been changed. Native `expression_ast.py` was found
to silently drop the `+ z` suffix in `x * y + z`. The corrected parser and
three strengthened inherited assertions are in commit `10c5f7c6`. The first
hosted canonical check exposed a lossless-ledger preservation conflict rather
than a parser test failure. Commits `6a22063d` and `cf78aa4f` preserve the
605-byte exact predecessor in governed evidence and apply a narrow,
source-archive-bound amendment without changing the sealed ledger. The
replacement parser's SHA-256 is separately pinned.

Hosted run 36539425191 on commit `6a22063d` passed the complete canonical
gate (9,381 tests) and Section 16 explicit gate (4,856 tests), with 10
overlapping IDs: 14,227 unique combined tests, zero required failures/errors/
skips. Evidence artifact 11020382247 has SHA-256
`8d06b05bcfc297ebf0ac7819abac65910628976f82bae49ecd1f1dd72ecbb6ad`.
This passing run predates the archive-identity tightening and PDF bridge;
it must not be reused as their exact-candidate receipt.

Commit `c595c612` adds one hash-pinned QA bridge from an operator-selected
canonical native-PDF text block to the corrected native math parser. It
retains source hash, page, region and geometry, emits only safe hashes/counts,
and fails closed on unsupported notation. Local tests: bridge 15/15,
adoption gate 36/36, targeted inherited adapter tests 16/16, and unchanged
817-path adoption verification PASS. The private 20-page Money PDF kept its
verified source hash and 755 source-linked blocks, but had zero strict
operator-containing math lines; its math capability is **not** validated by
this observation. No PDF or extracted text was committed or uploaded.

The exact `c595c612` hosted run 36542478700 passed: canonical 9,402 tests,
Section 16 4,856 tests, 10 overlapping original release tests, and 14,248
unique combined tests, with zero required failures/errors/skips. The uploaded
artifact is 11022043961, SHA-256
`c22b4d4488ec0b6974e6f3e1e4a023767319cb4c73b8381534d9443c714e142e`.
The workflow receipt explicitly records `section16_signed_off: false` and
`product_accepted: false`. A duplicate run 36542480007 was queued behind it;
its eventual result is separate. Section 16 is **not signed off**.
All 14 local capability-review records remain open, as do the 52 integration
and 30 deployment/acceptance records. The 17 historical local rechecks still
need candidate-bound disposition; passing a linked synthetic suite alone does
not close an original obligation. HARD-039 stays active, HARD-040 incomplete,
Task 028 paused, Sections 17/18 not started, and product acceptance false.

The only `BookPlan(` registration found under `bie/`, `tests/` and `scripts/`
is `tests/qa_hardening_h8/h8_helpers.py`, whose generated source is
`source.txt` and whose default profile is `DIAGNOSTIC`. A complete native
15-stage plan for an authorized real book has not been provisioned or
executed. Actual source-to-lesson/media/game output, independent semantic
and pedagogic assessment, native render/playable traces, and applicable
rights/authority remain required before any unqualified sign-off. The next
decision is to inspect the exact latest CI receipt, then resolve the remaining
capability and native integration obligations with positive and seeded-negative
evidence; do not infer completion from the synthetic full-chain fixture.

The 17 historical local-fix records are now crosswalked against the exact
passing candidate in
`docs/evidence/qa-section16/recovery-001/HISTORICAL_LOCAL_RECHECK_002.md`.
All 17 original IDs are present and remain OPEN; the record separates tested
local controls from unfulfilled native/operational requirements. The user has
specified configuration-driven OpenAI generation and independent Gemini-family
assessment through the existing model gateway. No OpenAI key was found in the
current process or the worktree's `.env`/`.env.local` locations; other approved
secret stores were not inspected. No live validation has run. Until
secure provisioning is approved, both live lanes are
`BLOCKED_BY_CREDENTIALS`; ordinary Section 16 CI stays credential-free.

The next credential-free controls and their exact limits are recorded in
`docs/evidence/qa-section16/recovery-001/NONCREDENTIAL_CONTROLS_001.md`.
They add a finite GAME branch/remediation/transfer/reset route census and a
real-PDF-to-H8-plan preflight outside the sealed adoption inventory. The
private Money PDF retained its verified 20-page/755-block baseline and the
safe preflight was deterministic, but all 15 native stage programs remain
unregistered for that real-book plan. No content generation, video rendering,
playable browser run, live assessment, rights clearance, or Section 16 sign-off
is claimed. The new candidate still needs hosted combined regression.
The exact 14-record capability review is separately dispositioned in
`docs/evidence/qa-section16/recovery-001/CAPABILITY_DISPOSITION_002.md`:
bounded controls, remaining implementation, candidate-native evidence and
later product/deployment gates are not conflated. Every original ID stays OPEN.
