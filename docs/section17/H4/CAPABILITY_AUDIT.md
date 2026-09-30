# H4 capability audit

# Section 17 • Hardening H4

## Start here
`combined_source/` is the assembled current source: all 257 published H3 code/test/tool inventory files were recovered and matched before the two shared-API changes and additive H4 files. The 1658-test H3 baseline reran successfully. No restart or substitute baseline was used.

H4 adds actual Chromium keyboard/game feedback, isolated rendered DOM/contrast observation, native PNG screenshots, fresh-context replay, durable evidence and explicit existing metric/rater integration. Each new atomic runtime is dependency-complete for its task within the supplied Python code; external Python/Playwright/Chromium tools are not bundled.

## Local verification
```sh
python tools/run_section17_h4_tests.py --output-dir /tmp/bie-h4-full-check
python tools/run_section17_h4_diagnostics.py --output-dir /tmp/bie-h4-browser-evidence
python tools/run_section17_h4_fault_controls.py --output-dir /tmp/bie-h4-fault-check
```
The actual tested environment is Linux/POSIX. Runtime tests use `/usr/lib/chromium/chromium`; adapt the operator-owned test configuration for a different provisioned native binary. Tests intentionally fail/block when a needed runtime is absent; missing runtime is not a skipped PASS. The context template must be populated with the real root and independently pinned Chromium SHA256. `python -m bie.evaluation.benchmarks.browser --help` documents the run/get/recover CLI.

## Transport and safety scope
The browser's managed URL policy blocked the first virtual-origin navigation. That failure is retained. The implemented local-document profile renders verified in-memory classic scripts and stylesheet bytes, aborts page/network requests, and records the shell/script hashes. No managed browser policy was disabled. Canonical-layout mode follows the inspected `browser_runtime.py` smoke-bundle convention; it is NOT a verified native generated-game run or ES-module/HTTP app boot. `reload` here recreates the local diagnostic document, not a URL reload. Original CSP is hashed but this path does not certify CSP enforcement. Production hostile-code isolation is not provided; this container used an explicit operator-only unsandboxed diagnostic opt-in for authored fixtures.

## Preservation and missing history
All 80 available earlier atomic ZIPs are unchanged and retained. The exact H2 master contains earlier masters and evidence. H3 atomic ZIPs, its reports/continuation/checksums and final-master-check ZIP are retained. The original H3 combined master itself was not available via current attachments or Library lookup. It has NOT been silently reconstructed or claimed preserved. Its published 257-file code inventory was fully recovered, but H3-only ancillary records not present in available files remain an explicit history gap. See `metadata/section17/H3_RECOVERY.json`.

Large historical media may be stored once inside `history/H2_EXACT_MASTER.zip` rather than duplicated in the assembled source. `HISTORY_LOCATIONS.json` records the exact archive/member/hash; no bytes are discarded. This does not affect running the cumulative test suite.

## Not accepted
No GitHub writes, Task028 resumption, Section18 start, native/Section16 caller adoption, full repository regression, real-book video/game E2E, live model calls, independent human reviews, learner trials or product acceptance occurred. New task count is not section completion. Continue from the actual residual ledger, not invented task numbering or repeated wrapper batches.

## Residual obligations

### NATIVE_ADOPTION
OPEN_IMPLEMENTATION_INTEGRATION: Canonical application and Section16 callers have not adopted or executed these local profiles. Full repository regression unrun.

### REAL_BOOK_E2E
OPEN_RUNTIME_EVIDENCE: No actual book -> canonical Remotion or canonical game generation was executed.

### REAL_SEMANTIC_QUALITY
OPEN_CAPABILITY_EVIDENCE: Literal UI expected-text checks and solid-color contrast are not semantic, cinematic, pedagogical effectiveness or perceptual/phonetic assessment.

### PRODUCTION_BROWSER_RUNTIME
OPEN_IMPLEMENTATION: Current profile is bounded in-memory classic/canonical-smoke diagnostic transport, not ES module/HTTP app boot. OS hostile-code/network containment, native deployed runtime, font/asset richness, browser platforms and full WCAG remain open.

### INDEPENDENT_EVALUATORS
OPEN_INDEPENDENT_EVIDENCE: No live model, independent reviewer/golden-book dataset, or real learner experiment was performed.

### H3_HISTORY_GAP
OPEN_ARTIFACT_RECOVERY: Original H3 combined master and some H3-only ancillary evidence are unavailable. Source recovery is exact for all 257 published code/test/tool inventory paths; history closure is not asserted.
