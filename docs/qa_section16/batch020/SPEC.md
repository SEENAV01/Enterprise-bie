# Batch020 — generated-code security and sandbox escape tests

## Original tasks and preservation
Original registry page18: BIE-QA-SEC-001 generated-code security; BIE-QA-SEC-002 sandbox
escape tests. This is an additive `bie/qa/security_v2` implementation on exact Batch019
bytes. All 5,934 parent file records are preserved; six superseded root metadata files
are archived under `history/section16_batch019`. No native repository file, Section15,
global continuation or Codex/Android code is changed. Local task scope is not acceptance.

## Threat model and trust boundary
Candidate code, metadata and execution reports are untrusted. Operator policy and
reviewer keys are supplied separately. The snapshot's artifact names, roles, hashes
and sizes are fixed before inspection. Byte changes, unsafe paths, links, extra files,
missing executables or a policy/candidate mismatch block the checks. Code and evidence
are read using existing SnapshotStore and exact snapshot verification.

The trusted computing base includes this evaluator, its authenticated-review adapter,
the operator-pinned Python/Node/TypeScript parser, and the underlying OS/kernel. A
forged report with a valid hash is not independently measured execution. An operational
reviewer's signature establishes provenance, not immunity from error or maliciousness.
No built-in credential grants authority; all positive credentials in tests are synthetic.

## SEC-001 — implemented static inspection
Python uses its real AST parser. The PURE profile admits a deliberately narrow
arithmetic/data/function subset, rejecting imports, attributes, decorators, loops,
comprehensions, arbitrary calls and dynamic execution. General Python remains review-
required. Capability names/imports and indirect access are conservative findings.

TypeScript/JavaScript/TSX uses the installed, hash-pinned TypeScript compiler parser in
a separate bounded process. Candidate text is supplied on stdin and never evaluated.
Escaped identifiers are inspected as parsed names. Dynamic import, dynamic construction,
process/network capabilities, prototype access and active HTML sinks are detected.
The DATA profile permits exported const literal structures; unknown executable nodes
fail closed. Broad application code remains review-required even after a clean scan.

Actual package.json bytes are read with duplicate-key rejection. Scripts must exactly
match operator declarations, versions must exactly match pinned dependency records,
and dependency artifact bytes must be present. Approved scripts still need isolation.
This is NOT transitive dependency scanning or an up-to-date vulnerability-feed service.

Relative imports must resolve uniquely to inspected code units; external module names
must be declared. HTML/SVG/CSS/native/script artifacts cannot be silently omitted from
executable inventory. Unsupported languages require a new governed adapter, not relabeling
as inert data. Language-to-path binding is enforced.

## SEC-002 — actual, fixed boundary probes
The collector creates disposable input/output trees and a synthetic outside canary.
It invokes ONLY the bundled trusted Python helper in a new process, with no candidate
code import, callback, shell command or exploit payload. This Linux x86_64 profile needs
a permitted root bootstrap; unsupported environments return NOT_RUN/BLOCKED.

In the child, setup tightens the current environment: private chroot and cwd, empty
supplementary groups, real/effective/saved UID/GID drop, measured zero capabilities,
no_new_privs, closed inherited descriptors, empty environment, finite resource limits,
and a seccomp default-deny filter with an x86_64 architecture check. The diagnostic
has no proc/dev mounts or runtime dependencies inside the root. Only narrow filesystem,
memory, signal and reporting syscalls are permitted; control-changing prctl requests,
network, fork/exec, namespaces and ptrace are denied. No parent control is relaxed.

Three fresh workers execute 18 observations: allowed input/output positive controls;
outside read/write; parent traversal; a link targeting the synthetic outside canary;
closed FD and clean environment checks; IPv4/IPv6/Unix socket denial; process spawn,
exec, privilege change, namespace and ptrace denial; file-size and FD-count limits.
No packet is sent and no real credential/file outside the disposable fixtures is read.
CPU/memory limits are installed and recorded, but stress exhaustion of those two limits
is NOT claimed; explicit file and descriptor exhaustion are exercised.

Returned receipts include logs, hashes, separate process IDs, nonces, controls and
probe observations. The evaluator checks their actual bytes, freshness, coverage,
unique identities, log/child equality, worker identity and expected outcomes/errno.
A supplied `passed=true` cannot replace a missing control or failed positive control.
Only diagnostic fixed-probe execution is recognized: `candidate_executed=true` is an
overclaim for this schema. Reused/mismatched records fail closed.

## What this does not establish
These tests are not a hostile-code runner API, general kernel exploit suite, proof of
absence of vulnerabilities, or certification of Python/Node/browser isolation. Chroot
and seccomp are not considered sufficient in isolation. Production workers still need
independently reviewed bootstrap, cgroup/namespace/container/resource policies, actual
native producer integration, operational attestation and broad adversarial evaluation.
Runtime/interpreter vulnerabilities, side channels, dependency behavior, native addons,
whole-program taint analysis and complete React/Remotion/game support remain open.

Healthy unsigned results require review. Even synthetic operational approvals cannot
turn these fixed probes into proof of native candidate execution. The release bridge
emits unsigned FAIL or NOT_RUN, never PASS for the full enterprise security gate.

## Execution evidence and packaging
154 new tests and 3,091 inherited tests passed. Fifteen targeted evaluator guard-removal
probes were detected with passing controls; the sandbox worker was never weakened.
Nine authored diagnostics include one real three-worker/18-observation boundary run,
static parsing cases, and four separately labeled evidence-only rechecks. Generated
programs executed: zero. The complete release evaluator was exercised and remains blocked.

The initial new tests exposed adapter mistakes: an optional receipt needed a narrow
codec wrapper and test code used incorrect inherited envelope field names. Those were
corrected without changing inherited APIs. Active-file inventory and language binding
were strengthened before final regression. Earlier results are retained in development/.
A rejected streaming-tool invocation did not execute. The final runner uses bounded
parallel independent suite processes to avoid redundant historical wrapper execution.

Source ZIP reproducibility means identical bytes from the same frozen inputs in this
environment, not universal cross-platform execution or signed publisher identity.
Atomic ZIPs share one tested cumulative payload; repeat counts are not multiplied.
The compact backup includes exact Batch019 Integrated plus current packages and records,
not a recursively duplicated archive of every older Master Backup. No fonts are bundled.

## Primary technical references consulted
- Linux kernel documentation, Seccomp BPF: https://docs.kernel.org/userspace-api/seccomp_filter.html
- Node.js permissions documentation: https://nodejs.org/api/permissions.html
- Node.js VM documentation: https://nodejs.org/api/vm.html
Consulted during this batch. The Node documentation explicitly warns that its permission
model is not protection against malicious code; this batch does not substitute Node VM
or API permission flags for an OS isolation claim. Kernel documentation supplies the
architecture/filter guidance, not a certification of this implementation.

## Next original entries
BIE-QA-PERF-001 render performance; BIE-QA-PERF-002 memory limits;
BIE-QA-PERF-003 queue throughput. Then REL001–004 and full-section audit, material
hardening, re-audit, governed canonical integration and real-book end-to-end proof.
