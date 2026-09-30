# BIE-EVAL-NATIVE-QA-001 — Real Section17 / canonical QA component bridge

## Motivation and scope

H5 explicitly leaves native/Section16 adoption open and forbids manufactured
wrapper task IDs. Live read-only inspection now observes Section16 QA on main
at `8b8e500bf7b83addfcecce41c3fca08563eceb41`. This task executes its actual
content-bound QA consumer, not the older metadata-only release contract.
The new task ID is an additional implementation task, not original registry text.

## Data and call flow

1. Verify the ten installed QA module files against operator-controlled pinned
   identities before and after execution. Importing code is trusted provisioning,
   not an untrusted-code sandbox.
2. Accept only a native frozen ReleaseCandidate at the pinned revision, fixed
   enterprise policy identity, exact check-plan identity and trusted Limits.
3. Require exactly the three versioned AV metric checks (012, 013, 015). Validate
   each reference/candidate hash, enforce one fully covered video, and bind media
   and captions to native paths, roles, sizes and SHA256 values.
4. Capture every native candidate artifact once into an isolated temporary
   directory. Stream bytes, check size/hash/stat changes, reject symlinks,
   hardlinks, replacements, file-directory collisions and ambiguous subjects.
5. Execute existing real AV collectors against private snapshots. Preserve
   negative reports and unavailable-execution outcomes.
6. Write exact report bytes and construct unsigned native GateEvidence for the
   benchmark gate. Status is NOT_RUN for three technical passes (full benchmark
   incomplete), FAIL for a detected defect, ERROR for blocked collection.
7. Invoke canonical ReleaseEvaluator with its deny-by-default verifier. Native
   artifact checks read actual bytes and the report hash; all enterprise gates
   remain required. No score, signature, approval or publication is manufactured.
8. Serialize native output through its own `to_bytes` wire serializer, not the
   tuple-bearing internal `to_dict`. CLI exports exact report/envelope/QA output
   to a fresh directory and binds those files with a receipt manifest.

## Trust and limits

The operator owns Python dependencies, filesystem parents, resource budgets and
external tool selection. File pinning after import cannot defend against a
hostile Python runtime. Input-parent immutability, OS/container/network isolation,
key provisioning, operator identity and deployment are separate responsibilities.
The command never bypasses managed browser restrictions.

The native candidate still requires source, video and game roles. Source/game
files here are byte-inspected only. No false assertion of source understanding,
playability, educational alignment or learning gain is made. Only one video is
supported by this slice; extra videos fail explicit coverage checks.
The native 256 MiB per-file / 2 GiB candidate caps are unchanged. CLI bounded
request files and explicit limits are validated; inputs cannot inject evidence,
verifiers, signatures, policies that relax mandatory gates or supplied PASS flags.
The fresh-directory CLI does not replace campaign scheduling or anti-retry ledgers.

## Acceptance of this task

Actual collectors, actual current-pinned QA consumer, retained positive/negative
fixtures, hash readback, CLI blocked exit semantics, 51 new tests and reversible
fault controls are required. Full canonical application integration, repository
regression and a book-to-BIE/Remotion/game execution remain out of this local
acceptance scope. This task never sets release_authorized/product_accepted true.
