"""Batch-001 reconciliation: two named APIs, one validated TTS handoff.

The 144 branch remains the default. The 204 branch is genuinely executable via
compat204; no function signature, language policy or parser fallback is guessed.
Both callers supply original inputs, and preparations are recomputed before use.
"""
from dataclasses import replace
from .common import fingerprint
from .speech_contract import SpeechPlan, SpeechSegment, SpeechSpan


def from_v144(utterances, **options):
    from .preparation import prepare_narration, validate_preparation
    prep=prepare_narration(utterances,**options)
    validate_preparation(prep,utterances,**options)
    output=[]
    for segment,spoken in zip(prep.segmentation.segments,prep.spoken_segments,strict=True):
        parts=[];cursor=segment.start_char
        def plain(a,b):
            if a<b:
                raw=segment.display_text[a-segment.start_char:b-segment.start_char]
                parts.append(SpeechSpan(a,b,raw,raw,segment.language,fingerprint(('literal/1',raw)),segment.evidence_ids))
        for reading in spoken.readings:
            plain(cursor,reading.start);r=reading.reading
            parts.append(SpeechSpan(reading.start,reading.end,reading.original,r.spoken,r.language,r.fingerprint(),
                tuple(dict.fromkeys((*segment.evidence_ids,*r.source_refs))),r.kind,r.phonemes,r.alphabet));cursor=reading.end
        plain(cursor,segment.end_char)
        output.append(SpeechSegment(segment.segment_id,segment.utterance_id,segment.utterance_fingerprint,segment.script_fingerprint,
            segment.scene_id,segment.voice_id,segment.language,segment.start_char,segment.end_char,segment.display_text,tuple(parts),
            segment.objective_ids,segment.pause_after_ms,segment.pause_refs))
        if output[-1].spoken_text!=spoken.synthesis_text:raise ValueError('RECONCILIATION_SPEECH_MISMATCH')
    return SpeechPlan('batch001-144',prep.fingerprint(),fingerprint(('language-policy','inherit/1')),tuple(output),prep.review_reasons)


def from_v204(document, lexicon, policy=None):
    from .compat204.voiceover_preparation import prepare_voiceover,verify_preparation
    from .compat204.narration_segmentation import SegmentationPolicy
    prep=prepare_voiceover(document,lexicon,policy or SegmentationPolicy());verify_preparation(prep,document,lexicon)
    source={x.block_id:x for x in document.blocks};output=[]
    for s in prep.segments:
        b=source[s.block_id]
        spans=tuple(SpeechSpan(x.start_char,x.end_char,x.original_text,x.spoken_text,s.language,x.decision_identity,
            x.source_refs,x.kind,x.phoneme or None,x.alphabet or None) for x in s.pieces)
        output.append(SpeechSegment(s.segment_id,s.block_id,b.upstream_fingerprint,document.script_fingerprint,s.scene_id,s.voice_id,
            s.language,s.start_char,s.end_char,s.original_text,spans,s.objective_ids))
        if output[-1].spoken_text!=s.spoken_text:raise ValueError('RECONCILIATION_SPEECH_MISMATCH')
    reviews=tuple(dict.fromkeys(f'{x.code}:{x.block_id}:{x.start}:{x.end}' for x in prep.issues))
    return SpeechPlan('batch001-204',prep.identity,fingerprint(('language-policy','inherit/1')),tuple(output),reviews)
