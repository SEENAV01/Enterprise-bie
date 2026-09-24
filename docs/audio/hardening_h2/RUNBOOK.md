# Run AUDIO H2

This is a cumulative standalone AUDIO workspace, not the complete Enterprise-bie monorepo. Keep the files at their supplied relative paths. Do not overlay the atomic ZIPs one after another: each is a self-contained shared-source task closure.

## Environment
Use Python 3.13 (verified here: 3.13.5), the inherited `requirements-audio-mix.txt` (NumPy), FFmpeg/ffprobe, and eSpeak for the inherited/native tests. H2 additionally uses `cryptography==46.0.4` from `requirements-audio-acoustic.txt` and installed legacy PocketSphinx/SphinxBase native libraries plus the English models. Exact detected package versions and limitations are in ENVIRONMENT.json. Models, executables, native libraries, fonts and private keys are not bundled. A missing or different runtime must be probed and deliberately approved; there is no automatic download or model fallback. Python PocketSphinx 5.1.1 was not installed or executed.

## Offline source and regression checks
Run from the extracted Integrated ZIP root:
```
python -B scripts/verify_audio_package.py .
python -B scripts/run_audio_tests.py --output /tmp/audio-h2-all-tests.json
python -B scripts/run_audio_tests.py --pattern 'test_audio_h2_*.py' --output /tmp/audio-h2-only-tests.json
```
Every native test requires the declared tools; missing dependencies fail, not skip. An atomic ZIP uses its TASK_RESULT.json command, for example `--pattern test_audio_h2_001.py`. Keep test output outside the extracted package, use `-B`, and verify the package again after tests. The exact-file-set verifier deliberately rejects extra files.

## Reproduce the real local benchmark
```
python -B scripts/benchmark_audio_h2.py --output /tmp/audio-h2-native --allow-local-diagnostic
```
Choose a fresh output path. This executes real local timed-eSpeak speech on synthetic English/Hindi source examples, actual FFmpeg MIX, and independent native searches. It deliberately creates a controlled silent final mix, then invokes the existing MIX function again and performs an authenticated new-media recheck. It also verifies deterministic repeated English analysis and rejects stale, revoked, unknown and publicly rehashed evidence. Hindi is explicitly BLOCKED by this English-only evaluator. Successful English/repair outputs remain REVIEW.

The benchmark creates its signer privately outside the output and deletes the private key after use. Its public trust file is labelled TEST ONLY; it is not production trust configuration. Packaged signed receipts are historical evidence of the run. They will fail normal freshness checks after their 600-second expiry; rerun the benchmark to obtain current receipts rather than weakening expiry checks.

## Operator-configured evaluation of an existing published MIX
Probe the installed runtime (a snapshot is not approval):
```
python -B scripts/audio_acoustic.py probe-runtime --with-dir-snapshot --output /tmp/audio-runtime.json
```
An operator independently provisions an authorized local diagnostic Ed25519 signer and trust file. Do not paste private keys into chat, commit them, or place them inside output directories. The raw private seed must be exactly 32 bytes in an owner-only regular file; key custody belongs outside the public workspace. The trust file must identify the issuer role, public key, approved current runtime fingerprint, validity interval, revocation state and freshness policy according to `validate_trust` in acoustic_evidence.py. The benchmark's test authority is never adopted implicitly.

```
python -B scripts/audio_acoustic.py evaluate /path/to/existing-published-mix \
  --with-dir-snapshot --runtime /tmp/audio-runtime.json \
  --private-key-file /private/evaluator.key --key-id approved-local-diagnostic \
  --trust-file /private/evaluator-trust.json \
  --output /tmp/audio-evaluation --allow-local-diagnostic

python -B scripts/audio_acoustic.py verify /path/to/existing-published-mix \
  --with-dir-snapshot --trust-file /private/evaluator-trust.json \
  --evidence /tmp/audio-evaluation
```
Exit 3 from evaluate is expected REVIEW, not a failed tool run; exit 2 indicates FAIL/BLOCKED. Exit 0 from verify establishes only current signature and publication validity, not acceptance. The operator can provide `--policy` using the exact AcousticPolicy JSON fields; changing policy invalidates old evidence. `--with-dir-snapshot` selects the unchanged standalone DIR closure, not a fake speech engine.

## Integrate later without losing history
Use the cumulative Integrated ZIP, its source-preservation report and INHERITED_RUNTIME_CHANGES.patch. The old qa_pipeline.py and all changed governance files have exact backups under history/hardening_h2. Keep the supplied original registry and prior tasks. Do not copy test trust keys into a deployment. Do not introduce a separate orchestrator for repairs: pending F03/F04 must adopt the existing BIE worker and downstream contracts. No GitHub integration is authorized by this batch's test pass alone; section corrections and the full re-audit/exit policy remain.
