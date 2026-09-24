# AUDIO Batch 002 — VO-006..010 contracts

## Continuation and scope
Original Section 14 titles are taken from the delivered `docs/audio/ORIGINAL_REGISTRY.json`. This batch implements multilingual terms, a provider-neutral TTS contract, voice selection, actual TTS generation and a local verified TTS cache. It does not modify COMP or any GitHub branch. The standalone dependency fixture retains five byte-identical canonical DIR modules from commit `16d4d87824e77db3565a231a332e7977d39d7117`. No upstream class is imitated with a test double in the real preparation/demo path.

## Batch-001 reconciliation
See BATCH001_RECONCILIATION.md/json and RECONCILIATION_FILE_MAP.json. Both exact original source ZIPs remain available. The modern API remains at `bie.audio`; the older one is explicitly versioned at `bie.audio.compat204`. Both feed one validated source-preserving SpeechPlan. The older 204-test implementation is not merely archived: its complete relocated test suite, CLI, and actual synthesis path execute.

## VO-006 — multilingual terms
`LanguageTerm` binds an exact utterance fingerprint, source offsets, unchanged original term, already prepared spoken text, spoken language, decision ID and evidence. `apply_languages` creates explicit language runs. It preserves all display text, prepared readings, scene/persona IDs, source/objective references and pauses. Locale assignment is not language detection, automatic translation, a new mathematical derivation, or a way to erase unresolved reviews.

Alias/transliteration readings are supplied through the existing scoped lexicon before language annotation. A language term may split a literal span at safe boundaries; it may not split a transformed pronunciation or cross a synthesis-segment/pause boundary. Incorrect surfaces, stale input, overlapping terms and wrong expected speech fail. Actual local examples exercise English, Hindi and an English term inside Hindi narration. This does not establish general multilingual quality or seamless same-voice switching.

## VO-007 — provider-neutral contract
Immutable SpeechSpan/Segment/Plan, AudioFormat, LocaleBinding, Voice/Catalog, SynthesisSettings, SynthesisRequest and ProviderAudio bind text, source, pronunciation, languages, voice/model/runtime identity and format. Typed provider protocol exposes catalog and synthesize. Complete request fingerprints drive cache identity. Unsupported styles, locales, IPA requirements, media formats, or byte/character limits are rejected before synthesis. Unknown settings are not silently dropped.

The current media contract is complete PCM16 WAV. It verifies RIFF length, chunk layout, PCM encoding, channel/rate/block alignment, decoded frame count, nonempty signal, duration and byte bounds. These checks do not recognize spoken words or prove acoustic quality.

## VO-008 — voice selection
Selection requires explicit provider and quality-class allowlists. It preserves a persona's exact chosen voice/model across later calls unless reapproved. Required language coverage, sample format, phoneme/style support and same-voice code-switching are checked. Stable preference/provider/voice order resolves eligible choices. A missing premium/neural provider does not cause silent selection of a technical voice. Updated source, catalog or model identity invalidates stale selections.

## VO-009 — real speech generation
`EspeakProvider` invokes an actually installed eSpeak executable with a documented SSML subset. Runtime identity binds executable, installed voice data, dependent shared libraries and adapter bytes. XML is constructed by escaping source text; no arbitrary input SSML, external audio tags, URLs, shell commands or API credentials are executed from a narration document. Reserved eSpeak phoneme-input syntax is rejected rather than interpreted as ordinary text.

The local adapter supports explicit English/Hindi language bindings discovered on this host, rate, pitch, amplitude and neutral style. It does not support IPA or neural expressive styles; those requests fail rather than silently lose their intent. eSpeak is an explicitly technical formant backend, not the final cinematic voice. CLI use requires `--allow-technical-voice`.

Subprocess output/log/time budgets, process-group cleanup and cancellation are enforced. Only explicitly retryable ProviderFailure errors are retried, with a bounded attempt count. Invalid source/identity/waveform results are not retried into a fake success. Provider receipts must match request, voice and runtime. Whole-waveform samples are validated. A requested pause appends an explicitly counted additional PCM silence interval after provider speech; native provider pauses are not claimed to be measured linguistic pause boundaries. Sample conversion uses half-up integer rounding, recorded in receipts. Word/phoneme timestamps are not fabricated.

This is a bounded local subprocess adapter, NOT a complete hostile-code OS/network sandbox. Production execution isolation must use the adopted deployment controls. No paid provider or cloud neural model was invoked.

## VO-010 — cache
The local namespace/request key covers source and preparation identities, language decisions, persona, selected voice/model/runtime, catalog/selection policy, audio format, rate, pitch, amplitude, style and requested pauses. Changed inputs generate a different key. Each read validates exact request and waveform hashes, real PCM metadata, provider PCM prefix identity, silence samples, schema and unaccepted quality flags.

Per-key Linux file locks avoid duplicate synthesis across cooperating threads/processes. Temporary directories and exclusive/atomic publication keep partial failures invisible. Failed, cancelled, incomplete or tampered results are never reported as cache hits. Namespace isolation, symlinks, unexpected files, missing media, stale model identity and altered metadata are tested. This is a service-account-controlled local cache, not a distributed cache, a signature from a speech provider, or a hostile shared-filesystem guarantee.

## CLI and measured output
`audio_synthesize.py` consumes a real Batch-001 preparation input using an explicit profile, optional language annotations and the actual DIR dependency closure. It writes individual WAVs, a concatenated PCM WAV, sample-based segment positions, original source input, full source/voice/cache receipts and hashes. It refuses existing/symlink output destinations. The concatenation is not loudness mastering, ducking, gapless prosody, word alignment or completed scene synchronization.

## Reproducibility and acceptance
The four technical fixtures use two fresh synthesis processes and a third cache-hit process each. Stable hashes only establish repeatability of this pinned local engine for those inputs. Invocation IDs naturally differ and are not equated with deterministic output. Human listening, pronunciation correctness, voice quality, real-book entailment, word alignment, scene/animation sync, mastering, actual Remotion rendering and enterprise product acceptance remain open.

## Test boundaries
All 204 earlier tests and 144 later tests remain. The new task suites include labelled waveform TEST DOUBLES for provider-failure tests plus a separate actual installed-eSpeak suite. Doubles never constitute speech evidence. Missing eSpeak in a full test deployment is a failure, not a silent skip or substituted waveform. Full preexisting 6,485-test enterprise regression is not claimed for this standalone AUDIO delivery.
