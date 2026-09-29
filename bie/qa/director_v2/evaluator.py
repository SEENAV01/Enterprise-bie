"""Four fail-closed director evaluators over byte-verified text and finite plans.

Semantic understanding still requires governed, authenticated contextual review.
Checks never treat a positive review as permission to ignore a structural failure.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import defaultdict
from fractions import Fraction
import re
from ..release_v2.contracts import ContractError, digest, integer
from ..source_v2.evaluator import evaluate as evaluate_source, EvaluationPair
from ..source_v2.models import Finding, Report
from .models import DirectorRequest, DirectorPolicy
from .attestation import Review, ReviewVerifier, review_targets
from .metrics import (merged_text, identity, codepoints, rate, ceil_fraction, contains_term,
                      sentence_lengths, has_unsafe_controls, needs_expanded_readout, windows)
from .adapters import to_native

LIMITATIONS = (
    'This is declared-plan and text QA, not evidence of rendered video, audible narration, cinematic engagement, game execution or learner comprehension.',
    'Scene purpose, promise payoff, term explanation, semantic transitions, source transformations and audience suitability require externally governed contextual assessments. Authentication does not establish assessor quality.',
    'Literal vocabulary, repetition, sentence and placeholder checks are bounded diagnostics. They are not universal language understanding or a validated age/reading-level score.',
    'Code-point rates and timeline gaps are operator-defined audience/language guardrails, not words-per-minute, empirical cognitive load or measured synthesized speech. Planned spoken forms are not produced audio.',
    'Only explicitly operator-enumerated finite routes are checked. Runtime branch equivalence, loops, canonical caller adoption and full-repository regression remain separate obligations.',
    'No live assessor, model, native PDF/OCR, audiovisual renderer, learner study or real-book end-to-end pipeline is executed here. Local fixture tests never authorize enterprise acceptance.',
)
AREAS = ('narrative', 'script', 'pacing', 'fidelity')
TASKS = dict(zip(AREAS, [f'BIE-QA-DIR-00{i}' for i in range(1, 5)]))
TEACHING = ('explanation', 'demonstration', 'payoff')
REPEAT_ROLES = ('recap', 'retrieval', 'feedback', 'emphasis')


@dataclass(frozen=True, slots=True)
class DirectorResult:
    source: EvaluationPair
    narrative: Report
    script: Report
    pacing: Report
    fidelity: Report
    native_architecture_fingerprint: str
    native_script_fingerprint: str
    @property
    def status(self):
        values = [self.source.grounding.status, self.source.provenance.status] + [getattr(self, k).status for k in AREAS]
        return 'BLOCKED' if 'BLOCKED' in values else ('REVIEW_REQUIRED' if 'REVIEW_REQUIRED' in values else 'CHECKS_PASSED')
    @property
    def product_accepted(self): return False
    def to_dict(self):
        d = {k: getattr(self, k).to_dict() for k in ('source',) + AREAS}
        d.update(status=self.status, product_accepted=False, native_architecture_fingerprint=self.native_architecture_fingerprint,
                 native_script_fingerprint=self.native_script_fingerprint)
        return d
    @property
    def content_digest(self): return digest(self.to_dict())


def evaluate(request, artifact_root, policy, *, as_of, reviews=(), verifier=None,
             source_assessments=(), source_verifier=None):
    if type(request) is not DirectorRequest or type(policy) is not DirectorPolicy:
        raise ContractError('DIR_EVALUATION_INPUT_TYPE')
    integer(as_of, 'as_of')
    if type(reviews) is not tuple or len(reviews) > 32768 or any(type(x) is not Review for x in reviews):
        raise ContractError('DIR_REVIEW_COLLECTION')
    if len({x.review_id for x in reviews}) != len(reviews): raise ContractError('DIR_DUPLICATE_REVIEW_ID')
    if len({(x.purpose, x.subject_id, x.evaluator_id) for x in reviews}) != len(reviews):
        raise ContractError('DIR_DUPLICATE_REVIEW_VOTE')
    verifier = ReviewVerifier() if verifier is None else verifier
    if type(verifier) is not ReviewVerifier: raise ContractError('DIR_REVIEW_VERIFIER_TYPE')
    claims = {c.claim_id: c for c in request.source.claims}
    if sum(len(claims[c].text) for b in request.beats for c in b.claim_ids if c in claims) + sum(len(claims[c].text) for x in request.spoken_forms for c in x.claim_ids if c in claims) > 16_000_000:
        raise ContractError('DIR_TEXT_WORK_LIMIT')
    source = evaluate_source(request.source, artifact_root, policy.source, as_of=as_of,
                             assessments=source_assessments, verifier=source_verifier)
    groups = {k: [] for k in ('common',) + AREAS}
    groups['common'].extend(source.grounding.findings + source.provenance.findings)
    def add(area, code, subject, detail, severity='BLOCKER'):
        groups[area].append(Finding(code, severity, subject, 'DIR.QA', detail))
    targets = review_targets(request); votes = {t: set() for t in targets}; invalid = set()
    rd, pd = request.content_digest, policy.content_digest
    for a in sorted(reviews, key=lambda x: x.review_id):
        t = a.purpose, a.subject_id
        if t not in targets:
            add('common', 'DIR_UNKNOWN_REVIEW_TARGET', a.subject_id, 'Unexpected review target cannot add approval.'); continue
        if set(a.evidence_ids) != set(targets[t]):
            add('common', 'DIR_REVIEW_EVIDENCE_MISMATCH', a.subject_id, 'The review must bind the exact evidence inventory.'); invalid.add(t); continue
        auth = verifier.verify_bound(a, rd, pd, policy.max_receipt_age_seconds, as_of)
        if not auth.authenticated:
            add('common', auth.code, a.subject_id, 'Review authenticity, scope or freshness failed.'); invalid.add(t); continue
        if not auth.operational:
            add('common', 'DIR_TEST_ONLY_REVIEW', a.subject_id, 'A synthetic/test-only review is not operational evidence.', 'REVIEW'); invalid.add(t); continue
        if a.verdict == 'REJECTED':
            add('common', 'DIR_REVIEW_REJECTED', a.subject_id, 'A reviewed rejection cannot be outvoted.'); invalid.add(t)
        elif a.verdict == 'UNCERTAIN' or a.confidence_ppm < policy.minimum_review_confidence_ppm:
            add('common', 'DIR_REVIEW_UNCERTAIN', a.subject_id, 'Uncertain or low-confidence assessment needs review.', 'REVIEW'); invalid.add(t)
        else: votes[t].add(auth.independence_group)
    for t in sorted(targets):
        if t not in invalid and len(votes[t]) < policy.minimum_independent_assessors:
            add('common', 'DIR_REVIEW_QUORUM_MISSING', t[1], 'Current independent contextual assessment is missing.', 'REVIEW')
    if (request.lesson_id, request.audience_id, request.language) != (policy.lesson_id, policy.audience_id, policy.language):
        add('common', 'DIR_LEARNER_SCOPE_MISMATCH', 'director-scope', 'The candidate cannot redefine the lesson, audience or language.')
    scenes = {s.scene_id: s for s in request.scenes}; beats = {b.beat_id: b for b in request.beats}
    scene_specs = {s.scene_id: s for s in policy.scenes}; route_specs = {r.route_id: r for r in policy.routes}
    citations = {c.citation_id: c for c in request.source.citations}; facets = {f.facet_id: f for f in policy.facets}
    for actual, expected, label in [(set(scenes), set(scene_specs), 'SCENE'),
                                   ({r.route_id for r in request.routes}, set(route_specs), 'ROUTE'),
                                   ({p.promise_id for p in request.promises}, set(policy.expected_promise_ids), 'PROMISE')]:
        if actual != expected:
            add('common', 'DIR_' + label + '_SCOPE_MISMATCH', 'director-scope', 'Missing or unexpected members do not redefine operator scope.')
    if not beats: add('common', 'DIR_EMPTY_BEATS', 'director-scope', 'An empty script cannot pass.')
    for s in request.scenes:
        spec = scene_specs.get(s.scene_id)
        if spec and (set(s.objective_ids) != set(spec.objective_ids) or set(s.parent_scene_ids) != set(spec.parent_scene_ids) or s.role not in spec.allowed_roles):
            add('narrative', 'DIR_SCENE_REQUIREMENT_MISMATCH', s.scene_id, 'Scene role, objective or required dependency differs from policy.')
    # Native builders are genuinely called, not only imported by unused adapters.
    af = sf = ''
    try:
        native = to_native(request, policy.policy_id)
        af = native.architecture.fingerprint(); sf = native.script.fingerprint()
    except (ContractError, ValueError, KeyError) as exc:
        add('common', 'DIR_NATIVE_CONTRACT_INVALID', 'director-scope', 'Pinned native architecture/script contracts rejected this projection.')
    texts = {}; by_scene = defaultdict(list); occurrences = defaultdict(list); valid = set()
    output_channels = {o.output_id: o.channel for o in request.source.outputs}
    channel_compatibility = {'narration': ('narration',), 'dialogue': ('narration',), 'on_screen': ('on_screen', 'caption', 'game_prompt', 'game_feedback', 'lesson')}
    for b in sorted(request.beats, key=lambda x: x.beat_id):
        if b.scene_id not in scenes or not set(b.claim_ids) <= set(claims):
            add('common', 'DIR_BEAT_REFERENCE_MISSING', b.beat_id, 'Scene and text references must resolve.'); continue
        if b.end_ms > scenes[b.scene_id].duration_ms:
            add('pacing', 'DIR_BEAT_OVERFLOW', b.beat_id, 'Declared speech/text cannot overflow its scene.'); continue
        if not set(b.objective_ids) <= set(scenes[b.scene_id].objective_ids):
            add('narrative', 'DIR_BEAT_OBJECTIVE_OUTSIDE_SCENE', b.beat_id, 'Beat purpose is outside the approved scene.'); continue
        if b.role in TEACHING + ('recap',) and not b.objective_ids:
            add('narrative', 'DIR_BEAT_OBJECTIVE_MISSING', b.beat_id, 'Teaching and recap require an explicit learning purpose.')
        try: txt = merged_text(claims, b.claim_ids)
        except ContractError:
            add('common', 'DIR_TEXT_SPAN_CONFLICT', b.beat_id, 'Overlapping spans conflict.'); continue
        if b.channel != 'pause' and any(output_channels.get(claims[c].output_id) not in channel_compatibility[b.channel] for c in b.claim_ids):
            add('common', 'DIR_CHANNEL_MISMATCH', b.beat_id, 'A declared output channel cannot masquerade as another medium.'); continue
        texts[b.beat_id] = txt; valid.add(b.beat_id); by_scene[b.scene_id].append(b)
        for c in b.claim_ids: occurrences[c].append(b)
        if has_unsafe_controls(txt): add('script', 'DIR_HIDDEN_OR_INVALID_TEXT', b.beat_id, 'Control characters or replacement glyphs require repair.')
        if re.search(r'\{\{[^{}]*\}\}|\[(?:TODO|TBD|INSERT[^\]]*)\]|\b(?:TODO|TBD|FIXME)\b', txt):
            add('script', 'DIR_UNRESOLVED_PLACEHOLDER', b.beat_id, 'Unresolved drafting markers remain in the actual declared script.')
        if any(n > policy.pacing.max_sentence_codepoints for n in sentence_lengths(txt)):
            add('script', 'DIR_SENTENCE_GUARDRAIL', b.beat_id, 'A sentence exceeds the configured audience/language guardrail.', 'REVIEW')
    for s in request.scenes:
        if not any(b.channel != 'pause' for b in by_scene[s.scene_id]):
            add('narrative', 'DIR_SCENE_WITHOUT_SCRIPT', s.scene_id, 'A pause-only or empty scene does not satisfy a required educational scene.')
    spoken = {s.beat_id: s.text for s in request.spoken_forms}
    for form in request.spoken_forms:
        bid = form.beat_id
        if not form.claim_ids:
            add('common', 'DIR_SPOKEN_FORM_UNGROUNDED', bid, 'Expanded narration needs actual inspected output text, not just metadata.', 'REVIEW')
        elif not set(form.claim_ids) <= set(claims) or any(output_channels.get(claims[c].output_id) != 'narration' for c in form.claim_ids):
            add('common', 'DIR_SPOKEN_FORM_EVIDENCE_INVALID', bid, 'Expanded speech references must resolve to narration output claims.')
        else:
            try:
                exact = merged_text(claims, form.claim_ids)
                if exact != form.text:
                    add('common', 'DIR_SPOKEN_FORM_TEXT_MISMATCH', bid, 'The expansion differs from the inspected output spans.')
                if bid in valid and beats[bid].channel in ('narration', 'dialogue'):
                    for cid in form.claim_ids:
                        if beats[bid] not in occurrences[cid]: occurrences[cid].append(beats[bid])
            except ContractError:
                add('common', 'DIR_SPOKEN_FORM_EVIDENCE_INVALID', bid, 'Expanded speech has conflicting source spans.')
    if set(occurrences) != set(claims): add('common', 'DIR_UNPRESENTED_CLAIMS', 'director-scope', 'Every declared output claim must appear in the scene/beat inventory.')
    for bid in spoken:
        if bid not in valid or beats[bid].channel not in ('narration', 'dialogue'):
            add('pacing', 'DIR_SPOKEN_FORM_ORPHAN', bid, 'Spoken forms require a valid spoken beat.')
        if has_unsafe_controls(spoken[bid]): add('script', 'DIR_HIDDEN_OR_INVALID_SPOKEN_TEXT', bid, 'Expanded speech contains hidden or invalid text.')
        if re.search(r'\{\{[^{}]*\}\}|\[(?:TODO|TBD|INSERT[^\]]*)\]|\b(?:TODO|TBD|FIXME)\b', spoken[bid]):
            add('script', 'DIR_UNRESOLVED_SPOKEN_PLACEHOLDER', bid, 'Expanded speech contains unresolved drafting markers.')
    rates = {}; max_speech = max_screen = peak_speakers = 0; window_count = 0
    for bid in sorted(valid):
        b = beats[bid]; txt = texts[bid]
        if b.channel in ('narration', 'dialogue'):
            if needs_expanded_readout(txt) and bid not in spoken:
                add('pacing', 'DIR_MATH_READOUT_REQUIRED', bid, 'Mathematical notation needs a reviewed expanded spoken plan.', 'REVIEW')
            # A supplied short readout cannot lower the cost of the inspected script.
            value = rate(max(codepoints(txt), codepoints(spoken.get(bid, txt))), b.end_ms - b.start_ms)
            max_speech = max(max_speech, ceil_fraction(value))
            if value > policy.pacing.speech_codepoints_per_minute:
                add('pacing', 'DIR_SPEECH_RATE_EXCEEDED', bid, 'Declared spoken text exceeds the approved code-point rate.')
        elif b.channel == 'on_screen':
            value = rate(codepoints(txt), b.end_ms - b.start_ms)
            max_screen = max(max_screen, ceil_fraction(value))
            if value > policy.pacing.screen_codepoints_per_minute:
                add('pacing', 'DIR_SCREEN_RATE_EXCEEDED', bid, 'Declared displayed text exceeds the approved reading-rate guardrail.')
        else:
            value = Fraction(0)
            if b.end_ms - b.start_ms > policy.pacing.max_pause_ms:
                add('pacing', 'DIR_PAUSE_TOO_LONG', bid, 'Explicit pause duration exceeds the operator budget.')
        rates[bid] = value
    peak_screen_rate = peak_speech_rate = 0
    for sid, s in sorted(scenes.items()):
        events = by_scene[sid]; cursor = 0
        for a, z, active in windows(events):
            window_count += 1
            if a > cursor and a - cursor > policy.pacing.max_unmotivated_gap_ms:
                add('pacing', 'DIR_UNMOTIVATED_GAP', sid, 'Unaccounted time is not a reviewed pause or storytelling beat.')
            if not active and z - a > policy.pacing.max_unmotivated_gap_ms:
                add('pacing', 'DIR_UNMOTIVATED_GAP', sid, 'A silent hole cannot be averaged away by other scene activity.')
            speech = [i for i in active if beats[i].channel in ('narration', 'dialogue')]
            paused = [i for i in active if beats[i].channel == 'pause']
            peak_speakers = max(peak_speakers, len(speech))
            if len(speech) > policy.pacing.max_concurrent_speech:
                add('pacing', 'DIR_OVERLAPPING_SPEECH', sid, 'Overlapping spoken beats exceed the approved concurrency.')
            speech_rate = sum((rates[i] for i in speech), Fraction(0))
            peak_speech_rate = max(peak_speech_rate, ceil_fraction(speech_rate))
            if speech_rate > policy.pacing.speech_codepoints_per_minute:
                add('pacing', 'DIR_CONCURRENT_SPEECH_RATE', sid, 'Overlapping speech exceeds the combined rate guardrail.')
            if speech and paused:
                add('pacing', 'DIR_PAUSE_OCCUPIED_BY_SPEECH', sid, 'A promised reflection pause cannot simultaneously contain narration.')
            value = sum((rates[i] for i in active if beats[i].channel == 'on_screen'), Fraction(0))
            peak_screen_rate = max(peak_screen_rate, ceil_fraction(value))
            if value > policy.pacing.screen_codepoints_per_minute:
                add('pacing', 'DIR_CONCURRENT_SCREEN_RATE', sid, 'Simultaneous text streams exceed the combined guardrail.')
            cursor = z
        if s.duration_ms - cursor > policy.pacing.max_unmotivated_gap_ms:
            add('pacing', 'DIR_UNMOTIVATED_GAP', sid, 'Scene tail is not covered by an explicit reviewed beat.')
    voices = defaultdict(set)
    for bid in valid:
        b = beats[bid]
        if b.channel in ('narration', 'dialogue'): voices[b.speaker_id].add(b.voice_id)
    for speaker, vv in voices.items():
        if len(vv) > 1: add('script', 'DIR_SPEAKER_VOICE_DRIFT', speaker, 'One speaker changes voice identity without a distinct declared speaker.')
    transitions = defaultdict(list)
    for t in request.transitions:
        transitions[t.from_scene_id, t.to_scene_id].append(t)
        if t.from_scene_id not in scenes or t.to_scene_id not in scenes or not set(t.claim_ids) <= set(claims):
            add('narrative', 'DIR_TRANSITION_REFERENCE', t.transition_id, 'Transition references must resolve.')
    for edge, tt in transitions.items():
        if len(tt) > 1: add('narrative', 'DIR_DUPLICATE_TRANSITION', tt[0].transition_id, 'Duplicate transitions cannot manufacture bridge coverage.')
    terms = {t.term_id: t for t in policy.terms}; introductions = defaultdict(list)
    for t in request.term_introductions:
        if t.term_id not in terms or t.beat_id not in valid:
            add('script', 'DIR_TERM_INTRO_REFERENCE', t.introduction_id, 'Term introductions need known terms and inspected beats.'); continue
        if beats[t.beat_id].role not in TEACHING + ('orientation',) or not any(contains_term(texts[t.beat_id] + '\n' + spoken.get(t.beat_id, ''), form) for form in terms[t.term_id].forms):
            add('script', 'DIR_TERM_INTRO_NOT_EXPLANATORY', t.introduction_id, 'An introduction must contain the term in a reviewed explanatory beat.'); continue
        introductions[t.term_id].append(t.beat_id)
    mapping = {f.claim_id: f for f in request.fidelity}; mapped_facets = defaultdict(set)
    if set(mapping) != set(claims): add('fidelity', 'DIR_FIDELITY_SCOPE_MISMATCH', 'director-scope', 'Every output claim needs an explicit source-transformation mapping.')
    for f in policy.facets:
        if not set(f.citation_ids) <= set(citations): add('fidelity', 'DIR_FACET_SOURCE_MISSING', f.facet_id, 'Operator-required source anchors are absent.')
    def visible_near(witness_id, primary, primary_claim):
        if witness_id == primary_claim: return False
        a, b = claims.get(witness_id), claims.get(primary_claim)
        if not a or not b: return False
        if a.output_id == b.output_id and max(a.start, b.start) < min(a.end, b.end): return False
        return any(w.scene_id == primary.scene_id and w.start_ms <= primary.start_ms and
                   (w.end_ms > primary.start_ms or primary.start_ms - w.end_ms <= policy.pacing.qualification_window_ms)
                   for w in occurrences.get(witness_id, ()))
    for f in request.fidelity:
        c = claims.get(f.claim_id)
        if c is None or not set(f.citation_ids) <= set(citations) or not set(f.facet_ids) <= set(facets):
            add('fidelity', 'DIR_FIDELITY_REFERENCE', f.mapping_id, 'Claim, source and facet references must resolve.'); continue
        if set(f.citation_ids) != set(c.citation_ids):
            add('fidelity', 'DIR_FIDELITY_CITATION_MISMATCH', f.mapping_id, 'An unrelated citation cannot be substituted during transformation.')
        if f.mode == 'question' and c.kind != 'QUESTION' or f.mode == 'instruction' and c.kind != 'INSTRUCTION':
            add('fidelity', 'DIR_NONFACT_LABEL_BYPASS', f.mapping_id, 'A non-factual label cannot hide a factual claim.')
        if f.mode not in ('question', 'instruction') and (not f.facet_ids or not f.citation_ids):
            add('fidelity', 'DIR_FACT_WITHOUT_FACET', f.mapping_id, 'A source-derived or creative explanation still needs its reviewed conceptual anchor.')
        if f.mode == 'quote' and (len(f.citation_ids) != 1 or c.text != citations[f.citation_ids[0]].quote):
            add('fidelity', 'DIR_QUOTE_CHANGED', f.mapping_id, 'Quotation text must exactly match its cited source span.')
        needed = set()
        for fid in f.facet_ids:
            spec = facets[fid]; needed.update(spec.condition_ids)
            if f.mode not in spec.allowed_modes or not set(spec.citation_ids) <= set(f.citation_ids):
                add('fidelity', 'DIR_FACET_TRANSFORMATION_INVALID', f.mapping_id, 'The transformation mode and evidence must satisfy the operator-required facet.'); continue
            if f.mode not in ('question', 'instruction', 'analogy', 'hypothetical'):
                mapped_facets[f.claim_id].add(fid)
        if {w.condition_id for w in f.conditions} != needed:
            add('fidelity', 'DIR_CONDITION_COVERAGE', f.mapping_id, 'Required source conditions may not be dropped or replaced.')
        for b in occurrences.get(f.claim_id, ()):
            for w in f.conditions:
                if not visible_near(w.claim_id, b, f.claim_id):
                    add('fidelity', 'DIR_CONDITION_NOT_VISIBLE', f.mapping_id, 'Each presentation needs a separate, local, reviewed condition witness.')
            if f.mode in ('analogy', 'hypothetical'):
                if not f.disclosure_claim_ids or any(not visible_near(cid, b, f.claim_id) for cid in f.disclosure_claim_ids):
                    add('fidelity', 'DIR_CREATIVE_DISCLOSURE_MISSING', f.mapping_id, 'An analogy or hypothetical needs an explicit nearby nonliteral disclosure.')
        if any(cid not in claims for cid in f.disclosure_claim_ids):
            add('fidelity', 'DIR_DISCLOSURE_REFERENCE', f.mapping_id, 'Disclosure text must resolve to inspected output bytes.')
    route_count = 0; used_edges = set(); peak_route_duration = 0
    for route in sorted(request.routes, key=lambda x: x.route_id):
        spec = route_specs.get(route.route_id)
        if not spec or set(route.scene_ids) != set(spec.scene_ids) or not set(route.scene_ids) <= set(scenes):
            add('narrative', 'DIR_ROUTE_MEMBERSHIP', route.route_id, 'A branch must include exactly its approved scenes.'); continue
        route_count += 1; offsets = {}; cursor = 0
        for sid in route.scene_ids: offsets[sid] = cursor; cursor += scenes[sid].duration_ms
        peak_route_duration = max(peak_route_duration, cursor)
        if cursor > spec.max_duration_ms: add('pacing', 'DIR_ROUTE_DURATION', route.route_id, 'Total route duration exceeds its budget.')
        ordered = sorted((b for sid in route.scene_ids for b in by_scene[sid]), key=lambda b: (offsets[b.scene_id] + b.start_ms, b.beat_id))
        content = [b for b in ordered if b.channel != 'pause']
        if not content: continue
        times = {b.beat_id: (offsets[b.scene_id] + b.start_ms, offsets[b.scene_id] + b.end_ms) for b in ordered}
        if content[0].role not in spec.opening_roles or content[-1].role not in spec.closing_roles:
            add('narrative', 'DIR_ROUTE_ARC_BOUNDARY', route.route_id, 'Every route needs its approved opening and closing roles.')
        for sid in route.scene_ids:
            for prior in scenes[sid].parent_scene_ids:
                if prior not in offsets or offsets[prior] + scenes[prior].duration_ms > offsets[sid]:
                    add('narrative', 'DIR_PARENT_NOT_READY', sid, 'A dependent scene appears before a required prior scene on this route.')
        for left, right in zip(route.scene_ids, route.scene_ids[1:]):
            edge = left, right; used_edges.add(edge); tt = transitions.get(edge, ())
            first = sorted((b for b in by_scene[right] if b.channel != 'pause'), key=lambda x: (x.start_ms, x.beat_id))
            if len(tt) != 1 or not first or first[0].role != 'transition' or not set(tt[0].claim_ids) <= set(first[0].claim_ids):
                add('narrative', 'DIR_TRANSITION_NOT_PRESENTED', route.route_id, 'Adjacent scenes need an inspected contextual bridge at the start of the destination.')
        taught = {}; seen_text = defaultdict(list)
        for b in content:
            start, end = times[b.beat_id]
            if b.role in TEACHING:
                for oid in b.objective_ids: taught[oid] = min(taught.get(oid, 10**18), end)
            if b.role == 'recap' and any(oid not in taught or taught[oid] > start for oid in b.objective_ids):
                add('narrative', 'DIR_RECAP_BEFORE_TEACHING', b.beat_id, 'A recap cannot replace or precede its explanatory teaching.')
            fp = identity(texts[b.beat_id])
            previous = [p for p in seen_text[fp] if times[p][1] <= start]
            # Simultaneous narration/caption mirrors are a distinct medium, not extra teaching.
            any_prior_same_channel = [p for p in seen_text[fp] if beats[p].channel == b.channel]
            if any_prior_same_channel and (b.role not in REPEAT_ROLES or not any(p in previous for p in b.repeat_of)):
                add('script', 'DIR_UNJUSTIFIED_REPETITION', b.beat_id, 'Repeated text needs an earlier explicit recap/retrieval/feedback purpose, not a new ID.')
            if b.repeat_of and (b.role not in REPEAT_ROLES or any(p not in times or times[p][1] > start for p in b.repeat_of)):
                add('script', 'DIR_REPEAT_TARGET_INVALID', b.beat_id, 'A repetition reference must be earlier on this same route and purpose-appropriate.')
            seen_text[fp].append(b.beat_id)
        if not set(spec.objective_ids) <= set(taught):
            add('narrative', 'DIR_ROUTE_OBJECTIVE_UNEXPLAINED', route.route_id, 'Hooks, transitions and topic mentions cannot replace explanatory beats.')
        for p in request.promises:
            if p.setup_beat_id not in times: continue
            setup = beats[p.setup_beat_id]; possible = [beats[x] for x in p.payoff_beat_ids if x in times and x in valid]
            if setup.role not in ('hook', 'problem') or not any(b.role in TEACHING and times[b.beat_id][0] >= times[setup.beat_id][1] and identity(texts[b.beat_id]) != identity(texts[setup.beat_id]) for b in possible):
                add('narrative', 'DIR_PROMISE_WITHOUT_PAYOFF', p.promise_id, 'A hook must receive a later explanatory payoff on every route where it appears.')
        for term in policy.terms:
            if term.assumed_known: continue
            intros = [x for x in introductions[term.term_id] if x in times]
            for b in content:
                if any(contains_term(texts[b.beat_id] + '\n' + spoken.get(b.beat_id, ''), f) for f in term.forms):
                    if b.beat_id not in intros and not any(times[x][1] <= times[b.beat_id][0] for x in intros):
                        add('script', 'DIR_TERM_USED_BEFORE_EXPLANATION', b.beat_id, 'The declared technical term is not explained before use on this route.')
        for t in policy.timing_constraints:
            if t.before_beat_id not in times and t.after_beat_id not in times: continue
            if t.before_beat_id not in times or t.after_beat_id not in times:
                add('pacing', 'DIR_TIMING_ROUTE_MISSING_ENDPOINT', t.constraint_id, 'A route cannot evade a required timing constraint by dropping one endpoint.'); continue
            gap = times[t.after_beat_id][0] - times[t.before_beat_id][1]
            if not t.minimum_gap_ms <= gap <= t.maximum_gap_ms:
                add('pacing', 'DIR_TIMING_CONSTRAINT', t.constraint_id, 'The required pause/response/ordering interval is violated.')
        explained = set()
        for b in content:
            if b.role in TEACHING:
                for cid in b.claim_ids: explained.update(mapped_facets[cid])
                for form in request.spoken_forms:
                    if form.beat_id == b.beat_id:
                        for cid in form.claim_ids: explained.update(mapped_facets[cid])
        if not set(spec.facet_ids) <= explained:
            add('fidelity', 'DIR_ROUTE_SOURCE_FACET_MISSING', route.route_id, 'Required source meaning needs a factual explanation, not just a question, analogy or mention.')
    for t in request.transitions:
        if (t.from_scene_id, t.to_scene_id) not in used_edges:
            add('narrative', 'DIR_UNUSED_TRANSITION', t.transition_id, 'An unused bridge cannot manufacture route coverage.')
    for p in request.promises:
        if p.setup_beat_id not in valid or not set(p.payoff_beat_ids) <= valid:
            add('narrative', 'DIR_PROMISE_REFERENCE', p.promise_id, 'Promise setup and payoffs must be inspected beats.')
    for t in policy.timing_constraints:
        if t.before_beat_id not in valid or t.after_beat_id not in valid:
            add('pacing', 'DIR_TIMING_ENDPOINT_MISSING', t.constraint_id, 'Operator-required timing endpoints cannot disappear from all routes.')
    evidence = digest(dict(source=source.to_dict(), reviews=[asdict(x) for x in sorted(reviews, key=lambda x:x.review_id)], trust=verifier.configuration_digest))
    inspected = tuple(sorted(set(source.grounding.inspected_artifact_ids) | set(source.provenance.inspected_artifact_ids)))
    measurements = {
        'narrative': (('routes_checked', route_count), ('declared_scenes', len(scenes)), ('declared_promises', len(request.promises))),
        'script': (('inspected_beats', len(valid)), ('declared_terms', len(terms))),
        'pacing': (('plan_windows', window_count), ('max_speech_codepoints_per_minute_ceil', max_speech),
                   ('max_screen_codepoints_per_minute_ceil', max_screen), ('peak_concurrent_screen_codepoints_per_minute_ceil', peak_screen_rate),
                   ('peak_concurrent_speech', peak_speakers), ('peak_concurrent_speech_codepoints_per_minute_ceil', peak_speech_rate), ('max_route_duration_ms', peak_route_duration)),
        'fidelity': (('declared_mappings', len(mapping)), ('required_facets', len(facets))),
    }
    def report(k):
        fs = tuple(sorted(set(groups['common'] + groups[k]), key=lambda x:(x.subject_id,x.code,x.severity,x.detail)))
        return Report(TASKS[k], rd, pd, evidence, as_of, fs, measurements[k], inspected, LIMITATIONS)
    return DirectorResult(source, *(report(k) for k in AREAS), af, sf)


def verify_reports(actual, *args, **kwargs):
    expected = evaluate(*args, **kwargs)
    if type(actual) is not DirectorResult or actual != expected: raise ContractError('DIR_STALE_OR_EDITED_REPORT')
    return actual


def evaluate_narrative(*args, **kwargs): return evaluate(*args, **kwargs).narrative

def evaluate_script(*args, **kwargs): return evaluate(*args, **kwargs).script

def evaluate_pacing(*args, **kwargs): return evaluate(*args, **kwargs).pacing

def evaluate_source_fidelity(*args, **kwargs): return evaluate(*args, **kwargs).fidelity
