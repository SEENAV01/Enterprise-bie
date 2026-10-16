# Task036 Phase 2R-C: owner-approved Section18 deadline

## Decision and exact scope

On 2026-10-16 the repository owner authorized decision D3 in the Task036
Phase 2R-C instruction: change only the `canonical-regression` job in
`.github/workflows/section18-implementation.yml` from 60 to 90 minutes, and
the matching expected value in
`tests/productization/scene_ir/test_canonical_history_workflows.py`.
The baseline is `ed9f845859a32107c021ff826761ae2350cd3125`, tree
`249065d3a5c748de7a52f5188c06ac194e3ecec1`.

All other budget assertions remain unchanged. In particular Post-DIR stays
45 minutes; Section18 `native-render` stays 20 minutes and
`section16-regression` stays 60 minutes. No job, step, trigger, command,
dependency, provisioning rule, permission, isolation policy, or test selection
changes as part of this deadline decision. The former Post-DIR deadline
increase was withdrawn and is not implemented.

## Evidence and limits

The owner's decision cites the read-only Phase 0D comparison: 734 mandatory
M1 tests added to canonical discovery; the source-ledger lane grew from about
21 seconds to 612 seconds; and the observed live Section18 job took about
65 minutes. The recorded lane comparison was 20.879 seconds on canonical
main versus 611.665 seconds on the PR. The relevant retained runs include
canonical Section18 `37804752372` and PR Section18 `38770118094`.
These are historical observations on their own candidates, not measurements
of this new candidate and not proof of a single causal explanation.

The separate Option S smoke change keeps each real child at the existing
30-second CPU and 45-second wall limits. This decision does not change
product-child, Chromium, render, memory, output, PID or sandbox limits.
The new candidate must still pass its actual required hosted gates; a longer
job deadline is neither a PASS receipt nor a waiver of any test.

## Governance and verification

This records the owner's specific authorization, not an independent review.
Existing sealed source ledgers, amendments, original preimages and historical
review records remain unchanged. The retained workflow test still rejects
every other unapproved canonical job deadline increase.

Per the owner, no YAML-parser dependency is installed for this change.
Local validation must prove the workflow byte diff is exactly the one
`timeout-minutes` substitution. GitHub workflow admission and the hosted
canonical-history controls remain required.

Task035's bounded canonical sign-off stands. Task036 is not canonical-complete.
Audio reconciliation remains OPEN and AUDIO_REPLAN_REQUIRED remains fail-closed.
Global VIDEO_CODE and later product stages remain NOT_RUN. There is no merge,
Task037, release-readiness or product-acceptance authorization in this step.
