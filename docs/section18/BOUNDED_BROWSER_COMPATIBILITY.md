# Bounded native Chromium compatibility investigation

This is diagnostic work under explicit human approval, not implementation
sign-off or a substitute for actual paint/render. Task028 remains paused.

Attempt015 preserved the exact unmodified Chromium `--version` SIGTRAP. Its
qualified logging-only mmap observer recorded two failed32GiB reservations
with ENOMEM under the unchanged8GiB worker policy. The observer does not change
allocation arguments/results, security flags, resource limits or production
environment. Section17's independent2023-method gate passed that same run;
the complete canonical regression remained NOT_RUN because native render was
red. These outcomes must not be conflated.

The next probe compares the already-installed Playwright1.57.0 full Chromium
and headless-shell revision1200, both version143.0.7499.4 according to the pinned
registry. The headless files are copied byte-identically inside an already
read-only system mount; no production browser switch is made. Every argv,
binary/registry hash, kernel receipt and failed observation is retained.

No larger address space, writable node_modules, disabled allocator hardening,
disabled V8 sandbox, new syscall permission, weakened namespace/capability
policy or allocator override is authorized. Even a successful version probe
does not prove Remotion execution, strict TypeScript, actual paint, produced
frames/media, decoding, CAS binding, media ranges or tamper rejection. Those
must pass their existing genuine native gates on the exact qualified tree.

The approved Node flag remains scoped to actual-paint/bundle argv. It is not a
Chromium allocator workaround and does not authorize unrelated Node options.
Diagnostic collection contributes zero new test methods and grants no PASS.
