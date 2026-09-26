# H6 continuation: legacy compatibility and real React runtime

This is an implementation and local-runtime checkpoint, not a finished H6 release.

## AUD-023: explicit legacy boundary

`bie.game_engine.contracts` is the exact canonical v1 contract at main commit
`375d99af0edd0086206817dae932156ddf61c569`, blob
`7e2e91539a2ad9c4bc49451af0ea9327cbd46931`. Its original ten tests are retained.
The package-level `GameDocument` remains v2; callers cannot confuse the two types.
Keep LF bytes for `contracts.py` when adopting this into Git: the compatibility
loader checks its SHA-256, not a newline-normalized approximation.

`legacy_codec.load_legacy` and `dump_legacy` provide strict, bounded, normalized
JSON round trips. Unknown fields, duplicate keys, malformed Unicode, nonfinite
values, type confusion, excessive size/depth and unknown versions reject.
Normalized JSON preserves the contract's data, not the original whitespace.

`legacy_migration.migrate_legacy` accepts a `MigrationEnrichment` containing the
supplied v2 candidate, text catalog, explicit typed-expression mappings, mechanic
mapping, policy evidence and a review reference bound to the exact input hashes.
`review_binding` exposes the exact bytes the external review must cover.
No legacy expression is evaluated or inferred. Identity, state/effects, entity
kinds/bindings, actions, learning references and source provenance are checked.
The result retains immutable legacy, candidate, enrichment and receipt bytes.

This is deliberately a constrained subset. Legacy hints, adaptations, vector/set
state conversions, computed/list effects, object properties and runtime capability
extensions are rejected. Extra v2 visual/audio intent must be supplied and reviewed.
Legacy metadata, labels and revision-strategy details without a direct v2 field
remain in the sealed legacy sidecar; no independent semantic equivalence is claimed.
A supplied hash-bound review reference is not proof of an actual independent expert
review. Receipts explicitly keep semantic-equivalence, runtime and product acceptance
false. More representative canonical-consumer migration cases are still required.

## AUD-024: actual React and lifecycle

The DOM adapter previously named React is replaced with bundled React 19.3.0 and
ReactDOM 19.3.0. The lockfile, esbuild 0.28.2 build, every bundled source hash,
vendor output hashes and full React/ReactDOM/Scheduler licenses are included.
The vendor manifest is pinned separately; missing, injected or modified files fail
before materialization. Runtime loading does not fetch dependencies from a CDN.
Rebuilding the pinned vendor produced the same manifest and JavaScript hashes.

Mounting uses `createRoot` and an initial `flushSync` because the existing controller
needs committed nodes before binding. A neutral outer container holds one application
region. Duplicate live mounts reject. Disposal removes handlers, pauses tracked audio,
unmounts React and rejects stale API dispatches. A fresh mount creates a fresh state
and telemetry sequence. No production Linux process or sandbox policy was relaxed.

Primary references: [React createRoot](https://react.dev/reference/react-dom/client/createRoot),
[React flushSync](https://react.dev/reference/react-dom/flushSync),
[esbuild bundling](https://esbuild.github.io/api/#bundle).

## Executed evidence

`evidence/h6_recovery/RESULT.json` records the exact portable suite results and source
inventory. Run with `python -X utf8 -B scripts/verify_h6_recovery.py` on Windows;
the inherited compiler architecture scan otherwise uses the Windows code page.
Two historical compiler tests are explicitly excluded, not silently skipped:
the old browser smoke disables Chromium's sandbox; the old TypeScript test needs
`tsc` on PATH. Strict TypeScript compilation is separately executed using locked
TypeScript 5.8.3 and `noEmitOnError` for all generated runtime modules.

`evidence/h6_runtime` includes compiler/build bindings and the browser UI receipt.
The standalone Edge automation attempt timed out and its failed receipt is retained.
The Codex app browser then loaded the actual compiled ESM page from a loopback HTTP
origin with the production CSP headers. Native Enter changed x from 1 to 2 and score
to 10, retained keyboard focus and emitted one consent-configured telemetry event.
Native narration activation completed real WAV playback and displayed the Urdu caption.
Test-only UI controls verified unknown-action rejection, duplicate-mount rejection,
idempotent cleanup, detached-handler removal, restored initial state, deterministic
replay and sequence reset in a second session. Browser errors were empty.

The audio is an explicitly generated 100 ms test tone, not book narration. The
visuals are a contract fixture, not an accepted product design. Browser proof is local
Windows evidence; it does not establish deployed-origin, Linux process isolation,
full responsiveness, real-book semantics or learner outcomes. The harness files are
separate test artifacts and are never included by the production build pipeline.

## AUD-026 and open gates

Seeded bounded properties now cover nested multilingual metadata, insertion-order
independence, normalized round trips, truncation, source/candidate mutations and
malformed Unicode. They found and fixed a Unicode-error boundary in the new legacy
loader. This is partial coverage, not full-section property/fuzz closure.

Remaining: full H1–H6 Linux cumulative regression and canonical consumer tests;
AUD-009 deployed-origin proof; broader AUD-026 generated/adversarial cases across
runtime/handoff/learning; independent migration cases; section re-audit; canonical
adoption ledger and repository integrity gates; exact GitHub commit/tree readback.
H6 completion, canonical integration and product acceptance remain false.
