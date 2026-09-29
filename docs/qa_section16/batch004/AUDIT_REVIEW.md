# Batch-local implementation review (not final Section 16 exit audit)

Inspected the new authentication/evidence/proof/readiness/uncertainty paths and exercised
malformed, unsupported and adversarial inputs with actual artifacts. Material protections
include inconsistent-root rejection, transitive readiness, no instruction-as-mastery
substitution, source-byte deduplication, counterevidence precedence, no test-key promotion,
request/policy freshness, exact heldout metrics and conservative action/disclosure checks.

The low-level public review verifier was strengthened to validate digest shape and lifetime
rather than relying only on its typed wrapper. Two regression tests were added. Initial
bridge tests incorrectly used `PreparedEvidence.evidence`/`EvaluationReport.status`;
inspection corrected them to the actual preserved APIs `envelope` and `release_status`.
No original API or implementation was changed to accommodate those test mistakes.

Development-run logs include these earlier test errors and later passing runs. A first
mutation command exceeded the execution-call timeout; its partial logs are retained.
The separate `mutation_probes_004_verified` run completed all 16 controls and assertion
failures. Only that complete receipt supports the mutation result. Timeout logs are not
counted as successful probes. No results from a changed source tree are reused as final
verification; current source/test hashes are recorded in the full runner receipt.

Remaining substantive gaps are preserved in the cumulative gap ledger: automated,
calibrated extraction and semantic mapping; genuine learner evidence; independently
validated source lineage; live heldout calibration; provider execution/provenance;
canonical adapters/callers and cross-platform tests; real rendered lesson/game evidence;
publication immutability; full Section 16 audit/hardening/re-audit and final acceptance.

A bounded propositional checker is not universal formal reasoning. Reviewed non-deductive
steps are not deterministic proof. An authenticated assessment is not automatically true.
The schemas are structural only; runtime validation remains authoritative. A text-only
PASS cannot certify the complete video/game release gate.
