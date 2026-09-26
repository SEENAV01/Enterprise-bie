# Section 15 GAME — Hardening H3: Secure Runtime Substrate

H3 is governed by Step-2 audit findings GAME-AUD-008 through GAME-AUD-012. It also removes the inherited dynamic `__import__(json)` hygiene issue (GAME-AUD-025) while rewriting the browser runtime boundary.

## Closed in H3

- **GAME-AUD-008** — Browser execution is bound to the current canonical browser-game worker contract and runs Chromium under an unprivileged UID/GID, `NoNewPrivs=1`, without `--no-sandbox`; renderer seccomp mode 2 is captured as evidence. Network is deny-by-default.
- **GAME-AUD-010** — Asset paths are content-addressed so sanitized names cannot silently overwrite distinct bytes.
- **GAME-AUD-011** — Runtime package manifest schema v2 contains a canonical self-hash for `build-manifest.json`; verification rejects manifest tampering and unexpected untracked files.
- **GAME-AUD-012** — build subprocesses use a minimal deterministic environment and explicit CPU/address-space/process-count/open-file/file-size limits plus `NoNewPrivs`.
- **GAME-AUD-025** — inherited dynamic `__import__(json)` in browser runtime is removed.

## GAME-AUD-009 status

H3 implements and verifies both components that can be verified in this execution environment:

1. a static loopback deployment origin serving the exact runtime package with production security headers and JavaScript MIME types; and
2. the exact linked ESM dependency graph executed by Chromium's native `type="module"` loader in a hermetic data-module graph.

The combined browser navigation to the loopback deployment origin is **not claimed as verified** because the host has a managed Chromium policy `URLBlocklist=["*"]`, which returns `ERR_BLOCKED_BY_ADMINISTRATOR`. This remains an explicit high-severity validation gap instead of being hidden behind a DevTools bundle smoke.

## Acceptance boundary

H3 does not make Section 15 implementation-scope complete and does not assert product acceptance. GitHub integration has not started.
