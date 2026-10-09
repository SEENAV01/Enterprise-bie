# Task036 M1 CI-R1: package-aware collection repair

This is a test-runner-only continuation of the motion/capability prerequisite,
not ordinary Task036 producer resumption or amendment sign-off.

## Pinned before evidence

Canonical base: `5b1cafc766c9df9c3e0748f459e6beb9b8f1f243`.
Starting M1 commit: `8b74de9029fd9011b626d1f03b1a0986550e6fde`.
Starting tree: `40932a2798fa1f245b39f93b82a03f18dd4a2580`.

Run `37850457870`, attempt 1, failed in native-extra job `113561790315`.
All 214 source paths were attempted, but only 2,382 methods were collected and
executed. Three **collection** errors were not failing test methods:

- `tests/compiler/test_comp_build_007.py`
- `tests/compiler/test_comp_build_008.py`
- `tests/compiler/test_comp_render_integration.py`

Each recorded `ImportError`, selected=0 and executed=0. The missing hosted
exception messages were not recovered. Artifact `11582096097` (1,901 bytes),
SHA256 `53718b9baf1f4a3dd69fee58fd644f954c0784c2c29e5ef612b0e51a736519fe`,
was downloaded and its digest and ZIP CRC verified.

The verify job `113561790859` passed its 52 M1 tests, unchanged Task035 129+4,972
inventory, separate 12+20 safety controls, strict H3 AFTER, legacy process/restart
checks and source audits. Artifact `11583373083` (33,601 bytes), SHA256
`98a45888dd5375a23c8354c2347510414ed57f155e3db4ed1d1929a48f6e3108`,
was independently verified. All eight historical render ZIPs were retained and
digest/CRC verified. These successes do not waive the failed native-extra gate
or establish results on the repaired candidate.

## Cause and narrow change

The old runner imported each source under a bare `m1_<hash>` alias. All three
modules use relative imports from `.render_test_support`, which require a real
package context. Adding their directory to `sys.path` cannot supply that context.
A minimal real-package fixture and each unchanged repository module reproduced
`ImportError` / `RELATIVE_IMPORT_NO_PARENT_PACKAGE` on Windows Python 3.13.5.
These are new local observations, not recovered historical Linux tracebacks.

`run_m1_tests.py` now imports canonical package-qualified names from the resolved
repository root. It verifies the target, parent packages and relevant helper
origins; rejects foreign cached modules; scopes and restores sibling import paths;
and removes temporary test-module aliases while preserving valid prior context.
Native preservation tests' deliberate sealed-preimage aliases are checked against
their actual checkout origins, not mistaken for nonexistent alias-named files.

`selected_suite()` remains authoritative when present. Logical identities use the
defining repository-relative file plus class/method, removing the complete known
module prefix rather than splitting at the first dot. Explicit parameterized IDs
remain distinct through a bounded hash suffix. Duplicate identities fail closed.
Receipts retain actual identities and verified relative import origins; collection
errors are reported separately from executed-test errors. Empty, incomplete,
failed, errored or skipped suites cannot pass. Exception messages are not exported.

One new runner-control file is assigned exactly once to the existing new lane.
All 214 native-extra paths remain identical to the failed run's requested paths;
none of the three previously uncollected modules is filtered. The workflow,
Task035 inventory and original 52 M1 tests are unchanged.

## Available Windows after evidence

Twenty-two new runner controls pass, separately counted from inherited tests.
The 13 exact-amendment/legacy tests, eight M1 evidence tests, and separate 12+20
Task035 safety tests also pass locally. Repeated diagnostic executions are not
additional authored tests.

The expanded local new lane executed 74 tests (original 52 plus 22 runner controls):
73 passed, zero failures, one error, zero skips and zero collection errors. The
erroring original method is `test_complete_native_source_composition_both_preferences`,
also present in the retained pre-repair Windows result; matching method/count does
not prove an identical underlying exception. The long-running original-M1 portion
started before the final parent-attribute cleanup refinement. Final runner controls,
scoped preservation/recovered suites and the collection audit were run after it.
This does not establish exact-candidate Linux, H3 or render closure.

Each of the three unchanged files now collects and executes its complete suite
with verified package/helper origins:

| File suffix | Selected/executed | Passed | Failures | Errors | Skips | Collection errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `test_comp_build_007.py` | 21/21 | 13 | 0 | 8 | 0 | 0 |
| `test_comp_build_008.py` | 19/19 | 3 | 0 | 16 | 0 | 0 |
| `test_comp_render_integration.py` | 13/13 | 2 | 0 | 11 | 0 | 0 |

Those Windows execution errors are retained, not repaired or called PASS. Observed
safe diagnostics include evidence-sealing `BuildError`, the native POSIX-process
restriction, fixture subprocess `FileNotFoundError`, and symlink-related `OSError`.
No universal cause is inferred from aggregate counts; no dependency/native fix is
included. Qualified before execution and repaired execution have the same counts.

The final Windows collection-only audit attempts all 214 files: 1,640 methods
collect; 39 sources fail while importing the unchanged Unix worker (`fcntl`).
It compares 1,587 previously loadable logical identities without changes and
recovers the additional 53 methods above. This is **not** a complete Linux
inventory or a test-execution PASS. Its partial identity SHA256 is
`bcc9df82807b0ba6aba6a14ac626869ff3f391be1752f19a196cd52f26f0eba1`.
The repaired complete Linux inventory/count/hash must be observed from hosted
execution; the deficient historical 2,382 count/hash is not pinned as a target.

## Preservation and remaining gate

The four M1 native edits, three new compiler modules, exact amendment manifest and
preimages, original design and proposal remain byte-identical to the starting M1
candidate. No second native amendment, requirement, installer, workflow, budget,
inherited-test or product-stage change is made. Original design SHA256 remains
`40cb141ded64d5691e7935ac963178afa254e1bcd7d6c8d5302f07f2de3393e8`;
amendment-document SHA256 remains
`b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c`.

Local Post-DIR and ingested-archive audits pass. The local canonical audit remains
non-green with four historical long-path content mismatches; its error set exactly
matches the retained pre-repair Windows audit. This is not full source-audit green
or a waiver of the hosted canonical audit.

The new exact candidate must pass the complete native-extra inventory, all M1 and
runner controls, original Task035 lanes, safety suites, strict H3 AFTER,
standard/reduced generated-consumer checks, eight render jobs, legacy process/
restart smokes and exact source audits. Old successful jobs are not substitutes.
Windows non-green history, four historical long-path mismatches and local positive
process timeouts (45.049/45.079/45.052 seconds) remain retained, with causes not
universally attributed to collection or compiler provisioning. Limits are unchanged.

Task035's original bounded sign-off stands. M1 remains unsigned pending full
coverage and external review. Ordinary Task036 remains paused; no planning-only
waiver applies. Audio reconciliation is open and AUDIO_REPLAN_REQUIRED remains
fail-closed. No global Scene IR/video-code/compile/render product completion,
educational quality or product acceptance is claimed. No PR, merge or Task037.
