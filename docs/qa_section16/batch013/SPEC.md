# Section 16 Batch 013 — governed bounded repair foundation

Original registry page 18: BIE-QA-REPAIR-001 failure classifier;
BIE-QA-REPAIR-002 owner routing; BIE-QA-REPAIR-003 bounded repair.
Additive namespace: `bie/qa/repair_v2`. This is cumulative Section16 work,
not a replacement for the enterprise architecture, original source, Section15,
or a full repository. Domain-specific proposal generators remain subsequent tasks.

## Trust boundary and inputs

`Snapshot` declares immutable original artifact identities and exact bytes.
`FailureBatch` binds actual evaluator report files to the run, revision, snapshot,
task, request and evaluator policy. The existing SnapshotStore rereads their bytes;
canonical report fields, observed artifact IDs, freshness and derived status are
validated. Finding owner labels, free text and suggested fixes are untrusted data.
No instruction from a report becomes a command or broad filesystem permission.

An operator supplies a `RepairPolicy` with exact `(task_id, code)` rules, known
owner identities, exact owned generated-file paths, validator fingerprints and a
finite acyclic check graph. Unknown codes, uncertain findings, environment faults,
evidence faults, security and rights issues are not automatically content-repaired.
The small catalog is deliberately nonexhaustive; it is not a complete root-cause AI.
Reviewed inventory authority is required independently of a report's own PASS label.

A `Proposal` identifies the exact base, policy, plan, run and revision, target
failure identities, one owner, existing before-hashes and replacement blob artifacts.
Only explicitly owned paths under `generated/` may be replaced. No creation,
deletion, command execution, arbitrary patch syntax or edits of tests, source-role
artifacts, evidence, policy or canonical repository files are supported. No-op,
stale, tampered, missing or oversized replacements fail. All affected original
source and support bytes are checked. Proposal review is distinct from failure
inventory review and is purpose-scoped, current and externally keyed.

The existing ReviewVerifier is reused. No production secret, automatic signer or
live reviewer is included. Rejections, invalid signatures and test-only assurance
cannot be outvoted by positive supplied scores. Diagnostic positive reviews use
explicitly SYNTHETIC credentials and do not prove assessor quality.

## Classification and ownership

`classify(...)` produces stable failure identities and routes only exact policy
matches. A finding's guessed owner cannot override the approved owner. REVIEW
findings and unknown codes are not auto-repaired. `route_summary(...)` returns an
intent, not queue dispatch. Supported targets may be staged while other findings
remain unresolved, but all remaining failure identities persist in the receipt.
No hidden conversion from a staged subset into overall quality acceptance exists.

`check_closure(...)` invalidates the owner's affected checks and all declared
transitive dependents. It includes required global checks and prerequisite checks,
and produces deterministic topological order. Old evidence is explicitly unusable
for the changed candidate. This relies on a complete operator-governed graph;
canonical task-graph migration and proving all necessary dependencies remain open.

## Durable budgets and crashes

`Journal` binds a local SQLite transaction log to run, revision, snapshot and policy.
BEGIN IMMEDIATE serializes reservations. Hash-chained events retain attempts,
reserved replacement bytes and worst-case worker-time charges. Failed attempts are
not refunded. Retrying identical content under another proposal ID cannot evade the
effect guard. Duplicate requests, rollback clocks, parallel pending attempts,
exhausted attempt/byte/time budgets and terminal staged sessions are rejected.

Reservations are persisted before execution. A crash that leaves a reservation
unfinished blocks further automatic work and requires operator investigation; it
is never silently treated as success or reissued. There is no automatic crash
recovery API or distributed worker lease in this batch. The journal holds the file
inode open, rejects links and detects path replacement; the regression suite tests
unlink/recreate behavior and concurrent claims. Journal paths and their parents
must be private, stable, operator-owned directories. The chain is not a signature
against a privileged actor rewriting or truncating the database or deleting it
and creating a new session. Distributed durability and stronger storage trust are
explicitly open rather than claimed from local SQLite tests.

## Execution and candidate preservation

`execute(...)` reclassifies actual reports, validates approvals and the complete
proposal, confirms fingerprints for required registered callbacks, reserves budget,
then copies declared original bytes into a new private staging directory. It
substitutes only approved complete replacement blobs. No original file is written.
The staging file set must match exactly, including no unknown files or links.

