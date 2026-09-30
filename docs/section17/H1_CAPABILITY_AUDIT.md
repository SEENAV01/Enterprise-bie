# Section17 — whole-roster capability review and H1 re-audit

## Outcome
All50 original task IDs have traceable scoped implementations; none is promoted to enterprise acceptance. Ten justified H1 hardening tasks were implemented and re-tested. This is a first whole-roster capability/source-boundary review, not an independent exhaustive line-by-line security audit or live canonical-repository audit.

## Method and evidence
The baseline master SHA256 was verified; original1181 tests reran. All50 specs, owned files, dependency references and their acyclic graph were checked. Actual function symbols, file hashes and executed test IDs are in `metadata/section17/H1_CAPABILITY_AUDIT.json`. Deeper adversarial probes targeted the release/evaluator/storage/archive trust boundaries. Scientific/oracle independence is not established by our co-authored code/tests.

## Preserved product ambition
The complete book/PDF → knowledge/prerequisites/math/reasoning → pedagogy/director → visual/animation/SceneIR → real compile/render/audio → playable learning game → QA/repair/release product contract remains unchanged. Cinematic engagement, correct science and measured learning are not replaced by counters or fixtures.

## Repaired H1 findings

### BIE-EVAL-H1-001 — Unicode-safe canonical evidence
Unpaired Unicode surrogates and oversized UTF-8 strings escaped the typed evidence boundary.
Reject invalid scalar strings/keys and byte budgets before serialization; retain Hindi/emoji and valid surrogate pairs.
Boundary: Unicode/byte limits are defensive input checks, not source truth or text semantics.

### BIE-EVAL-H1-002 — SQLite API compatibility and path custody
Registry unconditionally used a Python3.12-only SQLite keyword despite the advertised3.11 minimum; lexical parent symlinks were not centrally guarded.
Use explicit manual transactions with version-aware connection parameters and reject symlink/URI/traversal paths.
Boundary: Executed on Python3.13.5;3.11 API behavior is simulated, not an actual3.11 platform run. Single-owner preflight is not race-proof OS containment.

### BIE-EVAL-H1-003 — Deterministic execution and result boundary
Unexpected metric errors escaped; a malformed/misbound/overcredited result could escape or be represented incorrectly.
Freeze evaluator inputs; validate context pins, unit-weighted scores and receipt construction inside one fail-closed boundary; redact exception details.
Boundary: Bounded deterministic profiles still do not judge arbitrary language or guarantee scientific truth. Re-audit malformed-result failures and fixes are retained.

### BIE-EVAL-H1-004 — Immutable model request identity
A provider callback could mutate caller-owned rubric/context or its fixture identity across the call.
Use detached request-bound snapshots and recheck provider/model/fixture identity after execution.
Boundary: No live provider is selected or called. An in-process adapter is still trusted operator code; use the supervised wrapper for a hard deadline.

### BIE-EVAL-H1-005 — Supervised provider deadline
The model port delegated timeouts to the adapter; a hanging callback had no enforced process deadline.
Offer an operator-installed factory wrapper with spawned worker, bounded UTF-8 response channel, deadline termination and direct-child reaping.
Boundary: Not an OS sandbox: descendant, network, memory, service authorization and provider billing cancellation remain deployment concerns. Wrapper adoption by the native broker is not automatic.

### BIE-EVAL-H1-006 — Structured candidate bundle binding
Manifest artifact identity was a supplied hash, not verified against an exact structured candidate bundle.
Require exact roster, per-case candidate digests and whole canonical bundle hash in production; diagnostic behavior stays compatible.
Boundary: This binds supplied structured JSON only, not unseen video/audio or a native run.

### BIE-EVAL-H1-007 — Authenticated assessment admission
A content-hashed assessment could self-assert a production execution identity without a per-assessment service authorization.
Require exact signed assessment scopes, configured roles/identity/version/group, expiry/revocation, non-fixture execution and no reused secret across raters.
Boundary: Configured shared-secret service custody is not independent digital non-repudiation, actual reviewer expertise, honest external evidence or protected production key provisioning.

### BIE-EVAL-H1-008 — Full domain-metric coverage and operator path
Global metric and domain aggregates could conceal missing domain-by-metric cells; the hardened gate inputs also needed CLI wiring.
Pin an exact full17-metric roster per domain; require independent reference/leakage-group components per cell; bind the contract into external attestation scope and expose all required inputs through the CLI.
Boundary: No automatic not-applicable exemptions and no empirical calibration claimed. Synthetic full-matrix controls use invented evidence and test signing identities, not a real production/golden approval.

