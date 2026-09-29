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
