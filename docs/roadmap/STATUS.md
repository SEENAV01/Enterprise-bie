# BIE Status

Updated: 19 October 2026 · Read this first in every new session, then show Navin the current task card.

## Now

| Field | Value |
| --- | --- |
| Phase | 0 · Foundation |
| Current task | 037C · Let working source evolve (proposed; waiting for Navin's approval) |
| Branch | — |
| State | Proposed |
| Next task | 038 · Live AI and the blind test |
| Canonical main | `d464d7f79bb80c6ffe36c9feb335ea3e29c9a346` (Task 037A and 037B merged) |

## Done

| Date | Task | Result |
| --- | --- | --- |
| 2026-10-19 | 036 · Scene IR producer | Canonical-complete within its bounded scope; PR #29 and #30 merged; exact-main CI green |
| 2026-10-19 | Local work rescue | Director Step 4 and Step 5 pushed as `wip/task036-director-step4` and `wip/task036-director-step5` (not merged) |
| 2026-10-19 | 037A · Repository memory | `CLAUDE.md`, Vision Spec, roadmap and this file; PR #31, merged through PR #32 |
| 2026-10-19 | 037B · Fast lane and CI debts | PR #32 merged at `d464d7f7` after all 12 checks passed on its final head `ad1436e5`. F-08 instrumented, not closed |

## Task 037B · what changed

- **Fast lane.** PRs that change only `CLAUDE.md`, `docs/roadmap/**` or `docs/vision/**` skip the three heavy gates. Every other change still runs them; they also run on each push to `main` and nightly (Post-DIR 20:30 UTC, Section 18 21:30 UTC, Section 16 22:30 UTC). A newer push to a PR cancels that PR's older run.
- **Task 036 review lock removed** (approved by Navin). `engine_identity` records hashes of the Scene IR code that actually runs; it no longer refuses to run when the 210 reviewed files change. The sealed review records stay in `docs/productization/`. The workflow-byte profile pins and their tests were removed; the dependency-version checks remain. Scene IR lane after the change: 381 of 381 tests pass on Linux.
- **M1 `verify` limit** raised from 45 to 60 minutes (it used 35m35s on exact main `b3ce527f`).
- **CI failures are now readable from here.** Each heavy job prints a bounded failure summary (failing lanes, test identities, last exception line) as run annotations, which `gh api` can read even though logs and artifacts cannot be downloaded.
- **F-08 — instrumented, not yet closed.** At least six recorded failures in at least four runs (Task 033 post-merge, D5, D7 and one more two-failure run) all show the same picture: `Page.navigate` (CDP call 7) never answered within 10 s, the operator server answered `/healthz` with 200, the browser was alive, no response for `/` arrived. Phone, tablet and desktop modes all failed, so it is not one layout. Finding: the old harness reported a closed DevTools socket with exactly the same code, so the evidence could not tell the two apart. Changes: a closed socket is now reported at once as `CDP_SOCKET_CLOSED`; the diagnostic now records whether the request was sent, whether the frame started loading, the socket state and close code, and whether the page target was still listed; the browser starts with the standard automation switches Playwright uses for this same Chromium build; the failure is published as a "Section 18 browser failure" annotation. Regression tests: `tests/section18/test_browser_journey_cdp.py` (scripted DevTools endpoint; they fail on the old harness). Local repeat run: 0 stalls in 300 fresh-profile navigations on Chromium 141 (slowest 138 ms), so the stall did not reproduce here; the new switches made no measurable difference locally (median 18 ms either way). FR-1 stays until the new evidence names the cause or the nightly runs stay clean.

## Open decisions for Navin

- [x] Approve the fast lane (037B) — yes, 19 October 2026.
- [x] Who presses merge — Claude, once CI is green (19 October 2026).
- [x] Remove the Task 036 review lock — yes, 19 October 2026.
- [ ] Approve 037C (let working source evolve; evidence stays frozen).
- [ ] The repository is public: anyone can read the code, the Vision Spec and this roadmap, and CI minutes are free. Keep it public, or make it private (heavy CI then uses paid minutes)?
- [ ] Providers for the blind test (Claude, OpenAI, Gemini) and the monthly budget.
- [ ] First book, chapter and class level (ideally a subject Navin teaches).
- [ ] First language: Hindi, English or Hinglish.
- [ ] Narration voices.
- [ ] What the Dhanteras goal becomes (a pilot of a few chapters?).
- [ ] Parked Director Step 4–6 work: finish, rework or drop.
- [ ] Where courses are published first.
- [ ] Meaning of "real video lectures": teacher or avatar on screen, or fully animated.

## Known technical debts

- F-08: Section 18 browser gate flake (`CDP_TIMEOUT:Page.navigate`); instrumented in 037B, cause not yet proven. FR-1 allows one recorded rerun per job only for that exact failure (or `CDP_SOCKET_CLOSED:Page.navigate`).
- npm drift (found and fixed in 037B): from 17 October the Section 18 `native-render` job failed on every PR, docs-only #31 included, with `TOOLCHAIN_REMOTION_PAIR: mixed versions`. Cause, shown by the drift canary: the generated Remotion project has no lockfile, a newer webpack now gets hoisted, and npm nests Remotion's exact `webpack@5.105.0` under `node_modules/@remotion/bundler/`; the pairing check counts every entry under that prefix, including this non-Remotion package. 037B resolves those installs, and the M1 render runner's, as of 17 Oct 2026 12:00 UTC (`tools/npm_before.txt`); native-render is green again and the canary keeps reporting today's unpinned tree. Follow-up: commit a real lockfile and narrow the check to Remotion packages (needs 037C because the check is source-pinned).
- F-09 (seen once, passed on the next full run): Section 18 atomic `CancelRecovery.test_actual_two_process_cancel_returns_same_completed_state` failed in PR #32 run 39292713985 (both child processes exited 1). It passed on PR #31's run and 90 of 90 times locally (30 of them under full CPU load). Suspected: SQLite's 1 s busy timeout while two processes prepare the same cancel on a slow runner, so one child gets "database is locked" and the other times out at the test's 8 s barrier. Not proven; failure annotations now include the children's stderr.
- Source pins: `scripts/audit_canonical.py` and `scripts/verify_post_dir.py` byte-pin migrated working source (Task 037C).
- N-02: Section 18 source-ledger step slowed from 21 s to 612 s.
- Audio reconciliation open (`AUDIO_REPLAN_REQUIRED`); global VIDEO_CODE and later stages not run.
- PR29 follow-ups F-01..F-07 and PR30 follow-ups F1..F5 (low, non-blocking).
