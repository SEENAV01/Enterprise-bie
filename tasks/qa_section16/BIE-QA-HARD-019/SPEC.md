# BIE-QA-HARD-019 — Streaming long-form media inspection

Original audit-derived scope

Extend bounded media/storage readers with checked chunk/frame coverage suitable for high-resolution multi-minute lessons.

## Required closure evidence
- Boundary-frame defects, truncated chunks and omitted frames fail.
- Whole-file hashes and per-chunk coverage agree without unbounded memory.
- Large-media acceptance is tested at declared production sizes, not inferred from short clips.

## Local implementation in H5
Confined chunked immutable snapshots, actual full RGB decoding and timestamp coverage, continuous chunk-boundary comparisons, whole/segment hashes and sampled PNG export.

Code: bie/qa/media_runtime_v2/common.py, bie/qa/media_runtime_v2/stream.py, bie/qa/media_runtime_v2/storage.py, bie/qa/media_runtime_v2/process.py

## Verification
Shared H5 suite: 162 unique tests, not 162 per task. Final executed receipts are under `hardening/section16_h5/evidence/final_source_suites`. The 24 targeted safeguard-removal probes and authored diagnostics are recorded separately, never added as extra unique unit tests.

## Unresolved closure requirements
- Long-form diagnostics cover the declared two-minute 1080p SDR profile, not every production codec, HDR, 4K or arbitrary-duration workload.
- Logical pixel buffers are bounded; aggregate decoder/process/container/GPU resource enforcement and operational isolation remain open.

No historical obligation is closed by a local adapter, a synthetic authority, or an environment-blocked diagnostic. No Section15 or canonical GitHub code is changed.
