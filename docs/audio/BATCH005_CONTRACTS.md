# AUDIO Batch 005 — QA-001..005 contracts

## Current implementation and run path

`load_published_mix()` reads the actual MIX directory, verifies its exact files/bytes and reconstructs the typed source speech plan, selected voice, per-segment assets, timings and captions from `source.wav` and `SOURCE_SYNC.json`. It rebuilds the source→derived clock using the existing validators and compares caption exports to the computed originals. No source TTS call is made simply to rehydrate this source record.

`audit_mix()` executes five ordered scoped checks. `publish_qa()` writes a separate, exclusive diagnostic directory; it cannot overwrite the MIX input. Invalid JSON, symlinks, extra/missing files, wrong hashes, stale transcript/voice/media clocks and budget violations are rejected. Diagnostic QA is not a privileged artifact or production publisher. There is no claim of hostile multi-user filesystem isolation or authenticated source records; canonical INFRA adoption is an explicit hardening item.

Example, with pinned standalone DIR dependencies:

```
python -B scripts/build_audio_batch005_examples.py /tmp/audio-qa-examples --allow-technical-voice --standalone-fixture
python -B scripts/audio_qa.py /tmp/audio-qa-examples/english-sound/mix --caption-intent /tmp/audio-qa-examples/english-sound/CAPTION_INTENT.json --output /tmp/qa-result --standalone-fixture
```

The second command returns **3 for REVIEW**, 2 for FAIL/BLOCKED, and 0 only for PASS. Current QA-001/004/005 deliberately retain unverified independent-acoustic/render boundaries, so a currently valid complete run normally cannot be all-PASS. REVIEW is not a program crash and is not production acceptance. An unavailable meter is BLOCKED, not a passing skipped check. Cancellation is explicit.

## QA-001: pronunciation

Every protected or literal preparation span is tied to exact final media, original display text, expected spoken realization, source/rule references and voice identity. Reported MATCH/MISMATCH/UNCERTAIN records must use current media/target fingerprints. Reported mismatches create owned FAIL findings; positive unauthenticated records never establish phonetic correctness. A source-bound review queue is implemented, but independent automatic acoustic pronunciation checking, evaluator authenticity and calibrated listening acceptance remain OPEN. No transcriber or external evaluator was called.

## QA-002: clipping

Decode the actual output WAV and measure per-channel rail samples, consecutive same-sign rail runs and sample peaks. Default consecutive-rail limit is three samples; isolated rail contact requires review. Actual FFmpeg true-peak measurement is bound to decoded PCM identity, sample rate, channel count and duration. Default ceiling is -1 dBTP; silence does not become an accepted lecture. These are explicit engineering thresholds, not proof of universally optimal mastering, original analog clipping detection or formal metering certification. A safe signal and intentionally clipped/over-ceiling signals exercise the actual native meter.

## QA-003: missing audio

Validate every source speech segment against actual delivery windows. Nonzero background alone cannot satisfy narration presence: a separate implementation reconstructs MIX sample equations from source/stem WAV bytes, trims, channel transforms, gains, duck envelopes, protected pauses and quantization. It does not call the production gain/duck/mix/trim/peak functions. Maximum allowed numeric difference is one PCM16 unit for floating-point accumulation; selected positive fixtures measured zero. This uses the same NumPy arithmetic/library, and is not certified independent DSP or semantic transcript verification. Adversarial fixtures modify/re-hash delivery media; separate source replay still detects loss.

## QA-004: synchronization

Reconstruct source→derived sample clock and check every word/caption/scene/pause/animation record. Boundary probes evaluate forward/reverse seeking; selected unit fixtures also evaluate every frame. This does not mean a finished rendered video was inspected. Existing engine marker timings are source/audio-bound but independent phonetic word boundaries and actual rendered audiovisual synchronization remain REVIEW.

## QA-005: captions/accessibility

Generate an additional spoken-caption track, keeping original display/formula captions intact. Speaker labels and meaningful-sound descriptions are explicit authored, source-bound inputs; unknown sound meanings are not inferred from filenames. Overlapping speech and sound labels remain visible rather than one overwriting the other. Authored meaningful sound captions do not by themselves prove semantic correctness. Default limits (42 characters/line, two lines, 22 characters/second, 400 ms minimum) are configurable engineering diagnostics, not a universal WCAG rule or full accessibility compliance. Overflow/fast-reading findings do not delete text or time-stretch media.

WebVTT and SRT use the same sample clock with shared rounded boundaries; literal markup is escaped. Required pauses and sound intervals remain explicit. Actual rendered placement, visibility, contrast and whether essential visuals are obscured remain an open downstream gate.

## Evidence, identities and limits

Reports bind original source/MIX/clock bytes, QA source-code identity, policies, authored intent and observations. Strict status recomputation and mandatory uncertainty findings prevent a rehashed caller report from silently claiming all-PASS. A local hash is still not an authenticated evaluator or release authority; do not treat `require_qa_pass()` as product authorization.

Current native evidence: actual eSpeak synthetic English/Hindi speech, FFmpeg measurements and independently coded sample replay. No production neural voice, human listening, independent acoustic aligner, real textbook, actual Remotion renderer or full enterprise regression was executed. The standalone HTML preview uses real Chromium/audio/WebVTT, not a video renderer; local `--no-sandbox` is not production isolation proof. File navigation was disallowed by environment policy, so the browser received the same authored page bytes through set_content; policy was not bypassed or disabled.

## Recovery fixes retained

An initial diagnostic serialization mismatch was fixed by serializing tuple source refs consistently, without weakening schema validation. The first 92-task-test run contained one error because a SFX fixture mixed unquantized floating samples but supplied quantized WAV bytes as its source; the fixture now mixes the actual decoded WAV just as the file-based path does. The signal identity check was not relaxed. Original failing log and corrected run are retained. Bounded stem/window validation occurs before replay allocations; wrong-source and rehashed-status negative tests are retained.

## Packaging

The cumulative AUDIO Integrated ZIP preserves every parent file, with exact predecessor bytes for intentionally updated metadata. Atomic ZIPs contain independent declared test closures (shared source plus the selected task suite); they are not ordered deltas and not five unrelated implementations. Their included Batch004 test helper module supplies the unchanged animation fixture; only the requested QA suite is run for each atomic verification.

No font files or vendor executables are shipped. Runtime used here: Python 3.13.5, NumPy 2.3.5, FFmpeg/ffprobe 7.1.5 and eSpeak 1.48.15 with its installed data/library. Native version differences must be recorded and reverified rather than silently assumed identical.