### BIE-EVAL-H1-009 — Durable finalization and explicit recovery
A finalization could return a receipt without ensuring its reserved row was finalized; interrupted reservations lacked a governed terminal recovery path.
Compare-and-set finalization, read-back integrity, artifact/report bindings and explicit input-pinned operator recovery to terminal BLOCKED.
Boundary: Single-host privileged recovery requires stopping the abandoned worker first. It is not an authenticated public recovery endpoint or distributed crash reconciliation. Pre-H1 finalized receipts require explicit revalidation; do not rewrite archived evidence.

### BIE-EVAL-H1-010 — Portable archive custody and auditable replacements
Resolving paths before checking them hid root/parent symlinks; normalized Unicode/Windows aliases were not rejected. An inherited preservation assertion needed a tracked-change path rather than a skip.
Reject lexical symlink roots/parents and nonportable aliases, verify exact inventories, and require original preimages plus old/new hashes for intentional baseline replacements.
Boundary: Extraction remains for trusted operator-owned parents, not hostile concurrent filesystem writers. Historical original archives remain byte-identical; one old test file is deliberately updated and preserved.

## Remaining work — not hidden behind acceptance terminology

### H1-RES-001: Governed native BIE output adapter (IMPLEMENTATION_AND_INTEGRATION)
Implement exact canonical schema mapping, source/provenance capture and runtime evidence ingestion against an explicitly pinned repository checkout. Do not fabricate schemas from task names.

### H1-RES-002: Long-form audiovisual collectors (IMPLEMENTATION)
Replace the tiny bounded video-only path with resource-bounded streaming/chunked full-resolution long-lesson verification, decoded narration/silence/clipping and caption/audio timing checks. Add real files and corrupt/missing-stream controls.

### H1-RES-003: Live evaluator and human workflow (IMPLEMENTATION_AND_EXTERNAL_VALIDATION)
Wire an operator-selected provider through supervised execution, finite network timeouts and protected credentials; add independent reviewer onboarding/assignment/review custody and actual validation. No live call or real human review was done.

### H1-RES-004: Game/player/browser evidence (IMPLEMENTATION_AND_NATIVE_VALIDATION)
Connect actual playable-game outcomes, browser keyboard/screen-reader/player observations and learning event lineage; structured authored traces are not runtime evidence.

### H1-RES-005: Independent golden corpus and calibrated quality (SCIENTIFIC_VALIDATION)
Rights-cleared source snapshots, domain experts, blind heldout splits, rater calibration, validated thresholds and consented learning studies remain required.

### H1-RES-006: Corpus-scale anti-leakage (IMPLEMENTATION)
Implement/evaluate an indexed bounded duplicate/semantic-triage adapter beyond the inherited512-case pairwise cap without silent denominator dropping.

### H1-RES-007: Service isolation, protected keys and durable evidence (DEPLOYMENT_IMPLEMENTATION)
Provision authenticated services, secret custody, worker OS resource/descendant/network containment and off-host audit anchoring. The Python wrapper/HMAC helpers are not these services.

### H1-RES-008: Native external evidence truth (EVIDENCE_TRUST_BOUNDARY)
Verify real source/render/game artifacts via trusted native collectors and independent signoff. The local gate verifies configured signed assertions, not the truth of invented external artifact content. Test-only keys/evidence cannot authorize a real product.

### H1-RES-009: Actual supported runtime matrix (ENVIRONMENT_VALIDATION)
Run real Python3.11 and other supported platforms and native toolchains; the current host is Python3.13.5 and the older SQLite API test is simulated.

## Original50 capability-by-capability review

### BIE-EVAL-REG-001 — benchmark registry
Scoped behavior: Typed, source-bound immutable benchmark cases; transactional SQLite registration; duplicate rejection; detached nested data; redacted candidate view; hash-chained operator audit records.
Trace: `docs/section17/tasks/BIE-EVAL-REG-001/SPEC.md`; 5 owned files verified; 26 selected test IDs passed.
Remaining: Local typed registry and audit hashes do not establish authenticated multi-tenant/off-host custody.

### BIE-EVAL-REG-002 — benchmark versioning
Scoped behavior: Immutable dataset snapshots, monotonic semantic versions, exact parent linkage, lineage verification, comparison/diffs and public manifests without expected answers.
Trace: `docs/section17/tasks/BIE-EVAL-REG-002/SPEC.md`; 2 owned files verified; 19 selected test IDs passed.
Remaining: Immutable local snapshots do not prove distributed backup/recovery or a protected held-out deployment.

