# Evidence index

- BASELINE_REGRESSION.txt: actual unchanged parent, 751 tests.
- CUMULATIVE_REGRESSION.txt: actual current full suite, 921 tests.
- QA_00x_TEST_RESULT.txt: final individual task execution logs.
- TEST_SUMMARY.json: reconciled scope/counts, not product acceptance.
- ENVIRONMENT.json and NPM_REGISTRY_PROBE.txt: observed tools and dependency block.
- benchmark_final/BENCHMARK_RESULT.json: completed 19-case source benchmark; full compile false.
- BENCHMARK_PROCESS_RESULT.json: actual exit 2; expected incomplete full-compile gate.
- benchmark_final/<case>/: original fixture, generated project, contract/source maps, real AST, snapshots and diagnostic receipts.
- benchmark_preliminary/RUN_ABORTED.json: incomplete exploratory invocation, not a successful final benchmark.
- PACKAGE_VERIFICATION.json (external/master): tests rerun from fresh delivery ZIP extraction.

Earlier-development test logs are retained for traceability and are not additional independent test totals.
