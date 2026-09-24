# AUDIO H4-R1 recovery contracts

## Continuity, identity and scope
This source extends the byte-verified H3 Integrated archive, checkpoint
BIE-AUDIO-H3-005. The prior record documents H4-005, but its original bytes were
not available. These five tasks are a new, clearly labelled recovery revision
mapped to that documented capability list. No claim of source identity to the
original H4, or of reproducing all undisclosed original design decisions, is made.
No original Python source or test is overwritten. Changed root metadata and the
consolidated gap ledger have exact pre-change copies in lineage/audio_h4r1.

The full BIE book-to-learning-experience pipeline, provenance, reusable memory,
regression gates and downstream real-book/compile/render/game acceptance remain
the target. This batch implements one bounded diagnostic lane, not a smaller
replacement product, new orchestrator or alternative runtime architecture.

## H4-R1-001: selected execution profile
Eight compiler-worker modules are copied unchanged from the pinned canonical
repository commit 16d4d87824e77db3565a231a332e7977d39d7117. Git blob SHA-1 identities
are independently verified in addition to payload SHA-256. Existing ten pinned
DIR/core/store dependencies remain unchanged. These are standalone dependency
fixtures; do not overwrite a newer canonical repository with them.

Profile discovery hashes the selected kernel modules, fixed acoustic engine,
H4-R1 adapter, interpreter, unshare, and the original independently verified
acoustic runtime/model inputs. The profile includes Linux kernel release,
machine and resource policy. Discovery cannot authorize a profile: an externally
configured kernel trust document must explicitly approve its fingerprint and
its issuer. Runtime/profile/code changes require review and a new approval.
No installation, automatic model download, profile self-approval or signer
bootstrap is performed by the operational CLI.

Selected identities are not an attestation of the whole OS, dynamic loader,
all system libraries, hardware or an adversarial host. The service account,
canonical import paths, approved code and host controls are trusted. Source
hashes cannot establish hostile-host integrity. Root compromise, concurrent
same-account malicious code mutation and native exploit proof are outside this
claim. Read-only system runtime mounts are intentionally broader than an
individually allowlisted shared-library set.

## H4-R1-002: fixed operation
The public acoustic adapter takes a validated job, exact WAV bytes, approved
runtime/profile and optional cancellation event. It accepts no arbitrary command,
working directory, shell string, arbitrary import or caller-produced measurement.
A fresh 256-bit nonce binds the fixed request/result. Only measurement code and
its declared imports are staged read-only; private signing keys, durable stores,
source repositories and tests are not mounted in the workload.

The existing canonical worker provides private user/mount/network/PID namespaces,
no host procfs, private loopback without an external route, read-only workspace
and engine with one declared writable output directory, capability drop,
no-new-privileges, seccomp and resource limits. No replacement worker is added.
Policy: at most two concurrent jobs by default, 300 CPU seconds per process,
768 MiB address space, 8 MB per output file, 128 descriptors, 64 process limit,
128 MiB tmpfs, 1 MB captured process output and 4 MB result JSON. Existing job
wall-time, segment, media, duration and word budgets still apply. The namespace
launcher documents per-process/UID limits; these are not cgroup aggregate RSS,
CPU, process-fleet or whole-book throughput guarantees.

Only result.json, native.log and exact.fsg may appear in the output. Result files
must be bounded regular single-link files; symlinks/hardlinks, unknown files,
wrong operation/nonce, changed inputs/engine, failed process, cancellation,
missing policy proof or selected-source/runtime drift fail closed. No H2 local
worker fallback is allowed. Logs/native grammar are not published as acoustic
results. Cancellation and heartbeat control are cooperative host-side controls;
immutable orphan artifacts can remain after cancellation/crash before commit.

## H4-R1-003: authenticated v2 evidence
The original H2 measurement is unchanged: legacy English constrained word FSG,
unconstrained all-phone and N-gram searches are independent diagnostics, not
phonetic truth or a calibrated pronunciation grade. Unsupported Hindi, code
switching, phonetic overrides and OOV cases remain explicit. A real isolated
process executing an unsupported language does not turn it into supported audio.

