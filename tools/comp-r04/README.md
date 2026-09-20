# R04 validation branch — not acceptance

This branch adds isolated validation tools and a separate workflow. It tests canonical source `16d4d87824e77db3565a231a332e7977d39d7117` (tree `81febee6c9867648b58e0fc16464038b5ac4d12f`), not moving main or the driver commit. Only the exact branch `validation/comp-r04-20260920` triggers the validation job. Main is not modified.

The checked publisher and real-render harness remain unchanged. A real failure halts the slice; authentic logs and outputs are retained. No source edits, skipped gate, version downgrade, fake renderer or global acceptance promotion is authorized. Font binaries are excluded from evidence exports while their source hashes remain available.

The canonical PR regression workflow is unchanged. Do not merge merely because this synthetic clip renders. Product acceptance, real-book E2E, visual review and spoken narration remain separate gates.

## Retained execution history

1. Run `35495563384` failed before dependency installation because npm rejects using `/dev/null` for both user and global config. Artifact SHA-256: `bc76496a67d9392fdd1629696b259cbc2e3dc36b1dce7772362eb18309a638c7`. Correction `24d3519791d52b290cdf65f0f0151053e7d5de1b` uses distinct empty config files; 11 helper checks pass, including actual offline npm execution.
2. Run `35495874696` installed the exact dependencies, passed actual full pinned TypeScript compilation and bundled the composition, then failed launching the supplied full Chrome binary because old headless mode was removed. No smoke/full render occurred. Artifact `10599699753` SHA-256: `f7e4fec0645a82b0c17971be58b8322fb9a7c84c1cff5f1545baf75ab6009319`. Lock SHA-256: `e445be44573e1cbac454af2987d84f795c43e8bc826be5e86b754ee42073b1c7`.

## Browser correction, without dependency re-resolution

The workflow now restores that exact artifact and lock by hash, installs the same pinned dependency tree in a separate browser-provisioning workspace, and invokes Remotion 4.0.506's own `browser ensure` for Chrome Headless Shell 149.0.7790.0. Its executable hash/version is recorded. The unchanged checked validator receives this real managed binary. Browser provisioning alone is not render proof. Both actual render projects use the captured lock and clean npm ci, never another bootstrap resolution.

The workflow token has only contents-read and actions-read; actions-read retrieves the owned prior artifact. If the retained Actions artifact expires or fails its digest check, the workflow stops. The downloaded local evidence backup retains its original ZIP and lock; restore that verified input explicitly rather than silently re-resolving dependencies.

Reference: https://www.remotion.dev/docs/miscellaneous/chrome-headless-shell . The next hosted outcome is not assumed. Historical failure receipts and acceptance flags remain unchanged.
