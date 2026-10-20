# BIE Status

Updated: 20 October 2026 · Read this first in every new session, then show Navin the current task card.

## Now

| Field | Value |
| --- | --- |
| Phase | 0 · Foundation |
| Current task | 038 · Live AI and the blind test |
| Branch | `task038-blind-test-run` (report fix and status); part 1 merged as PR #37 |
| State | Live connections INTEGRATED and run on a real chapter; blind-test report waiting for Navin's verdict |
| Next task | 039 · Understanding the book with AI |
| Canonical main | `398b1acee655d23523999a577c7d772032b764a9` (Task 038 part 1 merged) |

## Done

| Date | Task | Result |
| --- | --- | --- |
| 2026-10-19 | 036 · Scene IR producer | Canonical-complete within its bounded scope; PR #29 and #30 merged; exact-main CI green |
| 2026-10-19 | Local work rescue | Director Step 4 and Step 5 pushed as `wip/task036-director-step4` and `wip/task036-director-step5` (not merged) |
| 2026-10-19 | 037A · Repository memory | `CLAUDE.md`, Vision Spec, roadmap and this file; PR #31, merged through PR #32 |
| 2026-10-19 | 037B · Fast lane and CI debts | PR #32 merged at `d464d7f7` after all 12 checks passed on its final head `ad1436e5`. F-08 instrumented, not closed |
| 2026-10-20 | 037C · Let working source evolve | PR #34 merged at `dce749ed` after all 12 checks passed on its final head `377e313c` |

## Task 037B · what changed

- **Fast lane.** PRs that change only `CLAUDE.md`, `docs/roadmap/**` or `docs/vision/**` skip the three heavy gates. Every other change still runs them; they also run on each push to `main` and nightly (Post-DIR 20:30 UTC, Section 18 21:30 UTC, Section 16 22:30 UTC). A newer push to a PR cancels that PR's older run.
- **Task 036 review lock removed** (approved by Navin). `engine_identity` records hashes of the Scene IR code that actually runs; it no longer refuses to run when the 210 reviewed files change. The sealed review records stay in `docs/productization/`. The workflow-byte profile pins and their tests were removed; the dependency-version checks remain. Scene IR lane after the change: 381 of 381 tests pass on Linux.
- **M1 `verify` limit** raised from 45 to 60 minutes (it used 35m35s on exact main `b3ce527f`).
- **CI failures are now readable from here.** Each heavy job prints a bounded failure summary (failing lanes, test identities, last exception line) as run annotations, which `gh api` can read even though logs and artifacts cannot be downloaded.
- **F-08 — instrumented, not yet closed.** At least six recorded failures in at least four runs (Task 033 post-merge, D5, D7 and one more two-failure run) all show the same picture: `Page.navigate` (CDP call 7) never answered within 10 s, the operator server answered `/healthz` with 200, the browser was alive, no response for `/` arrived. Phone, tablet and desktop modes all failed, so it is not one layout. Finding: the old harness reported a closed DevTools socket with exactly the same code, so the evidence could not tell the two apart. Changes: a closed socket is now reported at once as `CDP_SOCKET_CLOSED`; the diagnostic now records whether the request was sent, whether the frame started loading, the socket state and close code, and whether the page target was still listed; the browser starts with the standard automation switches Playwright uses for this same Chromium build; the failure is published as a "Section 18 browser failure" annotation. Regression tests: `tests/section18/test_browser_journey_cdp.py` (scripted DevTools endpoint; they fail on the old harness). Local repeat run: 0 stalls in 300 fresh-profile navigations on Chromium 141 (slowest 138 ms), so the stall did not reproduce here; the new switches made no measurable difference locally (median 18 ms either way). FR-1 stays until the new evidence names the cause or the nightly runs stay clean.

## Task 037C · what changed

