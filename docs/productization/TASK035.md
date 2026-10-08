# BIE-PROD-035 — governed current Visual to Animation planning

## Forensic design before implementation

The authorized base is `46977a2fb1d43fb655fb4be01d93a34f6151af09`,
tree `dc04cb0bb77a5d40e2ea05acd18c513e2be09d62`. Task034 is
canonical-complete. The Task035 profile adds only ANIMATION to its nine-stage
scope; historical profiles retain 3, 5, 6, 7, 8 and 9 stages.

The existing global graph already admits `visual.plan` and `director.plan`,
then emits `animation.plan`. No graph migration is needed. Task034 private
`visual.handoff`, current inputs, validation and stage records are supporting
evidence from that exact verified Visual stage, not alternative global inputs.

Native Animation source review found composable contracts for all nine internal
stages: VIS_ADOPT, SEM, ATTN, DOMAIN, EASE, TIMELINE, CONTINUITY, QA, HANDOFF.
The historical `ani_actual_e2e` helper defaults absent actions to reveal and
joins primitives/timing positionally. It is excluded from production composition.

### Two levels of target identity

Current Director Visual sync identifies an aggregate `visual-target-*`, while
the exact Task034 handoff identifies grammar primitives with
`<visual-intent-id>:<element-id>`. Native Director animation synchronization
requires the original aggregate target. It must not receive a relabelled child
target or a substituted Visual sync candidate.

Task035 therefore synchronizes a grounded aggregate AnimationIntent against
the retained native Director Visual sync, then realizes only its verified child
primitives. Every child is joined to `TimingBinding.visual_id` by exact identity;
duplicates, missing bindings and foreign elements fail closed. Each resulting
track retains its aggregate intent and sync provenance and must fit both its
exact primitive timing interval and the current aggregate narration interval.
This is explicit parent/child realization, not positional timing association.

### Bounded semantics

Source-declared categorical data supports descriptive introduction of the
declared series; chronology supports native chronology-ordered reveal, retaining
uncertainty; flat cellular structure supports native attention/emphasis on
the declared structure. Static cellular input does not establish transport,
process transitions, concentration or molecular flow. Native general selection
may be registered for that restricted domain capability; it is not evidence
of a biological motion model. No decorative motion or default-reveal fallback
is permitted. Unsupported purposes/actions remain blocked or abstain.

This first slice admits one current Director scene. Native Director cue times
are scene-local, while one AnimationPlan has one scene interval. Multiple scenes
fail closed with `animation_multiscene_timing_contract_required`; Task035 does
not fabricate offsets, superpose unrelated scene timelines, or claim course-wide
animation assembly. Static chart frames and timeline axes have explicit motion
abstentions while their source-declared semantic targets receive native actions.

Generic Director/Animation action intersection is enter, exit, reveal, emphasize,
trace, path_follow, transform and simulation_state. Equation morphing and
simulation require their specialized authoritative upstream contracts. Existing
`math_evidence_required` and `director_math_teaching_contract_required` remain
unchanged. No Math or simulation states are invented by Animation.

### Native composition and extra admission checks

Native semantic intent preserves uncertainty (the current `.5` source policy
returns REVIEW). Review is retained and never promoted to acceptance. Native
duration runs with `allow_scene_extension=False`; focal windows cannot extend
Director timing. Timeline, attention, continuity, purpose/synchronization,
temporal/motion, accessibility, performance and trace checks execute before
publication. SIMPLIFY/SPLIT_SCENE does not authorize discarding required tracks.

`AnimationPlan` recomputes its fingerprint and does not itself reject an
accepted constructor value; Task035 must separately reject accepted output and
compare the raw stored fingerprint to a fresh native computation. Native
orchestration stops only on BLOCKED, so the adapter must verify the complete
nine-stage prefix. Native Visual adoption does not validate every uniqueness
or fingerprint field, so Task034 `verified_visual` and explicit identity checks
remain authoritative. Native synchronization QA's overlap-based cue selection
is additional QA, not the authoritative primitive/timing join.

Task035 additionally verifies persisted global input order and every supporting
Visual/Animation parent edge. Correct CAS bytes alone cannot excuse edited
artifact-catalog ancestry. Readback independently rederives the current inputs,
native plans, handoff and receipts; stale revisions or changed intent fail closed.

Native `build_sceneir_handoff` and `require_sceneir_ready` can prove internal
handoff readiness (handoff schema `0.1.0`) without invoking the Scene IR adopter
or publishing `scene.ir`. The public stage output remains the native
`AnimationPlan`, schema `1.0.0`, as `animation.plan`.

## Acceptance and preservation boundary

