# BIE-QA-HARD-033 — Representative performance and aggregate memory

## Preserved registered scope
Measure actual native queues and render/browser process trees under declared workloads and platform profiles.

## Required closure evidence
- Fast incomplete outputs earn no throughput credit.
- Aggregate/cgroup or equivalent budgets and backpressure are tested.
- All submitted jobs, latency tails, retries and failures remain in workload accounting.

## Local implementation
Authoritative submitted-job and execution census, exact latency/throughput accounting and failed-output exclusion from throughput credit without excluding jobs. Actual cgroup-v2 child scope API reads back limits/counters and checks OOM; actual /proc group RSS is distinctly observational, not enforcement.

## Still required
- The cgroup filesystem is real but not delegated writable here; the attempted fresh group failed closed. No cgroup-constrained workload or aggregate enforcement success is claimed.
- The actual process-tree measurement is a sample, not a peak/enforcement guarantee. Workload verdict rows require an external approved output validator; production native queue benchmarks, backpressure and GPU accounting remain open.

## Trust, execution and acceptance
All generation/execution configuration is operator-owned, never taken from book instructions. Synthetic approvals are explicitly diagnostic. This task cannot issue a terminal production PASS and does not close the historical gap ledger. No GitHub, global continuation, Section15 or Codex/Android modification occurs.

## Verification
Shared suite: tests/qa_hardening_h7. Actual suite-qualified results: hardening/section16_h7/evidence/final_source_suites/TEST_RESULT.json. Selected mutation controls: hardening/section16_h7/evidence/mutations/MUTATION_RESULT.json. Diagnostics: hardening/section16_h7/evidence/diagnostics/EXECUTION_RESULT.json. Do not multiply shared tests across task packages.
