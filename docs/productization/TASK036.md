# BIE-PROD-036 — current Visual/Animation/Director to native Scene IR

Status: FORENSIC DESIGN GATE; producer implementation has not started.

Approved base: `5b1cafc766c9df9c3e0748f459e6beb9b8f1f243`.
Base tree: `ce5044e06c9b2fe8164b7fb15cc59976941f8116`.
Branch: `product/scene-ir-producer-001`.
Task035 is canonical-complete within its bounded technical planning scope.
This document grants no amendment, native edit, acceptance or downstream execution.

## Existing global contract and proposed scope

The active graph and preserved v1 graph agree on ordered SCENE_IR inputs:
`visual.plan`, `animation.plan`, `director.plan`; output `scene.ir`;
declared predecessors `VISUAL`, `ANIMATION`. Director must also be verified.
Neither graph needs alteration. The intended new profile alone has eleven stages:
SOURCE, DOCUMENT_INTELLIGENCE, KNOWLEDGE, PREREQUISITE, MATH, REASONING, PEDAGOGY,
DIRECTOR, VISUAL, ANIMATION, SCENE_IR. It is not implemented at this checkpoint.
Historical Task029–035 profiles remain 3/5/6/7/8/9/10 stages respectively.

The current native unified document/codec/compiler loader admit a single scene.
`bie.scene_ir.contracts.SceneDocument` also exists as an older multi-scene type,
but has different fields, element/time contracts and no demonstrated compatible
unified codec/loader route. It is not authorization to publish a scene list under
the current global output. Initial admission must require the COMPLETE Director
execution to be single-scene; reject multiple scenes, not select the first one.

## Handoff/document reconciliation and source-to-field plan

Task035's `animation.sceneir_handoff` is a private readiness record, schema
`0.1.0`. The native `UnifiedSceneIRDocument` is schema `1.0.0`. The handoff is
not a scene document and must remain byte-preserved. Its nodes retain actual
track IDs, target IDs, action, milliseconds, references, owner, parameters and
fallback identity. `adopt_ani_handoff` consumes those nodes and a caller-supplied
catalog; it does not recover source semantics or visual properties.

Prospective authoritative catalog inputs are the independently verified Task035
`animation.current_inputs.rows[].primitive_rows`, the exact same-stage Task034
grammar/layout/access/text/QA records, and current native Director execution:

| Scene field | Authoritative upstream source |
| --- | --- |
| scene ID and sole-scene admission | complete current Director architecture and timing scene set |
| title | current Director architecture title; no invented scene title |
| duration and timing basis | exact Director scene duration and timing basis, not max track endpoint |
| element identity | exact Visual primitive ID and grammar element ID, with reversible mapping |
| layout box and canvas | verified Visual layout box and explicit TargetProfile dimensions |
| chart values/categories/axis labels | native grammar series/frame plus independently verified source obligations |
| chronology/order/date uncertainty | native historical event payload plus source item/time-label/order obligations |
| cellular kind/label/declared structure | native cellular grammar payload plus source obligations; no inferred flow/containment |
| source/reasoning/concept/objective refs | verified current rows and native Director/source bindings |
| action, timing, parameters, easing | exact persisted Animation plan and handoff node, not helper defaults |
| narration links | current Director anchors/revision and identity-joined TimingBinding |
| accessibility | actual same-stage Visual accessibility records, not a invented PASS flag |

This table identifies inputs, not a completed/admitted element conversion policy.
Native Visual primitives include axis/bar, timeline axis/event marker/uncertainty
band, and cellular boundary/region/organelle. They are not automatically Scene IR
registered element types. A faithful native decomposition must be justified and
independently conservation-tested, not replace the families with generic captions.

The adopter indexes catalog rows by ID (duplicate rows can overwrite), defaults
missing start/end and coerces integers. Task036 must prevalidate exact nonboolean
finite values, bounds, uniqueness, lineage, node-to-plan equality and target IDs.
It emits only animated targets. Chart frames and timeline axes explicitly abstain
from motion in Task035; required static context must be composed separately using
native element/document APIs without new tracks, then FINAL-document validation.
Multi-target expansion requires a reversible track/target identity map.

## Native validation/currentness composition identified

`validate_scene_ir_document` invokes schema, semantic, reference, temporal, spatial,
accessibility and source/reasoning-trace validators. Require all seven reports and
`require_dsl_gate`. Registry checks alone are not domain conservation. Use native
element/domain contracts and separately compare complete upstream semantic inventory.

`encode_scene_ir`, `decode_scene_ir`, `roundtrip_scene_ir` and
`compiler.scene_ir_loader.load_scene_ir_payload` provide document/consumer admission,
NOT code generation or render evidence. A bounded strict JSON boundary must reject
duplicate/unknown keys, nonfinite values and coercions before permissive parsing.
Unicode, parameters and fingerprint/fields must survive exact round-trip.

