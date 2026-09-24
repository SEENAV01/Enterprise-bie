# ADR AUDIO-H1: explicit neural adapter, not a voice-quality declaration

Status: adopted for documented component implementation; production/listening validation pending.

Existing F01 needs an executable neural service integration instead of eSpeak relabelling. Add one ElevenLabs adapter to the current SpeechProvider/SynthesisRequest pipeline. Choose multilingual-v2 as explicit production-narration configuration default and flash-v2.5 as an explicit forced-language option; do not use a product-marketing claim as QA evidence. No automatic voice fallback is permitted.

The official same-response timestamps endpoint allows audio/time binding without a second synthesis pass. Decoding is strict and preserves original request text; provider timestamps remain self-reported, so they do not close independent acoustic F02. Maintain fixture provider and timing identities distinct from the official transport.

Persist response plus timing in a private sealed extension using existing locks/cache contracts. Do not claim this is canonical CAS/kernel-worker adoption. Preserve the existing local and timed-eSpeak modules. Only two inherited SYNC modules are amended for the new explicit timestamp basis and truthful replay-call count; originals remain in lineage. No completed original task numbering is changed and no second Batch005 is created.

Alternative universal provider/SSML/IPA/code-switch implementation was not implied by this change. Unsupported neural capabilities remain explicit errors and backlog limits until an adopted implementation is tested. H1 moves F01 from absent adapter to implemented/contract-tested with live/listening still open; it does not exit AUDIO.
