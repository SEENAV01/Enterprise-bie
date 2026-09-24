# Run and verify H5

Use a supported Linux service environment with the inherited dependency versions. This delivery was executed on Python 3.13.5 with NumPy 2.3.5, cryptography 46.0.4, eSpeak and FFmpeg. It requires /usr/bin/unshare, /usr/bin/espeak and /usr/bin/ffmpeg and working user/mount/PID/network namespace support. Exact selected identities are discovered and approved per host; a profile from another host is not portable approval. No Windows-native, Android-native or hosted production deployment is claimed. Nothing downloads or installs dependencies automatically.

From an extracted, clean Integrated package:

```sh
python -B scripts/verify_audio_package.py .
python -B scripts/run_audio_tests.py --pattern 'test_audio_h5_*.py' --output /tmp/h5-tests.json
python -B scripts/run_audio_tests.py --output /tmp/all-audio-tests.json
python -B scripts/benchmark_audio_h5.py --output /tmp/bie-h5-new-benchmark
```

The last destination must not already exist. The benchmark uses synthetic two-scene text, makes its own disposable test-only key, invokes five fresh CLI processes (probe, prepare, native run, stored reuse, verify) and saves a technical export and public test evidence. It deliberately does not supply production credentials or pronounce this voice accepted. Listen to technical_export/master.wav only as a technical sample, not a production-quality promise. Timestamped test receipts will expire under their included test policy; regenerate the benchmark instead of weakening expiry checks or blindly trusting its public key.

## Governed execution outside the disposable benchmark

```sh
python -B scripts/audio_pipeline.py --standalone-fixture probe --output /private/service/profile.json
python -B scripts/audio_pipeline.py --standalone-fixture request examples/audio_h5/two_scenes.json \
  --profile /private/service/profile.json --run-id 01952504-3824-4000-8000-000000000105 \
  --job-id lesson-test --revision r1 --key-id YOUR_APPROVED_EXECUTOR \
  --output /private/service/request.json
```

Provide a policy satisfying pipeline_evidence.validate_trust from an authorized trust-management process, approving the reviewed profile fingerprint and executor public key. Provide the matching owned mode-0600 raw Ed25519 private key through --private-key-file. Do not copy the benchmark's public key into production trust. The service directory and state must be private to the service account. Do not put keys in the repository, request JSON, ZIP or chat.

```sh
python -B scripts/audio_pipeline.py --standalone-fixture run \
  --request /private/service/request.json --profile /private/service/profile.json \
  --trust /private/service/trust.json --private-key-file /private/service/executor.key \
  --root /private/service/state --output /private/service/first-export \
  --allow-technical-voice --allow-review-output
python -B scripts/audio_pipeline.py --standalone-fixture verify-export /private/service/first-export \
  --request /private/service/request.json --profile /private/service/profile.json \
  --trust /private/service/trust.json
```

Repeat the run into a NEW output directory with the same request/state to reuse a current valid stored result. A changed source under the same job revision fails; use a new governed revision. Expired/revoked receipts, missing dependencies, policy/profile changes, disabled isolation, oversize inputs or cancellation must not be bypassed. A new host profile requires reviewed approval. Canonical integration must remove reliance on standalone snapshots only after comparison with actual repository HEAD and a full enterprise regression.
