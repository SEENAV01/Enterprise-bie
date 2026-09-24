# Bounded recovery re-audit

This is a review of the five implemented recovery tasks, not a full AUDIO section
exit review and not a comparison against unavailable original H4 source bytes.

## Findings addressed during implementation
The original H3 bounded acoustic child was not a canonical isolated execution.
The recovery uses the actual pinned canonical worker and isolates a fixed acoustic
operation rather than recreating infrastructure. Eight dependency Git blob hashes
are independently verified; the ten inherited dependency identities remain.

Legacy signed measurements cannot prove an isolated execution. A separate v2
signature domain and explicit approved-profile trust now preserve that distinction.
The same actual measurement is embedded as v1 only for existing QA compatibility.

Media/job/profile binding alone would leave exported durable run/job labels
unauthenticated. The recovery additionally signs the complete durable request
fingerprint and rechecks it in storage, completion and publication. Rehashing a
relabeled export cannot satisfy that signature.

Canonical H3 envelope and lease logic is preserved. Reusing a legacy result as
kernel-verified evidence is rejected; the wrapper requires the fourth envelope,
current approval/signature and original parent chain. Stale lease owners and a
claim-complete/lease-incomplete crash are tested at the same canonical boundaries.

## Remaining limitations, not hidden passes
The native worker is still a bounded Linux adapter with trusted host/service
assumptions, broad read-only system runtime mounts and per-process limits, not
full OS attestation or a formal sandbox proof. Real boundary fixtures demonstrate
specific enforced controls, not universal exploit resistance.

The diagnostic evaluator remains legacy English with explicit unsupported cases,
uncalibrated raw scores and no verified pronunciation or ground truth. TTS, neural
provider calls, SYNC and MIX are not all moved into this worker by this batch.
Paid-call uncertainty, fleet coordination, aggregate budgets, orphan GC,
long-book scene scheduling, live key custody, owned repair dispatch, actual
DIR/ANI/COMP handoff and render/real-book gates remain unresolved.

## Next governed implementation direction
Continue F03 with an inventory of actual remaining TTS/cache/SYNC/MIX/native
call sites and the canonical worker/secret/network contracts they require. Derive
bounded tasks from those verified interfaces; do not assume the network-disabled
acoustic profile is suitable for paid synthesis. Keep F02 multilingual/calibration
and F04 actual consumer/invalidation/render requirements open. Do not exit AUDIO
merely because these five recovery tasks or a planned batch count have finished.

## Deployment host resolution boundary
The unchanged canonical worker resolves `unshare` using its host PATH. The current
verification host resolves it to the same `/usr/bin/unshare` selected by the
profile; HOST_RESOLUTION.json records this observation. The wrapper does not
claim to pin every future hostile/custom PATH, dynamic loader or system library.
Production deployment must control and verify launcher resolution and service
PATH as part of the remaining F03 host-policy gate. This is not a whole-host
attestation or a closed production-security finding.
