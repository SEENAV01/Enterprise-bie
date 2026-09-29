# BIE Section 16 Batch 022 — release assembly and certification

## Original task mapping
The original master registry lists REL-001 (release manifest) on page 18 and
REL-002 (release evidence graph), REL-003 (release blocker report) and REL-004
(production SUCCESS certification) on page 19. This batch continues, rather than
replaces, the original RELEASE-001 implementation. Namespace: `bie/qa/publication_v2`.

## Input and trust boundaries
`PublicationRequest` contains the existing `EvidenceBundle`, a release ID/version,
explicit candidate-artifact lineage, three section-exit records and any open items.
Every candidate contains source, video and game artifacts. Governance records cover
**audit, hardening and re-audit**. There is no optional-gate flag, score average,
policy weakening switch, implicit approval, key in request JSON or submitted callback.

`PublicationPolicy`, the existing evidence verifier and an `AuthorityStore` are
separately provisioned operator inputs. The default mode is **diagnostic**. The
command-line interface is read-only and has no signing, revocation or deployment
command. The signing API is a separate, explicitly invoked operator operation.

## REL-001: manifest
The existing release evaluator rereads every candidate/report file using its bounded,
no-follow ArtifactStore. Additional proof/support/exit documents are read through
SnapshotStore. Identity, role, storage path, SHA-256 and byte length are preserved.
Conflicting ID/path aliases fail. The manifest binds release identity, environment,
revision, candidate, evidence bundle, both policies, graph and the rerun gate report.
It is a delivery inventory, not automatic discovery of every artifact on a filesystem.
Independent inventory approval and an enumerated-only publisher remain required.

## REL-002: evidence graph
Constructed typed nodes represent the release, all mandatory gates, submitted gate
evidence, proof reports, supporting report bytes and candidate artifacts. Edges
express requires/evaluated_by/reported_in/inspected/supported_by/derived_from.
References must exist; derived subjects must reach a source; source objects may not
be rewritten as derived outputs. Cycles and dangling edges block. Terminal supporting
reports cannot point back at a top-level proof or candidate. Deterministic ordering,
node/edge limits and exact graph hashes are included. This is provenance structure,
not a proof that the semantic explanation is correct.

## REL-003: blockers
All inherited global, per-gate and per-evidence diagnostics survive. Missing gates,
unauthenticated records, failed checks, nonnative proof scope, missing audit stages,
unclosed must-haves and explicit open items block. A proof claiming PASS cannot hide
a failed/skipped/review-required check. Recognized negative top-level source-report
statuses, false success flags and unclosed gap ledgers also block. Unknown production
report formats require an adapter instead of being silently cleared. Reason codes,
subjects and owner routing are deterministic; private secrets and raw stacks are not
copied into the blocker report.

## REL-004: conditional certificate lifecycle
`issue()` reruns inspection. Every existing release gate must reach READY_FOR_REVIEW;
its earlier report still does not itself certify anything. Three distinct authorized
principals approve the **exact assessment digest** for inventory, evidence/section
exit and release authorization. A separate fourth issuer signs the certificate.
Signature, purpose, principal, decision, key status, validity interval and binding
are verified. Different principals cannot count independent copies of the same
shared secret. Rejected reviews are never outvoted.

Only explicit production policy plus operator-managed authority can issue SUCCESS.
Diagnostic mode issues DIAGNOSTIC_ONLY with `release_authorized=false` and
`product_accepted=false`. All execution examples in this package are diagnostic.
No production SUCCESS certificate was issued for BIE in this batch.

The assessment clock and issuance clock are separate: reviewers can approve a frozen
assessment later, while issuance rechecks current evidence. Future-dated assessments
are rejected. This prevents a same-second approval requirement without reusing stale
evidence. The expiry is capped by policy, every gate-evidence expiry, approval expiry and issuer
key expiry. A private local SQLite journal reserves each release/version/environment
identity transactionally. Exact same-certificate retries are idempotent; conflicting
content cannot overwrite a version. Verification rechecks the current files, gate
trust, approvals, issuer trust, time and journal/revocation record. Revocation is an
explicit API operation. No GitHub commit, artifact deployment or publication occurs.

## Evidence format and integration
Five JSON schemas provide structural checks only. The Python codec and evaluator
apply additional byte, identity, graph and authority constraints. Gate proofs use
`bie.qa.release-proof/1`; exit records use `bie.qa.section-exit/1`. Their supporting
reports are actually read, but arbitrary domain meaning is still assessed by the
independently authorized evaluator. A signed status is not a substitute for its
real native execution and scientific/educational evidence.

Existing bounded bridges stay unchanged and return FAIL or NOT_RUN. They are not
upgraded to native proof. New native adapters and trusted operational assessments
must establish full-candidate scope before certification is available in practice.
The legacy evaluator's historical certification-boundary string remains unchanged;
it describes that older evaluator, not the existence of this additive module.

## Operational limits
This local implementation reuses the existing size-bounded POSIX artifact readers;
proof JSON is limited to 4 MiB and supporting snapshots to the inherited IO budget.
The root must be operator-owned and immutable while inspecting and publishing. The
journal requires a private operator-owned directory. HMAC is shared-secret integrity,
not asymmetric non-repudiation or a remote KMS/attestation service. The local journal
is not distributed, cannot prevent operator rollback/deletion, and does not provide
atomic deployment of a product. Clock, reviewer competence, inventory completeness,
secret provisioning, current-HEAD integration, deployment transactions and revocation
distribution require production integration and independent validation.

## Run
From the extracted Integrated package, with inherited dependencies installed:

```sh
python -B scripts/verify_qa_publication22_batch022.py --output ../release22-tests --workers 4
python -B scripts/verify_qa_publication22_mutations.py --output ../release22-mutations
python -B scripts/verify_qa_publication22_execution.py --output ../release22-diagnostics
python -B -m bie.qa.publication_v2 request.json --root artifacts --environment staging --as-of 1790546400
```

The last clock is an example supplied explicitly for replay, not a production clock.
Each verification output directory must be new. CLI exits 3 for blocked inspection
and 4 for invalid input; it cannot issue a certificate even when input claims PASS.

## Continuation rule
All 76 original Section16 entries have bounded local implementations after this
batch. That does NOT mean full implementation-scope completion or product acceptance.
Next is the full enterprise-completeness audit against the entire original scope,
vision and cumulative gap ledger. Material gaps must produce traceable hardening
atomic tasks, followed by re-audit and governed integration. Do not jump to Section17
or infer acceptance from these local tests. Section15 remains externally managed.
