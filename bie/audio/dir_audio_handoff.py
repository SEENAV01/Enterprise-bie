"""H10-001: exact canonical DIR narration -> AUDIO identity handoff.

This adapter validates that AUDIO's immutable SpeechPlan is still exactly bound to
canonical DIR SpeechUtterance records. It does not rewrite narration, infer missing
provenance, or claim acoustic/pronunciation acceptance.
"""
from __future__ import annotations
from dataclasses import asdict
from .common import AudioError, fingerprint
from .speech_contract import SpeechPlan

SCHEMA='bie.audio.dir-audio-handoff/1'


def _source_refs(segments):
    out=[]
    for s in segments:
        for span in s.spans:
            for ref in span.source_refs:
                if ref not in out: out.append(ref)
    return tuple(out)


def bind_dir_utterances(utterances, plan: SpeechPlan):
    """Fail closed unless every DIR utterance and AUDIO segment binding is exact."""
    try:
        from bie.director.speech_timing import SpeechUtterance
    except Exception as exc:  # dependency snapshot/canonical repo is mandatory
        raise AudioError('DIR_AUDIO_CANONICAL_DEPENDENCY_MISSING') from exc
    if type(plan) is not SpeechPlan: raise AudioError('DIR_AUDIO_PLAN_REQUIRED')
    plan.require_ready()
    if type(utterances) is not tuple or not utterances or any(type(u) is not SpeechUtterance for u in utterances):
        raise AudioError('DIR_AUDIO_UTTERANCES_REQUIRED')
    by={}
    for s in plan.segments: by.setdefault(s.utterance_id,[]).append(s)
    if set(by)!={u.utterance_id for u in utterances} or len(utterances)!=len(by):
        raise AudioError('DIR_AUDIO_COVERAGE')
    rows=[]
    for u in utterances:
        if u.review_reasons: raise AudioError('DIR_AUDIO_UPSTREAM_REVIEW')
        segs=by[u.utterance_id]
        if segs[0].start!=0 or segs[-1].end!=len(u.text): raise AudioError('DIR_AUDIO_SOURCE_RANGE')
        if ''.join(s.display_text for s in segs)!=u.text: raise AudioError('DIR_AUDIO_TEXT_MISMATCH')
        binding=(u.fingerprint(),u.script_fingerprint,u.scene_id,u.voice_id,u.language)
        for s in segs:
            if (s.utterance_fingerprint,s.script_fingerprint,s.scene_id,s.persona_id,s.language)!=binding:
                raise AudioError('DIR_AUDIO_BINDING_MISMATCH')
        if u.segment_id!=u.utterance_id: raise AudioError('DIR_AUDIO_SEGMENT_ID_MISMATCH')
        if set(_source_refs(segs))!=set(u.evidence_ids): raise AudioError('DIR_AUDIO_SOURCE_REFS_MISMATCH')
        objectives=[]
        for s in segs:
            for x in s.objective_ids:
                if x not in objectives: objectives.append(x)
        if set(objectives)!=set(u.objective_ids): raise AudioError('DIR_AUDIO_OBJECTIVES_MISMATCH')
        rows.append({'utterance_id':u.utterance_id,'utterance_fingerprint':u.fingerprint(),
            'script_fingerprint':u.script_fingerprint,'scene_id':u.scene_id,'language':u.language,
            'voice_id':u.voice_id,'segment_ids':[s.segment_id for s in segs],
            'source_refs':list(_source_refs(segs)),'objective_ids':objectives,
            'text_sha256':__import__('hashlib').sha256(u.text.encode()).hexdigest()})
    receipt={'schema_version':SCHEMA,'speech_plan_fingerprint':plan.fingerprint(),
        'utterances':rows,'source_text_mutated':False,'product_accepted':False}
    receipt['fingerprint']=fingerprint(receipt)
    return receipt


def validate_dir_audio_handoff(receipt, utterances, plan):
    expected=bind_dir_utterances(utterances,plan)
    if receipt!=expected: raise AudioError('DIR_AUDIO_RECEIPT_MISMATCH')
    return receipt
