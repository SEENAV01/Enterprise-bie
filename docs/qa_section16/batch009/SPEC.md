# Section 16 Batch 009 — animation-quality evaluators

## Governing scope and status

Original registry page 18: BIE-QA-ANI-001 temporal alignment, BIE-QA-ANI-002
excessive motion, BIE-QA-ANI-003 animation-semantic alignment. These are additive
bounded local implementations under `bie/qa/animation_v2`, not replacements for
Section 11's native ANI engines. They are IMPLEMENTED LOCALLY, NOT PRODUCT ACCEPTED.
Section 15 remains externally managed. No repository/global continuation writes.

BIE's target is source-grounded, accurate, cinematic educational video and meaningful
playable learning games. The diagnostic rectangles included here are QA fixtures,
not the product's desired teaching style or evidence of its cinematic quality.
The original registry remains a capability baseline; material gaps require later
traceable hardening and re-audit, then canonical integration and real-book E2E proof.

## Architecture and trust boundaries

`AnimationRequest` is a candidate. `AnimationPolicy` is independently supplied by
an operator: required modes, objects, source claims, tracks, cue windows, semantic
requirements, invariants, motion limits and capture-frame schedule. Candidate
metadata cannot silently lower the quality bar or redefine the reviewed scope.

The evaluator reuses `source_v2` to inspect source/output artifact bytes and exact
text/citation bindings, `reasoning_v2` for purpose-scoped authenticated reviews,
and `release_v2` for candidate/run/revision/evidence contracts. Nothing in this
package establishes that an authenticated reviewer is calibrated or correct.
Positive review fixtures are explicitly SYNTHETIC; no operational keys are supplied.
Missing or uncertain reviews require review. Rejection cannot be outvoted. Duplicate
identities, wrong context, stale/revoked keys or bad signatures cannot obtain approval.

The compatibility adapter imports the actual preserved native ANI `Event`, temporal
and motion evaluators. Native fingerprints are retained as diagnostics only. Their
metadata scores and PASS labels never authorize the new checks or product release.
Those native files are a verified historical snapshot, not a statement about current
GitHub HEAD. The pinned commit and Git-blob/SHA-256/length identities are recorded.

## Temporal evaluator — ANI-001

Times are bounded integer milliseconds. Frame time is an exact Fraction computed
from frame index and reduced rational FPS (including 30000/1001); repeated rounding
cannot silently accumulate drift. A capture records that exact prescribed clock,
although the browser necessarily receives a finite-precision time for measurement.

Check object/mode lifetimes, operator cue windows, before/after/start-sync/end-sync,
coverage and overlap obligations. Simultaneous tracks on distinct properties are
permitted; overlapping writers on the same mode/object/property are rejected.
Cue windows are declared timing evidence, NOT actual TTS word timing or audio sync.

## Excessive-motion evaluator — ANI-002

For supported piecewise-linear or step-end scalar tracks, evaluate the union of
all keyframe boundaries. Moving-object concurrency and total normalized rate use
peak intervals, not a low average. Translation checks vector speed (x²+y²), not
only each component separately. Rotation, scale, opacity and progress have explicit
rate guards. Steps have per-event and aggregate jump limits. Reversals are counted
across split tracks; an unexplained discontinuity between separated tracks is a
blocker. A zero net displacement does not imply zero intervening motion.

Reduced-mode requirements retain the same operator-approved essential semantic
identity set and apply explicit reduced motion limits. This does not prove that
remediation teaches equally well, satisfies all accessibility criteria or is safe
for a particular person. Thresholds are engineering guardrails, not clinical or
empirical cognitive-load measures. Flash/photosensitivity evaluation remains open.
Camera composition, arbitrary CSS transforms/springs, perspective and 3-D occlusion
are not certified by these scalar checks and require review/rendered evidence.

## Animation-semantic evaluator — ANI-003

Check actual source-claim coverage, purpose and semantic identity, approved ranges,
required endpoints and monotone/constant trends across INTERMEDIATE keyframes.
Conditions and not-to-scale disclosures must cover the entire declared transform.
Authenticated mapping/inference assessments remain mandatory for contextual meaning.

Bounded invariants support equal quantities, ordered quantities and constant sums
of same-property scalar tracks. For linear and step-end interpolation these are
linear constraints: extrema occur at the union of knots and their left/right
limits inside the closed proof window. At the start boundary only the state
AT that time is included; the preceding left limit lies outside the window.
The end boundary includes its post-jump state. Checking those points proves only
the specified constraint over the
specified declared trajectory. It is not a general theorem prover or validation
of a physical law, biological process, arbitrary simulation or rendered depiction.
Unknown interpolation, missing members or shortened coverage cannot claim proof.

## Optional Chromium capture and evidence verification

`browser.collect` loads only trusted authored diagnostic HTML, disables page
JavaScript and external requests, pauses CSS animations and sets their currentTime
at operator-prescribed frames, then records DOM rectangles/opacity/display and PNGs.
It limits input size, pixels and sample count and refuses existing output folders.
It is NOT a hostile-input isolated worker; OS/process/network/security attestation
and production quotas are separate deployment obligations.

