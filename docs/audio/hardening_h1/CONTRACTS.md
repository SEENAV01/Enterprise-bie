# AUDIO H1 — neural-provider adoption contracts

## Scope and authority
Continue the exact Batch005 package (SHA-256 `87c295e3ed54a22c2b04609453c2922e25126e0c23e8bf80b5ba3e600ae33ac1`) and its finite AUDIO-AUDIT-001-F01..F04 backlog. H1-001..005 are new engineering task subdivisions of F01, not recovered or original-registry IDs. Original 25 task records, both reconciled Batch001 implementations and local speech providers are preserved. This is not a new full section re-audit. No GitHub write is performed.

## Implemented path
Realized DIR/144 or compat204 preparation -> existing SpeechPlan -> explicit NeuralDeployment + existing VoiceCatalog/selection -> existing TTSCache/generate_speech -> ElevenLabsProvider -> exact PCM response + original character timestamps -> existing AlignedSpeech, captions, scene/animation/pause clock -> existing MIX publication -> existing QA.

`prepare_neural_sync` returns the existing SynchronizedAudio type. It does not create a competing timeline or storage/orchestration framework. An operator may continue using the unchanged local eSpeak adapters explicitly; there is no automatic cloud-to-local voice downgrade.

## Supported deployment contract
A named voice, operator deployment revision, full model/voice metadata fingerprints, primary two-letter language, usage/rights references and explicit data-transfer approval are required. Settings include stability, similarity, style, speaker boost, speed and optional seed. Supported modes are `eleven_multilingual_v2` with **provider_auto language** and `eleven_flash_v2_5` with **enforced language_code**. The default is the former; there is no model fallback. The multilingual-v2 API does not enforce language_code, so a requested forced-language contract is rejected instead of being silently ignored.

The actual current model/voice metadata is fetched before every uncached remote synthesis and compared with the approved snapshot. TTS capability, language, length, style and speaker-boost support are checked. Metadata or settings change invalidates the deployment/cache identity. These are remote model aliases, **not immutable neural-weight hashes**. An unchanged cached response is reuse of old approved request bytes, not a fresh check of account rights/revocation or backend weights.

Only mono PCM16 at 16,000/22,050/24,000 Hz is currently adopted. Maximum source request length is 4,000 characters, bounded further by the model's response metadata. This is an engineering bound, not a claim that the API has no larger formats/contexts. Existing prepared segments are used; overflow raises a specific error, never truncates speech. Voice speed is explicitly bounded to 0.7–1.2 in this implementation. Legacy WPM/pitch/amplitude controls cannot silently translate to unrelated neural controls: nondefault unsupported fields reject.

Source-bound alias/expanded pronunciation text is sent exactly. Provider normalization is off. Pronunciation phonemes/IPA, mixed language runs within one utterance, provider dictionary uploads, SSML, v3 tags, conversational streaming, cloning and expressive voice-directing automation are not adopted here. Existing local capabilities are retained. Bracket/tag-like unprepared instructions reject rather than being interpreted as emotion or control instructions.

Adjacent text context is available only from the same exact SpeechPlan and the same scene/persona. Its full plan fingerprint binds provider/runtime/cache identity. The adapter sends previous_text/next_text only, never truncates neighbor text, never substitutes caller text from another plan, and does not claim prosody continuity has been independently heard or graded.

## HTTP, credential and side-effect contract
Only official `api.elevenlabs.io` HTTPS endpoints are allowed: model listing, one approved voice, and the speech-with-timestamps route. Standard certificate verification is enabled. Redirects, compressed/unexpected content, missing required request identity, malformed length, extra-large responses and unknown origin/path are rejected. No secret is included in command-line arguments, reports, response-store entries, provider representation or published examples. The secret is read from `ELEVENLABS_API_KEY` only after explicit CLI opt-in.

