# AUDIO Hardening H9 Contracts

Scope: close the remaining **implementation-framework side of F02** without pretending that unit fixtures are a real multilingual evaluator, independent listener panel, or calibrated production deployment.

Key invariants:
- evaluator capability support is explicit by language, accent, IPA, OOV, code-switching, outputs and workload budgets; unsupported requirements fail closed;
- evaluation reports are bound to the exact delivered media hash, source/readings, voice identity, evaluator model/revision/runtime, target coverage and uncertainty;
- a report is measurement evidence only and cannot self-authorize pronunciation acceptance;
- held-out calibration computes deterministic false-positive/false-negative rates under explicit policy, excludes excessive-uncertainty cases and preserves fixture-vs-independent scope;
- a synthetic/test calibration may exercise mechanics but cannot authorize production;
- evaluator release authority is signed against an out-of-band trust root and exact profile+calibration identity; TEST_ONLY issuers, local-file custody and non-independent calibration cannot authorize production;
- calibrated pronunciation PASS/FAIL is possible only when report, production authority and held-out independent calibration all validate; otherwise evidence is REVIEW/BLOCKED;
- high evaluator uncertainty never silently becomes PASS;
- a pronunciation failure creates an unchanged-reading resynthesis intent with downstream invalidation obligations, but no F04 repair dispatch/invalidation is claimed here;
- existing H2 legacy English acoustic diagnostics remain valid as diagnostic evidence and are not silently replaced;
- no live multilingual evaluator, independent human listening, neural-provider listening, real-book calibration, HSM/KMS deployment, canonical F04 dispatch or render was executed in H9.
