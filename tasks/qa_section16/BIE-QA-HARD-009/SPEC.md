# BIE-QA-HARD-009 — Operational assessor adapters and untrusted-content defense

## Original audit requirement
Connect provider-neutral structured assessment with evidence provenance, retry/abstention and human escalation; documents are data, not instructions.

## Implemented local scope
Provider registry is configured out-of-band. The unchanged native ModelRequest/ModelResponse contract has an adapter with request/provider/model/provenance checks. Strict responses cannot choose gates, authority, executable callbacks or tools. Retry only transient errors; contradictions/malformed answers cannot be retried until favorable. A pinned subprocess transport enforces a process-group timeout. Generic registered provider objects retain responsibility for interruptible transport deadlines.

## Executed / tested behavior
- Fixed rubric/system/tool configuration is preserved against source instructions and extra response authorization fields.
- Unavailable/malformed/contradicted/truncated/foreign provider records remain blocked or review-required.
- Two actual local assessor subprocesses executed diagnostic responses; native gateway contract tests use explicitly synthetic providers.

## Required closure still open
- No live authorized provider was invoked or provisioned. Full HARD009 operational closure therefore remains OPEN.
- Prompt framing and strict output controls do not prove semantic immunity to every prompt injection.
- Operational credentials, retry economics/rate limits and independent assessor calibration remain deployment obligations.

This task has a local adapter/interface implementation, not full operational closure. Source files and old evaluations are never rewritten to create a pass. No release is authorized. Read the shared execution receipts; do not multiply shared test counts by five.
