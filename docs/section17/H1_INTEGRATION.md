# H1 controlled integration and run path

No repository write was performed. Preserve Task028/global continuation. Use the complete H1 `combined_source/`, never overwrite a canonical tree by replaying old atomics. Compare owned paths against the exact live checkout under a separately authorized integration action. Reference answers, candidate workers, signing keys and operator policy must be isolated.

## Basic local checks
```sh
python -B tools/verify_section17_package.py verify .
python -B tools/run_section17_h1_tests.py --output-dir /tmp/bie-h1-tests-new
python -B tools/run_section17_h1_diagnostics.py --output-dir /tmp/bie-h1-diagnostics-new
python -B tools/run_section17_batch005_diagnostics.py --output-dir /tmp/bie-legacy-diagnostics-new
```
The full suite also needs the inherited TypeScript/FFmpeg tools. See actual version receipts. H1 selected tests alone do not require a live provider. A real3.11 runtime has not been exercised; its SQLite API fallback is simulated.

## Production-mode input migration
The release operator CLI now additionally accepts `--candidate-bundle`, `--assessment-authorizations`, `--coverage-contract`, `--coverage-sha256`. Existing diagnostic calls remain compatible. Production without these inputs blocks. `manifest.artifact_sha256` now hashes the exact canonical structured bundle, whose exact case roster and per-case candidate digests must match the manifest. This hash is not the raw video hash. Native media remains a separately verified artifact/evidence scope.

Each assessment requires a configured service authorization for `EVALUATOR_ASSESSMENT`. Reference, policy, bundle, coverage and signed records must be frozen before external native/golden attestations are issued. Use `gate.production_input_bindings(...)` and `gate.evidence_scope(..., production_inputs=...)`; legacy external scope signatures do not authorize changed H1 inputs. Existing context/rater/version/independence and required17 metrics are not dropped.

Keys come from explicitly named operator environment variables, not test helpers. The test helpers intentionally construct synthetic production-mode logic controls with invented evidence; never load those identities into a production trust store. An HMAC/signature or a local gate PASS does not prove an unseen native run or authorize deployment.

## Providers
`SupervisedProvider` requires an operator-installed, importable trusted factory and a guarded main entry point. It enforces a direct-worker deadline and response budget. It does not sandbox hostile code or descendants. The inherited direct model adapter path remains for compatibility; native production broker wiring to this wrapper and finite network cancellation remains open. No provider installation/call or API key creation occurs here.

## Durable recovery and archived receipts
Stop an abandoned worker first. An authorized single-owner operator may call `ReleaseLedger.recover_incomplete` with the exact reserved input hash and reason; the reservation becomes terminal BLOCKED and is not reset for another attempt. Compare-and-set finalization prevents overwriting a recovered row. Pre-H1 receipts without the new artifact binding must be explicitly revalidated by an operator; keep the original archive/runtime for historical reading, do not silently rewrite old SQLite records.

## Custody, rollback and packaging
Review H1_CHANGE_LEDGER and metadata preimages. Keep original archives immutable. One inherited preservation test was intentionally strengthened to permit only ledger-bound replacements; no old test method was removed/skipped. Root and ancestor symlink checks assume trusted operator-owned directories and are not race-proof multi-user containment. The package verifier imposes size budgets; review actual artifact budgets rather than disable checks or drop files for a larger later cumulative archive.

Section17 is not ready for enterprise exit merely because all50 original IDs exist. Read GAP_LEDGER and H1_CAPABILITY_AUDIT before choosing H2 work. Do not start Section18 or accept the product here.
