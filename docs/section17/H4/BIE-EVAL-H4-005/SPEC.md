# BIE-EVAL-H4-005 — Isolated rendered DOM and screenshot observation

## Governing gap
H3 audit: static contrast/focus fields not actual runtime. Additional hardening, not a renamed original registry item.

## Implemented scope
CDP isolated-world text/style/geometry observations plus native PNG capture; candidate style API overrides do not supply the scores.

## Inputs and outputs
Operator-owned reference `examples/section17_h4/reference.json`, candidate asset manifest, actual local asset directory and pinned native Chromium executable. Shared schema is `browser-reference-1` / `browser-candidate-1`. Output is candidate/reference/tool/code-bound observed evidence, or explicit BLOCKED; missing actions cannot disappear from the reference denominator.

## Code and test traceability
Implementation: `bie/evaluation/benchmarks/browser/observe.py`. Task-specific tests: `tests/section17/test_h4_005.py`. Shared contracts and observer/runtime dependencies are included in each atomic runtime snapshot. Every atomic ZIP is extracted and its selected tests are executed independently before delivery.

## Verification command
```sh
python tools/run_section17_h4_tests.py --pattern test_h4_005.py --output-dir /tmp/BIE-EVAL-H4-005-checks
```
Use a fresh output directory. Linux/POSIX, Python, Playwright and pinned native Chromium are required for runtime tests; not all platform/tool combinations are validated.

## Fail-closed behavior
No supplied `passed` field, provider response, manifest label or signature grants browser execution or product acceptance. Unsupported module boot, unavailable tools, corrupt assets, admission errors and unfinished execution are blocked. Observed defects are measured FAIL, not dropped cases. Nonzero game behavior scores do not establish real learner improvement.

## Boundaries
Actual execution is the authored local browser slice, not a canonical book-to-game/browser/application run. Production hostile-code isolation, complete accessibility, speech/semantic assessment, independent human/golden review, real learner outcomes and native/Section16 adoption remain separate gates. An operator-only unsandboxed diagnostic opt-in was used in this container; no managed Chromium policy was disabled.
