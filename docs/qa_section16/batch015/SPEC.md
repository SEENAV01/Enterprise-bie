# Batch015: visual, animation, generated code and finite-game repair

## Contract and scope
Original registry page18: QA-REPAIR008 visual,009 animation,010 code,011 game.
The additive namespace is `bie/qa/media_repair_v2`. Existing source_v2, visual_v2,
animation_v2, game_v2, repair_v2 and domain_repair_v2 interfaces are reused without
rewriting their code. This is cumulative Section16, not the full repository.
Section15 is externally owned and never modified or certified by this batch.

## Authority, deterministic generation and revalidation
`Job` binds the exact source snapshot, failure batch, request/target artifacts,
repair policy, domain policy and resource limits. Both the approved inventory and
proposal generation need current purpose-scoped authenticated reviews. Candidate
suggestions cannot change the owner. A matching authenticated failure must bind
both the current request digest and the original evaluator-policy digest; a wrapper
repair-policy digest is not a substitute for the latter.

`preview` is read-only, unauthorized and returns proposed bytes and a witness.
`generate` checks authorization and provenance, invokes a bounded deterministic
worker, then rereads original bytes. `prepare` creates a new exclusive no-follow
content-addressed proposal under `proposals`; it never modifies originals.
The unchanged repair_v2 controller requires a separate fresh proposal approval,
consumes persistent SQLite attempt/time/replacement budgets, copies the artifact
snapshot into private staging, runs registered validators and checks immutable files.
Generated proposals never certify release. Changed candidate records invalidate old
reviews, compile/render/runtime receipts and bindings; downstream manifests must be
rebuilt. Preserving a request's source IDs does not reauthorize their old evidence.

## REPAIR008: translation-only declared visual layout
Permissions name a state/object, allowed region and maximum translation. A bounded
nearest-first search translates whole axis-aligned boxes and their glyph/line boxes;
font sizes, box sizes, text, colors, opacity, clipping, timing, claims and relations
stay unchanged. Safe areas, protected caption regions, overlap and specified spatial
relations constrain candidates. Every examined position, including rejected positions,
consumes the search budget. Exhaustion or no supported candidate escalates; it is not
an unlimited layout solver or proof of mathematical unsatisfiability.

Only unobserved declared static geometry can be repaired. Captured measurements and
sampled states are immutable evidence, not layout parameters. A changed plan requires
a fresh capture. Existing full visual evaluators are run after the transformation;
clutter/readability/semantic blockers are retained rather than hidden by removing
content or shrinking fonts. Unsigned contextual reviews remain review-required.

## REPAIR009: exact timing changes, preserved values
An operator approves a specific new time window for each selected track. The worker
maps each original knot into that window using exact rational arithmetic and requires
integer millisecond results. It never rounds off a problematic intermediate knot.
Every original value, order, interpolation and semantic identity remains present.
Only linear and step_end scalar trajectories are supported. Cues/lifetimes cannot be
moved to conceal drift. Existing temporal/motion/invariant evaluators rerun; a remaining
speed, reversal, endpoint or interval violation escalates. Actual audio alignment,
continuous playback, springs, arbitrary easing, camera and 3-D behavior remain open.

## REPAIR010: owned generated TypeScript data modules
This bounded profile reconstructs named const exports from independently approved
strict JSON values and source-claim IDs. The original module must carry the exact
owned generator/module header. Handwritten or unknown modules are protected.
The emitter uses a closed no-import data grammar, escaped JSON, explicit identifier
checks, exact safe integers, depth/count/byte limits and prohibited prototype keys.
It does not execute model-supplied code. `as const` is compile-time readonly typing,
not deep runtime freezing. This is not general syntax/type/React code repair.
Successful byte regeneration is not compile/runtime evidence: independent tsc/Node
checks are mandatory before claiming those technical outcomes.

## REPAIR011: independently specified finite game reducer
The operator-supplied existing GamePolicy is the oracle, not a proposal-generated
test. The worker reconstructs only an owned pure transition/state data module.
Every state, score, action, feedback and prescribed scenario is preserved. All states
must be reachable and the explicit scenarios executable. Prompts must appear in each
required response pre-state, not only somewhere in the graph. Feedback/hints/instructions
must match inspected source claims. A map-backed reducer rejects undefined state/action
pairs and returns fresh observation objects. The bounded profile does not repair UI,
DOM events, asynchronous state, persistence adapters or native Section15 compiler code.
A technically correct reducer does not prove actual learner mastery or browser operation.

## Input/output and execution
Public dataclasses: Limits, VisualRepairPolicy/LayoutPermission,
AnimationRepairPolicy/TrackWindow, CodePolicy/ExportValue/CodeRequest,
GameRepairPolicy/GameRepairRequest and Job. `read_request`/`read_policy` parse strict
closed records. Seven JSON schemas under schemas/qa_section16/batch015 establish
structure; Python constructors/evaluators enforce semantic and cross-record constraints.
Errors raise ContractError with stable explicit reason codes; no fallback returns PASS.

Read-only demonstration, using the packaged authored diagnostic artifacts:

```bash
PYTHONPATH=. python -B -m bie.qa.media_repair_v2 BIE-QA-REPAIR-008 \
  evidence/qa_section16/executed_run_015/diagnostics/generated-repair-8/artifacts/generated/request.json \
  evidence/qa_section16/executed_run_015/diagnostics/generated-repair-8/domain-policy.json \
  --root evidence/qa_section16/executed_run_015/diagnostics/generated-repair-8/artifacts
```

Exit3 means unauthorized preview/review, not an error-free approved repair. Exit2 is
explicit escalation. Programmatic generation needs externally provisioned authorization;
the packaged test keys must NEVER be used as production trust.

## Reproduction
Use the recorded Python environment and installed local tsc/Node. No network installs
occur in these functions. Keep output directories NEW and outside the package:

```bash
python -B scripts/verify_qa_media_repair16_batch015.py --output /tmp/qa15-tests-new
python -B scripts/verify_qa_media_repair16_mutations.py --output /tmp/qa15-probes-new
python -B scripts/verify_qa_media_repair16_execution.py --output /tmp/qa15-demo-new
python -B scripts/verify_qa_section16_package.py
```

The mutation runner works on a private source copy. A full shared test run executes
all inherited local suites; it is not the canonical repository suite. The exact package
manifest rejects additions including interpreter caches, so retain -B and external outputs.

## Production obligations
No live model/assessor, hostile-code sandbox, distributed journal, native scene compiler,
Remotion render, browser game, calibrated educational quality or real-book E2E is proven.
Production workers must supply isolated trusted validators and fresh downstream evidence.
Do not merge these bundles blindly over latest HEAD. After all original tasks: audit,
material hardening, re-audit, governed staging/integration and full regression are required.
Next original entries: REPAIR012 repair evidence and REPAIR013 repair regression.
