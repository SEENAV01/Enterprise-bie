# AUDIO H3 runbook

Use the Integrated archive as a standalone AUDIO workspace, or its reviewed
source changes in the existing BIE monorepo after the AUDIO section exits. Do not
copy the dependency snapshot over a newer canonical repository. No GitHub writes
are part of these commands.

## Verify and test

Run from the extracted archive root:

```sh
python -B scripts/verify_audio_package.py .
python -B scripts/run_audio_tests.py --pattern 'test_audio_h3_*.py' --output /tmp/audio-h3-tests.json
python -B scripts/run_audio_tests.py --output /tmp/audio-all-tests.json
```

The inherited requirements apply: Python 3.13.5 was tested, NumPy 2.3.5 and
cryptography 46.0.4, plus installed eSpeak, FFmpeg, the legacy libpocketsphinx.so.3 /
libsphinxbase.so.3 and the installed en-US model data documented in the H2 runbook.
No weights, fonts or native binaries are included. No automatic package/model
or network download is performed. Tests that require real native dependencies
fail when unavailable; they are not silently skipped.

## Configure the diagnostic authority

Use an administrator-reviewed runtime snapshot and an out-of-band H2 evaluator
trust JSON. The private Ed25519 raw key is 32 bytes in a service-owned mode-0600
file. Do not upload the key to ChatGPT, GitHub, the source ZIP or evidence output.
The private key and trust files must be outside the source, store and output
folders. Test-only keys/receipts in historical benchmark data are not deployment
credentials. Production evaluator authority and key custody remain open F02/F03
work. The adapter does not equate key possession with phonetic correctness.

A probe snapshot is only discovery, not an approval:

```sh
python -B scripts/audio_acoustic.py probe-runtime --output /tmp/runtime.json --with-dir-snapshot
```

## Evaluate and persist

Replace the explicit paths/IDs with your reviewed deployment configuration:

```sh
python -B scripts/audio_durable.py evaluate \
  --input /srv/audio-input/scene-mix \
  --output /srv/audio-evidence/scene-review-1 \
  --store /srv/audio-state/durable \
  --runtime /srv/audio-authority/runtime.json \
  --trust-file /srv/audio-authority/trust.json \
  --private-key-file /srv/audio-authority/evaluator.key \
  --key-id approved-evaluator-id \
  --run-id 01952504-3824-4000-8000-000000000003 \
  --job-id lesson-1-scene-1 --revision 1 \
  --allow-local-diagnostic --with-dir-snapshot
```

`--with-dir-snapshot` verifies both dependency manifests and enables the exact
standalone dependency fixtures. Omit it in a reviewed canonical deployment.
`--input` is the complete published MIX folder, not an arbitrary WAV alone.
Output paths must be new. Exit 3 means REVIEW; exit 2 means blocked/fail. An
unsupported-language diagnostic can be durably COMPLETED while its quality
verdict remains BLOCKED. No diagnostic result is product acceptance.

Run the same request with a different output folder before receipt expiry to
exercise current-authenticated reuse. It reports cache_hit=true and
native_evaluations=0; it does not regenerate speech or infer a new word alignment.

```sh
python -B scripts/audio_durable.py inspect --store /srv/audio-state/durable --with-dir-snapshot
```

## Recovery and freshness

A second live worker is blocked. After a crash and lease expiry, a new epoch may
reclaim only the matching request. A saved completed result must pass current
signature and source checks before either marker can be reconciled. If a result
expired, was revoked or the source/voice/runtime/policy changed, do not alter the
receipt or rewrite the original job. Make an explicit new job revision after
review. H2 receipts currently expire after 600 seconds; reusing a waveform does
not renew an evaluator signature. Automatic local retries are bounded; this lane
is not authorized to repeat billable synthesis.

After a crash before result-pointer commit, local native evaluation may repeat.
Orphan CAS data is retained; this package does not delete it or implement garbage
collection. Original narration and historical signed evidence remain unchanged.

## Reproduce the technical benchmark

```sh
python -B scripts/benchmark_audio_durable.py --output /tmp/audio-h3-native-evidence
```

This uses synthetic test-source narration, actual native speech/MIX/analysis, an
ephemeral TEST-ONLY authority and cold CLI processes. No private key is retained.
It is not real-book, neural-listening, production-key or rendered-video acceptance.
