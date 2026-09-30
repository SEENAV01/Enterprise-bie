# H2 operator path and governed integration

Use the master `combined_source/` as the complete Section17 runtime through H2. Atomic ZIPs are traceable self-contained selected-task distributions, not patches to install one by one. Read the current root `BIE_SECTION17_CONTINUATION.json`; archived metadata remains historical.

## Run all tests
```sh
python -B tools/run_section17_h2_tests.py --output-dir /tmp/bie-h2-all-tests-new
```
Python3.13.5/Linux and FFmpeg/ffprobe7.1.5 were actually used. Linux/POSIX is currently required by the streaming runner. Older advertised Python compatibility, Windows/macOS, other encoders and real kernel sandbox deployments are not verified by these tests.

## Regenerate the actual media experiment
```sh
python -B tools/run_section17_h2_av_diagnostics.py --output-dir /tmp/bie-h2-media-new
```
Requires locally installed FFmpeg/ffprobe and eSpeak. It creates authored fixtures without network/model calls, runs17 scenarios into SQLite, reopens receipts, and preserves all files/commands. Input files and reports from the executed run are already under `evidence/section17/h2/diagnostics/`. It never creates a native BIE lesson or signs production approval.

## Evaluate an existing file
Use operator-pinned SHA256 values for both media and policy. `--captions-sha256` binds raw caption bytes; the policy's `caption_text_sha256` separately binds expected plain text. Omissions and malformed references must not be turned into permissive defaults.
```sh
python -B -m bie.evaluation.benchmarks.av run \
  --database /tmp/bie-h2-new.sqlite --campaign operator-approved-campaign --run-id run-001 \
  --media /absolute/lesson.mkv --media-sha256 MEDIA_SHA256 \
  --policy /absolute/policy.json --policy-sha256 POLICY_CANONICAL_SHA256 \
  --captions /absolute/lesson.srt --captions-sha256 CAPTION_FILE_SHA256
python -B -m bie.evaluation.benchmarks.av get --database /tmp/bie-h2-new.sqlite --run-id run-001
```
The policy canonical hash is `bie.evaluation.benchmarks.models.digest(parsed_policy)`, not the raw JSON file hash. Template fields are documented in `av/service.py`; actual policies and SHA256s are bundled. Exit0 is DIAGNOSTIC_PASS, never release authorization; FAIL/BLOCKED exit2. Use fresh operator campaign/run IDs; the same candidate in a campaign cannot silently retry, and policy/code/resource pins cannot change inside that campaign.

## Native mapping
`map-native --help` lists the exact arguments. Pin the actual commit, run, recipe, input fingerprint and canonical contract bytes. Mapping only checks declarations against local observations. A receipt or signature fabricated from test keys cannot prove a native run. Current pinned schema is render-only; full orchestrator/SceneIR/audio/game/provenance integration remains open.

## Integration before any GitHub write
Obtain an explicitly pinned complete canonical checkout plus the governed Section16 bundle; inspect actual producer/consumer paths. Add H2 APIs to the real metric/rater routes only through versioned contracts and full regression tests. Do not silently route existing metric012/013/015 calls to a different result schema, replace source guards, loosen hard floors, overwrite source/asset directories or import archived fixture approvals. Keep old bounded profiles versioned for reproducibility and use v2 only under an explicit compatible adapter.

Existing `bie/`, test and tool files from H1 are unchanged; new modules live in `bie/evaluation/benchmarks/av/`. Source metadata/README/continuation changes have exact preimages. H2 SQLite uses new `av_h2_*` tables and does not migrate the legacy gate's evidence into production truth. Back up databases and make new native evidence; never rewrite prior finalized receipts.

Interrupted reservation recovery is operator-only and terminal BLOCKED. First stop the abandoned worker, then use `recover --help` with exact stored candidate/policy pins and reason. This is not an authenticated public endpoint or distributed recovery service.

Section and product acceptance remain false. Task028 stays paused; no Section18 jump. The final combined-package requirement includes all future justified hardening and evidence, not only the original task count.
