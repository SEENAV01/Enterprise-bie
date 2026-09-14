# BIE-DIR-TIME-003 — emphasis timing

Owned source: bie/director/emphasis_timing.py

Direct task dependencies: BIE-DIR-TIME-001, BIE-DIR-LESSON-008.

# BIE DIR timing batch 003

Original tasks BIE-DIR-TIME-001…005 are implemented and unit/contract tested.
GitHub canonical integration is pending the complete DIR section, enterprise
audit and required hardening. This batch is NOT ACCEPTED as a product.

## Authority and scope

The original 18-section atomic registry, page 10, gives the five task IDs,
titles and order. It does not specify these APIs. The APIs and numeric policy
defaults below are new implementation decisions derived from the recovered
DIR contracts and the preserved BIE vision; they are not recovered historical
specifications or empirically established teaching rules.

The canonical base remains SEENAV01/Enterprise-bie at
bc3147db408fc5a5d54017c8b907f580477ff2c3. Original LESSON/SCRIPT module and test
bytes are preserved in this runnable DIR subset. This is a validation bundle,
not the full canonical repository, an integration commit, or a new roadmap.

## Running the delivered bundle

Python 3.12 was used; the implementation requires Python 3.10+ and uses only the
standard library. Run from the extracted bundle root:

```bash
python3 scripts/check_dir_timing.py
python3 examples/timing_walkthrough.py
```

The first command runs all 99 DIR tests: 34 original, 56 new task unit tests,
and 9 cross-contract tests. The second prints a synthetic input/output trace.
Individual atomic ZIPs are provenance units with declared dependencies, not
independent installations. Use this combined bundle to avoid manual assembly.
The existing canonical integrated gate still excludes tests/director; section
integration must connect its test discovery and archive preservation checks.

## Contracts

| Original task | Public entry points | Responsibility |
| --- | --- | --- |
| TIME-001 speech timing | utterances_from_script, estimate_speech, align_reported_speech | Grounded realized text to ordered words and milliseconds; validated script/voice/source lineage |
| TIME-002 pause timing | build_pause_timing | Explicit pause cues at word boundaries; shared-boundary max hold; recorded silence reconciliation |
| TIME-003 emphasis timing | build_emphasis_timing | Explicit source-bound concept anchors to local word slowdown; preserves source EmphasisDecision |
| TIME-004 scene-duration fit | fit_scene_durations | Compose scene-local timeline without loss/double counting; assess soft ScenePacing targets |
| TIME-005 WPM adaptation | adapt_wpm | Content-driven bounded rate proposal, rebuilding all timing dependencies after rate changes |

Working namespace is bie.director. timing_contract.py belongs to TIME-001;
it is shared support, not a sixth atomic task. Existing consumed contracts are
SCRIPT-001 ScriptPlan, SCRIPT-002 VoiceoverDraft, LESSON-007 ScenePacing and
LESSON-008 EmphasisDecision. No existing module is replaced.

### Speech and order

The ScriptPlan adapter requires an explicit complete segment order because
the recovered builder sorts segment IDs. It consumes actual VoiceoverDraft
text, never ScriptSegment.text_intent. Each draft must join one existing
segment and its evidence must be a nonempty subset of that segment's evidence.
Unsupported claims remain withheld and review flags propagate.

SpeechUtterance carries utterance, segment, scene, voice and language IDs,
realized text, evidence/objective IDs and the script fingerprint. Direct
SpeechUtterance construction supports multiple speakers/utterances, but its
source claims must be supplied by the upstream structured script producer.
Timing validation verifies internal consistency, not the truth of source IDs.
Scenes must be contiguous in caller-supplied narrative order. Multiple script
revisions cannot be mixed in one speech plan. No learner profile is required.

WordTiming uses zero-based lexical indices and exact text character offsets.
The unicode-word-runs/1 tokenizer counts Unicode alphanumeric runs and internal
apostrophes. It is a transparent lexical estimate, not a language-specific
pronunciation engine. Numbers/symbols and non-English/non-ASCII lexical text
carry explicit realization/tokenization review flags. Prefer expanded spoken
narration for equations and numbers; AUDIO alignment must eventually replace
estimated word times. Char anchors and all timestamps bind the exact text.

ESTIMATED_WPM uses cumulative ceil(i * 60000 / wpm) boundaries. Default WPM is
150, with configurable bounds 80–200; the contract supports finite operational
bounds within 1–1000. These defaults are engineering heuristics. All estimates
remain reviewable, including apparently ordinary English prose.

