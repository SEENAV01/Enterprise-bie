# Section 16 non-credential controls — candidate evidence, not sign-off

Scope: HARD-039 only. This record does not close any of the 113 original
obligations, authorize HARD-040, or establish product acceptance. It adds two
supplemental controls outside the sealed 817-path Section 16 adoption corpus;
the inherited 4,856-test denominator and original source hashes are unchanged.

## Finite playable-game oracle depth

`bie/section16/oracle_depth.py` consumes the existing canonical QA GAME
`GamePolicy` and its finite route oracle. Operator-owned requirements must
declare branch, wrong-answer-to-success remediation, distinct-objective and
distinct-prompt transfer, and terminal-to-initial reset routes. Missing or
ambiguous declarations fail closed. The optional `GameResult` must bind to the
same policy and cover required transition IDs. Output is safe IDs/status only;
it **never** claims native game acceptance or learner mastery. Structural route
coverage is not a browser trace, content truth, or empirical learning result.

Local structural tests: `tests/assembly/test_oracle_depth.py`, 14/14 PASS,
including seeded missing-branch, missing-remediation, indistinct/missing
transfer, missing-reset, unknown-reference, omitted-role, and foreign-policy
cases. This is partial local progress for `QA16-GAP-034` and
`QA16-GAME-ORACLE-DEPTH`, not closure. Native entrypoint player/game traces,
independent pedagogic judgment and genuine learning outcomes remain open.

## Real-book H8 path preflight

`bie/section16/native_book_preflight.py` binds exact PDF bytes to a single
`BookPlan` source row, validates the expected SHA-256/page/block baseline
through the canonical Task 016 PDF inspection, and reports the 15 required H8
stage registrations. It verifies registered native program bytes when present
but never invokes a program, generates content or fabricates a stage result.
Local structural tests: `tests/assembly/test_native_book_preflight.py`, 9/9
PASS, including wrong hash, page/block baseline, plan inventory, diagnostic
profile and malformed PDF failures. Existing adoption-gate tests: 36/36 PASS;
`verify_adoption` confirms the original 817-file corpus unchanged.

The private real educational PDF `3. Money.pdf` at its previously authorized
exact path was read locally, not copied or uploaded. Its SHA-256 is
`8fbe1357179b364824d97861152a31055c45b87177198b40f39c98f726e06857`;
byte length 2,296,324; page count 20; source-linked blocks 755. The safe
preflight repeated deterministically. All 15 native stage programs were
`NOT_REGISTERED` for this real-book plan. This is a concrete missing
implementation/integration prerequisite, not a credential-only blocker.
Generator, independent assessor, rights clearance, native video and native
playable-game execution remain `NOT_RUN`; Section 16 sign-off is false.
No real PDF bytes or extracted book text were committed or uploaded.

## Local platform boundary and remaining gates

The inherited GAME QA suite cannot run to completion under this Windows
profile: `SnapshotStore` fails closed with `SECURE_ARTIFACT_IO_UNSUPPORTED`.
An attempted 170-test discovery (157 inherited plus the 13 initial
supplemental tests before they were relocated outside the sealed suite)
reported 70 failures and 9 errors; sampled traces were rooted in that local
platform boundary, so no hosted regression conclusion is drawn from the run.
The supplemental tests were then moved to `tests/assembly`, preserving the
inherited suite; their final count is 14. This Windows result is not a hosted
Linux regression verdict. The exact new candidate still needs a fresh hosted
combined run and artifact inspection; the previous green run 36542478700
predates these controls.

Open: 17 historical recheck originals (local control/residual split recorded
separately), 14 capability-review records, 52 integration validations and 30
deployment/final-acceptance records. Live generator and independent-assessor
evidence is `BLOCKED_BY_CREDENTIALS`; no provider call ran. Provider/model
identity remains configuration-driven, and any future hosted live job must be
manual with protected-environment approval and job-scoped secrets. Ordinary
CI remains credential-free. HARD-039 active, HARD-040 incomplete, Task 028
paused; Sections 17/18 untouched; no PR or merge authorized by this record.
