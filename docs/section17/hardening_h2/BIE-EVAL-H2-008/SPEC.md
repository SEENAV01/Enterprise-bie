# BIE-EVAL-H2-008 — Pinned AV policy and evidence receipt

## Authority and scope
Derived hardening after the original 50-task roster and H1, from residual **H1-RES-002 / H1-RES-008**. This is not an invented original registry task. Baseline master SHA256: `a18ea349f09d42fd7aa1e5ecfaa5e8ffbd6d0658548224ffdca8349865994fd6`.

## Implemented behavior
Run real collectors behind frozen reference policy; DIAGNOSTIC_PASS/FAIL/BLOCKED outcomes, artifact/reference/code/limits/tool-binary identities and non-escalating receipt integrity.

Owned implementation: `bie/evaluation/benchmarks/av/service.py`.
Dependencies: BIE-EVAL-H2-001, BIE-EVAL-H2-002, BIE-EVAL-H2-003, BIE-EVAL-H2-004, BIE-EVAL-H2-005, BIE-EVAL-H2-006, BIE-EVAL-H2-007.
Shared runtime is intentionally included in each atomic ZIP; use the combined source for integration, not arbitrary overlays. All prior code, test and tool files are byte-preserved.

## Inputs, outputs and errors
Executable examples are `tests/section17/test_h2_008.py` and `h2_support.py`. The included `EXAMPLE_INPUT.json` describes the actual frozen long-file experiment; `EXAMPLE_OUTPUT.json` is copied from executed evidence, not a fabricated success template. The native example explicitly uses authored declarations and does not authenticate execution.

Checks reject unsupported or missing input/evidence; no candidate-provided PASS flag grants acceptance. Admitted collector failures are BLOCKED; measured policy violations are FAIL. DIAGNOSTIC_PASS remains local signal evidence only.

## Actual verification
20 selected distinct test methods passed in the combined 1,493-method suite. Individual ZIP extraction tests are in the outer master's `verification/atomic_checks/`. Full method IDs/results are in `TASK_RESULT.json`. Ten targeted fault injections and restored controls are separate evidence and do not increase test counts.

Run from the ZIP's `runtime/` or the master `combined_source/`:
```sh
python -B tools/run_section17_h2_tests.py --pattern test_h2_008.py --output-dir /tmp/bie-eval-h2-008-fresh
```
Linux/POSIX, Python 3.13.5, FFmpeg/ffprobe 7.1.5 were executed here. Missing tools fail tests, not silently skip. Other Python/platform/toolchain combinations remain unverified.

## Explicit residual boundary
This v2 operator path is additive. Legacy metrics012/013/015 and the existing release gate are not automatically rerouted. Hashes do not authenticate untrusted self-authored receipts.

## Integration / rollback
Read `docs/section17/h2/INTEGRATION.md`. No GitHub write, native adoption, migration of the canonical repository, product acceptance, Section18 advance or Task028 change is authorized by this archive. Removing the additive `av/` runtime would not migrate data safely; preserve its evidence/database and restore documented metadata preimages only under governed rollback.
