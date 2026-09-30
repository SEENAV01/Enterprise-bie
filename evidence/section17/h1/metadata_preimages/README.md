# BIE Section17 — cumulative through Batch005

**50/50 original task IDs have scoped local implementations. Whole-section audit/hardening/re-audit and product acceptance remain open.**

Use this assembled source rather than merging atomic ZIPs manually. Old executable code/tests/tools are retained byte-for-byte. The historical `metrics.evaluate` API remains a16-metric snapshot; the new `release.deterministic.evaluate_metric` API supports all17. This is deliberate compatibility, not an unimplemented regression metric.

```bash
python -B tools/verify_section17_package.py verify .
python -B tools/run_section17_batch005_tests.py --output-dir /tmp/bie-s17-tests-new
python -B tools/run_section17_batch005_diagnostics.py --output-dir /tmp/bie-s17-diagnostics-new
```

The diagnostic driver actually executes17 deterministic metric profiles, a fixture model-adapter path and fixture-signed human reviews, then persists seven release-gate scenarios. It does not contact a live model, obtain real human review, render a native BIE video or accept the product. Use a fresh output directory each time.

See `docs/section17/BATCH005_API_AND_INTEGRATION.md`, `docs/section17/NEXT_ACTION_SECTION17_AUDIT.md` and the continuation/gap ledger. No GitHub writes were attempted; Task028 remains paused.
