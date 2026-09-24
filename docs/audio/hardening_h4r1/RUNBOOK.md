# AUDIO H4-R1 local runbook

## Verify and test
Use a Linux host capable of the existing user/mount/PID/network namespaces,
libseccomp and the inherited native eSpeak, FFmpeg and legacy PocketSphinx
runtime. Keep the inherited requirements and pinning files; no automatic upgrades.
No model weights, fonts, native libraries or private keys are included.

```sh
python -B scripts/verify_audio_package.py .
python -B scripts/run_audio_tests.py --pattern 'test_audio_h4r_*.py' --output /tmp/h4r-tests.json
python -B scripts/run_audio_tests.py --output /tmp/all-audio-tests.json
python -B scripts/benchmark_audio_kernel.py --output /tmp/bie-h4r-native-new
```

Use a new benchmark output directory. Benchmark authority is ephemeral TEST ONLY;
its private key is removed when the process exits. The evidence retains public
trust/profile, exact source/media, proofs and test logs. Expired benchmark receipts
remain historical evidence, not currently authorized operational receipts.

## Operational flow
Create a current runtime description through the existing acoustic runtime probe.
Profile discovery consumes that runtime but does not authorize it:

```sh
python -B scripts/audio_kernel.py probe-profile --runtime /srv/bie/runtime.json --with-dir-snapshot > /srv/bie/candidate-profile.json
```

An operator must independently review selected source/runtime identities and
configure `bie.audio.kernel-trust/1` with an approved profile fingerprint and the
existing `bie.audio.evaluator-trust/1` issuer configuration. Do not copy benchmark
trust, auto-approve a discovered profile, or paste any production key into chat.
Load a separately provisioned Ed25519 raw 32-byte private key in a protected local
0600 service-owned file. Keep it outside input, output and durable-store trees.

```sh
python -B scripts/audio_kernel.py evaluate --with-dir-snapshot --allow-local-diagnostic \
  --input /srv/bie/input-mix --output /srv/bie/new-evidence \
  --store /srv/bie/durable-audio --runtime /srv/bie/runtime.json \
  --profile /srv/bie/approved-profile.json --trust-file /srv/bie/kernel-trust.json \
  --private-key-file /srv/bie-keys/evaluator.raw --key-id operator-approved-issuer \
  --run-id 01952504-3824-4000-8000-000000000004 --job-id lesson-scene-001 --revision r1
```

The input is an actual publication from the inherited MIX pipeline, not arbitrary
WAV/transcript JSON. Preserve its source and timing references. Reuse the same
run/job/revision and input/profile for a verified warm lookup, with a different
new output directory. Change the revision when declared inputs or approved
configuration change. Cache entries reverify current signatures; expiry/revocation
blocks reuse rather than silently blessing old evidence. Operational refresh and
paid provider retry policy remain separate future lifecycle work.

Expected local English diagnostic outcome remains REVIEW/exit 3. Unsupported
Hindi can produce a signed diagnostic FAIL/exit 2. Neither is production acoustic
acceptance. No network synthesis or paid provider request is part of this command.

## GitHub integration boundary
Do not copy dependency_snapshot over a newer repo. At the eventual governed
integration point, compare all selected worker/core/DIR files at the actual target
commit, preserve later Codex changes, resolve interface/version differences,
run full repository and real-book gates, and record exact source/commit identities.
This delivery has not written to GitHub or integrated into the Codex track.
