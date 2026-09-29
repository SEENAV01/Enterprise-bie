# AUDIO QA specification — Batch010

## Inputs and authority
AudioRequest references exact source/output/WAV/timing/caption/assessment artifact bytes. AudioPolicy is supplied independently by the operator and binds narration, language, voice, sample rate, approved timeline, visual cues, source claims, term occurrences and accepted phonetic forms. Changing any request or policy invalidates reviews. No signing keys are embedded in runtime code.

## Implemented tasks
AUDIO001: actual PCM16 inspection; rational sample time; timeline containment; cue alignment; complete word/text linkage; rate, overlap, silence/clipping guards. Acoustic alignment requires separately authenticated forced-alignment or human-alignment records; their quality is not self-proving.
AUDIO002: bounded plain SRT/WebVTT parsing; strict UTF-8; integer times; complete ordered caption-to-word text coverage; overlap, sync, exposure, line and rate checks. No rendered geometry or player proof.
AUDIO003: audio/transcript/language/voice-bound per-occurrence observations, allowed-form comparison, exact assessed occurrence windows and authenticated contextual review. Missing, uncertain or text-only evidence cannot pass.

## Supported limits
32 clips,64 caption tracks,16MiB per artifact,64MiB declared total; WAV duration<=600 seconds; PCM16 mono/stereo,8–192kHz; script<=32000 code points; no floating-point media boundary calculations. Plain subtitles use hours/minutes/seconds/milliseconds (hours00 or01), no styles/regions/settings/tags. Structural schemas are not substitutes for runtime validation.

## Trust and failures
Actual hashes identify bytes, not truth. Operator-owned immutable artifact roots remain a deployment requirement. Unknown or tampered media blocks. Unsupported format blocks in this lane. Missing contextual review requires review. Rejected review blocks. Shared-secret review verification authenticates an operator-provisioned identity, not independent empirical accuracy. Synthetic assessments cannot be used as production evidence.

## Reuse and integration
Imports existing source_v2/io/evaluator, reasoning_v2 review verifier, release_v2 policy/evaluator. Native receipt adapter maps only reviewed original fields and never changes engine events into measured phonetic boundaries. No native AUDIO/Section15/global registry edits. Current-HEAD compatibility and full-repo regression remain later integration gates.

## Acceptance scope
Local executable checks + tests are implemented. No live acoustic assessor, full media/game, real-book E2E or product acceptance. The full timing_audio_sync gate cannot PASS from this module; bridge results are unsigned FAIL/NOT_RUN.