Capture verification re-reads confined regular files, validates hashes/lengths,
HTML identity, plan/policy/mode/viewport bindings, exact rational frame order, PNG
format/dimensions and observed coordinates/visibility against the declared tracks.
Unsupported paint/overlays/active content are surfaced, not silently accepted.
Hash checks bind evidence bytes; they do not independently prove collector honesty
or that a fabricated measurement represents those PNG pixels. Production capture
attestation and pixel-semantic validation remain open.

Capture plan_digest deliberately excludes captures and the final candidate digest:
otherwise capture inclusion would create a recursive hash dependency. It still
binds source bytes, source claims, run, revision and the whole animation plan.
Full authenticated review and release envelopes independently bind the final
request/candidate including every capture artifact. The integration tests exercise
this sequence and reject missing candidate artifacts or context changes.

Paused frames are SAMPLES. They are not real-time playback, unsampled-frame proof,
actual narration alignment, full Remotion/video/game execution or learner outcomes.
Even a healthy fully authenticated sample remains REVIEW_REQUIRED. The complete
`animation_quality` release gate is only FAIL or NOT_RUN and always unsigned.

## Modules and interfaces

- `models.py`: immutable strict contracts; bounded inventories/units and references.
- `metrics.py`: exact rational clocks, interpolation, constraints and peak motion.
- `attestation.py`: scoped review obligations using inherited trust contracts.
- `evaluator.py`: three task reports, source checks, deterministic recomputation.
- `capture_evidence.py`: byte/clock/PNG/geometry sample verification.
- `browser.py`: optional trusted diagnostic CSS collector; Playwright + Chromium.
- `adapters.py`: actually exercised pinned native ANI diagnostics.
- `bridge.py`: unsigned candidate-bound release evidence; never full-media PASS.
- `codec.py`, `__main__.py`: closed-world JSON and unsigned CLI.

Three JSON schemas describe request/policy/review STRUCTURE. Runtime validation is
still required for bounds, units, cross-references, authority and actual file bytes.

## Execution

From the extracted cumulative package, Python 3.11+ (verified environment is in
TEST_RESULT.json). The test stack uses jsonschema and Pillow; browser diagnostics
add Playwright and an installed Chromium binary. No credentials/network required.

```sh
python -B scripts/verify_qa_animation16_batch009.py --output /tmp/bie-qa009-new-run
python -B scripts/verify_qa_animation16_mutation_probes.py --output /tmp/bie-qa009-new-mutations
python -B scripts/verify_qa_animation16_browser.py --output /tmp/bie-qa009-new-browser
python -B scripts/verify_qa_animation16_browser.py --recompute evidence/qa_section16/browser_run_009
python -B scripts/verify_qa_section16_package.py
```

All receipt destinations must be NEW. A CLI demonstration using real packaged
source/capture bytes (returns 3 / REVIEW_REQUIRED, not a success certification):

```sh
D=evidence/qa_section16/browser_run_009/healthy-linear
python -B -m bie.qa.animation_v2 --request "$D/request.json" --policy "$D/policy.json" \
  --artifact-root "$D" --as-of 1800000000 --output /tmp/qa009-unsigned-new.json
```

Exit 0 means only bounded CHECKS_PASSED; exit 2 BLOCKED, 3 REVIEW_REQUIRED, 4 input/
filesystem error. The CLI accepts no inline secret keys and never overwrites output.
For authenticated use call `evaluate` with independently configured ReviewVerifier
and source AssessmentVerifier. Call `prepare_release_evidence` for unsigned report
bytes/envelope; signing, trusted storage and canonical routing are not implemented.

## Verification and reproducibility

Actual test IDs, counts, subcases, platform, dependency versions and source/test
hashes are in executed_run_009. Historical tests are run in isolated subprocesses.
Interrupted command-window attempts remain development evidence; they are not
successful test receipts. Neither repeats, subtests nor shared atomic packages add
to unique test counts. Mutation probes are selected, not exhaustive.

Frozen archives use deterministic filenames/order, timestamps, modes and compression.
Byte-identical reconstruction is verified on the SAME frozen inputs/environment,
not claimed across browser/OS/library versions. PNG rendering determinism is separate.
See the external DELIVERY.json for actual final archive hashes, fresh-extraction
reruns, manifest checks, corruption rejection and backup verification.

## Explicit remaining acceptance work

Current-HEAD reconciliation and caller adoption; full canonical regression;
operational assessors and measured audio/word timing; native scene/Remotion/game
capture; unsampled motion/3-D/compositing and flash checks; capture-worker attestation
and isolation; real-book/learner validation; downstream gates; section audit,
hardening/re-audit and enterprise release. Nothing in this batch closes those gaps.

## Implementation references

Browser API use: W3C Web Animations (pause/currentTime/getAnimations):
https://www.w3.org/TR/web-animations-1/
W3C CSS Animations Level 2:
https://www.w3.org/TR/css-animations-2/
These document APIs, not validation of BIE's educational effectiveness.
