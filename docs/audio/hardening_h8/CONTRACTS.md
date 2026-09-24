# AUDIO Hardening H8 Contracts

Scope: finish the remaining **implementation-side F03** controls around paid/remote neural-provider calls without creating a second BIE orchestrator or pretending remote exactly-once semantics.

Key invariants:
- provider credentials are resolved at request time from an approved environment binding and are never serialized into evidence, call journals or command lines;
- network authority is exact-origin/path fail-closed and complements the existing HTTPS transport allowlist;
- live provider workloads are preflighted as a whole and are never silently truncated;
- a paid POST has a durable content/configuration-bound intent before dispatch;
- an in-flight call whose completion becomes ambiguous is persisted as `UNCERTAIN` and the same identity cannot be resent until explicit evidence-bound operator resolution;
- a confirmed response without a surviving local cache is blocked rather than silently resynthesized;
- known HTTP rejection and ambiguous transport outcomes are distinguished; neither is automatically retried;
- host-local concurrency is bounded with OS-released slot locks; this is not a distributed fleet scheduler or autoscaler;
- fixture/local providers preserve their original behavior and cannot masquerade as live provider evidence;
- the inherited H6 summary schema and H5 dry-pipeline validator agree on stem fields after the H8 compatibility repair;
- no live ElevenLabs call, independent listening, HSM/cloud secret manager, distributed scheduler, real book, render or product acceptance is claimed.