The v2 Ed25519 domain is separate from H2. Its signed payload binds the approved
profile, selected runtime, exact job/media, nonce/request/result hashes, native
kernel proof, host/child namespace identities, process outcome, compatibility
receipt and, for durable requests, the complete canonical request fingerprint.
Export relabelling of run/job/revision cannot reuse that signature. The embedded
signed v1 receipt serves existing QA only. It alone never establishes isolation.

Verification uses current configured trust, not trust embedded by the claimant.
It rejects revocation, expiry, future issue times, unapproved profiles/runtimes,
wrong signatures/schemas, changed source, replayed execution hashes, extra fields,
boolean/integer ambiguity in critical evidence and acceptance inflation.
Private keys are explicitly supplied through the inherited protected 0600 local
key loader, never generated or exposed by the production CLI, and never mounted
inside the child. Signatures authenticate an authorized service's assertion;
they do not prove that an authorized malicious signer or host is honest.

## H4-R1-004: canonical persistence and recovery
The original H3 durable request schema and implementation remain unchanged.
Its policy revision incorporates the base durable policy and approved profile.
This prevents legacy H3 requests or another profile silently aliasing the same
run/job/revision. A changed request requires explicit revision handling; no
silent overwriting or cross-context cache reuse occurs.

The original three-envelope chain is preserved: declared source provenance,
request and signed acoustic evaluation. A fourth canonical kernel-evaluation
envelope points to the original evaluation and retains its provenance summary.
Both graph and media hashes, exact request/profile, inner/outer receipt equality
and current signatures are reverified on load and immediately before completion.
Source declarations imported from H3 are not a newly verified real PDF or a full
canonical DIR artifact handoff. Durable artifacts are local to a single trusted
service account with cooperative filesystem/SQLite locking.

The existing DirectorLeaseStore and SQLiteIdempotencyStore remain the queue/fence
mechanisms. The adapter adds outer v2 verification at the existing completion
transition. Stale/expired owners cannot commit. A claim-complete/lease-incomplete
crash is recovered after reauthentication. An interrupted native operation can
be retried at least once, not exactly once. Garbage collection, uncertain paid
provider reconciliation, distributed fleet recovery, all AUDIO operation types,
repair dispatch and bounded book-scene scheduling remain open.

## H4-R1-005: CLI, publication and evidence
`audio_kernel.py evaluate` requires explicit diagnostic opt-in and disjoint input,
output, store, runtime, profile, trust and key paths. Configuration is bounded;
symlinked paths, existing output and missing authority block execution. `probe-profile`
discovers but never approves. `inspect` is storage inspection only and may create
an empty local catalog under its explicitly requested store; it is not evidence
of acoustic/signature/section acceptance.

Exports contain the original acoustic/QA publication plus signed kernel receipt,
approved profile and canonical request, under an exact bounded SHA-256 inventory.
Both outer signature and inherited derived QA/captions reverify before atomic
promotion. Rehashed manifests alone cannot authorize a changed receipt or request.
The exported receipt expires and revocation remains effective after publication.
A stale benchmark's ephemeral trust/key must never be reused for production.

Operational diagnostic CLI exit 3 means REVIEW and exit 2 means blocked or a
non-passing diagnostic QA result. A signed unsupported-language export may exist
with exit 2; inspect the explicit QA and status, not just the presence of a file.
Exit 0 is used only for profile discovery or storage inspection. There is no
section/product acceptance exit path. The synthetic benchmark's exit 0 means
its declared expected pass/block/review checks passed, not that all audio passed.

## Retained acceptance gates
No live neural provider, independent human listening, held-out phoneme/word
calibration, production key custody/deployment, real textbook, real DIR/ANI/COMP
handoff, actual Remotion render, frame inspection, revision-game runtime or full
enterprise regression is established by this AUDIO package. F01, F02, wider F03
and F04 remain explicit. GitHub and the separate Codex workflow are unchanged.
