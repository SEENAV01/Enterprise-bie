# AUDIO Batch 001: source-to-speech preparation contracts

This is continuation of canonical BIE, not a replacement book-to-video product. Original Section 14 tasks VO-001..005 are implemented here. The registry supplies their names; these implementation contracts make them executable. The current output is a pronunciation/preparation artifact, NOT sound, a provider request, accepted pedagogy or an accepted lecture.

## Existing producer adoption

`from_director_script()` calls the real canonical `validate_script_plan()` and `utterances_from_script()` producers. They accept the existing `ScriptPlan`, realized `VoiceoverDraft` records, explicit narrative order and locale, and produce the existing `SpeechUtterance` records. `text_intent` is never narrated. Source/objective IDs, exact text, voice, scene, script revision and unresolved upstream review reasons are preserved. The canonical production director also uses these original types; this batch does not run a live director LLM or a book extraction pipeline.

Five upstream files are included only as an immutable, blob-verified standalone dependency fixture. Production `bie/audio/` imports canonical `bie.director`, never archived ZIPs or the fixture directory. The standalone CLI requires `--standalone-fixture` to opt into that test environment. No canonical source files were modified.

## VO-001: segmentation

Offsets are Unicode code points, never guessed UTF-16 offsets. Segments reconstruct each original utterance exactly, including whitespace, trailing text, negation, source references and explicit pauses. Scene/voice/revision boundaries are never merged. Hard char/UTF-8/request-count limits are operational limits, not a fixed lesson duration. Splitting happens at safe sentence/whitespace boundaries, with conservative abbreviation and decimal handling. Protected equation/term spans, grapheme joins and CRLF are not split. An indivisible over-limit unit fails explicitly rather than truncate. Supplied pauses own an exact boundary and remain requested milliseconds, not measured speech times. Plan validation recomputes the complete plan from its original inputs.

## VO-002: lexicon

Frozen versioned entries declare surface, locale, domain/sense, alias or IPA, case policy and evidence references. Selection is exact-locale first with optional explicit primary-language fallback. Exact domain outranks wildcard; unresolved homographs or equally specific conflicting rules fail. Phrase scanning is longest whole-token match, preserving original offsets. No implicit inflection, proper-name lookup, remote dictionary fetching or acoustic validation is claimed. A PLS alias/IPA subset can be safely exported with escaped XML; no remote XML import exists.

## VO-003: math reading

An actual bounded tokenizer and AST parser read numbers, single Latin/known Greek symbols, groups, arithmetic, fractions, one relation, powers/subscripts, square roots, vectors and explicit grouped sin/cos/tan/log/ln/exp. Operator scope and negation are preserved, with spoken boundaries for fractions/groups/functions; no CAS simplification is performed. Only numeric juxtaposition such as 2x is supported; f(x), unknown multi-letter identifiers and unsupported LaTeX commands fail rather than be guessed. Multi-digit or signed scripts require explicit groups. Leading zeros/decimal zeros and scientific exponents are preserved. English and a technical Hindi reading convention are supported; Hindi integers above twenty use explicitly labelled digit reading, not a claim of natural cardinal-number speech. Phonetic quality, proof correctness, calculus/matrix/chemistry language and general LaTeX are not certified.

Only explicit `\( ... \)` math markers are auto-discovered. Dollar currencies are not silently interpreted as math. Other formulas may be passed as exact revision-bound spans by the upstream stage.

## VO-004: symbols

Exact symbol/locale/domain/sense lookup supports explicit technical units and ambiguous symbol resolution. Uppercase/lowercase and unit powers remain distinct. A small English/Hindi comparison/percent reading convention is supplied. Degree, mu/micro, variable/unit or subject-specific ambiguity requires a declared rule/sense; no dimensional or physical inference is made. Rule evidence is a source identifier, not an independently verified pronunciation judgement.

## VO-005: acronyms and combined preparation

Explicit LETTERS, WORD or EXPANSION modes distinguish initialisms from spoken acronyms. Expansions and word readings require supplied evidence. Unknown uppercase candidates remain visible review items; ordinary lowercase words are not silently expanded. Default letter names are a versioned technical convention, not a universal accent model. General code-switching/multilingual term policies remain VO-006.

Combined preparation automatically applies scoped lexicon matches, recognized explicit math and declared acronym policies. Every change has an original span and a typed reading; display/caption text stays unchanged. Ambiguous or still-unowned numerical/symbolic text prevents a clean preparation result. Spoken expansion length is checked separately: overflow is reported without truncation, and provider-aware rechunking remains a downstream TTS-contract obligation. IPA is retained as an explicit provider requirement, not dropped into a plain-text approximation. Revision/voice/table/policy changes invalidate preparation identities. A direct validator recomputes the preparation rather than trusting a caller-authored PASS flag.

## Execution, publication and truth boundary

The CLI emits complete UTF-8 JSON through an exclusive atomic file publication. Existing receipts are never overwritten. Exit zero means preparation succeeded within these contracts; exit two signals review or a blocking input error. No WAV/MP3 file is created, no TTS API or provider key is used, and no duration or alignment result is fabricated. `tts_request_ready`, `audio_generated`, `audio_verified` and `product_accepted` remain false.

Full canonical regression is not rerun in this delivery; the locally executed tests use the exact selected canonical DIR dependencies. GitHub main and its existing 6,485-test CI record remain unchanged. Complete enterprise regression and artifact integration belong to the AUDIO section-end adoption workflow.
