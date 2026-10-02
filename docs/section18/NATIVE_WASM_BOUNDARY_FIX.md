# Bounded native Wasm compatibility correction

Finding: Attempt009 (`321e002f`, run37014412643) progressed beyond read-only
dependency cache failure and reproduced real Remotion/Webpack Wasm startup OOM.
The unchanged WorkerPolicy enforces8GiB RLIMIT_AS. Pinned Node22.16 documents
its default10GB Wasm virtual cage and an inline-bounds-check alternative:
https://nodejs.org/download/release/v22.16.0/docs/api/cli.html#--disable-wasm-trap-handler

The current user explicitly approves a narrow `--disable-wasm-trap-handler`
invocation correction. It is added only to `produce_actual_paint`'s active
producer argv, and that argv is retained in PROCESS.json. Generic workers,
TypeScript invocation, unrelated Node work, NODE_OPTIONS and resource/security
policies remain unchanged. The final CLI is not preemptively altered; a later
concrete failure would require a separately recorded bounded correction.

Five new focused methods cover unflagged genuine bundle failure reproduction,
real Wasm out-of-bounds trap,64KiB growth plus OS virtual-reservation denial,
unrelated command scope and exact producer argv/receipt scope. The two existing
bundle-cache methods are not inherited or counted a second time. Their positive
control uses the approved flag. All controls require exact Node22.16, unchanged
native policy receipts and installed dependency identity; no process/witness
double or budget widening is permitted.

Native execution is PENDING until exact-head hosted receipts are inspected.
These are synthetic technical controls, not real-book/product acceptance.
Attempt009 and earlier failed artifacts remain immutable. Task028 remains paused.
