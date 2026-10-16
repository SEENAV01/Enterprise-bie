# Task036 bounded cause investigation and verification cost correction

Candidate parent: `c40a6e6d1dea8a4ce5bebec3827f13a8df57dd22`.
This is an investigation checkpoint, not independent review, runtime acceptance,
canonical completion or authorization to merge failed gates.

## Confirmed and unresolved findings

The old a24 Scene admission failures are not the latest failure. Current c40
push 38677995666 and PR 38677999465 each passed 437/437 Scene controls. Their
quantitative and chronology children still returned -9 around 30.1 seconds,
after all eleven stages SUCCEEDED and all eleven queue items ACKED. Their last
checkpoint was SCENE_IR operation 11, before_next_admission. This contradicts
the claim that these particular runs stopped before Scene IR at Pedagogy.
Thirty-second CPU exhaustion is a hypothesis; those historical receipts did
not record final child CPU usage or a kernel kill reason. A 45-second wall
deadline, Windows incompatibility or missing fixture is not established by them.

The latest c40 M1 PR 38677999492 failed in
`tests/compiler/test_comp_h4_005.py::RepairPublicationTests.setUpClass`.
Sixteen methods were selected and none executed. The native result was
ENVIRONMENT_OR_VALIDATOR_BLOCKED; the actual lower exception was swallowed by
the existing repair boundary. Push 38677995661 passed. A fixture lifecycle
error identifies a failing setup boundary, not proof that fixture data is absent.

An isolated hosted diagnostic, run 38689015618 at
`c7eef34392cffc44c0a9123623491d2f530fbf44`, kept c40 native source, original
limits and test order. Quantitative process and restart/replay passed: first
child CPU 23.541257 seconds, wall 25.3205 seconds, max RSS 120312 KiB;
3.212365 CPU seconds occurred after the eleven-ACK checkpoint. Native-extra
passed 2435/2435, including all sixteen H4 methods, with no observed exception.
Both artifact ZIPs were checked against GitHub API size, SHA256 and ZIP CRC.
This non-reproduction does not identify the intermittent M1 cause or prove the
historical Scene kill mechanism. Original real render gates remain required.

## Minimum source correction

`scene_ir_m1_review.lf_source` avoids scanning an already LF-only source buffer
again for CRLF replacement. It preserves exactly `data.replace(b"\r\n", b"\n")`
semantics, including isolated CR, arbitrary binary bytes and mixed line endings.
All files are freshly read in full; all fixed expected hashes, census checks,
containment and descriptor checks remain. No hash is cached across operations.
The 40,505,121-byte preserved ledger was repeatedly normalized in this path.
An isolated normalization-plus-hash microprobe improved from 1.28 to 0.57 seconds
over twenty iterations; this is not an end-to-end or hosted failure cure claim.
Three additional controls exercise exhaustive short byte combinations and full
real ledger LF/CRLF identity. No native compiler or historical authority changes.

## Preserve evidence on the actual required gates

`tools/task036_cause_closure.py --mode scene-full` delegates the original
four-case `run_smoke`, including restart, replay, blocked Math, private-evidence
checks and all original assertions. It preserves the original main receipt
shape and exit decision. Separate allowlisted receipts record per-child CPU,
wall, exit, bounded output size and resource ceiling. Each RUN has its own
checkpoint directory. The unchanged original child executes under -I/-B and
the identical supervisor and process budgets; there is no additional retry.

The native mode delegates the full original native-extra inventory and ordering.
Only the H4 test file temporarily observes exceptions from six exact native
code/global bindings. It exports fixed class/category labels in a separate
receipt; raw exception text, traceback, argv, paths, tokens and media are never
exported. Unknown categories stay unclassified. Existing tracing is preserved
and marked unavailable. The observer restores bindings in finally and cannot
make a failed native result pass. Ten separate observer/delegation controls are
diagnostic controls, not extra native or product acceptance tests.

The two existing workflows retain their approved pinned provisioning, mandatory
Task035 129/4972 inventories, twelve/twenty safety controls, native inventories,
source audits, eight real-render matrix cases, dependencies and timeouts.
No skip, budget extension, permission relaxation or blanket retry is introduced.

## Available local verification

Python 3.13.5 on Linux passed all ten observer/delegation controls and fourteen
existing M1 evidence/workflow controls. All four real Scene process cases passed,
including separate restart and replay: first-child wall times were quantitative
20.325, chronology 19.424, cellular 19.472 and blocked Math 2.373 seconds. The full
440-method Scene inventory and required integrated gate were also invoked; their
final receipts, and the final hosted candidate gates, must be assessed separately.
This checkpoint does not turn an in-progress or unavailable check into PASS.

## Reproduction and remaining requirements

Use the pinned Python 3.13.5 / Node 22.16.0 environment and the unchanged setup
steps in the corresponding workflow, then run:

```sh
python -B tests/diagnostics/test_task036_cause_closure.py
python -B tools/run_task036_tests.py --output /tmp/task036/new.json
python -B tools/task036_cause_closure.py --mode scene-full --output /tmp/task036/process.json
python -B tools/task036_cause_closure.py --mode native --output /tmp/m1/native-extra.json
python scripts/integrated_check.py --output-dir /tmp/task036-integrated
```

Local kernel/browser restrictions cannot certify the owned render supervisor.
Use the unchanged hosted M1 workflow for all eight real renders. All required
push and PR gates must pass on the final source candidate, followed by genuine
independent review of the implementation and its evidence. If a failure recurs,
inspect these separate cause receipts before choosing another correction.
Do not equate one successful diagnostic with a fixed intermittent failure.

Task036 remains review-required and unaccepted. Audio reconciliation remains
OPEN/AUDIO_REPLAN_REQUIRED; accepted/release_ready/product_accepted stay false.
Global downstream execution and later product acceptance are not granted here.
