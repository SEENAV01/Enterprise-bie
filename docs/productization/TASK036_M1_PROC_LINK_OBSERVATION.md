# M1 proc-link observation — diagnostic only

Parent source: `f192ceb1cb92c111e7f081afc834d4f630b0d11c`, tree
`6b53cb970c4923e3877ce669b5f514d77ff14837`.

The two current M1 matrices each passed seven of eight render cases, not a
combined passing matrix. The PR chronology/reduced and push cellular_reduced/
reduced cases failed with `CHROMIUM_RESOURCE_FAILED`. Their authenticated parent
observations identify `PermissionError` at the pinned worker's shared
`MONITOR_EXE_OR_ROOT_LINK` expression. They do not establish why access failed,
which link failed, or whether the process was live. No timeout, OOM, PID exhaustion,
successful cleanup or historical root cause is inferred from missing evidence.

This test-only observation answers a bounded question on the next candidate:
which exact monitor link rejected, and what a newly acquired process-level pidfd
reports in a nonblocking sample after that original rejection. It authenticates
the original worker bytes, code, actual frame type, caller namespace and line;
captures the native frame reader and native
pidfd-open/close/poll bindings; and delegates the original readlink exactly once.
It returns the identical result or rethrows the identical original exception.
Observation failures cannot turn rejection into success. The original worker,
painter, H3 caller, owner supervisor, workflow and amendment seals are unchanged.

The closed schema is `bie.task036.m1.proc-link-identity-observation/1`. Only fixed
provenance, availability/reason, source identity and bounded EXE/ROOT, errno-code
and boolean-or-UNKNOWN acquisition/terminal/close fields are retained. No PID,
descriptor, proc path, frame contents, exception message, receipt, stdout/stderr,
command, grants or mappings are retained or exported. Existing private receipt
TOO_LARGE/INVALID states remain independent and unchanged.

The pidfd/path association is **non-atomic**. Termination describes the acquired
fd's referent at sampling time; numeric PID reuse or intervening state changes are
not excluded. This is not proof that the denied pathname referred to a terminal
process, cgroup ancestry, admission, final process outcome or cleanup. No skip,
grant, retry, wait, signal, resource widening or native repair is implemented.
Readonly syscalls and temporary binding introduce nonzero overhead; absolute
timing/concurrency noninterference is not claimed. The existing wrapper is a
bounded, single-worker test process, not a production instrumentation interface.

New controls are explicitly split between synthetic privacy/noninterference
tests and mandatory Linux kernel tests. The latter check native API binding
authentication, a live nondumpable child, and a dead thread-group leader with a
remaining live thread. These are kernel fixtures, not browser/render witnesses.
They are NOT_RUN on the local Windows host and must execute in the governed
hosted NEW lane without skips. The new module is assigned once to NEW; the native
214-file discovery and all previous logical identities remain unchanged.

The independent reviewer requested caller-namespace and captured-native-API
provenance fixes; both were implemented, with negative controls. This note is
not a review approval. Current M1 render failures and Scene review/source binding
failures remain open pending actual candidate execution and independent review.
Historical records and sealed source identities are not overwritten.

All existing execution limits and isolation policies remain unchanged, including
45-second product child, 600-second owner, 192-second 48-frame worker, 30-second
shot, 20-minute render job, 2-GiB physical memory, zero swap and 128 PIDs.

Task035's bounded sign-off stands. M1 and Task036 are not complete. Audio remains
OPEN; AUDIO_REPLAN_REQUIRED is fail-closed. Review and acceptance flags are not
promoted. No global VIDEO_CODE/COMPILE/RENDER, product acceptance or Task037 is
claimed by diagnostic kernel fixtures or native M1 fixture rendering.
