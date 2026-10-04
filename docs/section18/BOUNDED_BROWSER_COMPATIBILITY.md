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

## Attempt016 result: no qualified browser correction

Run37061512154 on cef8c3dee7add6978664e228ea9b5b079ec56b18 retained the
unchanged full browser and headless-shell failures. The uninstrumented binaries
both exit SIGTRAP; the qualified observer sees two32GiB mmap requests rejected
with ENOMEM from the headless shell too. Every kernel receipt retains exactly
8589934592 address-space bytes and the existing namespace/seccomp/capability,
network, filesystem and other resource bounds. The pinned headless binary hash
is20ffc88be1c6f7dc8351bebfaca965ff9a07617bddf696f0b67ef85e5868b29a;
the full binary hash is2e61bc3fd990bd4d7b419ef6b6303c67aaed683e5b83b3b25e416f015f343209.

The artifact11250544577 is retained unchanged:2981790 bytes,
SHA25690affcb2a08938fc0f30488b41ee33188650fc563e35768f5ee859b2ca9fb3d0.
Its native Wasm5, bundle2, game3, typecheck4, browser21 and complete Section17
2023 controls passed with no failures/errors/skips. Native render ran zero
methods with one setup error; complete canonical regression did not run on
that candidate. A successful diagnostic collection step is not browser PASS.

There is no qualified safe browser switch within this tested pinned profile.
The current evidence is consistent with Chromium's compiled PartitionAlloc
pool reservation, but no allocator call-stack was collected; that attribution
remains an inference. No allocator/V8 hardening is disabled, no limit is raised,
and no production browser selection changes. Independent full canonical
regression is now collected separately without suppressing this required red
render gate. Section implementation sign-off remains forbidden.
