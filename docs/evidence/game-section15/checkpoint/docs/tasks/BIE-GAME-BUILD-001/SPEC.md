# BIE-GAME-BUILD-001 — reproducible TypeScript/runtime package build

## Purpose
Provide a production-oriented BUILD capability over the content-addressed GAME Compiler output. This task must preserve compiler provenance, fail closed on invalid/tampered inputs, and never claim product acceptance.

## Enterprise invariants
- exact Batch 06 compiler receipt/artifact binding is verified before build;
- workspace paths are root-confined and normalized;
- toolchain identities are versioned and executable-hashed;
- build processes have explicit timeout/output/package-size bounds;
- final artifacts are content-addressed and covered by a deterministic package manifest;
- external network is forbidden by default;
- generated runtime preserves studio-grade semantic entities, accessibility and anti-slide intent;
- failures produce stable machine-readable evidence without persisting raw sensitive stacks;
- `product_accepted=false`.

## Capability-specific scope
reproducible TypeScript/runtime package build.

## Verification
Dedicated task tests plus cross-cutting build integrity, ESM graph, security, browser-quality, process-bound and end-to-end pipeline tests. The complete Batch 07 suite is 75 tests; upstream cumulative regression is 701 additional tests.

## Acceptance boundary
Passing this task is component implementation evidence only. Native static-origin module loading is not claimed in this sandbox because Chromium policy blocks `http://`, virtual HTTPS, and `file://` navigations with `ERR_BLOCKED_BY_ADMINISTRATOR`; real Chromium execution is instead verified using the exact self-contained linked build bundle via Playwright DevTools execution. Canonical CI/full deployment validation remains downstream.
