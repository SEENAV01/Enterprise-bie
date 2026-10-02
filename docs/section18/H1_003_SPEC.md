# BIE-APP-H1-003 — bounded PDF processes and cancellation recovery

Finding-derived local hardening, not a new engine, automatic retry policy,
public deployment or product acceptance. Canonical Sections 1–17 are unchanged.

## Source admission

The HTTP source remains bounded to 25 MiB. A dedicated isolated Python child
calls the genuine canonical base PDF inspector. Hard CPU and memory budgets
are applied before importing the parser: 30 CPU seconds and 1 GiB. Limits may
be lowered, not widened. Unsupported/denied enforcement fails closed.

The parent enforces 45 wall seconds and 4096 output bytes, kills/reaps failed
children and never propagates provider or operator credentials to source
inspection. Malformed/encrypted documents are INVALID; containment/tool failure
is BLOCKED, not fake VALID. Neither failure stores source bytes in CAS.

Linux uses hard resource limits; Windows uses a private unnamed Job Object.
These are resource controls, not network isolation or an untrusted-code sandbox.

## One-job controlled worker

The existing CLI delegates to one independently supervised child. The child
applies the same CPU/memory caps before importing engines. Parent wall-time
enforcement does not depend on a Python timer inside the worker. Output is
bounded and strictly validated. Only the necessary process-provisioned operator
credential is forwarded; other API/provider secrets are excluded. No secret
value is printed, packaged, persisted or placed in command-line arguments.

The trusted Python `Service.work_once` port is not a shared-server OS containment
boundary. Operational worker execution must use the controlled CLI. No browser
or Android worker-launch endpoint is added.

## Queued cancellation

A durable hash-bound cancellation intent and audit credits are committed before
native queue/persistence changes. Pending cancellation prevents controlled
dispatch, pause/resume and successful status claims. Repeating the identical
authorized cancellation reconciles only validated partial canonical transitions:
queue DEAD_LETTER, attempt BLOCKED, cancellation event, run BLOCKED. It does not
fabricate boundaries, erase the parent or weaken canonical contracts.

Same-process overlapping identical cancellations use the existing bounded
single-flight admission. Cross-process completion replays only an exact committed
operation and native cancellation proof, never recreates missing audit credits.
Revocation, tenant ownership, source/config identity and revision are rechecked.

Running-job cancellation, arbitrary native-state repair, crashed-worker audit
reservation recovery and distributed atomic transactions are not implemented by
this task. Such states remain REVIEW_REQUIRED/BLOCKED, not fake cancellation.

## Evidence

31 distinct local methods cover actual OS memory denial, canonical child parsing,
actual bounded worker execution, wall/output/startup controls, secret isolation,
four durable cancellation fault cuts, restart, revocation, tampering and actual
two-process cancellation. Fault controls/reruns do not inflate distinct counts.

The added Linux game-preview lane executes the canonical build/compiler/browser
and binds the actual package to operator CAS. Its game/source are explicitly
synthetic. Linux execution, full cumulative regression and final archive replay
must have their own candidate-bound passing receipts before final promotion.

Task 028 stays PAUSED. No SECTION-COMPLETE, PRODUCT-ACCEPTED or DEPLOYED claim.