### BIE-EVAL-REG-003 — governance
Scoped behavior: Snapshot-bound approval verification, independently configured reviewer roles, quorum, rejection veto, author/reviewer separation, validity windows, revocation and signed review-evidence hashes.
Trace: `docs/section17/tasks/BIE-EVAL-REG-003/SPEC.md`; 2 owned files verified; 23 selected test IDs passed.
Remaining: Configured HMAC authorities, not verified expert identity, independent non-repudiation or actual reviewed golden cases.

### BIE-EVAL-REG-004 — anti-gaming rules
Scoped behavior: Cross-split problem/group/prompt leakage triage; bounded near-duplicate work; atomic one-attempt claims; pinned candidate/dataset/policy identity; complete frozen denominator; missing/error/abstain penalties; persisted reports; structured-output import CLI.
Trace: `docs/section17/tasks/BIE-EVAL-REG-004/SPEC.md`; 8 owned files verified; 28 selected test IDs passed.
Remaining: Bounded pairwise leakage triage (512 cases/2048-character prompts) needs a scalable/indexed governed adapter; training leakage remains unverified.

### BIE-EVAL-PHY-001 — Coulomb benchmark
Scoped behavior: Signed 3D point-charge force, vector superposition, inverse-square distance, explicit SI conversions, configurable pinned Coulomb constant and coincidence rejection.
Trace: `docs/section17/tasks/BIE-EVAL-PHY-001/SPEC.md`; 3 owned files verified; 20 selected test IDs passed.
Remaining: Point-charge/SI/vector profiles, not complete electrostatics textbook or visualization coverage. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-PHY-002 — mechanics benchmark
Scoped behavior: Constant-acceleration 1D kinematics, net-force 3D acceleration, perfectly inelastic 1D momentum/energy loss and constant-force dot-product work; units, limits and sign checks.
Trace: `docs/section17/tasks/BIE-EVAL-PHY-002/SPEC.md`; 3 owned files verified; 20 selected test IDs passed.
Remaining: Specified Newtonian calculation profiles, not all mechanics or native free-response reasoning. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-PHY-003 — waves benchmark
Scoped behavior: Linear wave properties and superposition, traveling-wave samples with distinct phase/particle velocities, fixed-string harmonics, phase/units/mode validation.
Trace: `docs/section17/tasks/BIE-EVAL-PHY-003/SPEC.md`; 3 owned files verified; 20 selected test IDs passed.
Remaining: Selected linear wave/harmonic profiles, not complete wave physics or visual verification. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-MATH-001 — functions
Scoped behavior: Exact rational polynomial/rational evaluation, original-domain holes, order-sensitive composition, affine inversion, finite-relation function/injectivity and bounded arithmetic.
Trace: `docs/section17/tasks/BIE-EVAL-MATH-001/SPEC.md`; 3 owned files verified; 20 selected test IDs passed.
Remaining: Bounded rational/polynomial/finite-relation profiles, not arbitrary functions. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-MATH-002 — calculus
Scoped behavior: Analytic bounded polynomial derivatives/antiderivatives, explicit arbitrary constant, oriented definite integrals, tangent coefficients, absolute-value cusp and reciprocal singularity guards.
Trace: `docs/section17/tasks/BIE-EVAL-MATH-002/SPEC.md`; 3 owned files verified; 20 selected test IDs passed.
Remaining: Bounded polynomial calculus and selected singularity handling, not arbitrary symbolic calculus. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-MATH-003 — geometry
Scoped behavior: Stable triangle area/perimeter, simple-polygon validation/shoelace area/orientation, rigid planar transforms and square-law similar-area scaling with units.
Trace: `docs/section17/tasks/BIE-EVAL-MATH-003/SPEC.md`; 3 owned files verified; 20 selected test IDs passed.
Remaining: Selected planar geometry/transformation profiles, not full geometric proof or diagrams. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-BIO-001 — photosynthesis
Scoped behavior: # BIE-EVAL-BIO-001 — photosynthesis
Trace: `docs/section17/tasks/BIE-EVAL-BIO-001/SPEC.md`; 5 owned files verified; 22 selected test IDs passed.
Remaining: Authored photosynthesis resource/budget abstractions, not full biological mechanism understanding. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-BIO-002 — genetics
Scoped behavior: # BIE-EVAL-BIO-002 — genetics
Trace: `docs/section17/tasks/BIE-EVAL-BIO-002/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Declared inheritance/equilibrium assumptions, not all genetics or empirical biological validity. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-BIO-003 — physiology
Scoped behavior: # BIE-EVAL-BIO-003 — physiology
Trace: `docs/section17/tasks/BIE-EVAL-BIO-003/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Selected ideal physiology/unit calculations, not clinical guidance or complete physiology. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-CHEM-001 — bonding
Scoped behavior: # BIE-EVAL-CHEM-001 — bonding
Trace: `docs/section17/tasks/BIE-EVAL-CHEM-001/SPEC.md`; 4 owned files verified; 22 selected test IDs passed.
Remaining: Bounded electron/charge/VSEPR profiles, not general molecular or chemical interpretation. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-CHEM-002 — reaction mechanism
Scoped behavior: # BIE-EVAL-CHEM-002 — reaction mechanism
Trace: `docs/section17/tasks/BIE-EVAL-CHEM-002/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Selected mechanism conservation/rate/energy annotations, not general mechanism discovery. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-CHEM-003 — stoichiometry
Scoped behavior: # BIE-EVAL-CHEM-003 — stoichiometry
Trace: `docs/section17/tasks/BIE-EVAL-CHEM-003/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Bounded formula/stoichiometry/yield calculations, not arbitrary chemistry. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-HIST-001 — French Revolution
Scoped behavior: # BIE-EVAL-HIST-001 — French Revolution
Trace: `docs/section17/tasks/BIE-EVAL-HIST-001/SPEC.md`; 4 owned files verified; 22 selected test IDs passed.
Remaining: A small source-dated authored event set, not independent multi-source historical scholarship. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-HIST-002 — historical causality
Scoped behavior: # BIE-EVAL-HIST-002 — historical causality
Trace: `docs/section17/tasks/BIE-EVAL-HIST-002/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Declared causality annotations, not source entailment or independent historiographical adjudication. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-HIST-003 — chronology
Scoped behavior: # BIE-EVAL-HIST-003 — chronology
Trace: `docs/section17/tasks/BIE-EVAL-HIST-003/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Ordering and date precision checks, not verification of every historical assertion. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-GEO-001 — plate tectonics
Scoped behavior: # BIE-EVAL-GEO-001 — plate tectonics
Trace: `docs/section17/tasks/BIE-EVAL-GEO-001/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Declared simplified plate-motion/boundary profiles, not full earth-science corpus. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-GEO-002 — maps
Scoped behavior: Printed map length/area scale, signed DMS coordinates, spherical distance and grid bearings.
Trace: `docs/section17/tasks/BIE-EVAL-GEO-002/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Map-coordinate/scale calculations, not interpretation of arbitrary scanned maps. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-GEO-003 — climate systems
Scoped behavior: Declared global energy/water budgets, 30-year anomaly arithmetic, area weighting and feedback polarity.
Trace: `docs/section17/tasks/BIE-EVAL-GEO-003/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Declared budget/anomaly/climate profiles, not a validated climate model or complete geography. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-CIV-001 — civics/institutions
Scoped behavior: Descriptive selected UK institution roles, ordinary two-house bill traces, and explicit fictional power tables.
Trace: `docs/section17/tasks/BIE-EVAL-CIV-001/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Selected dated jurisdictional educational profiles, not cross-jurisdiction coverage or any political merit evaluation. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-DATA-001 — tables/charts
Scoped behavior: Exact table arithmetic and structured cell-to-chart fidelity with explicit missing data and axes.
Trace: `docs/section17/tasks/BIE-EVAL-DATA-001/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Structured tables/chart values, not native chart-image extraction or independent visual-statistical literacy. Authored references are not independent golden/holdout evidence.

### BIE-EVAL-METRIC-001 — grounding metric
Scoped behavior: Candidate-bound weighted proposition/citation checking against exact captured authored source text.
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-001/SPEC.md`; 7 owned files verified; 20 selected test IDs passed.
Remaining: Exact annotated claim/span/hash checks, not general semantic entailment or real-book provenance capture.

