# AUDIO Batch 003 — SYNC-001..005 contracts

## Source authority and scope

Original Section 14 titles come from the preserved ORIGINAL_REGISTRY.json. Continue VO-010; no COMP restart, no architecture reset, no GitHub write. Both Batch001 profiles and all Batch002 sources/tests remain unchanged. Five pinned canonical DIR files remain an exact dependency fixture, not a replacement production package. This batch is not the section-wide audit.

## SYNC-001: actual word-timing producer

SpeechAsset bytes, request, voice/catalog/runtime, source-span mappings and explicit pause must validate before alignment. The installed native eSpeak library runs in a fresh bounded child process. Public callback timestamps are integer milliseconds converted half-up to sample coordinates; internal ABI sample fields are not treated as a public guarantee. Exact replay PCM must match the generated/cached speech prefix byte-for-byte before its events are attached. Every prepared lexical unit must have an ordered nonzero interval and correct source/rule references.

The legacy WORD offset route is implemented and fails closed on malformed/missing source coverage. Actual experiments reproduced invalid source offsets and missing boundary MARKs for some legacy-engine multi-sentence input. TimedEspeakProvider is an additive backend with a different provider, voice/model, runtime and cache identity. It emits source-owned MARK pairs and resets native synthesis at source sentence boundaries, preserving each clause's actual PCM and spacing. It does NOT attach modified-markup timings to old VO-009 audio. These technical sentence resets/marks may change prosody; no production/cinematic equivalence is asserted.

Public MARK positions denote engine source boundaries. They are NOT independently measured phonetic word endings, forced alignment or proof of correct pronunciation. External reported intervals remain REPORTED_UNVERIFIED; tests using proportional sine-wave intervals are explicitly SYNTHETIC_TEST_DOUBLE and cannot pass the normal measured-only pipeline. Pipeline-owned native producer validation is the trust boundary; a supplied arbitrary JSON or basis string is not a cryptographic attestation.

The timing replay makes native synthesis calls even on a VO-cache hit. TTS generation calls, native calls including replay, and timing replay calls are reported separately. No false zero-compute cache claim.

## SYNC-002: caption alignment

Source/display and prepared/spoken channels remain separate. Exact raw caption text concatenates to its chosen source; only layout whitespace is normalized in separate lines. Multiple spoken words belonging to one original formula/term remain a single display atom. Every word is covered exactly once. Declared line, duration, gap and reading-rate bounds are technical policy, not accessibility certification. Indivisible over-limit text causes an explicit upstream resegmentation/extension failure; never delete text, shrink it silently, invent time or compress audio.

WebVTT and SRT are UTF-8, escaped literal payloads, ordered positive time intervals. One shared sample rate is required. Shared endpoints use identical half-up millisecond rounding; collision/zero-duration export blocks. Native Chromium WebVTT parsing is separately exercised. General captions QA remains QA-005.

## SYNC-003: measured scene clock

Scene order comes from the prepared narration, never lexical sort. Actual PCM sample lengths plus declared pauses determine positions. Only identical verified PCM16 formats concatenate; no implicit resample, mix, speech-rate change or truncation. Samples are authoritative. Rational frame boundaries use exact ceiling arithmetic on a shared clock (including 30000/1001); frame tail padding is explicit quantization, less than one frame. Budget violations request scene extension or an explicit upstream hold. Noncontiguous scene reuse, missing segments, changed audio/plan or inconsistent formats block. Current job cap is 30 minutes / 64 MB; larger lessons must be split into complete jobs.

## SYNC-004: animation anchors

An explicit source-plan-bound specification names target/action, start/end narration segments and word identities, source/reasoning references, minimum frame count, offsets, dependencies and a pause policy. The adopted adapter binds them to measured sample/frame intervals. No word positions are guessed. Missing/changed words, stale fingerprints, inverted/out-of-scene intervals, undersampling, dependency order and simultaneous same-action writers block. Different actions' semantic/property compatibility remains upstream ANI/COMP responsibility.

Pure forward/reverse frame seeking yields the same state. Crossing pedagogical pauses requires explicit forbid/hold/continue. Hold removes only declared pause samples from motion progress; provided sample keyframes preserve a flat interval. This is actual deterministic timing realization and a tested native-media monitor, not a Remotion video or automatic invention of teaching animation.

## SYNC-005: pauses

Additional requested pause frames use the same half-up sample conversion as VO-009. Their samples must all be zero, exact in length and bound to the original pause references. Native engine spacing is retained separately, not counted as teacher-requested silence. Captions must not bleed into the declared pause; scene/animation offsets include it exactly once. Current supported insertion is after each prepared segment, not arbitrary intraword splicing. Preserve content; resegment upstream for other boundaries. Silence trimming in MIX must honor this provenance and cannot erase teaching pauses.

## Existing DIR handoff

The real unchanged ReportedAlignment/align_reported_speech interfaces accept an exact whole unchanged utterance with matching lexical tokens. This route deliberately retains DIR's reported-alignment review/audio_verified=False. Chunked/expanded text cannot be mislabelled as the original transcript; the richer AUDIO source map remains authoritative and further deployment wiring is a section-audit item.

## Runtime controls and limits

Native workers are bounded child processes with sanitized environment, no shell, process-group cancellation, deadlines, byte limits and resource limits. They are NOT claimed as a full operating-system/network sandbox. No external speech provider, API key, remote upload or GitHub mutation occurred. Native binaries/voices/fonts remain installed dependencies; none are redistributed.

## Verification boundary

Inherited test APIs and assertions are not changed. Unit fixtures are labelled test doubles; actual synthesis, exact waveform replay, independent processes, cache behavior, native audio playback, actual WebVTT parsing, every-frame forward/reverse monitor states and exact source-byte preservation are separate evidence. No human listening, acoustic alignment calibration, cinematic neural narration, actual compiled Remotion video, real-book E2E or product acceptance is established.
