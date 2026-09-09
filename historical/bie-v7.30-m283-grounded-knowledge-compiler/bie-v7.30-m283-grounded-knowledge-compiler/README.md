# BIE v7.30 — M283 Grounded Knowledge Compiler

M283 converts the structured Document IR into a source-grounded Knowledge IR.

The key invariant is simple: **no claim without evidence**.

The implementation is intentionally conservative. It does not silently turn word co-occurrence into causal or semantic truth.
