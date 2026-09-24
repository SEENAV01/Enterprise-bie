# AUDIO Batch 004 — MIX-001..005

This release continues the supplied `BIE_AUDIO_BATCH_004_WORKING_RECOVERY.zip`, not a replacement implementation. The unchanged Batch 003 baseline remains the predecessor at BIE-AUDIO-SYNC-005. Existing Batch 001 preparation variants and Batch 002/003 TTS/SYNC modules remain intact. This is a bounded component implementation, not section exit or product acceptance.

## Input and actual execution path

Existing DIR ScriptPlan/realized voiceover → either reconciled preparation profile → TimedEspeakProvider and TTSCache → measured SynchronizedAudio → MIX → PCM16 master WAV + derived MIX_CLOCK + VTT/SRT + source-bound receipts. The API `mix_synchronized` accepts the existing SynchronizedAudio object; `_verified_sync` reassembles source audio, captions and pauses from actual assets before mixing. The CLI exercises this path, not a replacement synthetic narration API.

A mix specification pins exact preparation and measured-timeline fingerprints. Stem assets are relative local regular files bound to SHA-256, decoded rate/channels, source references and declared rights basis. Byte changes, stale timelines, unsafe paths, absent assets, mismatched channels or sample rates fail before publication. The presence of a rights reference is not independent verification of rights.

## MIX-001 — loudness normalization

`loudness_normalization.py`, `mix_meter.py`, `mix_contract.py`.

PCM input is decoded to immutable little-endian float64 with headroom; overrange sums are never silently clamped. Actual FFmpeg `loudnorm` INPUT measurements determine integrated loudness and true peak. The filter's normalized output is sent to null and is never adopted. Python applies one declared gain and remeasures. The default engineering policy is -23 LUFS, tolerance 0.5 LU and -1 dBTP ceiling, with explicit boost/attenuation limits. These are configurable defaults, not a blanket delivery-platform recommendation or formal EBU conformity claim. Mono/dual-mono treatment is explicit.

Narration and programme are measured separately. If the target cannot be reached within peak/gain constraints the `review` policy returns an explicit constrained result; `fail` rejects it. A post-quantization target failure also obeys this policy. Silence/too-short material cannot be assigned invented LUFS. No hidden dynamic compression, loudness-range mastering or automatic time stretching is applied.

FFmpeg jobs have bounded deadlines/output, cancellation, process-group termination and executable identity checks. This is not the adopted hostile-code operating-system sandbox or publisher attestation.

## MIX-002 — music ducking

`music_ducking.py`.

A narration-only, channel-linked RMS sidechain detects active sample windows. Declared reduction, pre-duck attack, hold and release generate an actual sample gain envelope. Stereo channels share the gain and opposite-phase signals do not cancel in the energy detector. Overlapping envelopes merge deterministically. Pre-duck changes the background gain before speech, not the narration clock. The original narration samples and timestamps are not displaced. RMS activity is not speech recognition or verified intelligibility.

## MIX-003 — SFX mixing

`sfx_mixing.py`, `mix_io.py`, `mix_pipeline.py`.

Music and SFX are placed on separate float buses using exact sample offsets, trims, gain, explicit repeat counts, fades and declared channel mapping. Stable asset-ID order gives repeatable float accumulation; there is no implicit looping, resampling or clipping. Unsupported assets extending beyond the current scene/audio timeline request explicit extension rather than truncation.

The default `all_stems_silent` pause policy mutes music over required narration pauses and rejects overlapping SFX. Explicit `narration_only` permits a background or cue in those windows while preserving narration silence; that policy change is visible in the receipt. Required content, asset IDs, source references and declared rights metadata survive.

## MIX-004 — silence trim and timing preservation

`silence_trim.py`, `mix_clock.py`, `mix_pipeline.py`.

Only contiguous exact-zero edge samples may be removed. All nonzero samples (including a single quiet PCM16 sample), internal gaps, word/caption spans, requested pauses, declared assets and animation spans are protected. The trim has padding, minimum duration and maximum edge limits. No breath detection, acoustic silence classifier, internal jump cut or speech editing is claimed.

