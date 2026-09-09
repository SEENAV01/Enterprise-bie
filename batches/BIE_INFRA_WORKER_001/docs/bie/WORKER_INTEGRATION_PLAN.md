# Worker Integration Plan

1. Add resource requirements to each StageDefinition.
2. Scheduler selects eligible worker before lease acquisition.
3. Acquire worker lease for selected `(run_id, stage_id, attempt)`.
4. Reserve scheduler capacity only after successful lease acquisition.
5. Heartbeat updates health/lease state during long execution.
6. On completion/failure, release capacity and lease.
7. Persist worker capability snapshots with execution evidence.
8. Render/game/browser workers should run sandboxed.
9. Model/tool capability should be advertised abstractly; provider-specific routing stays behind Model/Tool Gateway.
10. Add queue priority/fairness only after correctness and capability coverage are stable.
