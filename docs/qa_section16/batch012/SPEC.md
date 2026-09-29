# BIE Section 16 / Batch 012 — GAME QA contracts

## Scope and ownership
Original registry page 18: BIE-QA-GAME-001 build evidence; BIE-QA-GAME-002
runtime evidence; BIE-QA-GAME-003 interaction QA; BIE-QA-GAME-004 learning alignment.
This is additive `bie/qa/game_v2`, NOT a replacement for the Section15 game engine.
Section15 remains owned by the other session. No canonical branch, global registry,
Codex or Android implementation is modified. Cumulative Section16 delivery is not a
complete repository backup. All previous limitations and evidence remain in place.

## Independent expected behavior, not a self-reporting game
The operator supplies GamePolicy independently of GameRequest. Its input inventory
binds source/code/toolchain artifacts; its observable selectors, finite states,
actions, transitions, scenarios, viewports and learning targets define expected
behavior. The candidate cannot select an easier path or change an expected answer.
Policy construction rejects duplicate, contradictory or ambiguous identities.
BFS checks state reachability and a success path. Every required transition must
appear in an approved scenario and must actually be observed. This is complete
coverage of the finite declared oracle, NOT exhaustive analysis of arbitrary code,
all possible click sequences, every browser event or every academic interpretation.

Canonical inventory hashes include sorted paths, IDs, roles, byte sizes and SHA256.
Request and source evaluation share run/revision/candidate identities. The capture
oracle digest deliberately excludes the input digest/source policy so that the
build/capture/release candidate does not require a circular hash. Final signed review
still binds the entire request and policy, including the actual runtime artifact.

## QA-GAME-001: build evidence
Inspect actual source, dependency/toolchain inputs, emitted HTML/JS/assets, compiler
receipt and encoded stdout/stderr bytes with the inherited SnapshotStore. Verify
sizes/hashes, safe paths, identity aliases, build run/revision/game, input and output
inventories, entrypoint, tool allowlist, freshness and execution outcome. A started
process with a nonzero exit, timeout or a tsc diagnostic cannot pass because someone
set `success=true`. Non-native or reported execution requires review. Compiler logs
are integrity-bound, not independent proof that their purported producer is honest.
No arbitrary build command is executed by evaluate(). The diagnostic runner alone
invokes a fixed operator-selected tsc command on authored trusted input.

## QA-GAME-002: runtime evidence
Require a bound build-receipt hash, output inventory, oracle digest and code revision.
A native-origin record must say `http_entrypoint`, name the approved HTML entrypoint,
use a plain HTTP(S) origin, and carry every required loaded asset with the exact
inspected hash/size. Required assets must be loaded per scenario/replay, not merely
somewhere in the run. About:blank, injected bundles, redirected entrypoints, stale
records, missing modules and wrong versions cannot establish native-origin proof.
Browser exceptions, console errors and unapproved requests block the relevant check.
Screenshots are byte-checked PNGs with expected viewport dimensions. PNG identity is
not a visual-semantic judgment, nor proof of every unsampled rendered frame.

## QA-GAME-003: interaction QA
Each approved scenario has exactly its boot snapshot and ordered UI actions, for
all independent replays. Observe visible DOM values rather than accepting the game's
own dispatch return value. Validate one visible element per selector, state values,
score, feedback, before/after transition, order, timings and screenshots. Check
repeated-submit idempotence, correct/error paths, hints, reset and reload where the
operator asks for these. A correct default path cannot cover up a failed keyboard,
mobile-viewport or other approved path. Replays compare actual state trajectories.
Observed transition credit requires both adjacent checkpoints to be valid.

Supported capture actions: locator click, key press, fill, drag-to and reload. Tests
and authored browser cases exercise click, key press, reset and reload. Fill/drag
capture dispatch exists but was NOT exercised in real browser diagnostics here.
A mobile viewport is not evidence of a real Android touch device or touch gesture.
Canvas, WebGL, 3D, inaccessible controls and non-DOM state need separate adapters.

## QA-GAME-004: learning alignment
Use existing source grounding/provenance checks on actual UTF8 claims and citations.
Require the source-linked challenge to be visible before the response, and distinct
correct/error feedback to match the expected source-linked claims after the response.
Both outcome classes must be observed; repeated replays do not create new learning
opportunities. Hints/instructions also require explicit source mapping. No unbound
claim can hide outside the approved content inventory. Purpose-scoped independent
assessment is required for pedagogical/scientific meaning, scope and mechanic fitness.
Mechanical correctness and a score of 10 never prove that a real learner mastered
anything. General misconception diagnosis and assessment quality remain open.

## Trust and release
Reuse ReviewVerifier purpose-scoped HMAC records: calibration for build/runtime,
inventory for content scope, teaching for each challenge. Enforce exact evidence
sets, current request/policy binding, age, authorized keys, independent groups and
confidence. Test-only/uncertain reviews require review; a rejection is never outvoted.
Positive unit fixtures are explicitly synthetic, including their `native` labels.
No live or calibrated independent assessor is executed.

