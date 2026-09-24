"""H5-002/003: exact byte bundle and existing source/clock/caption replay.

The index is integrity only. Authenticity comes from pipeline_evidence and the
caller-supplied trust policy; this module never upgrades acoustic acceptance.
"""
from __future__ import annotations
from dataclasses import asdict
import hashlib
from .common import AudioError, fingerprint, strict_json
from .acoustic_contract import canonical, fields
from .pipeline_contract import BOUNDARIES, OPERATION, SCOPE, PipelineLimits, validate_request

NAMES=frozenset({'master.wav','source.wav','SOURCE_SYNC.json','MIX_CLOCK.json',
    'MIX_RECEIPT.json','captions.vtt','captions.srt','ENGINE_EVIDENCE.json','PIPELINE_SUMMARY.json'})


def index_files(files,limits):
    if type(limits)is not PipelineLimits or type(files)is not dict or set(files)!=NAMES:
        raise AudioError('PIPELINE_FILE_SET')
    total=0;index={}
    for n,b in sorted(files.items()):
        if type(b)is not bytes or not 0<len(b)<=limits.max_file_bytes:
            raise AudioError('PIPELINE_FILE_BUDGET')
        total+=len(b)
        index[n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    if total>limits.max_bundle_bytes:raise AudioError('PIPELINE_TOTAL_BUDGET')
    return index


def validate_bundle(files,request,profile):
    from .qa_source import restore_sync
    from .mix_pipeline import MixedAudio,verify_mixed_source,export_mixed_captions
    from .timed_espeak_provider import words_from_marks,lexical_ranges
    plan=validate_request(request)
    limits=PipelineLimits(**request['limits']);index=index_files(files,limits)
    sync=restore_sync(strict_json(files['SOURCE_SYNC.json'].decode()),files['source.wav'])
    mixed=MixedAudio(files['master.wav'],files['MIX_CLOCK.json'].decode(),files['MIX_RECEIPT.json'].decode()).validate()
    verify_mixed_source(mixed,sync)
    if sync.plan!=plan or sync.plan.fingerprint()!=request['plan_fingerprint']:
        raise AudioError('PIPELINE_SOURCE_BINDING')
    if sync.selection.catalog_fingerprint!=profile['catalog_fingerprint']:
        raise AudioError('PIPELINE_CATALOG_BINDING')
    if any(a.request.voice.provider_id!='espeak-timed-local' or
        a.request.voice.runtime_fingerprint!=profile['provider_runtime_fingerprint'] for a in sync.assets):
        raise AudioError('PIPELINE_VOICE_BINDING')
    if sync.timeline.total_samples>limits.max_audio_seconds*sync.timeline.sample_rate:
        raise AudioError('PIPELINE_AUDIO_BUDGET')
    receipt=mixed.receipt()
    if receipt['music']['stems'] or receipt['sfx']['stems']:
        # Existing MIX receipts use lists for stems; the lane is deliberately dry.
        raise AudioError('PIPELINE_UNDECLARED_STEMS')
    if fingerprint(receipt['meter_identity'])!=profile['meter_runtime_fingerprint'] or receipt['numpy_version']!=profile['numpy_version']:
        raise AudioError('PIPELINE_METER_BINDING')
    for ext in ('vtt','srt'):
        if files['captions.'+ext]!=export_mixed_captions(mixed,ext).encode():
            raise AudioError('PIPELINE_CAPTION_CHANGED')
    evidence=strict_json(files['ENGINE_EVIDENCE.json'].decode())
    if type(evidence)is not list or len(evidence)!=len(sync.alignments):
        raise AudioError('PIPELINE_ENGINE_EVIDENCE')
    for e,a,asset in zip(evidence,sync.alignments,sync.assets):
        if fingerprint(e)!=a.event_fingerprint or e.get('pcm_sha256')!=asset.provider_pcm_sha256:
            raise AudioError('PIPELINE_ENGINE_BINDING')
        words=words_from_marks(asset.request.segment,e,lexical_ranges(asset.request.segment.spoken_text),
            a.provider_samples,a.sample_rate)
        if words!=a.words:raise AudioError('PIPELINE_WORD_REPLAY_CHANGED')
    summary=strict_json(files['PIPELINE_SUMMARY.json'].decode())
    expected={'schema_version':'bie.audio.local-pipeline-summary/1','operation':OPERATION,'scope':SCOPE,
        'request_fingerprint':request['fingerprint'],'plan_fingerprint':plan.fingerprint(),
        'segments':len(sync.assets),'provider_calls':len(sync.assets),
        'mix_stems':len(receipt['music']['stems'])+len(receipt['sfx']['stems']),
        'mix_stems_fingerprint':request['mix_stems_fingerprint'],
        'timing_replay_calls':len(sync.assets),'internal_cache_hits':list(sync.cache_hits),
        'source_sync_fingerprint':fingerprint(sync.receipt()),'mix_fingerprint':receipt['fingerprint'],
        'technical_review_required':True,**BOUNDARIES}
    if summary!=expected or any(sync.cache_hits):
        raise AudioError('PIPELINE_SUMMARY_BINDING')
    return {'index':index,'summary':summary,'sync':sync,'mixed':mixed}
