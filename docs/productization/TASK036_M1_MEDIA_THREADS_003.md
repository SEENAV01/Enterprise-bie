# M1 explicit governed media-thread policy

Status: IMPLEMENTED CANDIDATE; hosted after proof and independent review pending.
This is a rendering-call allocation repair, not diagnostic-only work and not
ordinary Task036 producer implementation. Original M1 and observation amendments
remain sealed; their historical pause/review fields are not rewritten.

## Evidence and bounded hypothesis

Parent source is `7c9bafce7cc025f7e134ec6fb46a66197686ec5e`, tree
`01eb1a9e52a41f1fd1488e06f056a0aab437d396`. Hosted run38049163555 attempt1
completed FAILURE: three mandatory non-render jobs and seven renders succeeded;
cellular/reduced job114208618210 failed. Artifact11669337466 SHA256
`fc08b7645e070277cfb7013382811f945ae9acc127b9fb214464d65954c9e8ef`
is independently ZIP/CRC verified. The actual owned invocation reached the
RENDER_MEDIA boundary after48 still-frame schedules and96 emitted comparisons.
It recorded kernel task-ceiling enforcement: pids.max128, max_events1, peak128.
The anonymous child-event sequence was exit0 then245, without executable identity.
The worker returned FAILED/exit2/duration112482ms; memory events were zero and
cleanup flags true. Raw PROCESS remained TOO_LARGE and RESOURCE remained INVALID.

The independent reviewer returned REVIEW_INCOMPLETE with mandatory render finding
open, record SHA256
`e7616347ca5ea0220ed097d7e230e54c082bc58ab1663e07cc0db01b57a734d3`.
This supports a targeted hypothesis that automatic media subprocess thread pools
conflict with the fixed128-task ceiling; it does not identify FFmpeg from an
anonymous exit, establish the sole causal chain, or explain historical failures.

Pinned Remotion4.0.506 public `prespawn-ffmpeg.ts` and
`stitch-frames-to-video.ts` dispatch ffmpegOverride with pre-stitcher/stitcher
argument arrays. The native source omits explicit codec/filter thread allocation.
FFmpeg's documented filter_threads/filter_complex_threads bound filter pools;
codec threads is applied before the corresponding input/output. No upgrade,
dependency, CPU/memory/PID/output/deadline increase is used here.

## Selection and execution contract

`real_paint._governed_media_thread_policy` invokes current native M1 document
admission: exact profile, tracks, catalog, target, source-bound parameters and
live scoped authorization. A schema string or caller safety flag is not enough.
Unversioned documents retain the actual old renderMedia call and result shape.
The new fixed policy is `bie.comp-m1.media-threads/1`, producer-motion-v1,
Remotion4.0.506; decoder/encoder/filter allocations are each1. Both standard and
reduced M1 paths use this same resource allocation, without changing their motion.

One trusted CJS helper returns new argv arrays from the pinned callbacks. It adds
only global filter_threads1/filter_complex_threads1, decoder threads1 before the
sole input, and encoder threads1 before the output. Every original token and
ordering is preserved; codec, CRF/preset/pixel format, frame rate/count, dimensions,
content and narration/timing remain untouched. Exact MP4 bytes across thread
policies are not promised; decoded semantic/frame conservation remains mandatory.

The pinned pre-stitch callback passes its24 FPS token as a number despite its
TypeScript string-array assertion. The helper preserves that exact token/type,
admitting only finite24 after the native -r option, not generic numeric coercion.
Supported scope is the current single-input, video-only libx264 pre-stitch and
libx264/copy stitch contract. Multiple inputs, another codec/callback, malformed or
already-thread-configured argv, duplicate callback invocation and unknown policy
fail closed. Future Audio/multi-input support is not inferred. The helper never
spawns, logs, serializes or retains commands, private output or paths. Completion
requires the final stitcher exactly once and records native optional pre-stitching
as actually executed zero or one times. Remotion's pinned memory decision can
legitimately omit pre-stitching; every observed callback receives the same bounds,
and repeats reject. The painter checks the closed shape and exact integer types
(not boolean/float equality), original admission and actual counts. It verifies the exact
helper hash and completed closed scalar execution record before minting a witness.
No synthetic fallback or PASS receipt is used to replace actual render execution.

## Preservation and tests

The new sealed thread amendment authenticates exact7c9 native controller/painter
and media/motion audit-resolver preimages, active replacements and one singleton
helper addition. The motion resolver's original compiler inventory is preserved;
the singleton extension is accepted only after the exact latest chain validates.
Rollback, missing chain, modified original documents, extra paths, recomputed
replacement hashes and helper tampering remain rejected. Historical ledgers,
archives, original b454/1526/7a624 documents and original native M1 source bytes
remain unchanged. Existing assertions are retained; only fixture completeness is
extended so old preservation tests exercise the full active chain.

New controls distinguish actual Task035 source-bound admission, Node-only policy
and controller doubles, exact amendment checks, and mandatory native Linux render
proof. No double produces render acceptance. The complete original286 NEW cases,
Task035129/4972, native-extra2435/214 files and safety12/20 remain mandatory;
new methods are separately counted and assigned once, not duplicated in extras.

The unchanged actual matrix must execute all eight cases, all48 decoded frames,
witness/fit/paint/raster and conservation. Current before failure is valid evidence;
only a fresh changed-source result can establish after behavior. Historic painter
causes and Windows limits remain UNKNOWN where previously unproven. A single green
matrix is bounded technical evidence, not production reliability/determinism.

Product child45s, owner600s, 48-frame worker192s, shot30s, render job20min,
raw-reader262144 bytes, memory2GiB/swap0/PIDs128, isolation and all fixtures are
unchanged. No global Scene IR/code/compile/render execution or acceptance is
claimed. Ordinary Task036 stays paused until complete technical proof and actual
independent review. Audio remains OPEN/AUDIO_REPLAN_REQUIRED fail-closed.

## Available local validation (Windows; not native render proof)

Frozen amendment SHA256:
`6b08edb6b6bbacba67c1c87780809a449a8073dbf882cf5e35a247a81ddc940c`.
Final policy/controller/amendment, existing media privacy, runner and original
motion-preservation selection:128 tests PASS, zero failures/errors/skips.
Existing capture selection:37 executed,36 PASS and one ERROR at unchanged
`CaptureSafeReader.test_source_link_is_not_retained`, Windows privilege1314.
No skip, assertion change or permission bypass was added. Six source-admission
controls also passed using actual existing Task035 synthetic-PDF artifacts; those
ran before the last completion-counter refinement, which did not change admission.
The first positive controller-double failure was a newly authored malformed
seven-token argument fixture, corrected to the supported metadata-bearing shape;
it was not native rendering evidence. Filesystem-sandbox Node EPERM observations
are separate from the unrestricted scoped outcomes above.

Exact final collection/source check selects333 NEW identities:all286 retained
and47 separately authored here. The inherited native214 files/2435 identities
and safety12+20 are unchanged, with no cross-lane duplicate. Every original test
method AST/assertion and runner algorithm remains unchanged. Test-only fixture
setup adds the exact current amendment chain; the historical documents themselves
are not rewritten. Hosted execution of the complete333 lane and all mandatory
native/render/preservation gates is required; local collection is not execution.
