# Task036 Step 1: withdraw the cause-closure execution wrapper

## Scope and identities

Owner authorized only this bounded correction, local verification and an optional
isolated local commit. No push, hosted execution, PR modification, merge, next
repair or Task037 is authorized by this step. This is not an M1 or Task036 approval.

Live PR #29 was read as OPEN, unmerged, with head
`151d54a512f24d162e07087dadf41a8cb74f7a3c`, tree
`c7258e85e2427cee57317313fd0a37acdd0b96f8`. An explicit fetch of the main and
feature refs confirmed that head. The default fetch retrieved only the handoff
branch; its stale feature tracking ref was not used as authority. Main remains
`5b1cafc766c9df9c3e0748f459e6beb9b8f1f243`, tree
`ce5044e06c9b2fe8164b7fb15cc59976941f8116`.

The original clean workspace remains on
`wip/task036-codespaces-handoff-20261015`, commit
`1673036b0504e895fd5dfbc9a260090db94d75c8`, tree
`cd933f91741fa5ec3803ee0b6facddb50410977f`. Its divergent source and handoff
records were not merged, cherry-picked, overwritten or discarded. The reported
Codespaces-local candidate was neither required nor imported.

This correction is isolated on `codex/task036-step1-withdraw-cause-wrapper`,
directly from the live PR head. The first attempted checkout encountered a
Windows historical filename-length error. Git removed that incomplete checkout;
a shorter checkout with command-scoped `core.longpaths=true` succeeded. No
global Git setting, BIE isolation or execution limit was changed.

## Confirmed defect and correction

At the PR head, `tools/task036_cause_closure.py` writes `tail-end.json` in its
child `finally` before restoring `Checkpoints.mark` and `sys.argv`. A write
failure can mask the original exception/SystemExit and prevent restoration.
Other writes and trace setup/restoration are also uncontained. Its transient
private-message classification is outside the older message-free diagnostic
assessment. Its in-budget `runpy` child substitution was not proven
noninterfering by the mocked delegation controls.

These are diagnostic defects, not demonstrated causes of the Scene child,
H4 setup or painter failures. No renderer, Director, source-admission or producer
optimization is included here.

Both workflow files are restored exactly, after Git checkout newline conversion,
to their pre-wrapper bytes at `c40a6e6d1dea8a4ce5bebec3827f13a8df57dd22`:

```sh
python -B scripts/smoke_bie_scene_ir.py --output "$RUNNER_TEMP/task036-evidence/process.json"
python -B tests/compiler/run_m1_tests.py --lane native-extra --output "$RUNNER_TEMP/m1-evidence/native-extra.json"
```

The original four smoke scenarios, restart/replay assertions, native inventory
and ordering, exit-status logic and root receipt paths are untouched. The Scene
artifact glob returns to the original `task036-evidence/*.json`; it retains all
original receipts and no longer collects the withdrawn wrapper's nested tail
files. M1 artifact collection, dependencies, all eight render cases, provisioning,
permissions, timeouts and budgets are unchanged.

The wrapper and its standalone ten-test file are retired together. Those ten
tests exist solely to exercise the now-withdrawn helper; leaving their mandatory
step would import that retired implementation. They were not original product,
native, security or source-preservation tests, nor part of the original native
2435 or Task035 inventories. No inherited assertion or selection is weakened.
All original bytes remain available in Git at the PR head. The historical cause
investigation document and its evidence are left unchanged, but its wrapper
execution instructions are superseded by this withdrawal. No replacement
observer is introduced, and no executable workflow/script/test path references
the retired module.

## Available focused verification

Runtime: Windows, CPython 3.13.5, existing development virtual environment;
`-X utf8 -B`. No dependency installation, Linux provisioning or renderer execution.
The actual retained package-aware `run_file(path, identities, ROOT)` runner was
used sequentially for these unchanged modules, with one shared identity set:

| File (under tests/) | Selected/executed | Failures | Errors | Skips |
| --- | --- | --- | --- | --- |
| compiler/test_m1_runner_loading.py | 22/22 | 0 | 0 | 0 |
| compiler/test_motion_m1_evidence.py | 8/8 | 0 | 0 | 0 |
| productization/scene_ir/test_positive_process_observations.py | 34/34 | 0 | 0 | 0 |
| productization/scene_ir/test_canonical_history_workflows.py | 6/6 | 0 | 0 | 0 |
| productization/scene_ir/test_monitor_binding_amendment.py | 13/13 | 0 | 2 | 0 |
| productization/animation/test_ci_r1_diagnostics.py | 12/12 | 0 | 0 | 0 |
| productization/animation/test_ci_r2_provisioning.py | 20/20 | 0 | 0 | 0 |

