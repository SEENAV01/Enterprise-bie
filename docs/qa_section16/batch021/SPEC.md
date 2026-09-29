# Batch021 specification — PERF001..003

## Governed scope
Original registry page18: render performance, memory limits, queue throughput.
Additive namespace `bie/qa/performance_v2`; preserved Batches001–020 are unchanged
except six root checkpoint metadata files, whose original bytes are archived.
This is local Section16 continuation, not canonical GitHub integration. Section15
is externally managed and not changed or reaccepted by these checks.

## Data and authority
`PerformancePolicy` is independently provisioned. It binds an exact source Snapshot,
all expected job IDs/producer IDs/inputs/outputs, producer configuration fingerprints,
a selected environment fingerprint, concurrency, deadlines and resource thresholds.
`PerformanceRequest` binds byte-identified execution, log, limit and output artifacts.
No request/receipt JSON can supply a callable or automatically execute a command.
Only an explicit trusted Python-side `Producer` registry is used by `collect()`.
Changing the input, recipe, frame count or policy changes those identities. No receipt
PASS label or confidence score overrides recomputed failures. Current inventory and
execution reviews require separate purpose-scoped operator credentials. Authentication
is not proof that an assessor or measurement service is honest or calibrated.

## PERF001: render performance
The collector executes approved binaries in fresh private working directories with
verified input copies. A separate Python launcher installs and reads back limits,
then execs the approved program in the same PID. Parent monotonic_ns clocks bracket
supervised execution (including launcher and log-drain/polling overhead); this is not
pure encoder CPU time. Integer nanoseconds do not imply nanosecond physical precision.

MP4 output is independently reopened with the preserved FFprobe/FFmpeg decoder. Known
width, height, complete frame count, frame rate and every decoded presentation step
must match the workload. BYTES outputs require an independently supplied golden hash.
The configured MP4 checks do not establish complete scene fidelity, scientific accuracy
or cinematic quality. FPS uses verified frame count divided by supervised wall time.
Partial/invalid/failed outputs never earn throughput-success credit. All required jobs,
including failed and slow ones, remain in the report and time window.

## PERF002: memory limits
Linux wait4 returns per-job resource usage after reaping. ru_maxrss is converted from
Linux KiB to bytes and recorded explicitly as a high-water metric, NOT summed to invent
a simultaneous worker-tree peak. User/system CPU figures are recorded as rounded
integer nanoseconds from the OS accounting values. Peak RSS budget failures block.

RLIMIT_AS imposes per-process virtual-address-space limits; it is not an RSS cap,
cgroup memory.max or GPU budget. A fixed benign child tests a successful1MiB mapping
and a denied anonymous mapping above the installed hard address-space ceiling. The
negative probe fails before host-sized memory is touched. Every job's limit readback
is bound to its execution ID and checked. File/output budgets and duplicate evidence
checks also apply. Distributed/container aggregate memory, descendants/GPU allocation,
OOM recovery and production isolation remain open. The trusted job launcher is NOT a
hostile-code sandbox and does not prove that a privileged/malicious child cannot alter
its execution environment. Canonical isolated workers must be integrated separately.

## PERF003: finite queue throughput
All prescribed jobs are admitted as one finite batch. A bounded local thread-pool
supervises at most the approved concurrent job count. Each job records enqueue,
dispatch, process start/end and completion after output verification. Intervals are
half-open for concurrency; touching boundaries do not count as overlap.

Queue waiting time = dispatch - enqueue.
End-to-end latency = completion - enqueue.
Service latency = completion - dispatch (includes private-copy setup/output checks).
Batch makespan = last completion - first enqueue; the separate memory probe is excluded.
Verified jobs/second = count of technically verified outputs/jobs / batch makespan.
P95 is nearest-rank ceil(0.95*n) across ALL job observations, not an interpolated value
or confidence interval. Failed jobs are not dropped to inflate the rate. Empty,
missing, duplicated, replayed or mismatched job sets fail closed. This finite drain
rate is NOT distributed steady-state broker throughput, a representative workload
benchmark, durable retries, fairness, crash recovery or an autoscaling result.

## Execution and limits
Linux and operator-installed FFmpeg/FFprobe are required for the collector/media
checks. No package installation occurs. Only trusted producers are executed; no shell
string expansion or network fetching is performed by the collector. This does not
impose a network sandbox on independently supplied programs. Limits:1–16 jobs,
1–4 workers,4 outputs/job, bounded16MiB artifacts inherited from SnapshotStore,
64MiB store budget,64MiB decoded RGB profile. Long/high-resolution native rendering
needs streaming/chunked evidence and production worker integration.

## Run
```sh
PYTHONDONTWRITEBYTECODE=1 python -B scripts/verify_qa_performance21_batch021.py --output /tmp/bie-qa021-tests --workers 3
PYTHONDONTWRITEBYTECODE=1 python -B scripts/verify_qa_performance21_execution.py --output /tmp/bie-perf021-diagnostics
```
Use new output directories. Audit an existing, byte-bound receipt without executing
its producer:
```sh
python -B -m bie.qa.performance_v2 request.json policy.json --root /path/to/artifacts --as-of 1234567890 --output /new/report.json
```
The explicit as-of clock supports replay; production must provision it independently.
The default CLI has no trusted assessor keys. Exit3 means review required, exit2 means
blocked checks, exit4 means input/output error. Existing output is never overwritten.
Schema documents validate structure; Python contracts/evaluator enforce cross-field,
byte, resource and semantic constraints. Wire decoding rejects unknown fields/types.

## Release boundary and verification
The bridge uses the existing `performance` release gate. It emits unsigned FAIL for
blocked checks and NOT_RUN otherwise, never full native-performance PASS. The full
existing release evaluator remains blocked. Same-host diagnostic success is not
native Remotion/game quality, canonical queue adoption or enterprise acceptance.

See the exact test IDs and hashes in executed_run_021/suites/TEST_RESULT.json, targeted
mutations/MUTATION_RESULT.json and diagnostics/EXECUTION_RESULT.json. Positive unit
review credentials are synthetic. The nine actual diagnostics use NO positive
assessor approvals; they remain blocked or review-required. Same frozen-input ZIP
reconstruction is separate from runtime performance reproducibility.

## Primary technical references
These references define API/accounting boundaries, not BIE acceptance criteria:
- Python resource: https://docs.python.org/3/library/resource.html
- Python monotonic clocks: https://docs.python.org/3/library/time.html
- Python wait4: https://docs.python.org/3/library/os.html#os.wait4
- Linux cgroup v2: https://docs.kernel.org/admin-guide/cgroup-v2.html
No cgroup setup or whole-OS reproduction was performed in this batch.
