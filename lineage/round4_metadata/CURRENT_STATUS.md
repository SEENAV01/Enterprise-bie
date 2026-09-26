# Section 15 GAME — audit round 4

This cumulative working ZIP adds input-routing repairs and verified native Windows browser evidence. Section 15 is still in hardening; this is not the final Integrated release or canonical GitHub adoption.

Five failures were reproduced before the repair: Enter dispatched multiple authored actions sharing one object; pointer release plus click dispatched multiple times; an accessibility-style click dispatched multiple actions; a secondary action lacked its own accessible control; and a selected challenge could not be routed with its matching learning objective. The sixth regression verified listener disposal. Original failing logs and before-images are preserved.

The generated UI now exposes one primary action per object, separate accessible controls for additional actions, and an explicit chooser when multiple challenges exist. The controller binds distinct controls, handles keyboard input, suppresses the duplicate click following pointer release, and records the selected challenge's objective.

**580 local tests passed**, with zero failures, errors or skips in the portable gate: 544 inherited tests, 13 H7 property/lineage tests, 11 emitted-runtime regressions, 6 differential expression tests and 6 input-routing regressions. This portable gate excludes the Linux-only browser/process suites by scope; it is not a full Linux pass.

The actual compiled React fixture also passed five native Windows browser gestures: Enter, primary click, Submit, selecting the second challenge followed by Submit, and Space. Six observed snapshots show x advancing exactly 1 to 6 and event count exactly 0 to 5, with the second challenge's correct objective and no observed page errors. The fixture, exact source hashes, compile receipt and transcribed visible evidence are included. This is a synthetic fixture; it does not prove real-book acceptance or the Linux/deployed-origin gate.

The earlier 1,062-test Linux success belongs only to the preserved H6 source. The changed candidate still needs its own Linux run, full specification/registry re-audit and section exit review. Canonical integration then requires selective adoption, full enterprise regression, PR/checks/merge, exact remote readback and final backups. Sections 16, 17 and 18 follow; Task 028 stays paused until that sequence is complete.

Automatic approval review rejected the public source upload and required explicit authorization for the payload and destination. The isolated CI security setup was separately approved. No rejected upload was retried or bypassed. The older frozen 39-file round-3 payload does not represent this newer candidate and must not be silently replaced.

Root CURRENT_STATUS.md and CONTINUATION.json describe this checkpoint. Earlier package results and integrated_state remain historical records. Original archives and previously delivered ZIPs are unchanged. implementation_scope_complete=false, github_integrated=false, product_accepted=false.
