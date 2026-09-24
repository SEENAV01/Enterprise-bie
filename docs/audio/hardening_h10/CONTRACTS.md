# AUDIO Hardening H10 Contracts

Scope: close the **implementation-side** of `AUDIO-AUDIT-001-F04` while preserving the section-end GitHub-integration rule and every external/acceptance boundary.

Key invariants:
- canonical DIR narration is accepted only through exact `SpeechUtterance` → `SpeechPlan` identity, source, objective, script, scene, voice and text binding; H10 never rewrites narration;
- the AUDIO→COMP adapter emits the exact `compiler_h6` narration fields and content-addressed PCM WAV shape observed at canonical `main` `dfc1ef9b59bf7d3a8f099a8ad2fb4a93895257e8`, pinned to the observed COMP source blob identities;
- final mixed AUDIO bytes are the media source for downstream narration assets; frame-quantization padding may add trailing silence but may never truncate speech;
- pronunciation repair preserves source/reading and invalidates all dependent AUDIO clock/caption/QA, COMP generated-source and render products; it does not invent a second orchestrator or mutate the canonical repository in this ZIP track;
- technical rendered evidence must come from a real bounded native process, contain actual video + audio + a non-empty round-tripped caption stream, and be byte/hash verifiable;
- FFmpeg technical AV evidence is **not** a Remotion render, cinematic-quality certificate, independent listening result or product acceptance;
- current pinned Remotion full compile/render remains a downstream environment/integration gate because the standalone AUDIO workspace does not contain/install the pinned React/Remotion toolchain;
- GitHub writes remain forbidden until the AUDIO section has passed final full regression and re-audit;
- `product_accepted`, section exit and full AUDIO regression remain false in H10.