Trimming creates a new clock with `output_sample = source_sample - keep_start`. Original SYNC/audio receipts remain unchanged and the original WAV can be published alongside the master. Word/caption/pause intervals, scene and segment boundaries, animation holds and rational keyframes are mapped to this clock. Frame boundaries are recomputed from the existing rational fps clock, not accumulated rounded durations. The result validates interval coverage and media/meter identity; `verify_mixed_source` recomputes the entire derived clock against the actual source SYNC object. Pure forward/reverse sample/frame seeking uses the trimmed clock including animation progress.

## MIX-005 — peak control

`peak_control.py`.

Actual true/sample peaks determine linked constant attenuation. The final PCM16 encoding uses nearest-even quantization and rejects a would-clip conversion. The encoded output is independently remeasured by the native meter, must meet the ceiling, and has unchanged length/rate and zero processing latency. This is not a nonlinear look-ahead limiter, creative compressor or mastering engineer. High-crest-factor material can remain loudness-constrained and review-required rather than being distorted to force a target.

## Output, budgets and integrity

Publication is an exclusive new directory, uses the existing file-lock helper with an explicit bounded timeout, and does not replace an existing output. It includes `master.wav`, `MIX_CLOCK.json`, `MIX_RECEIPT.json`, `captions.vtt`, `captions.srt`, hashes, and optionally the original WAV/SYNC and exact input specifications/assets. A review result requires explicit opt-in and is still not accepted. Inconsistent rehashed clocks, meter bindings, policy/review flags and source projections are rejected. Content hashes are not signatures or proof against a malicious author recomputing an entire report; production evidence-store/worker attestation is a separate integration concern.

Limits include mono/stereo PCM16 input, 8–192 kHz, 1,800 seconds and a 64 MB PCM budget (whichever is tighter), bounded float headroom, up to 128 stems, bounded track/events and process limits. Rejection requests a smaller explicit work unit; no automatic content loss is authorized. A long-book production scheduler must choose bounded scene/lesson jobs; this batch does not cap a whole book's content.

## Real verification and its boundaries

Tests exercise actual FFmpeg input metering, inter-sample overshoot, linked attenuation, RMS envelope math, source-to-mix execution, native speech in both preparation profiles, exact pause samples, caption/scene/animation preservation, stale/tampered assets and publication. Native benchmarks re-run CLI cases in independent processes and use separate FFmpeg `ebur128` metering/ffprobe plus independent numerical gain/placement replay. The filters share FFmpeg native libraries; these checks are not an independently calibrated laboratory or human listening panel.

No cloud/paid TTS call, production neural voice, completed Remotion render, real-book ingestion, linguistic/acoustic approval or cinematic-quality acceptance is claimed. QA-001..005, production voice/adapter integration, broader ANI/COMP handoff, deployment isolation and full section audit remain open. GitHub integration waits for AUDIO section exit.

## Reproducible commands

Install the included `requirements-audio-mix.txt` (NumPy 2.3.5) and the native FFmpeg/ffprobe + eSpeak engine/library required by the inherited tests. This delivery was executed with Python 3.13.5. No native executables, models or font files are bundled.

```sh
python -B scripts/verify_audio_package.py .
python -B scripts/run_audio_tests.py --output /tmp/audio-tests.json
python -B scripts/build_audio_batch004_examples.py /tmp/audio-mix-examples
python -B scripts/audio_mix.py /tmp/audio-mix-examples/english-mix/narration.json \
  --mix-spec /tmp/audio-mix-examples/english-mix/mix.json \
  --sync-spec /tmp/audio-mix-examples/english-mix/sync.json \
  --output /tmp/audio-mixed-output --cache /tmp/audio-cache \
  --cache-namespace local-example --allow-technical-voice --standalone-fixture
python -B scripts/verify_audio_mix_output.py /tmp/audio-mixed-output
```

Example manifests are source/runtime-bound. Regenerate the examples on another native speech runtime rather than editing a stale fingerprint until it passes. Source and receipts remain unaccepted even when all technical tests pass.
