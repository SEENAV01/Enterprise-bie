# BIE-PROD-031 — governed Math evidence and graph reconciliation

Explicit new continuation decision after canonical Task030. Base
`b9b65f423355b0856182b9f0e5c23cbff08e890b`, tree
`4ce6d36e7ccf5a24fed2b3e2219c6c2441c37deb`. Implementation is not integration
or product/academic acceptance. Full canonical Linux validation is required.

## Versioned composition

`source_grounded_di_knowledge_pr_math_reasoning_v1` executes exactly SOURCE,
DOCUMENT_INTELLIGENCE, KNOWLEDGE, PREREQUISITE, MATH and REASONING.
`math.evidence` has private schema `bie.math.evidence/1`.

The default enterprise graph now requires document.structured, knowledge.graph
and prerequisite.graph for MATH, and knowledge.graph, prerequisite.graph and
math.evidence for REASONING. Explicit anti-bypass checks reject missing Math,
altered Math input/output contracts and direct pre-Math paths into Reasoning.
All previous source/IR/release anti-bypass controls remain active.

The exact prior canonical graph is preserved in execution_graph_v1.py. Task029
and Task030 explicitly pin that factory. Their schemas, intent fingerprints,
capabilities and three/five-stage scopes do not silently gain Math. Task030
still blocks math-dependent Reasoning with math_evidence_required. The one old
Task030 test asserting globally absent Math now checks its pinned legacy graph:
this is an authorized architecture migration, not removal of its negative gate.
Persisted dependency/scope drift is rejected before worker admission.

Fresh Task031 admission is explicit. It cannot overwrite an old incompatible
tenant/key intent or silently promote an old persisted run. Task030's explicit
Task029 continuation remains supported unchanged. New interpretations require
a separate governed intent/revision, not reinterpretation of historical outputs.

## Bounded source-grounded Math

The producer reads FULL actual native DI block text, never prefilled equations.
It checks every extracted block and preserves the complete source inventory.
Applicability is REQUIRED, NOT_REQUIRED or REVIEW_REQUIRED. NOT_REQUIRED still
produces a verified persisted Math artifact, source/page/block inventory, hashes,
upstream identities, policy and evaluator identity. It is a technical syntactic
scope finding, NOT a semantic assertion that an arbitrary book has no implicit
mathematics, and cannot waive Section16 release/academic review gates.

Accepted grammar is deliberately narrow:

- Complete native display equalities of bounded exact rational arithmetic.
- Rational-polynomial identities with explicit source declarations such as
  `Symbols: x dimensionless.` No invented symbol meanings or physical quantities.
- Explicit bounded numeric unit equalities through the canonical immutable unit
  vocabulary and exact scale/offset conversion. Dimensions do not prove laws.
- Explicit `Step: before = expression => after = expression` source rewrites.
  Both source equations and reversible rewrite certificates must verify; every
  step remains source-linked. Broken adjacency and missing steps remain findings.

Prose equations, unknown notation, inequalities, calculus, matrices, unsupported
functions, unproved domains, ambiguous units/symbols and invalid equalities remain
REVIEW_REQUIRED. MATH becomes BLOCKED and REASONING remains unexecuted/PENDING.
The private review artifact and safe receipt remain in CAS/persistence; no false
successful output is admitted or ACKed. No OCR/LaTeX conversion is fabricated.

Native process_math, equation parsing, formula QA, make_step, validate_chain,
missing-step and numerical APIs are composed. Stronger canonical Section16 Math
expression, exact rational-polynomial, original-domain, reversible-step and unit
adapters provide certificates. Finite symbolic probes are NOT identity proof.
Native Math/QA engine source is unchanged. DI equation region/source/mode and KI
equation→claim/concept links bind actual page/geometry/anchors. Numeric-only items
do not invent concepts. A source-authored declaration is not expert verification.

Math artifacts retain run/source, exact document/knowledge/prerequisite IDs and
hashes, attempt, schema/policy, native module identities, private original and
normalized expressions, anchors, units/symbols, findings and review boundaries.
Engine identities are Git-LF-normalized code hashes, not expression normalization.

## Math-constrained Reasoning