- **One rule** (`scripts/source_evolution.py`): working source (`bie/`, `apps/`, `tests/`, `tools/`, `scripts/`) may change through reviewed PRs; evidence (`batches/`, `historical/`, `backups/`, `docs/`, `manifests/`, `metadata/`) may not. Original archive members and recorded before-images are still checked byte for byte. A working file that differs from its adoption record is reported as evolved, not failed; a deleted working file still fails.
- **Applied to every gate-level ledger check:** `audit_canonical.py` (and its four amendment resolvers), `verify_ingested_archives.py`, `verify_post_dir.py`, `verify_section17_adoption.py`, `section16_gate.py`, the GAME adoption identity in `game_section15_gate.py`, the Task 035 provisioning guard and its CI-R1 file pins, and the post-DIR adoption test.
- **Compiler amendment chain:** its 13 sealed amendments keep proving their exact history, now against baseline copies of the 25 working files they authenticate (`docs/evidence/source-baseline-037c/`, taken from main `6fd0bdd4`, protected from line-ending conversion). Tests that build temporary roots start from those bytes (`tests/source_baseline_fixture.py`).
- **Proof:** in a copy where all 3,812 code files were changed at once, all five ledger verifiers passed (820 + 1,210 + 777 + 298 files reported as evolved), while a changed evidence file, before-image or baseline copy still fails. `tests/test_source_evolution.py` repeats this on every canonical run without writing any file.
- **Still pinned, on purpose or for later:** vendored third-party files keep their integrity checks (for example the React vendor bundle). Section 15 GAME runtime seals (`bie/game_engine/operations_engine/canonical_bindings.py` pins `bie/bie_core/artifact_contracts.py`, `bie/infrastructure/artifact_store.py` and `bie/infrastructure/idempotency_store.py`; the legacy contract seal; `scripts/verify_dsl_traceability.py`) move with Task 044. AUDIO source-identity tests (`tests/audio/test_audio_batch001_integration.py`, `tests/audio/test_audio_h1_005.py`, `bie/audio/compiler_handoff.py`) move with Task 042. Section 17 EVAL keeps one contract-blob check (`bie/evaluation/benchmarks/av/native.py`, `tests/section17/test_h2_009.py`). A few compiler M1 tests pin `bie/compiler/chromium_resource_worker.py` and its observers, and inventory checks forbid new files in `bie/qa/` and `tests/qa_*`; they are converted when a task first edits those files.

## Task 038 · live runs (20 October 2026)

- **PR #37 merged** at `398b1ace` after all checks on its final head `cc28c52c` passed. Its first CI run failed in all three canonical gates on `tests/test_source_evolution.py`: the 037C test assumed the live tree had zero evolved files, which became false the moment Task 038 evolved `schema_validation.py`. The test now compares against the tree's own evolved set.
- **Secrets set by Navin:** `OPENAI_API_KEY` (direct), `AICREDITS_ANTHROPIC_API_KEY`, `AICREDITS_GEMINI_API_KEY`.
- **Probe** (run 39450001813, free): all three configured models available: `anthropic/claude-opus-5.5` and `google/gemini-4-argon` via AICredits, `gpt-6.1-sol` direct (the key also lists `gpt-6-astra`, `gpt-6-sol`, `gpt-5.6-*`).
- **Smoke** (run 39450174687): one structured call each, all valid JSON at the first attempt.
- **Blind test** (run 39450332562) on Navin's chapter "10. Tissues and Its Types" (Science and Technology, 14 pages, 11,233 characters of native text; pages 2, 7 and 8 are diagrams only and contribute no text), for UPSC / State PCS aspirants, in Hinglish. All three providers answered at the first attempt with no retries or repairs; total estimated cost about $0.36 including the AICredits markup. Outputs: `blindtest-results` branch, `runs/39450332562-blind-test/` (`REPORT.md` with letters A/B/C; `KEY.json` stays unread until Navin has chosen). The chapter PDF is on the `blindtest-inputs` branch; Navin confirmed he has permission to use it.
- Rendering fix: models that number their own section titles no longer show "1. 1." in the report.
- **Gate:** Navin scores A/B/C and picks the main model. Status words: the live connections are INTEGRATED (real upstream chapter text, real providers); nothing here is ACCEPTED.

## Task 038 · part 1

