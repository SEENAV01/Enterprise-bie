"""H5-001: bounded local TTS/SYNC/narration-MIX request over existing contracts.

AUDIO-AUDIT-001-F03 engineering extension, not a new original roadmap task.
No paid provider, arbitrary command, network endpoint or remote voice fallback.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
import uuid
from .common import AudioError, fingerprint, integer, text, digest
from .acoustic_contract import canonical, fields, plain
from .durable_contract import DurablePolicy, canonical_api_identity
from .speech_contract import SpeechPlan
from .qa_source import decode
from .pipeline_stems import canonicalize_stem_specs, stems_fingerprint

OPERATION = 'AUDIO_LOCAL_TTS_SYNC_DRY_MIX_V1'
SCOPE = 'ISOLATED_LOCAL_TECHNICAL_TTS_SYNC_NARRATION_MIX'
BOUNDARIES = {'product_accepted': False, 'pronunciation_verified': False,
    'independent_alignment_verified': False, 'real_video_render_verified': False,
    'live_neural_provider_verified': False}

@dataclass(frozen=True)
class PipelineLimits:
    max_segments: int = 8
    max_spoken_chars: int = 6000
    max_audio_seconds: int = 180
    deadline_seconds: int = 180
    max_file_bytes: int = 32_000_000
    max_bundle_bytes: int = 64_000_000
    def __post_init__(self):
        for name, low, high in (('max_segments',1,32),('max_spoken_chars',1,12000),
            ('max_audio_seconds',1,300),('deadline_seconds',1,300),
            ('max_file_bytes',4096,64_000_000),('max_bundle_bytes',8192,128_000_000)):
            integer(getattr(self,name),name,low,high)
        if self.max_file_bytes > self.max_bundle_bytes:
            raise AudioError('PIPELINE_BUNDLE_POLICY')


def prepare_document(source, profile='batch001-144'):
    """Use the actual existing preparation functions; source is never rewritten."""
    from .preparation_bridge import from_v144, from_v204
    if profile == 'batch001-144':
        from scripts.audio_prepare import read_request
        utterances, options = read_request(source)
        plan = from_v144(utterances, **options)
    elif profile == 'batch001-204':
        from .compat204.contracts import document_from_dict
        from .compat204.pronunciation_lexicon import lexicon_from_dict
        from .compat204.narration_segmentation import SegmentationPolicy
        fields(source, ('document','lexicon','policy'))
        plan = from_v204(document_from_dict(source['document']),
            lexicon_from_dict(source['lexicon']), SegmentationPolicy(**source['policy']))
    else:
        raise AudioError('PIPELINE_PREPARATION_PROFILE')
    plan.require_ready()
    return plan


def source_refs(plan):
    return sorted({ref for seg in plan.segments for span in seg.spans for ref in span.source_refs})


def build_request(source, *, profile_fingerprint, run_id, job_id, revision, key_id,
                  preparation_profile='batch001-144', limits=PipelineLimits(),
                  durable_policy=DurablePolicy(), mix_stems=None):
    if type(limits) is not PipelineLimits or type(durable_policy) is not DurablePolicy:
        raise AudioError('PIPELINE_POLICY_TYPE')
    source = plain(source)
    mix_stems = canonicalize_stem_specs([] if mix_stems is None else mix_stems)
    if len(canonical(source)) > 2_000_000:
        raise AudioError('PIPELINE_SOURCE_BUDGET')
    plan = prepare_document(source, preparation_profile)
    if len(plan.segments) > limits.max_segments or sum(len(s.spoken_text) for s in plan.segments) > limits.max_spoken_chars:
        raise AudioError('PIPELINE_SEGMENT_BUDGET')
    if not source_refs(plan):
        raise AudioError('PIPELINE_PROVENANCE_REQUIRED')
    try:
        if type(run_id) is not str or str(uuid.UUID(run_id)) != run_id: raise ValueError()
    except (ValueError, TypeError, AttributeError) as exc:
        raise AudioError('PIPELINE_RUN_UUID') from exc
    for v,n,limit in ((job_id,'job',256),(revision,'revision',120),(key_id,'key',256)):
        text(v,n,limit)
    digest(profile_fingerprint)
    if durable_policy.max_artifact_bytes < limits.max_file_bytes:
        raise AudioError('PIPELINE_STORAGE_FILE_BUDGET')
    value = {'schema_version':'bie.audio.pipeline-request/1','operation':OPERATION,
        'scope':SCOPE, 'run_id':run_id, 'job_id':job_id, 'revision':revision,'key_id':key_id,
        'source':source,'preparation_profile':preparation_profile,'plan':plain(asdict(plan)),
        'plan_fingerprint':plan.fingerprint(),'source_refs':source_refs(plan),
        'profile_fingerprint':profile_fingerprint,'limits':asdict(limits),
        'durable_policy':asdict(durable_policy),'canonical_api_identity':canonical_api_identity(),
        'mix_stems':mix_stems,'mix_stems_fingerprint':stems_fingerprint(mix_stems),
        **BOUNDARIES}
    value['fingerprint'] = fingerprint(value)
    return value


def validate_request(request):
    fields(request, ('schema_version','operation','scope','run_id','job_id','revision','key_id',
        'source','preparation_profile','plan','plan_fingerprint','source_refs',
        'profile_fingerprint','limits','durable_policy','canonical_api_identity','mix_stems','mix_stems_fingerprint',
        *BOUNDARIES,'fingerprint'), 'PIPELINE_REQUEST_FIELDS')
    expected = build_request(request['source'], profile_fingerprint=request['profile_fingerprint'],
        run_id=request['run_id'], job_id=request['job_id'], revision=request['revision'],
        key_id=request['key_id'], preparation_profile=request['preparation_profile'],
        limits=PipelineLimits(**request['limits']), durable_policy=DurablePolicy(**request['durable_policy']), mix_stems=request['mix_stems'])
    if canonical(request) != canonical(expected):
        raise AudioError('PIPELINE_REQUEST_DRIFT')
    return decode(SpeechPlan, request['plan'])


def request_key(request):
    validate_request(request)
    return 'AUDIO:LOCAL-PIPELINE:' + fingerprint({k:request[k] for k in ('run_id','job_id','revision')})
