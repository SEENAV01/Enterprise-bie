# BIE COMP Hardening H11 — release result

Date: 2026-09-19. Checkpoint: BIE-COMP-H11-004. Four bounded implementation tasks delivered. COMP remains IN PROGRESS, section exit false and product acceptance false. No GitHub read/write/integration was performed in this batch.

## Exact lineage

Parent: `913206a80d4a1d677438df9aa33485745681e132f4011c5919816d9c8ac75733` (H10 integrated). Final Integrated ZIP SHA256: `7f56278f6c8c797e4a0641a18307859a922decfe695118f0a62dabc61455b1e7`. All 5,407 parent paths retained. 456 inherited active Python files: 447 unchanged and 9 deliberately modified. One inherited measurement JavaScript file also changed. All changed originals have exact preserved bytes. Historical tests and fixtures were not rewritten.

## Implemented tasks

| Task | Capability | Actual restored tests |
|---|---|---:|
| H11-001 | Original ASSET receipt -> actual isolated image/video byte and metadata verification, source/rights binding | 38/38 |
| H11-002 | Explicit normalized/pixel crop and aspect-preserving image presentation, alternative text and original bytes retained | 18/18 |
| H11-003 | Finite source-verified video trim/display lifecycle, explicit audio policy and matching existing Remotion dependency pin | 25/25 |
| H11-004 | Existing checked publication, repair, CLI and render revalidation adoption; native-browser technical diagnostics | 20/20 |

Full contracts: BIE_COMP_HARDENING_H11_CONTRACTS.md and docs/comp_h11 in the source. These are a continuation of existing R01/R02 and original asset/media handoff, not four new unrelated original-roadmap features.

## Reproduced changes

Unmodified H10 could publish and revalidate a scene pointing at an absent image. Different image crops and different video trims produced identical source, while video code requested @remotion/media without a governed installed-project dependency. H11 now implements the crop/trim presentation, adopts the original asset bundler into a verified visual manifest, stages actual bytes and checks them again on repair/publication/render preflight. Missing/tampered bytes cannot pass those adopted paths.

This does not mean source compilation alone verifies file existence: actual bytes are required at binding/publication and revalidation. Rights references are preserved assertions, not independent licensing approval. Unsupported crop units/properties, non-CFR video profiles, unresolved external captions and unverified embedded-audio/narration mixes reject explicitly. No universal codec or caption resolver is claimed.

## Fresh release execution

Untouched H10 baseline: 2,327 tests passed. H11: 101 new tests. Final Integrated ZIP freshly extracted: **2,428/2,428 PASS**, zero failures/errors/skips; elapsed 359.98 seconds for this actual run. Workspace hashes unchanged after tests.

All four atomic ZIPs independently extracted and restored in order from a fresh exact H10 baseline. Complete restored workspace matches all 5,470 Integrated ZIP files byte-for-byte. Task suites then separately rerun: 101/101 PASS. Wrong order, repeat application, tampered payload, symlink base and FIFO/nonregular file were rejected without publishing output. Atomic packages require all four stages before execution; they are not standalone apps.

5,469 workspace checksum entries and 189 evidence entries verified. The Master embeds the exact integrated/atomic/evidence archive bytes and no recursive prior Master. Final Master verification is separately recorded to avoid circular self-hashes.

## Browser and native media

Five technical source cases repeated across ten independent generator processes. Actual Chromium measured 120 frames / 144 element-frame records; 15 screenshots saved. All five local fit cases passed. Real native image/video decoding was used after source-byte verification. TS/React/Remotion execution uses explicitly labelled API doubles, so this is NOT a Remotion render or production witness. Diagnostic videos are muted.

Three video cases: four predeclared pixels at each of twelve active frames were compared against an independently FFmpeg-decoded CFR fixture reference (144 pixel positions, 432 RGB channel comparisons). Maximum observed channel error was 4 under the predeclared threshold 5; seek time error was below 1e-6 seconds. This is sparse frame-clock evidence, not full-image semantic or colorimetric proof. Actual JPEG/WebP positive decodes and EXIF/animated-image negative cases also passed in isolated workers.

Original asset bytes are unchanged. Crop boundary resampling follows the native renderer; this is not nearest-neighbor or exact edge-pixel preservation. Synthetic graphics and a silent test clip are not a textbook, spoken narration or accepted learning experience.

## Initial findings retained

A development regression before four additional format tests ran 2,424 tests with five failures/errors in old ancestor-copy assertions. Ten exact old-byte copies were restored at the historical expected paths from hash-matched H10 members; the tests themselves were not weakened or edited. Final fresh release is green. Earlier runner/PYTHONPATH and diagnostic adapter/CORS mistakes and their failed logs are preserved in current evidence. Diagnostic CORS now permits only exact verified memory assets, not outside network access.

## Actual execution and remaining boundaries

The combined source and its image/video bytes passed publication and revalidation. Actual execution stopped at `FULL_TYPECHECK_BLOCKED: BLOCKED_DEPENDENCIES`. A real pinned npm registry probe returned `EAI_AGAIN`. No dependency installation, browser isolation waiver, fake pinned runtime, successful Remotion composition discovery, full compile or smoke/full render is claimed.

Remaining actual-render, operational browser isolation, visual/semantic and real-book acceptance gates stay in the consolidated ledger. H11 does not resolve every codec/property combination, external caption reference, embedded-audio narration mix or teaching-equivalence requirement. Resolved H9/H10 names/state combinations and H11 byte/crop/trim/pin defects should not be re-added as unchanged gaps. No new full section audit was performed in this batch; no automatic next original task numbering or section exit.

## Delivered files

Separate cumulative Integrated ZIP + Master Backup. Master contains that exact Integrated ZIP, four ordered atomic deltas, current evidence ZIP, reports, preview, regression and checksums. No font files are distributed. Local integrity checks are not an independent signature or proof of GitHub integration.
