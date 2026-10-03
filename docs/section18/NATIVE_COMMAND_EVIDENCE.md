# Actual-paint command evidence export

The canonical producer already records the exact Node argv and kernel policy in
`actual-paint/PROCESS.json`. The Section18 validation result previously omitted
that file from its uploaded evidence, leaving command requirement G incomplete.

The native render test now retains only its verified command, full kernel-policy
metadata, execution outcome and original receipt hash in the uploaded result.
Raw stdout/stderr, scene text, request bodies and secrets are not exported.
The exact approved flag is limited to the actual-paint command; the unchanged
default WorkerPolicy still has address-space bytes8589934592. The Wasm scope
control additionally checks that this export exists. No new method is counted.

This is an evidence-harness change, not a production renderer/browser change.
It cannot mint an ActualPaintWitness, suppress setup errors, mark actual paint
passed or waive the native render gate. A failed render remains failed even
when its authentic invocation is safely retained. Exact-head Linux execution
and independent artifact inspection remain required. Task028 stays paused.