Total: 115 selected/executed, 113 passed, zero failures, two errors, zero skips
and zero collection errors. This is NOT full green. Identity SHA256:
`417da32fef86682d70f76a5b6332fea0bfd2969d58061ae8f490bf15681a99f6`.
The separate 12/20 safety controls are included in this focused total, not added
again. No new test methods were authored. Fixture controls are not native runtime
or eleven-stage process proof.

The two errors are in `MonitorBindingAmendmentControls`:

- `test_admission_path_accepts_only_complete_authenticated_flat_namespaces`:
  `ProducerError / scene_ir_m1_monitor_source_identity`.
- `test_complete_original_two_monitor_gates_remain_active`:
  `ValueError / MONITOR_AMENDMENT_PREVIOUS_AUTHORITY`.

`python -X utf8 -B scripts/verify_post_dir.py --output <private-evidence>/step1-post-dir-source.json`
also exited 1 at `compiler_monitor_snapshot_amendment.validate` with
`ValueError / MONITOR_AMENDMENT_PREVIOUS_AUTHORITY`, before emitting a success
receipt. No complete source-audit PASS is claimed. The protected source, tests,
authorities and seals are unchanged by this correction.

Read-only byte comparison establishes the immediate authority mismatch:
`task036-motion-amendment/AMENDMENT.json` is 8942 bytes in Git with the preserved
SHA256 `b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c`,
but 9141 bytes after Windows checkout, SHA256
`4bd62c3508eea406851a37840fdafbda7696871075df48f9ae68e6dfe891cb82`.
The only difference is CRLF conversion. The working bytes equal `git cat-file
--filters` of the UNCHANGED PR-head blob. The source-chain index matches its
expected raw hash. The strict snapshot guard rejects that converted M1 seal at
`PREVIOUS_AUTHORITY`; the admission fixture also retains its identity rejection.
Two diagnostic repeats confirmed the exact exception/code pairs above; they are
excluded from the 115 unique-test count. This is not a separate full base-suite
execution and does not explain any hosted runtime failure. No seal, attribute,
guard, assertion or expected hash was edited to obtain green.

The original M1 amendment validator separately PASSED its four replacements and
three additions using its existing newline policy. That bounded result does not
override the stricter follow-on audit failure.

`inventory()` still selects 214 native-extra source files and has no overlap with
NEW, SAFETY or inherited ownership. Every original runner and selected test file
is unchanged. The full 2435-case native execution and full Scene/Task035 suites
were NOT_RUN in this step; unchanged selection is not a newly executed PASS.

## Reproduction and limits

The focused execution can be reproduced without the retired wrapper:

```python
from tests.compiler.run_m1_tests import ROOT, run_file
paths = (
    "tests/compiler/test_m1_runner_loading.py",
    "tests/compiler/test_motion_m1_evidence.py",
    "tests/productization/scene_ir/test_positive_process_observations.py",
    "tests/productization/scene_ir/test_canonical_history_workflows.py",
    "tests/productization/scene_ir/test_monitor_binding_amendment.py",
    "tests/productization/animation/test_ci_r1_diagnostics.py",
    "tests/productization/animation/test_ci_r2_provisioning.py",
)
identities = set()
rows = [run_file(path, identities, ROOT) for path in paths]
raise SystemExit(0 if all(row["passed"] for row in rows) else 1)
```

The two direct workflow commands above require their existing approved runtime
and, for native execution, the governed Linux host. They are reproducible next
verification commands, NOT executed here and NOT permission to start the next
step. Do not run the Linux installer blindly on Windows or weaken any checks.

All existing failure evidence, review records, amendment hashes, native sources,
requirements and source ledgers are retained. Task035's bounded canonical sign-off
stands. Task036/M1 runtime causes and final closure remain unresolved. Audio
reconciliation stays OPEN and AUDIO_REPLAN_REQUIRED fail-closed. Review/acceptance
flags and later global stage status are not promoted. No product acceptance.

STOP after reporting this step. No push, hosted run, PR change, merge or Task037.