The existing CAS, pipeline persistence, queue, orchestrator, idempotency and
fencing remain the global authorities. Section18 delegates a new versioned
profile. No native Animation, Visual, Director, Scene IR, compiler, Android,
Task028, Audio, historical pin or atomic-ID change is authorized here.

Output remains requires_review=true, accepted=false, release_ready=false,
product_accepted=false. `AUDIO_REPLAN_REQUIRED` blocks planning and is never
cleared. Audio is incomplete and graph reconciliation remains open. Timing is
current narration planning evidence, not final recorded audio. SCENE_IR and all
later global stages remain NOT_RUN. No academic, learner, rendered-media or
product acceptance follows from synthetic technical tests.

## Validation evidence

Initial local real-source service checks reached Animation for chart and
chronology. These exploratory checks are not added again to final unique test
counts. The final authored Windows lane passed 129/129: 109 producer controls
and 20 recovery controls, with zero failures, errors or skips. Its real-source
service tests cover quantitative, uncertain chronology and static cellular
planning; these are distinct from bounded child-process closure below.

The final selection contains 129 authored and 4,972 affected tests, qualified
by selected module and callable identity. Four legacy Reasoning bridge display
IDs collide, but wrap different source functions and assertions; removing them
by display ID would discard distinct controls. Exploratory reruns are not added
to the selected total of 5,101.

The completed local affected lane ran 4,950 tests with 144 failures, 81 errors
and zero skips. Adding the disjoint 22-test Post-DIR run below yields 4,972
affected tests, 144 failures, 84 errors and zero skips. Together with the green
129-test authored lane, 5,101 selected candidate tests executed; this is not a
5,101-pass claim. All 481 native Animation tests and all five selected Scene-IR
admission tests passed. Windows full-green is not claimed. Full hosted Linux
preservation and bounded-process evidence remain required.

The initial Windows bounded child-process smoke retained the unchanged
45-second budget. Quantitative stopped at 45.046 s, chronology at 45.058 s and
cellular at 45.045 s with `child_supervision_incomplete`; no successful Animation
output or second-process positive-path closure is claimed from those runs.
The unsupported-Math child control passed in 10.357 s, including second-process
restart, exact identities and no downstream execution. No budget was widened.
Hosted Linux multi-domain positive-process closure remains required.

A final-code smoke after the broad candidate lane finished also retained the
45-second limit. Quantitative stopped at 45.049 s with Visual RUNNING;
chronology at 45.079 s with Visual SUCCEEDED but its delivery not ACKed;
cellular at 45.052 s with Animation RUNNING and nine predecessors ACKed.
All three reported `child_supervision_incomplete` without safe stage diagnostics
or child output. Their causes remain unproven, and none establishes a successful
bounded Animation process or positive second-process restart. The final-code
unsupported-Math control passed in 8.140 s with a genuine second-process reopen,
exact identities, idempotent replay and correct terminal queue states. No
supervision limit or production logic was altered to obtain a local smoke pass.

The required integrated local gate stopped at four historical long-path
preservation mismatches. At path lengths 260/266/265/266, ordinary Windows
`Path.is_file()` failed; extended-length reads proved each candidate byte hash
equals its historical inventory and canonical Git blob. Canonical checkout
bytes differed only by CRLF for those four, with normalized identities equal.
The unchanged-base aggregate audit reported 10,596 mismatches, not the candidate's
four; identical aggregate reproduction and a universal cause are not claimed.
Neither historical bytes nor the audit policy were changed.

The separately selected Post-DIR preservation suite ran 22 tests: 19 passed,
0 failures, 3 errors, 0 skips. The three compiler-import errors all reported
the Windows-unavailable `fcntl` module and reproduced individually on unchanged
canonical main. These are preserved platform limitations, not waived tests.
The selection is included in the hosted affected lane; full governed PR Linux
gates still remain required. Windows full-green is not claimed.

Three additional unchanged-base module reproductions selected 97 tests:
Reasoning temporal migration (3 tests, 1 failure), Math derivation evaluation
(51 tests, 8 failures), and Math I/O/bridge (43 tests, 1 failure, 7 errors).
The candidate reported the same failed-method identities and counts for these
modules. Recorded baseline diagnostics include unsupported secure artifact I/O,
missing verified Math artifacts and Windows symlink privilege error 1314.
These 97 baseline executions are corroborating evidence, not additional unique
candidate tests. They do not establish a universal cause for other failures or
waive any preservation gate.

All six Animation QA modules were independently rerun on unchanged canonical
main: 206 tests, 39 failures, 12 errors, zero skips. Every module's counts and
exact failed/errored method set matched the candidate. Safe baseline diagnostics
were retained separately; these baseline reruns are not added to the candidate
test count. This corroborates those specific failures without declaring every
Windows issue identical or waiving hosted Linux validation.