Only verified REQUIRED or NOT_REQUIRED evidence unlocks Task031 Reasoning.
Reasoning records exact Math ID/hash and binds that evidence in each decision.
Executed types are teaching_order and evidence_arbitration through canonical
Reasoning contracts. General causal/temporal/spatial/mathematical_derivation
execution is NOT claimed. A supported numerical identity is not solving a book.
Technical uncertainty and semantic review requirements remain explicit.

## Durability and safety

The existing Task029/030 service, SQLitePersistence schema, durable task queue,
CAS, idempotency, EnterpriseOrchestrator, artifact resolver and fenced leases are
reused. No new infrastructure stack or model gateway. Task028 inspection worker
cannot consume this versioned capability. ACK follows verified publication,
safe evidence and persisted terminal commit. No implicit redrive or cross-store
atomicity is claimed. Explicit recovery retains interrupted failed attempts and
repairs publication/terminal-before-ACK boundaries under existing fencing.

Section18 remains the control plane. Its explicitly enabled trusted Math port
delegates to native composition; existing inspection/profile/HTTP/UI controls
are unchanged. Unsupported pause/cancel remains fail-closed. Android unchanged.
Safe projections expose only stage states, applicability, counts, IDs/hashes and
review codes, not text, equations, prompts, credentials or paths. Trusted children
retain the existing 1 GiB/30 CPU/45 wall-second budget; no limit is widened.

## Preservation and obligation boundary

The sealed lossless ledger is unchanged. A single source-archive-bound graph
amendment redirects the original row to its byte-exact active legacy module and
pins the new graph separately. Missing/altered/duplicate rows, manifests, original
bytes or active code fail verification. Original archives and atomic IDs unchanged.

QA16-GAP-030 remains **OPEN, technically narrowed**. This task supplies explicit
technical applicability and canonical Math migration, but the obligation also
requires actual broader caller migration/full current-head canonical regression
and governed scope/semantic review. Historical Section16 records are not rewritten.
The canonical readiness no-math review requirement and retained gate inventory
remain selected and unchanged. No release gate is waived.

AUDIO graph reconciliation remains OPEN and is not included. PEDAGOGY and all
later stages remain NOT_RUN. No lesson, audiovisual product, game, public
deployment, enterprise security or whole-product acceptance is claimed.

## Verification

Run tools/run_task031_tests.py new and affected lanes, then
scripts/smoke_bie_math_evidence.py. Three genuine native PDF journeys execute in
bounded child processes and reopen in second actual processes. Supported Math
and explicit no-Math complete; unsupported Math is BLOCKED with review evidence.
State, source/artifact hashes, queue terminals and Math→Reasoning binding verify.
Existing Task029 and Task030 process smokes remain required independently.
Seeded lease expiry is labelled test evidence, not a real-time expiry measurement.

Ubuntu CI is credential-free and preserves all focused legacy/native/QA suites.
Broad Windows platform/long-path and inherited path-separator failures remain
truthful evidence, not automatically Task031 regressions or green canonical proof.
No PR/merge/Task032 is authorized in this implementation pass.

Local evidence: 106 unique authored controls passed (82 producer/contract,
13 recovery, 11 preservation); repeated controls are not counted twice.
The selected affected suite contains 1,666 methods after installing the unchanged
approved Section16 QA profile. Its Windows result is NOT green: 22 failures,
25 errors, zero skips. The seven affected QA/Math modules reproduce the exact
same failed-method lists and counts on unchanged clean canonical main; their
POSIX secure-I/O/platform limits remain fail-closed. The inherited path-separator
failure also reproduces on clean main. These are not silently waived or claimed
to be Task031 regressions. Hosted Linux must execute the complete 1,772-method
focused/affected selection and full canonical preservation before integration.

The local integrated/preservation attempt stopped on four unchanged historical
Windows long-path files. Extended-path byte reads match the sealed ledger and
canonical Git blobs; the failed gate is retained, not labelled PASS. One earlier
generic process-smoke failure also remains retained and unattributed. Subsequent
current-head journeys passed with safe phase diagnostics and unchanged resource
ceilings; no precise cause for that earlier failure is asserted.
