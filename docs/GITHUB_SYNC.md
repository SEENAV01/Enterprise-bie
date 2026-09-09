# GitHub synchronization and downloadable backups

Canonical remote: `https://github.com/SEENAV01/Enterprise-bie`, branch `main`.

A real tiny file write/readback succeeded in commit `4b35084be062ae17b2b8ac8d99af78030e7c42e4`. The final backup's `BACKUP_MANIFEST.json` identifies its exact verified remote commit and tree.

## Ordinary authenticated Git checkout

Implement directly in the canonical modules, run `python scripts/integrated_check.py`, update evidence and commit intended files. Run `python scripts/sync_github.py --branch main`. It checks the exact remote, refuses divergence, performs a real probe commit/push/readback on a unique evidence branch, pushes without force and verifies the main branch SHA. Credentials stay in the existing Git setup.

```bash
python scripts/package_repository.py --commit HEAD --output ../BIE_CANONICAL_BACKUP.zip
```

This backup contains the complete committed repository and checksums. Atomic task ZIPs are optional evidence only; do not manually assemble them into production.

## Connector-only workspace

Read the branch and base tree; verify a tiny actual write; create blobs/trees from validated local changes while retaining the base; compare the resulting tree with the local Git tree; create a child commit; update the branch without force; read branch, commit and tree back and compare exact SHAs. Reconcile concurrent changes first. An uploaded blob or unattached commit is not synchronization.

Restricted shell network access can use this Git Data API route. Do not claim a shell push occurred. If synchronization fails, retain the workspace and deliver the repository backup with an explicit blocker.
