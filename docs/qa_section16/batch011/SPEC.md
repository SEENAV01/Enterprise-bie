# Batch011 specification — VIDEO001..007

## Scope and acceptance boundary
Original registry page18, lines834–840: compile evidence; render evidence; frame
sampling; blank-frame detection; overflow/crop detection; visual continuity; render
duration. Seven bounded local implementations, not seven production certificates.
No Section15 edits, GitHub writes or Codex/Android/global continuation changes.

## Contracts and verified behavior
VideoRequest binds run/revision/composition/candidate identities and actual video,
compile/render receipt, source/lock/assets inventory and compiled output references.
VideoPolicy is operator-owned: expected input digest, dimensions, exact rational
frame clock, frame count, required audio, tool/codec profiles, sampling schedule,
scene boundaries, permitted cuts/blanks, expected movement and complete-content
PNG reference regions. Candidate content does not choose these expectations.

Compile/render ExecutionReceipts bind inspected inputs/outputs, logs, parent compile
receipt, environment/tool identity, process result and full/smoke scope. Candidate
command arrays are never executed by the evaluator. Empty stdout/stderr are losslessly
stored in hashed base64 wrappers because the inherited ArtifactRef requires nonempty
artifact files. Reported/native flags and exit0 are not self-authenticating; current
purpose-scoped ReviewVerifier records are independently required. Authentication
establishes configured identity, not real-world independence or correctness. Diagnostic
receipts stay review-required. A negative review cannot be outvoted.

Actual bytes are read through the inherited one-descriptor SnapshotStore, checking
hash/length, regular files, links, read changes and confined paths. The decoder uses
operator-installed FFmpeg/ffprobe, fixed argv, a copied immutable local MP4 snapshot,
restricted MOV-family demuxing/protocols, disabled data references, no autorotation,
process-group termination, output/time budgets and exact raw-RGB frame counts.
No caller-supplied probe output, frame count or successful render flag replaces decode.
Tools are not a hostile-media sandbox; production isolation remains a hardening gap.

Probe/decoded presentation counts, timestamps, packet durations and exact rational
rates are compared to policy, including start offset, gaps, nonmonotonic timestamps,
missing frames, extra frames and duration. Non-square/interlaced/transformed profiles
are rejected. Bounded CFR is supported; general VFR/audio-clock proofs are not claimed.

Sampling always includes first/last, interval samples, scene/cut neighbors, window
edges and every required reference frame. Budget exhaustion or absent frames blocks;
required samples are not silently omitted. Blank and adjacent-frame continuity checks
run over ALL decoded RGB frames, not only the exported sample set. Blank detection
uses near-black fraction and per-channel uniformity. Continuity checks pixel difference,
approved cuts and unchanged runs within explicitly required-motion intervals.
The metrics are operator diagnostics, not aesthetic/scientific safety certificates.

Crop/overflow checks compare exact required screen bounds and independent complete
RGB PNG region templates against decoded pixels. Missing template evidence requires
review; changes in cropped/omitted/painted regions block. These checks do not discover
all undeclared objects, parse text/OCR, prove geometry beyond samples or understand3D
occlusion. Policy/template coverage requires separate authorized scope review.

## Integration
Existing ArtifactRef, ReleaseCandidate, GateEvidence, SnapshotStore, Finding, Report,
Review/ReviewVerifier and complete ReleaseEvaluator are reused, not overwritten.
`adapters.from_native_render` reads the pinned COMP RenderReceipt field set and binds
actual artifact identity, preserving full/smoke and unverified execution distinctions.
Representative adapter mappings are tested; no native COMP module is vendored or run.
`prepare_release_evidence` recomputes results, checks candidate refs including nested
logs/templates and emits unsigned code_compile/video_render/rendered_frame_inspection
reports: FAIL for blocked candidates, otherwise NOT_RUN. It never certifies native
pipeline or complete-media quality. All report bytes are content-hashed.

## Verification and artifacts
159 new unique unittest cases,58 subcases within those cases;1857 inherited cases
in eleven additional isolated suites. Seventeen targeted mutation probes run on a
PRIVATE copied workspace, restore mutated sources there, and test controls separately.
Actual authored TypeScript->JS RGB generator->FFmpeg MP4 diagnostics test healthy,
blank, crop, freeze, unexpected cut, wrong fps, short/corrupt media, compile failure,
missing required audio and smoke-only receipt. Their11 expected outcomes and specific
failure reasons are checked. The compile-error fixture deliberately continues to render
only to test rejection; production orchestration must stop on the failed compile.
Diagnostic clock1800000000 is synthetic; wall-clock execution is separately recorded.
This is not a native BIE Scene IR/Remotion output, book extraction, game or learning study.

Four JSON schemas are STRUCTURAL; runtime validators enforce cross-field bounds/trust.
CLI and sample exporter do not overwrite existing destinations. Prescribed sample PNGs
come from actual decoded MP4 bytes and carry frame/PTS/video/policy/tool fingerprints.

## Limits that must remain open
16MiB per artifact/64MiB total inherited byte-I/O; default64MiB raw decode maximum,
operator-set maximum256MiB. Long/high-resolution media beyond budget fails closed.
Governed streaming/chunk coverage and hostile-input isolation are not implemented.
No full repository regression, canonical caller migration, live independent assessment,
final A/V synchronization, arbitrary crop-semantic proof, real-book E2E or acceptance.

## Technical references consulted (not claims of native execution)
- FFmpeg ffprobe documentation: https://ffmpeg.org/ffprobe.html
- FFmpeg CLI: https://ffmpeg.org/ffmpeg.html
- FFmpeg protocol options: https://ffmpeg.org/ffmpeg-protocols.html
- SEENAV01/Enterprise-bie at375d99af0edd0086206817dae932156ddf61c569,
  bie/compiler/render_contracts.py, Git blob060ed3584703ec9d7d24aca57bbba670d94b78d9.
Native contract was inspected through the GitHub connector; native code was not
copied, executed or claimed byte-verified against a new local dependency.
