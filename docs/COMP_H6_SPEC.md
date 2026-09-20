# COMP H6 — existing R02 state/event/narration consumer backlog

This is an implementation batch in COMP_AUDIT_009_H1_H2_H3_CONTINUED, not a new full audit.
Parent: H5-005. Five audit-derived contracts (not new original-registry task numbers):

* BIE-COMP-H6-001: versioned `metadata.compiler_h6`, typed initial states, exact consumer/event/narration coverage, source references and deterministic frame quantization.
* BIE-COMP-H6-002: pure random-access state/event evaluation and visible text/opacity/visibility consumer; strict types, no scripts/handlers; preserve layout and literal multilingual strings.
* BIE-COMP-H6-003: actual PCM16 WAV bytes read under an explicit asset root, hash/size/header/duration verification, staging and render-time revalidation.
* BIE-COMP-H6-004: source-bound narration with scheduled Audio inside Sequence, matching captions on the same half-open frame interval, no silent time stretching or overlapping voices.
* BIE-COMP-H6-005: adoption in existing H3 checked compilation, source maps, CLI, source publication and actual-render revalidation. Legacy inputs and historical golden fixtures unchanged.

## Supported contract

`schema_version=bie.comp-frame-runtime.v1`. All state paths are flat literal keys, not evaluated property expressions. Every key has an initial scalar and nonempty source/reasoning references. `metadata.state_paths` equals those keys; every state has a bound visible property. Bindings are read-only and support identity (text/string, visible/boolean, opacity/number in [0,1]) or explicit clamp01 for opacity. Unsupported coercions fail closed. Text at frame zero preserves its source element's initial text.

Only timeline `state.set` is supported. Every event supplies the exact affected element IDs and source/reasoning references. Two changes to one state that quantize to one frame are rejected. Re-evaluating frames in reverse or random order does not replay effects. Events scheduled after the last renderable frame fail.

Narration uses existing Scene IR cue fields and explicit transcript records, audio descriptors and one segment per cue. Single-voice, no overlaps; mandatory explicit existing caption text element. Declared transcript hashes bind the segment to text but DO NOT establish that the audio actually speaks those words. Audio format is bounded local signed PCM16 WAV (mono/stereo, 8–96 kHz), content-addressed path, immutable SHA-256/size/sample metadata and declared rights/source references. No URL fetch. Compressed audio adapters, TTS and human/ASR speech alignment remain outside this batch.

Timing uses ceil(ms*fps/1000) at both boundaries and [start,end) frame intervals, with no early cue and <one-frame delay. Unobservable cues are rejected. `trim_before_frames` is explicit; resampling, speed changes and loudness repair are not performed. Asset coverage is checked with integer rational arithmetic, not rounded duration strings.

## Runtime adoption and verification boundaries

Empty legacy scenes do not emit H6 files. Active H6 metadata always undergoes validation; invalid contracts cannot bypass through the legacy diagnostic path. Audio source publication requires verified bytes and occurs in private staging before atomic publication. Render revalidation recomputes source and checks every PCM asset. Caller-supplied metadata is not accepted as evidence of decoded PCM content.

Generated state/opacity consumers are fixed-geometry layers; layout checking remains conservative and can reject a declared hidden overlap. Dynamic text/captions require new actual frame measurement; source PASS does not certify fit, speech alignment, teaching quality or rendered media. Strictly bounded React/Remotion test doubles, when used, are labelled diagnostic, never real Remotion execution.

## Documentation checked 2026-09-18

Primary API reference: https://www.remotion.dev/docs/media/audio and https://www.remotion.dev/docs/sequence . Installed project pins remain unchanged except H6 narration adds `@remotion/media` at the EXACT existing target Remotion version. `Sequence` controls placement/duration; `Audio.trimBefore` controls source trim. A full installed pinned-project compile and real render are separate required evidence gates.