`DSLVersionVector` and native replay/currentness can bind revisions/schema/target,
provenance/assets. Native currentness checks listed dependencies only; the adapter
must independently enforce exact complete dependency-set equality, including no
foreign extra parent. Existing producer guards, CAS, SQLite, queue, fencing and
Section18 delegation remain the intended persistence/control-plane architecture.
No new storage or authority is proposed.

## Motion/capability incompatibility requiring a governed decision

There are three different facts to retain: Scene IR name registration, compiler
capability declaration, and actual runtime/render support. None implies the others.

1. The canonical compiler capability factory
   `bie.compiler.qa_scene_compile.native_qa_capabilities` declares `comp:<kind>`
   version `1.2.0`, profile `web`, with `render` plus
   `registered_actions_for_kind(kind)`. It does NOT declare Task035's generic
   `reveal` or `emphasize` for chart/timeline/diagram. The additional architecture
   registry is a registration API, not a populated approved alternative profile.
2. Task035 deliberately retains native semantic fields and all current lineage in
   its actual AnimationTrack payload. `build_sceneir_handoff` copies that payload
   to `parameters`; native adoption retains it in `UnifiedTrack.parameters`.
3. `bie.compiler.animation_behavior.motion_contract` accepts only `easing` plus
   `direction` for reveal, or `peak_scale` for emphasis. Extra semantic/lineage
   fields are rejected with `AnimationCompilerError` /
   `ANIMATION_PARAMETER_UNCONSUMED`. Name registration is not parameter support.
4. Task035 cellular motion uses native attention-only accent/highlight with
   `scale_allowed=False`, identity/semantic value unchanged. The generic compiler
   emphasis implementation owns `scale`, requires peak scale above one and produces
   a scale pulse. Dropping the semantic fields and accepting this default would
   change the declared motion, not faithfully lower it.

These are downstream source-contract findings, NOT a Task035 planning regression
or a proven Scene IR codec defect. Loader/DSL admission can accept planning tracks
without proving the compiler motion contract. A successful loader call must not be
promoted to supported runtime motion or compiler/render readiness.

The Task036 request requires lossless motion semantics and fail-closed required
capabilities, prohibits invented fallbacks, and protects native compiler/Animation
engines. Before implementing a success path, external review must decide whether
an explicitly planning-only Scene IR may retain these unsupported downstream motion
obligations with a non-ready compiler capability result, or authorize a separate,
evidence-bound native contract amendment. No such decision has been inferred here.
No source fields were stripped, no default scaling/fallback was substituted, and
no capability registry was inflated to manufacture support.

## Evidence limits at this checkpoint

Local Windows native preservation checks: 29 hard adoption/codec/contract/orchestrator/
registry tests plus 5 native capability tests passed; zero failures/errors/skips.
These 34 existing tests are not authored Task036 tests or eleven-stage proof.
The original Task035 129 + 4,972 inventory and separate 12/20 safety suites remain
unchanged; they have not been re-executed as a Task036 candidate gate.

An external read-only synthetic-PDF probe checked the unchanged
Task035 persisted motion against the native consumer. It is an in-process forensic
probe, not a replacement Task036 child-process smoke or a new unit-test count.
Its first invocation had a diagnostic-helper field-name error (`KeyError`), not a
production exception. It grants no PASS; use the subsequent verified safe receipt
for observed native outcomes. Detailed source-derived data are not exported.

The corrected probe completed on Windows. Real generated native-PDF quantitative
and cellular journeys reached all ten existing Task035 stages successfully, then
`verified_animation` reopened their committed plans, supporting records and exact
handoffs. One quantitative reveal track and two cellular emphasis tracks were
projected losslessly to native UnifiedTrack and independently rejected by
`motion_contract` with `AnimationCompilerError / ANIMATION_PARAMETER_UNCONSUMED`.
Both cellular parameters retained `scale_allowed=false`. Actual canonical
`native_qa_capabilities` observations for chart/timeline/diagram were render=true,
reveal=false, emphasize=false under its declared web profile. This is bounded
Windows source-contract evidence, not Linux reproduction, rendered execution,
eleven-stage process success or a defect in Task035's upstream planning gate.
The external safe checkpoint retains artifact/handoff hashes and exception codes;
temporary synthetic run stores were closed and removed by the fixture cleanup.

No Task036 scene.ir, eleven-stage profile, workflow, implementation commit, push,
PR or merge exists at this design checkpoint. No Scene IR/code/render stage has
executed. All validated child/workflow/resource limits remain unchanged.
Windows non-green history and unproven 45-second timeout causes remain retained.
Audio reconciliation remains OPEN; AUDIO_REPLAN_REQUIRED stays fail-closed.
review_required=true / accepted=false are native document requirements; product
evidence also remains requires_review=true, release_ready=false, product_accepted=false.
No academic, live-model, learner, media, deployment or product acceptance is claimed.
