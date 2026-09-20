# BIE COMP original Batch 009 — QA-001..005

Date: 2026-09-18. Status: IMPLEMENTED AND LOCALLY TESTED; COMP IN PROGRESS; NOT ACCEPTED.

## Delivery

This continues the exact uploaded Batch 008 workspace. All 288 inherited Python files remain byte-for-byte unchanged. Before current metadata updates, all 388 original members matched; their hashes and parent archive identity are recorded in `lineage/BATCH_008_PRESERVATION.json`. Original current-manifest/continuation/checksum files were copied into lineage before replacement. New code adds QA and uses actual earlier code generators rather than a replacement simplified compiler.

| Original atomic task | Capability | Tests |
|---|---|---:|
| BIE-COMP-QA-001 | Content-bound compile diagnostics to Scene IR/source references | 29 |
| BIE-COMP-QA-002 | Applied capability fallback/source/accessibility and semantic-loss checks | 34 |
| BIE-COMP-QA-003 | Exact generated output determinism, including fresh processes | 28 |
| BIE-COMP-QA-004 | Immutable generated-source goldens, real TS AST and strict compile gates | 38 |
| BIE-COMP-QA-005 | Executable provenance-bound multi-domain source/compile benchmark | 25 |

154 new atomic tests and 16 integration tests were added. The restored 751 tests reran and the cumulative DSL+COMP regression passed 921/921, with no failures, errors or skips. These are not full-enterprise test totals.

## Actual benchmark and tool execution

The final benchmark matches 19/19 source expectations over ten domains: ten positive source passes and nine expected semantic/security defect rejections. All cases repeat identically in three independent processes (57 generator workers). Actual inherited emitters and the real installed TypeScript AST parser are used. Self-contained real TypeScript positive/negative tests exercise strict checking and real source-diagnostic mapping; no generated BIE Remotion project is thereby claimed fully typechecked.

Domains: mathematics, physics, chemistry, biology, statistics, economics, accountancy, history, geography and engineering. These are synthetic technical fixtures, NOT textbooks, comprehensive subject packs, scientific/medical validation or educational acceptance. Source timing/size is measured, not render performance.

The runner exited 2: source expectations matched, but no full generated-project compile was verified. All 19 projects have BLOCKED_DEPENDENCIES. Global TypeScript is 5.8.3; the generated target remains TypeScript 5.9.3, React 19.0.0 and Remotion 4.0.506. The registry probe again failed with EAI_AGAIN. No successful real Remotion composition discovery, smoke render, full render or frame inspection is claimed.

The preliminary run interrupted by the tool timeout is retained and marked aborted; only `benchmark_final` and its completed process receipt are used for benchmark conclusions.

## Material audit result

**Tests pass because negative fixtures are correctly rejected; the underlying emitter defects are NOT fixed.** The new QA flags chart-kind downgrade, signed-chart loss, dropped vector z-components, raw requested equation typesetting, literal text entering JSX execution, state-only simulations, metadata-only animation, unverified geographic projection and invalid model edges.

See `docs/COMP_BATCH_009_CAPABILITY_AUDIT.md` for each reproduction and closure requirement. The new QA adapter must be properly adopted by production paths; it does not silently modify all existing compiler entry points. This batch intentionally keeps emitter source intact and supplies evidence for governed hardening.

## Reproduce

```bash
PYTHONPATH=app python -m unittest discover -s tests -v
python scripts/run_compiler_qa.py --output /tmp/bie-comp-qa-new-run
```

The benchmark uses fresh output directories, reads immutable goldens and does not install npm dependencies or modify the canonical repository. Exit 2 is expected while full compile prerequisites remain absent. Missing tools/dependencies are not substituted with mock success. Existing Batch 008 rendering limitations remain in force.

## Continuation

Latest completed original task: BIE-COMP-QA-005. Next action: COMP capability audit and governed hardening based on the delivered open findings. No next original task number is invented. No automatic move to the next section or product acceptance is permitted.

There was no GitHub write, commit or integration. Real-book upstream/downstream E2E, actual video/audio/frame checks, playable games, expert/learner evidence and enterprise/product acceptance remain open. ZIP/member checksums and fresh-extraction results are in the final verification artifacts.
