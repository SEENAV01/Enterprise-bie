# Section 17 — H2 capability audit and re-audit

## Verified scope
Ten justified additive tasks address H1 long-form audiovisual and render-schema gaps. The original50 roster was not extended or reinterpreted. All prior1,320 test IDs/code/tests/tools remain;1,493 total methods pass. This is a local targeted implementation audit, not independent exhaustive security/scientific review or native acceptance.

## Concrete evidence
A120-second1280×720,24fps synthetic H.264/MKV test was fully decoded:2,880 RGB frames,7,962,624,000 uncompressed RGB bytes, and1,920,000 samples per channel at16kHz stereo. No rescale/frame sampling or early frame truncation was used. The diagnostic producer's observed max RSS was105,348KiB, while processing a larger sequential stream; this is a measurement, not an OS memory-limit guarantee. Decoder processes have separate observed resource use.

Seventeen persisted scenarios matched expectations:5 DIAGNOSTIC_PASS,7 FAIL,5 BLOCKED. Actual missing/silent/clipped audio, black frames, timestamp gaps, truncated/corrupt input, wrong caption text, missing captions, bad source hash and decode quotas were exercised. A separate locally generated eSpeak recording was decoded and caption-timed; no ASR or claim of semantic speech understanding is made.

The exact canonical RenderReceipt contract at `a68e054025b8fe7756a71e998d9e9103dad8e0f4` was retrieved read-only and the8,077-byte snapshot matches Git blob `060ed3584703ec9d7d24aca57bbba670d94b78d9`. Tests compare its AST fields with the adapter. Authored declarations plus actual MP4 facts map successfully but remain explicitly NOT authenticated native execution.

## Red-to-green findings
1. **H2-AUDIT-001:** an unexpected execution exception escaped; now admitted failures become redacted BLOCKED receipts, while process termination signals are not swallowed.
2. **H2-AUDIT-002:** an MKV could be declared with an MP4 filename; actual demuxed container type is now recorded and required by the native MP4 profile.
3. **H2-AUDIT-003:** zero/invalid low-level video/PCM constructor dimensions could create a zero-stride loop; typed positive dimensions, channels, rates, windows and hard resource ceilings now reject these inputs before decoding.
4. **H2-AUDIT-004:** low-level line/IO quotas and timeline-kind admission were incomplete; those boundaries are now typed and checked before process/frame work.
5. **H2-AUDIT-005:** a version string was weaker than binary custody; ffmpeg and ffprobe binary SHA256/size/path are captured before and rechecked after the run. This does not pin dynamic libraries or authorize a deployment.

Initial163-test run:161pass,1failure,1error. After the first repairs:163pass. Expanded173-test re-audit:165pass,7failed methods,1error. After repairs:173pass. All failed logs and exact preimages remain. Additional integrity checks bind reused storage/model helpers and reject rehashed native/speech acceptance flags. No old test was removed, skipped or weakened.

Ten isolated code mutations were detected by selected tests; all restored controls passed. This is targeted sensitivity evidence, not an exhaustive mutation score or independent oracle.

## Remaining implementation versus validation

### H2-RES-001 — IMPLEMENTATION_AND_INTEGRATION_OPEN
Adopt AV v2 under governed legacy metric/rater/release consumers and canonical native producer APIs; test full checkout and Section16 dependencies. No automatic replacement of metrics012/013/015 was made.

### H2-RES-002 — IMPLEMENTATION_AND_NATIVE_VALIDATION_OPEN
Authenticated native worker evidence, real source/recipe/manifests/artifact custody, SceneIR/audio/game adapters and actual book-to-Remotion compile/render. JSON declaration matching cannot establish execution truth.

### H2-RES-003 — QUALITY_IMPLEMENTATION_AND_VALIDATION_OPEN
Semantic narration/word alignment/pronunciation, readable science/math diagrams, cinematic/director quality, rich captions, accessibility/player behavior, multistream/HDR/VFR profiles as justified. Current signal checks are bounded and not full narration/visual QA.

### H2-RES-004 — IMPLEMENTATION_AND_EXTERNAL_VALIDATION_OPEN
Operator-selected supervised live evaluator, protected credentials, real independent reviewer assignment and review, golden corpus rights/provenance, held-out calibration, consented learning studies. No live calls/reviews/learners here.

### H2-RES-005 — IMPLEMENTATION_OPEN
Actual game/browser/player evidence and lineage; corpus-scale indexed anti-leakage beyond the inherited pairwise cap.

### H2-RES-006 — DEPLOYMENT_AND_ENVIRONMENT_VALIDATION_OPEN
OS CPU/RSS/network/descendant isolation, protected signing/database/off-host anchoring, actual supported Python/platform/codec matrix, per-campaign toolchain/OS/library policy. POSIX process groups and content hashes do not supply these controls.

## Limits and non-claims
Declared ceilings are2hours,4K default dimensions,64GiB decoded-byte budget and900-second decoder deadline, with individually validated configurable resource bounds. These ceilings are NOT a promise that every resolution×fps×duration combination fits all budgets; exceeded budgets block. Actual long-file evidence here is120seconds/720p/24fps, not a2-hour or4K lesson run. Activity/silence/clip thresholds are authored examples and require independent calibration for real lessons. Plain caption timing is not screen-reader/browser conformance.

Legacy collectors and release routes remain preserved. The v2 operator pipeline is runnable, but adoption into legacy/native consumers is an explicit remaining implementation item, not hidden as merely an approval step. No GitHub writes, native BIE/Remotion execution, live model calls, human reviewers, real books or learners were used. Task028 remains paused and Section18 is not started.
