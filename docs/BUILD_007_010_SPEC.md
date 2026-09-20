# COMP BUILD-007..010 — continuation specification

## Authority and scope

Continue the uploaded Batch 007 cumulative workspace, not a reconstructed replacement.
The two uploaded ZIPs were verified byte-for-byte where one embeds the other, and
all 11 master checksums were verified. The restored baseline reran as **657 tests**.
Older retrieved library reports said 656; these are a different document revision.
All pre-existing Python source and tests are preserved byte-for-byte in this delivery.

| Original task | Implemented entry point | Responsibility |
|---|---|---|
| BIE-COMP-BUILD-007 | `bie.compiler.smoke_render.smoke_render` | Explicit inclusive frame window, real local CLI adapter, no full-render promotion |
| BIE-COMP-BUILD-008 | `bie.compiler.full_render.full_render` | Whole declared composition, no subset flags, fail-closed media verification and exclusive publication |
| BIE-COMP-BUILD-009 | `render_logs` / `render_process` | Redacted structured events, ordered hash chain, bounded process output, cancellation, timeout, process-group teardown |
| BIE-COMP-BUILD-010 | `artifact_hashing` | Streaming SHA-256, normalized confined paths, exact source/recipe/artifact bindings, integrity verification |

Shared contracts and runtime are delivered in this same batch. Numerical task IDs
are not a dependency-execution order: hashing/logging support smoke/full execution.
No new original task IDs are invented and no original module is silently replaced.

## Input and compatibility contracts

`RenderRequest` consumes the existing `CompositionDescriptor`. `RenderProcessResult`
wraps the existing `ProcessReceipt`; failures use the existing `BuildError` family.
There are no new Python package dependencies. Python 3.10+ is required by the type
syntax. The process-group adapter is POSIX-only and explicitly rejects other OSes.
The current adapter is H.264 MP4 / yuv420p, with known even dimensions and finite FPS.
This is a backend profile, not a limitation on the product's eventual renderer-neutral IR.

Requests bind a SHA-256 scene fingerprint, composition metadata, run ID, source entry,
props file (optional), output, process budgets and operator-controlled tool paths.
Unknown composition metadata, path traversal, symlinks, inconsistent frame ranges,
nonfinite values, missing dependencies, lock/version mismatches and existing output
are rejected. Public callers must not control executable paths in a deployed service.

## Actual execution path

1. Create an exclusive attempt directory; record start or failure.
2. Fingerprint package/config files, `src/**`, `public/**`, entrypoint and supplied props.
3. Check lock root consistency and installed local Remotion/CLI/React version pairs.
4. Record CLI and operator binary hashes. Do not run `npx` or install implicitly.
5. Invoke local `node node_modules/@remotion/cli/remotion-cli.js render ...`, without a shell.
6. Smoke passes a precise frame range. Full mode does not pass a frame override.
7. Use a minimal inherited environment and empty dotenv input; preserve bounded redacted stdout/stderr.
8. On timeout/cancellation/output limit, terminate the owned POSIX process group.
9. Require a new nonempty regular file and count decoded frames using real ffprobe.
10. Verify exact dimensions, FPS, decoded-frame count, codec, pixel format and duration.
11. When requested, require an audio stream; do not synthesize one to hide its absence.
12. Recheck source and toolchain identity. Publish via an exclusive same-filesystem hard link.
13. Bind the probed media digest in the receipt and hash-chain the terminal event.
14. Seal all attempt records and media in an artifact manifest. Roll back our published link if sealing fails.

Every attempt has its own `render-evidence/<run_id>` directory. A repeated run ID is
refused, not overwritten. Failed partial output remains in evidence, not in the requested
release path. Successful media retains a staging hard link for audit/rollback.

`timeout_s` is a **per-subprocess** budget, not an overall end-to-end SLA. Frame delay
has its own Remotion timeout. Sample size is caller-selected; full lessons are not capped.

## Meaning of results

`passed=true` means the invoked technical operation and media integrity checks passed.
`accepted=false` remains mandatory in every produced top-level receipt. An injected
runner is explicitly labelled `INJECTED_TEST_RUNNER`. The public CLI does not expose
runner injection and rejects our known test fixture on its real execution path.
A completed render receipt must be accompanied by a valid artifact manifest; an
unsealed terminal log is not a completed result.

Source fingerprints identify the captured generated-project files. They do not prove
semantic source truth, hermetic remote assets, immutable node_modules contents, or a
supply-chain signature. Binary hashes and lock/version checks identify the environment;
they do not prove cross-machine byte-identical MP4 output. Browser launcher hashing is
not a complete hash of the browser installation.

## Security and deployment boundary

The subprocess wrapper is not a security sandbox. Remotion executes JavaScript and
may fetch assets. Use BIE's governed container/OS sandbox, network allowlist, resource
quotas, trusted dependencies and secret policy before running untrusted inputs. Working
files must be owned exclusively by the render worker. Path checks and O_NOFOLLOW hashing
reduce local path hazards; they do not replace multi-tenant isolation or crash recovery.
A host crash may leave an unsealed attempt requiring recovery; it must never be promoted.
Log redaction handles common credential patterns and supplied literal secrets, not every
possible confidential value. Do not publish evidence without its normal access controls.

## Verification and deliberate non-claims

New tests include real POSIX process lifecycle tests, real FFmpeg-generated technical
test patterns, and real ffprobe decoding. The renderer call in media integration tests
is explicitly injected. Those tests do **not** demonstrate a successful Remotion render.
The original React emitters also generated a separate real-Remotion-ready fixture, but
npm registry lookup failed with `EAI_AGAIN` in this session. Dependencies were not installed;
full-project TypeScript, real CLI discovery, smoke/full render, and rendered-frame inspection
remain NOT RUN. No test-pattern MP4 is presented as a BIE lesson.

Remaining gates include real installed-Remotion execution; generated-code and multidomain
coverage; render/frame/audio QA; remote-asset policy; broader orchestration; real-book E2E;
learning quality; game runtime; regression in the canonical monorepo; and product acceptance.
The COMP section remains IN_PROGRESS. GitHub was not modified by this batch.

## Next original family

The user's original 18-section master registry lists, immediately after BUILD-010:

- BIE-COMP-QA-001 — compile diagnostics mapping
- BIE-COMP-QA-002 — capability fallback QA
- BIE-COMP-QA-003 — deterministic output test
- BIE-COMP-QA-004 — generated-code regression
- BIE-COMP-QA-005 — multi-domain compile benchmark

These are the next original tasks, not an automatic section exit. After original COMP
work, re-audit capabilities, add justified hardening, rerun regression and re-audit.
Integration and acceptance remain separate recorded events.

## API references checked for this implementation

- Remotion render CLI: https://www.remotion.dev/docs/cli/render
- Remotion composition CLI: https://www.remotion.dev/docs/cli/compositions
- ffprobe: https://ffmpeg.org/ffprobe.html

The checked CLI documentation supports local entrypoints, composition IDs, frame ranges,
explicit codec/pixel format, browser path and timeout options. The real invocation in
this environment remains unverified; documentation is not execution evidence.
