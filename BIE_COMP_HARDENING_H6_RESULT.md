# COMP Hardening H6 — state, event and narration consumers

## Result and scope

Checkpoint `BIE-COMP-H6-005`. Five audit-derived tasks from the existing H3-R02 consolidated backlog are implemented in the existing checked compilation/publication/render-revalidation path. This batch is NOT a new full section re-audit. COMP remains IN_PROGRESS, section exit is not permitted, product accepted=false, and no GitHub write or commit was performed.

| Task | Bounded implemented capability | Atomic tests |
|---|---|---:|
| H6-001 | Versioned state/event/narration contracts; source lineage; frame quantization; exact coverage | 23 |
| H6-002 | Random-access timeline state and visible text/visibility/opacity consumers | 18 |
| H6-003 | Actual local PCM16 WAV verification, private staging and render-time byte checks | 20 |
| H6-004 | Single-voice scheduled audio source, explicit trim/gain, synchronized captions | 22 |
| H6-005 | Existing checked compiler/CLI/source maps and frame-aware measurement integration | 16 |

The four primary producer/consumer modules and integration changes add real generated behavior rather than merely rejecting all state/event/audio requests. Unsupported instructions fail closed. A pure evaluator computes a requested frame from the declared initial state and preceding events; random-access and reverse-order rendering do not depend on previous side effects. Caption intervals and audio placement derive from the same frame plan. Actual audio source publication requires content-addressed local bytes and validates their PCM header/sample duration, not only user-supplied metadata.

## Executed verification

Restored H5 baseline: 1,652 tests passed in 227.323 seconds. Dedicated H6: 99 atomic + 10 integration = 109 tests passed. Cumulative development regression: **1,761 tests passed in 234.148 seconds**, zero failures/errors/skips. The fresh-extraction and restored-delta results are reported separately in the accompanying `BIE_COMP_HARDENING_H6_FINAL_VERIFICATION.json`; they must not be inferred just from these development results.

A real installed TypeScript 5.8.3 compiler also strictly compiled the standalone no-dependency generated frame runtime. That is NOT a full pinned React/Remotion project compile: the generated project still targets TypeScript 5.9.3 and Remotion 4.0.506.

The fixed source benchmark contains ten cases, compiled in three independent generator processes each: five expected source passes and five expected source rejections. All **30 executions** matched their predeclared outcomes and repeated manifest identities. One source-positive case is intentionally a later content-fit failure; source PASS does not certify layout.

## Browser, timing and asset evidence

Actual Chromium painted five synthetic scenes: **240 frames, 336 element-frame records, 15 selected screenshots**. Four positive content-fit cases passed; the fifth late-event overflow case was correctly rejected. Python and generated-JavaScript states agreed for every frame. The browser exercised safe literal multilingual text, out-of-order event evaluation, explicit hidden state, caption gaps and shifted/trimmed cue timing.

The diagnostic bridge is an explicitly labelled **React/Remotion API test double**, including a non-playing Audio marker. It observed **71 audio-component-frame records**, not 71 audio playback events. No sound was played or decoded by Remotion in this evidence. The supplied PCM is a generated 440 Hz technical signal, not narrated speech. Byte integrity, format/duration and timing checks do not establish that audio speaks the transcript, is pedagogically correct or is pleasant to hear.

Selected final-frame positive and middle-frame negative screenshots were visually inspected. The negative visibly overflows, as its diagnostic reports. It remains a detected defect/input needing more layout space, not an automatic repair success.

## Corrections during implementation

A canonical optional self-fingerprint caused raw/canonical runtime-plan disagreement; the derived fingerprint was removed from plan input identity and covered by a roundtrip test. Strict standalone TypeScript exposed extra provenance fields in generated event/binding/cue objects; the actual types were corrected rather than weakening strict compilation. Earlier failed development logs are included where retained. The first source-benchmark attempt was interrupted by an outer tool timeout and is explicitly marked incomplete; a new full run produced the reported 30 outcomes.

## Real execution boundary

A combined technical state/narration project passed checked source publication, including actual verified PCM assets. The real validation harness then returned exit code 2: **FULL_TYPECHECK_BLOCKED: BLOCKED_DEPENDENCIES**. Full target dependency types, actual composition discovery and smoke/full rendering were not run. A separate npm probe returned **EAI_AGAIN** for the registry. No network install, version downgrade or simulated success was substituted. Real-book, spoken narration/learning quality, game runtime and enterprise acceptance are open.

## Preservation and packaging

All 4,965 H5 parent members remain accounted for. Of 377 inherited active Python files under app/tests/scripts, **372 remain byte-identical and five are deliberately modified**. One inherited JavaScript measurement-support file is also deliberately changed. Current metadata is updated, and changed originals are preserved in lineage; inherited fixture/golden bytes are not rewritten. Full member verification is supplied separately.

The separate integrated ZIP is the full current DSL + COMP workspace; it is not the entire canonical BIE repository. The Master contains that exact ZIP, five task deltas, current evidence, reports and checksums. Previous Masters are NOT recursively embedded. Required inherited validation fixtures remain in integrated source; the new bulk browser/generated-project evidence is separate. Font files and installed dependencies are not distributed.

Atomic packages are ordered source deltas, not standalone applications. **Restore all five before running task suites**, because individual suites exercise producer/consumer integration that lands in H6-005. Each package declares this dependency. The complete restored workspace can be compared byte-for-byte to integrated source; no claim is made that a half-restored batch is independently runnable or accepted.

## Existing gaps retained open

R01: trusted actual-render measurement provenance, full-ink/contrast/readability and learning-preserving dynamic repair remain open. Combining H6 audio assets with the H4 static repair branch is explicitly blocked until joint support exists; a late state can overflow and requires diagnostic/upstream correction.

R02: broader state expressions/ownership interactions, interactive or game event consumers, compressed media/audio mixing, broader specialized morphs and instructional reduced-motion equivalence remain open. This batch implements a bounded single-voice PCM timeline consumer, not all audio or lesson-generation capabilities.

R03: operational OS/network isolation and full toolchain controls remain open. Resource/file checks are not a complete hostile-code sandbox. R04 remains environment-blocked for pinned compile/actual Remotion. R05 remains downstream real-book/learning/game acceptance.

Next work must derive concrete tasks from the same consolidated ledger. No automatic section exit or newly restarted full audit.