### BIE-EVAL-METRIC-002 — semantic metric
Scoped behavior: Weighted trusted concept facets and relation fidelity without keyword-overlap grading.
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-002/SPEC.md`; 3 owned files verified; 18 selected test IDs passed.
Remaining: Typed concept/facet matching, not a free-text/diagram semantic evaluator.

### BIE-EVAL-METRIC-003 — prerequisite metric
Scoped behavior: Prerequisite transitive closure and teach-before-use under a trusted acyclic graph.
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-003/SPEC.md`; 3 owned files verified; 18 selected test IDs passed.
Remaining: Checks a declared prerequisite graph; the correctness/completeness of extracted native prerequisites still requires validation.

### BIE-EVAL-METRIC-004 — reasoning metric
Scoped behavior: Finite forward Horn-rule proof checking with trusted facts and no invented premises.
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-004/SPEC.md`; 3 owned files verified; 18 selected test IDs passed.
Remaining: Checks supplied formal rules and proof steps; not a general reasoning or natural-language proof verifier.

### BIE-EVAL-METRIC-005 — math metric
Scoped behavior: Unit-aware exact arithmetic, bounded polynomial identities and rational-expression domain preservation.
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-005/SPEC.md`; 3 owned files verified; 20 selected test IDs passed.
Remaining: Bounded exact arithmetic/unit/algebra profiles; not full scientific/advanced-math coverage.

