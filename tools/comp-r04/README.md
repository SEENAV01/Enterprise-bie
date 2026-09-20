# R04 validation branch — not acceptance

This branch adds only a validation driver, helper contract tests and a separate workflow.
It tests canonical source 16d4d87824e77db3565a231a332e7977d39d7117 (tree 81febee6c9867648b58e0fc16464038b5ac4d12f), not moving main or the driver commit.

The exact branch `validation/comp-r04-20260920` opts into first npm lock resolution on push. The lock is captured, then installed with npm ci and replayed in a second fresh project. Bootstrap is not historical lock approval.

The current checked publisher and real-render harness remain unchanged. A real failure halts the slice; logs and outputs are retained. No source edits, skipped gate, version downgrade, fake renderer or global acceptance promotion is authorized.

The canonical PR regression workflow is unchanged. Do not merge merely because this synthetic clip renders. Product acceptance, real-book E2E, visual review and spoken narration remain separate gates.

Compared with the original handoff, the driver excludes font binaries from every evidence copy, while retaining their source hashes. The added ninth helper test covers that export rule.

## Reproduced helper-only correction

Hosted run 35495563384 stopped before dependency installation because npm rejects loading `/dev/null` as both user and global config. The retained artifact's SHA-256 is `bc76496a67d9392fdd1629696b259cbc2e3dc36b1dce7772362eb18309a638c7`. The helper now creates two distinct empty config files outside the canonical checkout. Two added tests cover the files and a real offline npm 10.9.2 version invocation. Original failure evidence and all BIE source/gates/pins remain unchanged.
