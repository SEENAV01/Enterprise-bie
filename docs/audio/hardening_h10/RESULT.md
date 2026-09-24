# AUDIO Hardening H10 — F04 canonical handoff, invalidation and rendered-AV evidence

H10 continues the exact H9 Integrated parent and implements five bounded F04 tasks:

- **H10-001** — exact canonical DIR `SpeechUtterance` → AUDIO `SpeechPlan` identity/source/objective/voice binding.
- **H10-002** — canonical-main-pinned AUDIO → COMP `compiler_h6` narration/media/frame/caption handoff with content-addressed final-mix PCM assets and no speech truncation.
- **H10-003** — repair-owned transitive invalidation from TTS cache through SYNC/MIX/captions/animation clocks/QA/COMP generated source/render, while unchanged DIR source/reading stays intact.
- **H10-004** — actual bounded FFmpeg technical AV render with real H5 synthetic eSpeak mixed WAV, H.264 video, AAC audio and an embedded `mov_text` caption stream that is independently round-tripped back to SRT and text-matched.
- **H10-005** — F04 implementation evidence gate binding DIR handoff, COMP handoff, invalidation and actual technical rendered evidence.

Fresh H10 focused verification: **62/62 PASS**. H9 governance + AUDIO reconciliation compatibility: **83/83 PASS**. Combined targeted execution: **145/145 PASS**, zero failures/errors/skips. The H10 tests also execute and validate the actual H5 local TTS/SYNC/MIX bundle used by the handoff fixtures.

Native technical evidence was executed with FFmpeg/FFprobe 7.1.5. The generated technical MP4 contains video, audio and a non-empty caption packet; the caption stream was extracted and its caption text matched the original generated SRT. A representative video frame was decoded and inspected. This proves the bounded AV/caption plumbing for the synthetic fixture, not pedagogical/cinematic quality.

**Truth boundary:** real Remotion compile/discovery/full render was not executed in this standalone AUDIO package; the current canonical compiler contract is pinned by commit/blob identity and adapter schema, and canonical GitHub integration is intentionally deferred until section completion. Live neural listening, independent multilingual calibration, production KMS/HSM/fleet deployment and real-book E2E remain external/downstream gates. Full AUDIO regression and final re-audit are still mandatory next. Product acceptance is false.