### BIE-EVAL-METRIC-006 — causal metric
Scoped behavior: Directed graph and intervention/counterfactual fidelity in declared acyclic linear structural causal models.
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-006/SPEC.md`; 3 owned files verified; 20 selected test IDs passed.
Remaining: Fidelity to declared causal models is not empirical causality or observational identification.

### BIE-EVAL-METRIC-007 — pedagogy metric
Scoped behavior: # BIE-EVAL-METRIC-007 — Pedagogy
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-007/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Structured objective/activity coverage does not prove understanding or effective teaching.

### BIE-EVAL-METRIC-008 — director metric
Scoped behavior: # BIE-EVAL-METRIC-008 — Director
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-008/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Authored beats/timing/word density do not validate cinematic narration or multilingual spoken pacing.

### BIE-EVAL-METRIC-009 — representation metric
Scoped behavior: # BIE-EVAL-METRIC-009 — Representation
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-009/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Declared labels/layout/relations are not actual rendered semantic perception.

### BIE-EVAL-METRIC-010 — animation metric
Scoped behavior: # BIE-EVAL-METRIC-010 — Animation
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-010/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Sampled trajectories are not continuous visual correctness or native animation-engine execution.

### BIE-EVAL-METRIC-011 — compile metric
Scoped behavior: # BIE-EVAL-METRIC-011 — Compile
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-011/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Small Python/TypeScript source compiles do not bundle a native Remotion project or validate dependency closure.

### BIE-EVAL-METRIC-012 — render metric
Scoped behavior: # BIE-EVAL-METRIC-012 — Render
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-012/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Collector caps20MB,320x180,300frames,20s; audio presence only. Full-size lesson/video/audio implementation remains open.

### BIE-EVAL-METRIC-013 — frame-quality metric
Scoped behavior: # BIE-EVAL-METRIC-013 — Frame quality
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-013/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Small decoded RGB comparisons are not native long-video quality, OCR/readability, perception or independent aesthetic judgement.

### BIE-EVAL-METRIC-014 — game-learning metric
Scoped behavior: # BIE-EVAL-METRIC-014 — Game learning
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-014/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Authored response traces and paired calculations are not actual game runtime telemetry or causal human-learning improvement.

### BIE-EVAL-METRIC-015 — accessibility metric
Scoped behavior: # BIE-EVAL-METRIC-015 — Accessibility
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-015/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Static contrast/caption/focus data are not browser/assistive-technology or decoded caption conformance.

### BIE-EVAL-METRIC-016 — reproducibility metric
Scoped behavior: # BIE-EVAL-METRIC-016 — Reproducibility
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-016/SPEC.md`; 3 owned files verified; 16 selected test IDs passed.
Remaining: Local output-byte comparisons are not reproducibility of complete native provider/render/game pipelines.

### BIE-EVAL-METRIC-017 — regression metric
Scoped behavior: Exact paired-roster deltas, critical floor and allowed-drop checks with pinned dataset/environment/evaluator identities.
Trace: `docs/section17/tasks/BIE-EVAL-METRIC-017/SPEC.md`; 4 owned files verified; 20 selected test IDs passed.
Remaining: Paired bounded reference-case regressions still need an independently governed held-out native suite.

