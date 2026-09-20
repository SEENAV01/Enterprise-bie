# COMP Hardening H4 — implementation batch result

**BIE-COMP-H4-001..005: bounded source-preserving local layout repair implemented and tested.**
COMP remains IN PROGRESS / NOT ACCEPTED. No GitHub changes, section exit, or new full section re-audit was performed.
This is a correction batch against H3-R01 in the existing consolidated gap ledger.

## Implemented tasks

| Task | Capability | Atomic tests |
|---|---|---:|
| H4-001 | Exact-source visual-owner permissions, finite deterministic candidates and semantic invariants | 28 |
| H4-002 | Opt-in actual text wrapping and responsive map-legend source output; legacy output preserved | 22 |
| H4-003 | Complete owner text/measurement checks and within-owner collision detection | 24 |
| H4-004 | Internal bounded compile/measure/repair loop; explicit upstream revision or environment block | 20 |
| H4-005 | CLI integration, checked source publication, tamper revalidation and replayable evidence | 16 |

The 1,409-test H3 baseline reran successfully. 110 atomic plus eight new integration tests bring the DSL + COMP suite to **1,527 passed**, zero failures/errors/skips. The final development run took 179.335 seconds. Fresh packaged-source and ordered-delta verification are recorded separately in FINAL_VERIFICATION.json; this report does not imply those tests were run before the packages existed.

## Actual local evidence

Eight synthetic technical cases matched expectations: seven found a locally measured fitting source and one correctly requested upstream revision because permitted space was insufficient. Actual Chromium measured **528 frames / 552 element-frame records**, with 66 selected screenshots. Cases cover dense paragraph reflow, long map legend, undersized equation, same-owner label collision, no-space failure, Hindi/Urdu/literal text, authorized owner relocation and unchanged frame-driven animation.

The probe executes generated TypeScript through explicit React/Remotion API doubles, followed by real Chromium DOM painting. **This is not actual React/Remotion rendering.** The probe measures all frames within explicit budgets, rather than claiming exhaustive QA from selected screenshots. The selected seven source cases also matched across **21 independent generator processes**. This is source repeatability, not complete runtime determinism or real-book acceptance.

Only authorized rectangles and presentation fields change. Wording, mathematical expressions, units, geographic coordinates/projection, narration/timing, tracks, accessibility and provenance stay unchanged under the semantic contract. No automatic font reduction, ellipsis, hidden overflow or deletion is used. Upstream Visual/Director must approve extra occupied space. A permitted map plot-height change is not proof of equal cartographic feature readability or instructional equivalence. Correct negative rejection is not counted as automatic repair.

## Compatibility and preserved source

All **4,866 parent file members** remain available. Of **349 active parent Python files**, **346 are byte-identical** and three are deliberately modified: text compiler, map compiler and checked-source CLI. Exact original bytes are preserved under lineage/hardening_h3; the parent inventory binds every file. Historical golden fixtures remain unchanged. The no-policy CLI and old emitter defaults retain H3 behavior. H4 source repair is an explicit branch, not silently enabled scene rewriting.

## Real execution boundary and remaining work

The selected paragraph source passed H3 recomputation/publication. The actual execution harness then returned exit 2 at **FULL_TYPECHECK_BLOCKED: BLOCKED_DEPENDENCIES**. Its dependency-install stage was not requested; a separate npm registry probe failed with EAI_AGAIN. Full exact pinned React/Remotion project compilation, composition discovery and smoke/full render are therefore **NOT RUN**. No rendered video, real-book learning or playable-game acceptance is claimed.

Local Chromium network requests are blocked, but Chromium uses no OS sandbox. Hashes prove consistency rather than trusted external measurement origin. Whole ink/contrast/occlusion, broad locale/font coverage, trusted actual renderer linkage, general instructional layout redesign, specialized scene consumers, reduced-motion instructional equivalence and operational isolation remain on the existing backlog. No production release can be authorized by the local layout receipt.

## Packaging

The separate INTEGRATED ZIP is the cumulative directly runnable DSL + COMP source/tests/fixtures workspace. Atomic ZIPs are smaller **ordered deltas**, not standalone projects; their APPLY_DELTA.py validates the exact incoming file tree and creates a separate restored output without modifying the base. The Master contains the identical integrated ZIP, these current deltas, current evidence and reports, **not any prior Master Backup**. Legacy evidence required by inherited tests stays in the integrated ZIP. Large new screenshots and generated projects are separate in the evidence ZIP. No font/browser/dependency binaries are distributed.

## Next continuation

Checkpoint **BIE-COMP-H4-005**. Continue already-recorded R01/R02/R03 findings under scoped implementation tasks. Keep R04 environmental execution and R05 real-book/game/enterprise acceptance separate. Full section re-audit follows closure of the consolidated implementation backlog, not each hardening delivery.