The bridge uses inherited four gates: game_build, game_runtime, game_interactions,
game_learning_alignment. All report bytes are candidate-bound and unsigned; a blocked
result produces FAIL, otherwise NOT_RUN. It never produces a full game release PASS.
The inherited ReleaseEvaluator is exercised and blocks the incomplete evidence bundle.

## Capture modes and actual environment blocker
The default collector serves an immutable snapshot of approved output bytes on a
loopback HTTP origin, loads the real entrypoint and uses real locator input. It does
not substitute responses or call a game's internal dispatch. The collector requires
explicit trusted-diagnostic opt-in and reports production sandbox verification false.

Execution here encountered Chromium's managed `URLBlocklist: ["*"]` and
`net::ERR_BLOCKED_BY_ADMINISTRATOR` on loopback navigation. Policies were NOT changed
or bypassed. The denied attempt and partial run are preserved as failure evidence;
native-origin execution is NOT verified. A separately explicit `diagnostic_inline`
mode loads the authored page and the actual compiled one-file JavaScript in an IIFE.
It is labelled injected_bundle/about:blank, carries NO fabricated loaded-asset list,
and necessarily fails the native-entrypoint/runtime gate. It supports only one simple
module without imports/exports. Real UI interaction checks can be inspected separately
without upgrading injected evidence to native evidence. No clinical, accessibility,
hostile-code isolation or enterprise security certification is implied.

The actual browser cases are technical defect fixtures, not BIE's cinematic educational
game design. Default runtime collection must still be executed under an authorized
worker environment and on completed native Section15 output during integration.

## Bounded resources and failure behavior
At most128 states/actions,512 transitions,64 scenarios,128 actions/scenario,2–4
replays;4096 declared steps maximum. The diagnostic collector caps total snapshots at256.
Source SnapshotStore bounds remain16MiB/artifact and64MiB total. Strict JSON decoding
rejects extra fields, booleans as numbers, duplicate JSON keys and nonfinite numbers.
PNG dimensions are checked before verification. Policy thresholds and required
coverage are operator-controlled; timestamps are integer milliseconds. CLI input
files are bounded4MiB. Inputs beyond these limits fail closed, not silently truncate.
Immutable publication, signed worker identity, distributed scheduling, full-process
sandboxing, adversarial generated-code security and all-device behavior remain open.

## Execution
From a fresh extracted package (install inherited dependencies in an operator-managed
virtual environment; Python3.13 was the executed interpreter):

```bash
python -B scripts/verify_qa_section16_package.py
python -B scripts/verify_qa_game16_batch012.py --output /tmp/bie-qa12-tests-new
python -B scripts/verify_qa_game16_mutations.py --output /tmp/bie-qa12-mutations-new
python -B scripts/verify_qa_game16_browser.py --output /tmp/bie-qa12-http-new
# Separate restricted offline diagnostic, never native runtime proof:
python -B scripts/verify_qa_game16_browser.py --output /tmp/bie-qa12-inline-new --diagnostic-inline
```

A prior output directory is never reused. Default HTTP diagnostics will fail under
this environment's current managed network policy; do not disable that policy.
Run them on the separately authorized worker. Evaluating a packaged inline case:

```bash
python -B -m bie.qa.game_v2 \
 --request evidence/qa_section16/browser_run_012/healthy/request.json \
 --policy evidence/qa_section16/browser_run_012/healthy/policy.json \
 --artifact-root evidence/qa_section16/browser_run_012/healthy \
 --as-of 1800000000
```

Expected overall exit2 BLOCKED for injected evidence even when interaction checks
pass. The `as-of` value is the explicitly synthetic diagnostic evaluation clock,
NOT a claim of wall-clock collection time. Actual compilation wall time is separate.
Other CLI exits:0 bounded checks passed;3 review required;4 invalid input/output.
No CLI path creates operational trust keys or accepts a candidate-provided policy.

## Native compatibility inspection
Read-only contract inspection at commit a68e054025b8fe7756a71e998d9e9103dad8e0f4:
`bie/game_engine/build_runtime_engine/contracts.py` and `browser_runtime.py`.
The inspected BrowserEvidence smoke implementation uses an about:blank/injected
self-contained bundle. The adapter preserves that distinction; flags such as
studio_grade or slide_deck do not certify experiential quality. No new canonical
file was vendored, executed or declared byte-preserved. This snapshot is not a claim
about the latest repository HEAD or Section15's current completion status.

## Test map and remaining work
- test_evaluation.py: byte tampering, schema/receipt scope, finite oracle, observed
  score/feedback/lifecycle, replay, viewports, module coverage, screenshots, source links.
- test_trust_contracts.py: strict JSON, bounded contracts, attestation replay/age/purpose,
  independent quorum, uncertain/rejected/test-only judgments, path and type failures.
- test_bridge_cli_adapter.py: unsigned bridge, inherited release block, schema documents,
  conservative native adapter, CLI result codes and overwrite refusal.
- Selected private-copy mutation probes remove individual safeguards and require their
  specific regression to fail. This is not exhaustive mutation testing.

Continue original REPAIR tasks, then full-section completeness audit, material
hardening, re-audit, current-HEAD conflict checks/integration, canonical regression
and real-book/video/game/learner end-to-end acceptance. No section exit is claimed.