### BIE-EVAL-RATER-001 — deterministic evaluator
Scoped behavior: Execute the actual 17 supported metric profiles, bind candidate/reference/rubric/service-code digests, retain detailed metric receipts and blocked failures.
Trace: `docs/section17/tasks/BIE-EVAL-RATER-001/SPEC.md`; 2 owned files verified; 18 selected test IDs passed.
Remaining: 17 actual bounded evaluators and hardened fault handling, not free-text/native scientific coverage.

### BIE-EVAL-RATER-002 — model evaluator
Scoped behavior: Provider-neutral callable port, version-pinned request/response envelopes, fixed weighted rubric roster, evidence-ID checking, response limits and fail-closed errors.
Trace: `docs/section17/tasks/BIE-EVAL-RATER-002/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Provider-neutral port plus optional hard-deadline wrapper; live provider selection, broker integration and calibration remain unimplemented/unvalidated.

### BIE-EVAL-RATER-003 — human evaluator
Scoped behavior: Operator-authenticated subject, candidate/rubric-bound assignment, HMAC service attestation, reviewer-role checks, expiry/revocation, conflicts and explicit unit judgements.
Trace: `docs/section17/tasks/BIE-EVAL-RATER-003/SPEC.md`; 3 owned files verified; 22 selected test IDs passed.
Remaining: Signed review data/assignment checks, not an actual reviewer interface/onboarding workflow or independent reviews.

### BIE-EVAL-RATER-004 — evaluator agreement
Scoped behavior: Complete paired panels, binary observed agreement, exact Cohen kappa and mean absolute score differences; missingness and undefined statistics remain explicit.
Trace: `docs/section17/tasks/BIE-EVAL-RATER-004/SPEC.md`; 2 owned files verified; 18 selected test IDs passed.
Remaining: Exact paired statistics are implemented; rater agreement does not demonstrate correctness and calibration is open.

### BIE-EVAL-RATER-005 — conservative aggregation
Scoped behavior: Minimum score across a pinned rater roster, required deterministic evaluator, unique declared independence groups, zero credit for absent/blocked raters and disagreement adjudication blocks.
Trace: `docs/section17/tasks/BIE-EVAL-RATER-005/SPEC.md`; 2 owned files verified; 18 selected test IDs passed.
Remaining: Conservative aggregation/service admission does not prove real-world evaluator independence or rater accuracy.

### BIE-EVAL-REL-001 — enterprise threshold
Scoped behavior: Exact weighted metric thresholds and measured-fraction checks using an operator-pinned denominator; missing metrics remain zero.
Trace: `docs/section17/tasks/BIE-EVAL-REL-001/SPEC.md`; 2 owned files verified; 15 selected test IDs passed.
Remaining: Weighted numerical thresholds are operator policy, not empirically validated learning-quality standards.

### BIE-EVAL-REL-002 — critical hard floors
Scoped behavior: Mandatory per-metric floors and measured-status requirements that cannot be overridden by a high overall average.
Trace: `docs/section17/tasks/BIE-EVAL-REL-002/SPEC.md`; 2 owned files verified; 14 selected test IDs passed.
Remaining: Hard floors cannot certify the truth of supplied upstream evidence or completeness of selected profiles.

### BIE-EVAL-REL-003 — domain minimums
Scoped behavior: Per-domain weighted score/coverage floors, fixed case rosters and minimum independent leakage-group counts.
Trace: `docs/section17/tasks/BIE-EVAL-REL-003/SPEC.md`; 2 owned files verified; 16 selected test IDs passed.
Remaining: Full pinned domain-metric cells and reference-group checks do not create independently reviewed domain coverage.

### BIE-EVAL-REL-004 — release benchmark gate
Scoped behavior: Aggregate actual evaluator receipts, enforce agreement/enterprise/critical/domain gates, verify scoped signed external evidence and persist single-use attempts with frozen campaign identity.
Trace: `docs/section17/tasks/BIE-EVAL-REL-004/SPEC.md`; 4 owned files verified; 41 selected test IDs passed.
Remaining: Hardened bundle/service/coverage bindings and signed external attestations are not native artifact verification or production deployment permission; operator honesty/custody remains a trust boundary.

## Re-audit and claims
139 new tests and the1181 retained IDs pass in the1320-method cumulative suite. One inherited preservation assertion changed to demand exact before/after hashes and a retained preimage instead of silently skipping a changed file. Initial failures, additional malformed-result defects, deliberately injected faults and interrupted attempts remain recorded. Actual independent expert reviews, live model calls, native book runs and product approvals in H1: zero.
