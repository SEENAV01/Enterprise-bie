# Run AUDIO H1

The Integrated ZIP is a standalone AUDIO workspace, not the whole canonical repository. Install the inherited requirements/native tools (Python, NumPy from `requirements-audio-mix.txt`, FFmpeg/ffprobe, eSpeak for inherited tests). Cloud transport adds only Python standard-library code.

## Offline verification (no provider credentials or network)
```
python -B scripts/verify_audio_package.py .
python -B scripts/run_audio_tests.py --output /tmp/audio-all.json
python -B scripts/run_audio_tests.py --pattern 'test_audio_h1_*.py' --output /tmp/audio-h1.json
python -B scripts/benchmark_audio_h1.py --case english --output /tmp/audio-h1-offline-example
```
The last command makes a clearly labelled synthetic provider-response/PCM fixture and runs the real local MIX/QA pipeline. Its output is not a neural speech demonstration. The QA verdict must remain REVIEW. Use a fresh output directory.

## Approved live deployment (not executed by this release)
Never paste API keys into chat or add them to Git. Set `ELEVENLABS_API_KEY` through the deployment secret manager or an environment variable outside recorded commands. Use a provider voice you are authorized to use. The following command makes GET requests only; it does not synthesize speech:
```
python -B scripts/audio_neural.py --with-dir-snapshot --allow-live-provider \
  --probe-voice-id YOUR_APPROVED_VOICE_ID --probe-language en \
  --probe-model eleven_multilingual_v2 --output /tmp/neural-catalog
```
`--with-dir-snapshot` loads the five unchanged DIR dependency files for this standalone package. It does NOT select a fake speech engine. Omit it only when the canonical DIR package is already installed/importable. The older alias `--standalone-fixture` means the same dependency option.

Inspect MODEL_METADATA.json and VOICE_METADATA.json. Copy deployment.template.json to an operator-owned deployment.json. Replace the revision and rights/usage placeholder references; approve source-data transfer explicitly after reviewing provider retention and account policy. Keep the exact metadata hashes. The default multilingual-v2 mode is `provider_auto`: it must not be relabelled as language enforcement. For explicitly forced language choose the supported flash-v2.5 mode instead. Do not claim voice quality or rights review merely because a template exists.

The next command is a real remote synthesis invocation and may incur charges; run only after authorization:
```
python -B scripts/audio_neural.py examples/audio/english.json \
  --with-dir-snapshot --deployment /secure/deployment.json \
  --cache /private/audio-cache --seal-key-file /private/audio-seal.key \
  --output /private/neural-mix --allow-live-provider --allow-review-output
```
The output and sibling `neural-mix-qa` must not exist. Do not store the private seal key inside the response-entry directory or share it. Requests, timings, pauses, source spans, original successful responses and hashes are retained in MIX publication. QA is run with the existing engine and remains diagnostic; CLI exit 3 means REVIEW, 2 means blocked/failure and 0 means all current checks passed, not product acceptance.

`--profile batch001-204` selects the preserved earlier preparation API. `--sync-spec` and `--mix-spec` accept the existing source-bound specifications. Supported PCM rates and deployment settings are checked, not guessed. Do not resubmit timed-out synthesis automatically: remote completion/billing may be unconfirmed. Missing/corrupt timing evidence does not trigger a second waveform and pretend it was the first.

## Required live validation after setup
A real run must save returned waveform/response/timings and verify caption/scene/pause consistency, model/voice metadata pins, clipping, content coverage and cache reuse. Separately evaluate English/Hindi pronunciation and narration with independent listening/acoustic checks. This release has not done those steps. F02 will add independent evaluation; F03 canonical operational adoption; F04 downstream real AV integration. Do not wait indefinitely on unavailable credentials before addressing those separately governed implementation findings.
