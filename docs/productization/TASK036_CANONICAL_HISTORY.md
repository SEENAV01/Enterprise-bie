# Task036 canonical checkout-history provisioning

This is a CI-only historical-object provisioning repair, not a compiler,
Scene IR, source-amendment or acceptance change. Task036 is not yet canonical-
complete and still requires fresh full canonical, PR and exact-main closure.

## Observed before evidence

Candidate `25bee87b1cf2d079638bfa77b6e1a2f5a150d036`, tree
`d97ae1044a52ae7f7f47021495a6bc182a1f2ae0`, passed the focused Scene IR run
38139523067 and complete M1 run 38139523062, attempt 1. The separate reviewer
verified their safe receipts, including the actual eight native render cases.
These passes are not substitutes for the required complete canonical gate.

Canonical dispatch run 38143716880, attempt 1, failed on that exact candidate:
1,266 selected file rows, 9,905 executed tests, zero assertion failures, five
errors and zero skips. Five unchanged M1 exact-preimage test methods raised
`subprocess.CalledProcessError` from historical `git show` calls, exit 128:

- media diagnostics: `test_fixed_complete_chain_and_exact_parent_blobs`;
- media policy: `test_exact_git_preimages_and_chain`;
- media source pin: `test_exact_git_preimages_and_complete_previous_chain`;
- media threads: `test_complete_exact_chain_and_git_preimages`;
- stitch inputs: `test_all_exact_17da_git_preimages`.

Actual checkout used `--depth=1`. The pinned checkout action defaults to depth 1;
the three canonical-gate callers omitted an override. The current focused M1
checkout uses full history and those same assertions passed there. Available
historical error evidence does not include a retained, exact fatal Git message.
No renderer, kernel or preimage-byte mismatch is inferred from exit 128 alone.

A disposable real local depth-1 clone at the same HEAD reproduced all 17
historical object reads in the five groups returning 128. After fetching full
history into that clone, without changing HEAD or any source bytes, the same
reads succeeded and matched every immutable sealed preimage byte-for-byte.
This comparison ran on Windows Git 2.55.0; it is not a Linux after-suite pass.
Diagnostic repetitions are not new authored unit-test methods.

Safe comparison record SHA256:
`4abc67b69a06f9a2a49afd817953d0c6a4c6a3093c1daf17f922c652bb9eb2b1`.
Failed canonical artifact 11704756497 ZIP SHA256:
`294ca3bbdfa7b7ffc454dfaa99764252a910ca444cf72e994a15ee4561e58ecb`;
digest and CRC verified. Its three source audits, AUDIO 1,684 and GAME 1,123
tests passed, but full Section17 and final preservation gate receipts were
absent/skipped after integration failed. They are not claimed green.

## Exact change and preservation

Add only `fetch-depth: 0` to the existing pinned checkout's `with` block in each
`canonical-regression` job: Post-DIR catch-up, Section16 combined, Section18.
Section18's other two jobs retain their original checkout behavior. No new
token, credential retention, explicit revision override, installer, dependency,
job topology, timeout, test assertion, native source or sealed ledger change.
The previous workflow Git blobs at candidate 25bee87b are respectively:

- `3f95bbff25fa7e9cd18d054eb5bee04d76933655`;
- `815d39ea01c9af372019da95be7567dec61df2d1`;
- `9535d80047645ca22cb0c7229366f2029ad3dc5f`.

Six additive source-contract controls are owned exactly once by the Task036
new-test lane. The original 184 Scene IR identities and all M1/Task035/native/
safety identities remain mandatory. No failed or missing gate is waived.
The original M1 amendment SHA256 remains
`b454659994bdbfb2e931ebac6d6b9915c88c8b7a78f02c5a5363106fa5b39a1c`.

Fresh Linux execution must prove the complete canonical gate on the repaired
candidate, including Section17 and final preservation. Until that evidence and
separate review are complete, Task036 closure remains unapproved. Historical
painter causes and Windows timing limitations remain UNKNOWN, not retroactively
attributed to this checkout repair. Audio reconciliation remains OPEN;
Scene IR is review-required/unaccepted and later global stages remain NOT_RUN.
