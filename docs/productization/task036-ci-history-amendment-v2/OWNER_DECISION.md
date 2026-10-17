# Task036 closure owner decision D6

Status: DRAFT_PENDING_REVIEW_NOT_APPROVAL. This records owner scope, not an
independent review, successful execution, merge authorization or acceptance.

The owner authorized Post-DIR canonical-regression 45 -> 75 minutes and
Section18 canonical-regression 90 -> 120 minutes in the Phase 10B instruction.
This is a capacity decision, not a performance fix. No other job, test selection,
command, trigger, dependency, renderer, child or isolation limit changes.

Evidence motivating the decision: exact-main Post-DIR run 38927953175 at
4d5a284c9a51f4e3536852453d6e7543447d2e68 was cancelled at its 45-minute
deadline, with the canonical gate taking 2,567 seconds. Section18 run
38927953187 attempt 1 took 87m42s against 90 minutes. These are historical
observations, not evidence that these new workflow bytes have executed.
The previously disclosed D4/D5 owner retries remain exceptions in history;
this amendment grants no retry policy and establishes no flake root cause.

The v1 amendment, seals, historical profile pins and all original reviewer
records stay immutable. Five immediate-parent Git preimages establish the
v2 chain. REPLACEMENTS.json is fixed integrity evidence, never approval.
Independent review and exact reviewed bindings are absent in Commit A.
New authority constants remain PENDING, so product admission must fail closed.
Commit B may install genuine byte-exact review/binding records only after
independent review; no current-file hash can substitute for that decision.

No Task036 canonical-completion claim. Audio reconciliation remains OPEN;
AUDIO_REPLAN_REQUIRED remains fail-closed. VIDEO_CODE and later stages are
NOT_RUN. Review is required; accepted, release_ready and product_accepted
remain false. Task035's original bounded sign-off stands. No Task037.