Registered validators run in a separate POSIX process group with a hard overall
timeout and CPU/address-space/file/open-file limits. The registry accepts top-level
Python functions pinned by defining module bytes, function source, name and Python
version; it does not accept imports, commands or callbacks supplied in the proposal.
Transitive imports, external binaries and environment closure are not fully pinned.
Results cross the boundary as canonical JSON, not arbitrary pickled objects. The
supervisor verifies ordered check coverage, exact candidate/policy binding and
status, and terminates the process group on completion or timeout.

This is a resource-bounded trusted-validator worker, NOT a hostile-code filesystem
or network sandbox. The operator functions retain the user's process authority;
untrusted code must not be registered. Production namespaces/containers, network
restrictions, least privilege, secret separation and hostile generated-code workers
remain required. Resource limits alone do not establish those properties.

Every required check must PASS. FAIL, REVIEW, NOT_RUN, exceptions, timeouts, missing
results, state mutation, extra files and byte changes reject the proposal. Stage
bytes and original bytes are reread after execution. Rejected staging is discarded;
success is renamed to a separate candidate directory and marked STAGED_FOR_REVIEW.
The private output root must be disjoint from the original and have no untrusted
concurrent writers. A crash after rename but before final journal completion leaves
an unresolved attempt, not a publication. There is no in-place patch, merge,
repository push, task acceptance, deployment or production certification.

## Public paths and schemas

Python API: `classify`, `route_summary`, `check_closure`, `Journal`, `execute`.
The strict CLI is intentionally read-only; production key or executable provisioning
must not be smuggled through a JSON request:

```sh
python -B -m bie.qa.repair_v2 --snapshot snapshot.json --batch failure_batch.json \
  --policy policy.json --artifact-root artifacts --as-of 1790485200 --output report.json
```

Read-only CLI exit: 3 when review is required, 2 on invalid input, 4 if the exclusive
output already exists. A default invocation does not fabricate review authority.
Six structural JSON schemas accompany Snapshot, FailureBatch, RepairPolicy,
Proposal, CheckOutcome and Review. Runtime contract/semantic validation remains
mandatory; schema conformance alone is not acceptance.

`adapters.bind_report` consumes actual existing Report objects. The narrow native
AUDIO invalidation-receipt adapter was based on read-only inspection at a68e054.
It checks declared node/status scope, not native runtime, actual queue dispatch or
complete canonical provenance. No native dependency was vendored or executed.

The release bridge rereads the staged candidate, validates receipt/hash bindings
and emits unsigned NOT_RUN evidence for the full regression gate. It does not turn
bounded checks into full canonical regression. The existing ReleaseEvaluator is
actually exercised in tests and keeps the incomplete release BLOCKED.

## Executed verification and reproducibility

```sh
python -B scripts/verify_qa_repair16_batch013.py --output /tmp/new-qa16-run
python -B scripts/verify_qa_repair16_mutations.py --output /tmp/new-mutation-run
python -B scripts/verify_qa_repair16_execution.py --output /tmp/new-repair-demo
python -B scripts/verify_qa_section16_package.py
```

Use fresh output directories outside the frozen payload. Python bytecode files are
not allowed to silently change its manifest. The runner isolates inherited test
modules; new tests and cumulative tests are not counted again for atomic ZIP copies.
The shared pipeline executes actual arithmetic checks and actual staging/SQLite
operations on authored fixtures. Its proposed fixes are manually specified; no live
LLM, autonomous subject-domain repair or native video/game repair was executed.

Executed unit counts, names, hashes, logs, selected mutation results, diagnostic
cases and parent-byte preservation are under evidence/qa_section16. The external
DELIVERY.json records final archive extraction, shared regression, atomic payload
identity, corruption rejection and same-input ZIP reconstruction after freeze.
Same-input archive reconstruction is not cross-platform semantic reproducibility.

## Continuing obligations

Original REPAIR004-011 domain-specific workers, REPAIR012 repair evidence and
REPAIR013 broader repair regression still follow this foundation. Production
orchestration, canonical dispatch, independent review quality, complete dependency
invalidation, real-book E2E and all prior native render/game/learning gaps remain.
Section15, Codex/Android, global continuation and GitHub are not changed here.