REPORTED_AUDIO_ALIGNMENT accepts one complete utterance audio clip record per
utterance, with a sha256 content reference, exact utterance fingerprint,
aligner version, duration and one nonoverlapping positive interval per word.
The utterance hash binds text, voice and grounding. Intervals are clip-local;
the scene composer concatenates clips in the requested order. The adapter
does not read audio bytes or establish the accuracy of a caller's alignment.
audio_verified therefore stays false. Full-audio segmentation, acoustic QA
and actual measured audio verification remain AUDIO/QA responsibilities.

### Pause and emphasis

Pause boundary 0 is before word 0; boundary N follows the last word. Explicit
cue reasons and evidence are required. Coincident cues share max(duration),
not their sum. Within a scene, the previous utterance's tail and the next
utterance's head are one shared boundary. Pauses across different scenes are
separate scene-local requests. covered_boundaries preserves both clip anchors.

For estimates, missing silence is added once. For reported clips, leading,
internal, trailing and shared tail/head silence already contributes to the
clip duration. Available silence is compared with the requested hold. Shortfall
sets requires_rerender/requires_audio_replan; the existing audio is never
stretched or supplied with invented timing. Overlapping audio intervals fail.

EmphasisAnchor uses an explicit half-open [start_word, end_word) span and an
existing EmphasisDecision; no semantic mapping is guessed from keywords.
Evidence must belong to that utterance. Overlapping spans are rejected for
upstream resolution. Requested local rate factor is 1 − 0.25 * emphasis by
default. Effective estimated WPM cannot fall below the speech policy floor.
Word duration is conservatively rounded upward when slowed; floor-limited
emphasis is flagged. A zero-strength or floor-blocked request adds no time.
Reported audio word times stay fixed and emphasis needs acoustic QA.

### Scene fit and rate adaptation

SceneDurationPlan exposes speech, planned pause and recorded-gap events with
source/objective/concept/cue anchors, exact predecessor fingerprints, policies,
review reasons and basis. Times start at zero within each scene. Total duration
equals all original speech/recorded gaps + additional pauses + emphasis time.
No words, audio gaps or source references are dropped to meet a target.

ScenePacing is optional and its targets are soft. Status is NO_TARGET,
WITHIN_TARGET, EXTEND or SPLIT_OR_EXTEND. The split hint defaults to 1.5 times
the preferred target and does not split or truncate a scene. The independent
requires_audio_replan flag must be consumed even when duration fits.

planning_upper_ms adds a configurable 20% engineering margin to estimated
speech plus emphasis (pauses remain exact). It is not a statistical confidence
bound or an empirically calibrated comprehension guarantee. Target fit can
coexist with an uncertainty/review warning. Reported alignment gets no invented
statistical margin and still requires audio QA.

ContentLoad has source-bound conceptual complexity, prerequisite novelty and
notation scores in [0,1]. Its default rate factor is
1 − 0.20*conceptual − 0.10*novelty − 0.15*notation. Preferred WPM and content
ceiling apply that factor to the speech policy default/maximum respectively,
clamped at its minimum. All weights/version identifiers remain in the result.
Repeated adaptation derives from the policy baseline, avoiding cumulative
slowdown. These supplied load scores are not an automatically inferred or
empirically calibrated learner model.

For estimates, all scene budgets are checked including pauses and emphasis.
If needed, a bounded deterministic search over 0.1-WPM candidates (plus the
exact ceiling endpoint) finds a fitting rate, followed by actual candidate
recomposition. Minimal-rate optimality is not claimed at millisecond rounding
boundaries. If the content ceiling cannot fit, EXTEND_OR_SPLIT_REQUIRED keeps
the preferred content rate. No text is removed, pause shortened or ceiling
exceeded. For reported audio, AUDIO_REPLAN_REQUIRED preserves the original
audio alignment and returns no newly asserted speaking rate.

## Validation boundaries and follow-up

The suite checks arithmetic, order, source/revision mismatch, NaN/infinity/bool,
grounding, generator inputs, invalid/overlapping spans, reported audio gaps,
shared pause boundaries, deterministic fingerprints, dense-content rate bounds,
unsatisfiable targets and recovered-script-to-timeline contracts. Synthetic
fixtures and a small deterministic property grid are not real-book benchmarks.

The three recovered legacy observations stay open for the DIR section audit:
LESSON-001 scene-parent cycles, SCRIPT-001 blank grounding IDs, and SCRIPT-010
blank game-handoff IDs. New timing boundaries reject malformed narration
inputs, but do not claim those original source modules are corrected.

Next original work is SYNC-001…005, then QA-001…007. Scene timelines provide
explicit word/cue/concept anchors for SYNC. Real BI/KI/PR/MATH/RE/PED/DIR
textbook lineage, calibrated multi-domain benchmarks, visual/animation
consumers, actual audio/render QA, playable-game runtime QA and cumulative
learning remain required before product acceptance. The original vision and
the section-completion GitHub workflow are unchanged.