- **Live connections** behind the existing thin adapters (`ClaudeAdapter`, `GPTAdapter`, `GeminiAdapter` take a client): `bie/model_gateway/live/` adds real Anthropic (Messages API, `output_config.format` JSON schema), OpenAI (Responses API, strict JSON schema) and Gemini (`generateContent`, `responseJsonSchema`) clients on the standard library only, no vendor SDK. Keys come only from `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` (GitHub Actions secrets); a provider without a key is reported as not configured, never faked. Provider error text is redacted (exact key, masked `sk-ab****xyz9` forms, key-shaped tokens).
- **`LiveGateway`:** bounded retries for timeouts, rate limits and outages (existing `retry_policy`), a content-addressed disk cache keyed by provider, model, messages, schema and prompt version, strict schema validation (new opt-in `strict=True` in `schema_validation.py`; existing callers unchanged) plus a content check, one repair turn that shows the model its error, provenance per answer, and a JSONL ledger with tokens and estimated cost for every call. Prices are estimates from public secondary sources (`pricing.py`, dated), not verified; token counts are exact.
- **AICredits route (Navin's choice, 20 Oct 2026):** Navin pays OpenAI directly and pays for Claude and Gemini through AICredits (aicredits.in, rupee wallet via UPI), an OpenAI-compatible reseller endpoint (`https://api.aicredits.in/v1`, model ids such as `anthropic/claude-opus-5.5`, `google/gemini-4-argon`; Navin keeps one key per model family: `AICREDITS_ANTHROPIC_API_KEY`, `AICREDITS_GEMINI_API_KEY`). `compat_client.py` plugs into the same Claude and Gemini adapters; route rule: a direct key wins, else `AICREDITS_API_KEY`, or force with `BIE_<PROVIDER>_VIA`. Its documented JSON mode is `json_object`, so the schema also goes into the prompt and is validated locally; `no_cache` is always sent so the reseller's semantic cache never answers for the model. Ledger, provenance and `KEY.json` record the route and the model id the reseller reports; cost estimates add its 10% (5% fee + 5% forex buffer). Note: chapter text then passes through one more company (AICredits) besides Anthropic and Google; fine for textbook chapters, to be reviewed before any student data (Phase 4).
- **Deterministic fake provider** drives the real adapter → gateway → validation → ledger path offline; it proves execution, not quality.
- **Blind test** (`bie/model_gateway/live/blind_test.py`, `tools/run_blind_test.py`): chapter PDF → canonical DOCUMENT_INTELLIGENCE native text runtime → identical prompt and schema to every provider → lesson plan, narration script and exactly 5 questions → one template renders all answers → random letters A/B/C in `REPORT.md`; the letter → provider key, tokens and cost stay in `KEY.json` until Navin has chosen. Modes: `probe` (lists models each key can use, no cost), `smoke` (one tiny call each), `blind-test`.
- **CI:** `.github/workflows/task038-live-ai.yml`. Pull requests run the offline lane (188 tests incl. the 30 imported gateway contract files, a fake end-to-end blind test, canonical audit). The live lane runs only by manual dispatch from `main`; keys are given to that one step, and outputs (no keys) are pushed to the `blindtest-results` branch because artifacts cannot be read from the cloud workspace. The repository is public, so those outputs are public too.
- **037C in practice:** `bie/model_gateway/schema_validation.py` is a migrated, ledger-pinned file; `audit_canonical.py` now reports it as "evolved since adoption" and passes.
- **Next:** Navin adds the secrets (`OPENAI_API_KEY`, `AICREDITS_ANTHROPIC_API_KEY`, `AICREDITS_GEMINI_API_KEY`); probe run confirms model names; smoke run; blind test on his chapter; Navin scores A/B/C and picks the main model.

## Open decisions for Navin

- [x] Approve the fast lane (037B) — yes, 19 October 2026.
- [x] Who presses merge — Claude, once CI is green (19 October 2026).
- [x] Remove the Task 036 review lock — yes, 19 October 2026.
- [x] Approve 037C (let working source evolve; evidence stays frozen) — yes, 20 October 2026.
- [x] Repository visibility — stays public (20 October 2026); CI minutes stay free.
- [x] Security timing — development speed and quality first; full security hardening before launch (planned in ROADMAP Phase 4), 20 October 2026.
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
- npm drift (found and fixed in 037B): from 17 October the Section 18 `native-render` job failed on every PR, docs-only #31 included, with `TOOLCHAIN_REMOTION_PAIR: mixed versions`. Cause, shown by the drift canary: the generated Remotion project has no lockfile, a newer webpack now gets hoisted, and npm nests Remotion's exact `webpack@5.105.0` under `node_modules/@remotion/bundler/`; the pairing check counts every entry under that prefix, including this non-Remotion package. 037B resolves those installs, and the M1 render runner's, as of 17 Oct 2026 12:00 UTC (`tools/npm_before.txt`); native-render is green again and the canary keeps reporting today's unpinned tree. Follow-up: commit a real lockfile and narrow the check to Remotion packages (possible now that 037C allows the edit).
- F-09 (seen once, passed on the next full run): Section 18 atomic `CancelRecovery.test_actual_two_process_cancel_returns_same_completed_state` failed in PR #32 run 39292713985 (both child processes exited 1). It passed on PR #31's run and 90 of 90 times locally (30 of them under full CPU load). Suspected: SQLite's 1 s busy timeout while two processes prepare the same cancel on a slow runner, so one child gets "database is locked" and the other times out at the test's 8 s barrier. Not proven; failure annotations now include the children's stderr.
- F-10 (seen once, passed on the next full run): `tests/compiler/test_comp_render_integration.py` errored once in the canonical gate of PR #34 run 39362113041. Nothing under `bie/compiler/` or `tests/compiler/` changed between that run and the previous green run of the same PR. The file contains a 0.8-second process-start timeout (`test_process_group_timeout_stops_descendant`), the likely cause on a busy runner. Not proven; canonical-gate annotations now include each failing test's exception line.
- N-02: Section 18 source-ledger step slowed from 21 s to 612 s.
- Audio reconciliation open (`AUDIO_REPLAN_REQUIRED`); global VIDEO_CODE and later stages not run.
- PR29 follow-ups F-01..F-07 and PR30 follow-ups F1..F5 (low, non-blocking).