`--allow-live-provider` permits remote calls; the deployment must independently approve source-data transfer before synthesis. The catalog probe sends no narration and creates an unapproved template. Live generation can incur provider charges. There is no automatic retry of ambiguous POST timeouts/errors, because the remote service might already have completed or charged a request. Deadline/cancellation terminates the local child, **not a guarantee of remote cancellation or refund**. Per-call response size is <=7.5 MB and deadline <=180s; the provider enforces a total budget across metadata and synthesis calls. Public provider code fixes the worker target; offline tests do not gain the live identity.

The killable transport child is not the canonical kernel-isolated BIE worker. Private filesystem permissions, fixed HTTPS origin and process deadlines do not close F03. Canonical deployment/secret/network/resource isolation, durable CAS, lease recovery and distributed job accounting are still required.

## Same-response audio/timing contract
One successful JSON response must contain raw PCM and original character timing whose characters reconstruct exact prepared spoken text. If normalized_alignment is supplied, it must also reconstruct the same text. All timing values must be finite, ordered, in bounds and yield positive non-overlapping spoken-word windows. Decimal-second conversion uses explicit sample rounding. Unsupported/mismatched text or events are rejected **before response-cache persistence**, not repaired by interpolated timings.

The PCM is wrapped in WAV without modifying samples. Alignment must match the exact ProviderAudio/SpeechAsset bytes and invocation. Existing requested pauses are appended by existing speech production and counted once by existing SYNC. Source codepoint spans and pronunciation-rule references survive; engine replay is zero for these same-response timings.

A synthetic timing basis cannot satisfy the existing measured-event gate by default. An explicit process-local diagnostic context is required for fixture generation, MIX publication and reload; live CLI never enters it. The basis must also match the fixture provider identity. Relabelling fixture timings as the live provider basis is rejected. This does not create a release/acceptance override.

Provider timings are not independently measured phonetic word endings, correct pronunciation or an acoustic alignment certificate. Their basis is explicit. A contract fixture has a distinct provider/runtime identity and `NEURAL_CHARACTER_FIXTURE_SAME_PCM`, requires explicit opt-in, and cannot be represented as live neural speech. Downstream QA continues to require review.

## Cache and evidence
NeuralResponseStore retains the exact successful JSON response together with a local HMAC seal, keyed by the existing exact speech-request fingerprint. Source, pronunciation, model/voice settings, deployment, adjacent context and output format all affect identity. Store loads validate request/runtime/payload/response identity and the seal. A changed response plus recomputed public hash cannot pass without the private key. Store publication is exclusive/atomic, under the existing lock helper. If the waveform TTS cache exists but its timing response is unavailable, **do not synthesize again** and attach timings from different speech; raise an explicit missing-evidence error.

The seal key is a private 32-byte file outside entries, created exclusively with restricted permissions; it is never placed in a delivery bundle. This local HMAC is not an ElevenLabs signature, not independent QA, and not protection from a malicious owner of the signing service/key. Canonical artifact authority belongs to F03; evaluator authority belongs to F02.

Published MIX inputs now also include the exact successful provider response(s), response hashes, request IDs and source-bound timing evidence. The API credential and private seal are never exported. The existing publication manifest binds these bytes. Response publication does not prove publisher authenticity independently of the TLS acquisition record.

## Verification boundaries
H1 tests exercise explicit HTTP-shape fixtures and real local transport process behavior (deadline/cancel/crash). Four synthetic response/PCM cases execute the existing native FFmpeg MIX, publication, reload and QA; each is repeated in two independent CLI processes. They are synthetic tones with fabricated character times, **not neural speech**. No paid provider request or real neural waveform is generated during this release. Real-world metadata variations, voice response/schema behavior, listening quality, pronunciation, end-to-end latency and acoustic alignment remain unverified.

F01 is **adapter implemented/contract-tested, live execution and listening pending**, not closed. F02/F03/F04 remain open. No full 6,485-test enterprise regression, real Remotion output, real-book lesson, cinematic acceptance or section exit is claimed.
